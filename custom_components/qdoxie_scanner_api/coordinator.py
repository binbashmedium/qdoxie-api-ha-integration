"""Coordinator + sync worker for Doxie -> Paperless-ngx."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import timedelta
import logging
import os
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_CONSUME_DIR,
    CONF_DELETE_ON_SUCCESS,
    CONF_DOXIE_HOST,
    CONF_DOXIE_PASSWORD,
    CONF_DOXIE_PORT,
    CONF_INTERVAL_SECONDS,
    CONF_MODE,
    CONF_PAPERLESS_PASSWORD,
    CONF_PAPERLESS_TOKEN,
    CONF_PAPERLESS_URL,
    CONF_PAPERLESS_USERNAME,
    CONF_WAIT_FOR_TASK,
    DEFAULT_INTERVAL_SECONDS,
    MODE_CONSUME_DIR,
    MODE_PAPERLESS,
)
from .doxie_api import DoxieClient
from .paperless_api import PaperlessClient

_LOGGER = logging.getLogger(__name__)


class DoxiePaperlessCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry_id: str, config: dict[str, Any]) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.config = config

        interval = int(config.get(CONF_INTERVAL_SECONDS, DEFAULT_INTERVAL_SECONDS))

        super().__init__(
            hass,
            _LOGGER,
            name=f"doxie_paperless_{entry_id}",
            update_interval=timedelta(seconds=interval),
        )

        session = async_get_clientsession(hass)
        self.doxie = DoxieClient(
            session,
            host=config[CONF_DOXIE_HOST],
            port=int(config.get(CONF_DOXIE_PORT, 80)),
            password=config.get(CONF_DOXIE_PASSWORD) or None,
        )

        self.paperless: PaperlessClient | None = None
        if config.get(CONF_PAPERLESS_URL):
            self.paperless = PaperlessClient(
                session,
                base_url=str(config[CONF_PAPERLESS_URL]),
                token=config.get(CONF_PAPERLESS_TOKEN) or None,
                username=config.get(CONF_PAPERLESS_USERNAME) or None,
                password=config.get(CONF_PAPERLESS_PASSWORD) or None,
            )

        self._last_recent_path: str | None = None
        self._sync_lock = asyncio.Lock()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch status data for sensors."""
        try:
            hello = await self.doxie.hello()
            recent_path = await self.doxie.recent()
            scans = await self.doxie.scans()
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(str(err)) from err

        # Track recent so we can expose it without triggering sync logic from sensors.
        self._last_recent_path = recent_path or self._last_recent_path

        return {
            "hello": asdict(hello),
            "recent_path": recent_path,
            "scan_count": len(scans),
            "scans": [s.path for s in scans],
        }

    async def async_sync_once(self) -> dict[str, Any]:
        """Check for a new scan and process it."""
        async with self._sync_lock:
            result: dict[str, Any] = {
                "changed": False,
                "processed": False,
                "deleted": False,
                "reason": None,
                "scan_path": None,
            }

            try:
                recent_path = await self.doxie.recent()
            except Exception as err:  # noqa: BLE001
                result["reason"] = f"doxie_recent_failed: {err}"
                return result

            if not recent_path:
                result["reason"] = "no_recent_scan"
                return result

            result["scan_path"] = recent_path

            if self._last_recent_path == recent_path:
                result["reason"] = "already_processed_recent"
                return result

            result["changed"] = True

            # Find metadata (modified) from scan list, if available.
            modified: str | None = None
            try:
                scans = await self.doxie.scans()
                for s in scans:
                    if s.path == recent_path:
                        modified = s.modified
                        break
            except Exception:  # best-effort
                pass

            try:
                content = await self.doxie.download_scan(recent_path)
            except Exception as err:  # noqa: BLE001
                result["reason"] = f"download_failed: {err}"
                return result

            filename = os.path.basename(recent_path)
            mode = self.config.get(CONF_MODE, MODE_PAPERLESS)

            try:
                if mode == MODE_CONSUME_DIR:
                    await self._save_to_consume_dir(filename, content)
                else:
                    await self._upload_to_paperless(filename, content, modified)
                result["processed"] = True
            except Exception as err:  # noqa: BLE001
                _LOGGER.exception("Processing failed")
                result["reason"] = f"process_failed: {err}"
                return result

            # Delete on success
            if self.config.get(CONF_DELETE_ON_SUCCESS, True):
                try:
                    await self.doxie.delete_scan(recent_path)
                    result["deleted"] = True
                    self._last_recent_path = recent_path
                except Exception as err:  # noqa: BLE001
                    result["reason"] = f"delete_failed: {err}"
                    # do not update last_recent_path if delete failed
                    return result

            return result

    async def _save_to_consume_dir(self, filename: str, content: bytes) -> None:
        consume_dir = self.config.get(CONF_CONSUME_DIR)
        if not consume_dir:
            raise ValueError("consume_dir not configured")

        path = Path(str(consume_dir))
        if not path.is_absolute():
            path = Path(self.hass.config.path(str(consume_dir)))
        path.mkdir(parents=True, exist_ok=True)

        target = path / filename
        # Avoid overwriting
        if target.exists():
            stem = target.stem
            suffix = target.suffix
            i = 1
            while True:
                alt = path / f"{stem}_{i}{suffix}"
                if not alt.exists():
                    target = alt
                    break
                i += 1

        await self.hass.async_add_executor_job(target.write_bytes, content)

    async def _upload_to_paperless(self, filename: str, content: bytes, modified: str | None) -> None:
        if not self.paperless:
            raise ValueError("paperless_url not configured")

        task_id = await self.paperless.upload_document(
            filename=filename,
            content=content,
            title=filename,
            created=modified,
        )

        if not self.config.get(CONF_WAIT_FOR_TASK, False):
            return

        # Best-effort wait for task completion.
        # We don't assume schema details; just check for status/state in the returned task object.
        for _ in range(30):  # ~30 * 2s = 60s max
            task = await self.paperless.get_task(task_id)
            if task.status:
                status_upper = task.status.upper()
                if status_upper in ("SUCCESS", "FAILURE", "FAILED", "ERROR"):
                    if status_upper != "SUCCESS":
                        raise ValueError(f"Paperless task status={task.status}")
                    return
            await asyncio.sleep(2)
        # If it never reported a terminal status, treat as success-started (per API docs it is async).
        _LOGGER.debug("Paperless task %s did not reach terminal state within timeout", task_id)
