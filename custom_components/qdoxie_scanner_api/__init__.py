"""Doxie -> Paperless-ngx integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS, SERVICE_SYNC_NOW, CONF_INTERVAL_SECONDS, DEFAULT_INTERVAL_SECONDS
from .coordinator import DoxiePaperlessCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up integration (YAML not supported; config flow only)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = DoxiePaperlessCoordinator(hass, entry.entry_id, {**entry.data, **entry.options})
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async def _handle_sync_now(call: ServiceCall) -> None:
        res = await coordinator.async_sync_once()
        _LOGGER.info("Manual sync result: %s", res)
        # Refresh sensors after manual sync
        await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_SYNC_NOW, _handle_sync_now)

    # Periodic sync worker (independent from coordinator polling for sensors)
    interval = int(({**entry.data, **entry.options}).get(CONF_INTERVAL_SECONDS, DEFAULT_INTERVAL_SECONDS))

    async def _periodic_sync(_now) -> None:
        res = await coordinator.async_sync_once()
        if res.get("changed"):
            _LOGGER.debug("Periodic sync result: %s", res)
        await coordinator.async_request_refresh()

    unsub = async_track_time_interval(hass, _periodic_sync, timedelta(seconds=interval))
    hass.data[DOMAIN][entry.entry_id + "_unsub"] = unsub

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        unsub = hass.data.get(DOMAIN, {}).pop(entry.entry_id + "_unsub", None)
        if unsub:
            unsub()
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        # NOTE: not unregistering service, as HA services are global and we might have multiple entries.
    return unload_ok
