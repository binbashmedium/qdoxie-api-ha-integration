"""Paperless-ngx API client (upload + task status).

Uses ONLY endpoints documented in the official REST API docs:
- POST /api/documents/post_document/
- GET /api/tasks/?task_id={uuid}
- (Auth headers per docs)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from aiohttp import BasicAuth, ClientSession, FormData


@dataclass
class PaperlessTask:
    raw: Any
    status: str | None = None
    document_id: int | None = None


class PaperlessClient:
    def __init__(
        self,
        session: ClientSession,
        base_url: str,
        token: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._basic = BasicAuth(username, password) if (username and password) else None

    def _headers(self) -> dict[str, str]:
        if self._token:
            return {"Authorization": f"Token {self._token}"}
        return {}

    async def upload_document(
        self,
        filename: str,
        content: bytes,
        title: str | None = None,
        created: str | None = None,
    ) -> str:
        """Uploads a document and returns the consumption task UUID (string).

        The API docs state it returns HTTP 200 with the UUID in the response body.
        Some deployments may return JSON; we accept both.
        """
        url = f"{self._base_url}/api/documents/post_document/"
        form = FormData()
        form.add_field("document", content, filename=filename)
        if title:
            form.add_field("title", title)
        if created:
            form.add_field("created", created)

        async with self._session.post(
            url,
            data=form,
            headers=self._headers(),
            auth=self._basic,
        ) as resp:
            resp.raise_for_status()
            # Try JSON first; else treat as plain text.
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "application/json" in ctype:
                data = await resp.json(content_type=None)
                # commonly: {"task_id": "uuid"} or "uuid"; keep flexible.
                if isinstance(data, str):
                    return data
                if isinstance(data, dict):
                    for k in ("task_id", "id", "uuid"):
                        if k in data and isinstance(data[k], str):
                            return data[k]
                raise ValueError(f"Unexpected JSON response from Paperless upload: {data!r}")
            text = (await resp.text()).strip().strip('"')
            if not text:
                raise ValueError("Empty response from Paperless upload")
            return text

    async def get_task(self, task_id: str) -> PaperlessTask:
        """Fetch task state. Returns raw response; tries to extract status/document id."""
        url = f"{self._base_url}/api/tasks/?task_id={task_id}"
        async with self._session.get(url, headers=self._headers(), auth=self._basic) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)

        # The schema isn't described in detail in the snippet; keep parsing best-effort.
        status: str | None = None
        doc_id: int | None = None

        if isinstance(data, dict):
            # often paginated results: {count, results:[...]}
            results = data.get("results")
            if isinstance(results, list) and results:
                item = results[0]
                if isinstance(item, dict):
                    status = item.get("status") or item.get("state")
                    doc_id = item.get("related_document") or item.get("document_id")
                    if isinstance(doc_id, str) and doc_id.isdigit():
                        doc_id = int(doc_id)
        return PaperlessTask(raw=data, status=status if isinstance(status, str) else None, document_id=doc_id if isinstance(doc_id, int) else None)
