"""Loopback-only companion: an inbox of Codex chats and a per-turn summary of each, keyed by thread id."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from importlib.resources import files
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from codex_companion.rollout import THREAD_ID, Sessions

LOOPBACK_HOSTS = ["127.0.0.1", "localhost", "[::1]"]
POLL_SECONDS = 1.0
HEARTBEAT_SECONDS = 15.0
INBOX_LIMIT = 30
PAGE_POLICY = (
    "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)
ASSET_TYPES = {".css": "text/css", ".js": "text/javascript"}


def _static(name: str) -> str:
    return files("codex_companion").joinpath("static", name).read_text(encoding="utf-8")


def create_app(
    codex_home: Path, poll_seconds: float = POLL_SECONDS, should_stop: Callable[[], bool] = lambda: False
) -> FastAPI:
    app = FastAPI(title="Codex companion", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=LOOPBACK_HOSTS)
    sessions = Sessions(codex_home)

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any) -> Response:
        response: Response = await call_next(request)
        response.headers["Content-Security-Policy"] = PAGE_POLICY
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    def checked(thread: str) -> str:
        if not THREAD_ID.match(thread):
            raise HTTPException(status_code=400, detail="thread must be a Codex thread id")
        return thread

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return _static("index.html")

    @app.get("/assets/{name}")
    def asset(name: str) -> Response:
        media_type = ASSET_TYPES.get(Path(name).suffix)
        if media_type is None or name not in {entry.name for entry in files("codex_companion").joinpath("static").iterdir()}:
            raise HTTPException(status_code=404)
        return Response(_static(name), media_type=media_type)

    @app.get("/api/inbox")
    def inbox() -> list[dict[str, Any]]:
        return sessions.inbox(INBOX_LIMIT)

    @app.get("/api/threads/{thread}")
    def thread_state(thread: str) -> dict[str, Any]:
        data = sessions.snapshot(checked(thread))
        if data is None:
            raise HTTPException(status_code=404, detail="no rollout file for this thread")
        return data

    @app.get("/api/stream")
    async def stream(request: Request, thread: str | None = None) -> StreamingResponse:
        if thread:
            checked(thread)

        def current(last: str | None) -> tuple[str, Any]:
            """Blocking file reads; called off the event loop so one large chat cannot stall every stream."""
            if thread:
                data = sessions.snapshot(thread)
                return (str(data["version"]) if data else "missing"), data
            marker = sessions.inbox_fingerprint(INBOX_LIMIT)
            return marker, sessions.inbox(INBOX_LIMIT) if marker != last else None

        async def events() -> AsyncIterator[str]:
            last, idle = None, 0.0
            while not should_stop() and not await request.is_disconnected():
                marker, data = await asyncio.to_thread(current, last)
                if marker != last:
                    last, idle = marker, 0.0
                    yield f"event: {'thread' if thread else 'inbox'}\ndata: {json.dumps(data)}\n\n"
                elif idle >= HEARTBEAT_SECONDS:
                    idle = 0.0
                    yield ": heartbeat\n\n"
                await asyncio.sleep(poll_seconds)
                idle += poll_seconds

        return StreamingResponse(events(), media_type="text/event-stream")

    return app
