"""Doxie HTTP/JSON API client.

Uses ONLY endpoints documented in the uploaded Doxie API PDF:
- GET /hello.json
- GET /scans.json
- GET /scans/recent.json
- GET /scans{path}
- DELETE /scans{path}
- POST /scans/delete.json
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import BasicAuth, ClientResponseError, ClientSession


@dataclass
class DoxieHello:
    model: str | None = None
    name: str | None = None
    firmware: str | None = None
    firmwareWiFi: str | None = None
    hasPassword: bool | None = None
    MAC: str | None = None
    mode: str | None = None
    network: str | None = None
    ip: str | None = None


@dataclass
class DoxieScan:
    path: str
    size: int | None = None
    modified: str | None = None


class DoxieClient:
    def __init__(self, session: ClientSession, host: str, port: int = 80, password: str | None = None) -> None:
        self._session = session
        self._host = host
        self._port = port
        self._auth = BasicAuth("doxie", password) if password else None

    @property
    def base_url(self) -> str:
        return f"http://{self._host}:{self._port}"

    async def _json(self, method: str, path: str) -> Any:
        url = f"{self.base_url}{path}"
        async with self._session.request(method, url, auth=self._auth) as resp:
            # Doxie uses 204 for "no content".
            if resp.status == 204:
                return None
            resp.raise_for_status()
            return await resp.json(content_type=None)

    async def hello(self) -> DoxieHello:
        data = await self._json("GET", "/hello.json")
        if not isinstance(data, dict):
            return DoxieHello()
        return DoxieHello(**{k: data.get(k) for k in DoxieHello.__annotations__.keys()})

    async def scans(self) -> list[DoxieScan]:
        data = await self._json("GET", "/scans.json")
        if not isinstance(data, list):
            return []
        out: list[DoxieScan] = []
        for item in data:
            if isinstance(item, dict) and "name" in item:
                out.append(DoxieScan(path=str(item["name"]), size=item.get("size"), modified=item.get("modified")))
        return out

    async def recent(self) -> str | None:
        """Returns the last scan path (e.g. /DOXIE/PDF/IMG_0001.PDF) or None."""
        data = await self._json("GET", "/scans/recent.json")
        if data is None:
            return None
        if isinstance(data, dict) and "path" in data:
            return str(data["path"])
        return None

    async def download_scan(self, scan_path: str) -> bytes:
        """Downloads a scan using GET /scans{path}."""
        url = f"{self.base_url}/scans{scan_path}"
        async with self._session.get(url, auth=self._auth) as resp:
            resp.raise_for_status()
            return await resp.read()

    async def delete_scan(self, scan_path: str) -> None:
        """Deletes a scan using DELETE /scans{path}."""
        await self._json("DELETE", f"/scans{scan_path}")

    async def delete_scans(self, scan_paths: list[str]) -> None:
        """Deletes multiple scans using POST /scans/delete.json."""
        if not scan_paths:
            return
        url = f"{self.base_url}/scans/delete.json"
        async with self._session.post(url, json=scan_paths, auth=self._auth) as resp:
            # Doxie returns 204 on success, 403 on error.
            if resp.status == 204:
                return
            resp.raise_for_status()
