from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from intake.config import settings

PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


def install_api_key_auth(app: FastAPI) -> None:
    """Install optional API key auth for the API.

    If INTAKE_API_KEY is unset, the app stays open for local development. If it is
    set, all non-public routes require `X-Intake-Api-Key` or `Authorization:
    Bearer <key>`.
    """

    @app.middleware("http")
    async def require_api_key(
        request: Request,
        call_next: Callable[[Request], Awaitable[object]],
    ) -> object:
        if not settings.api_key or request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        supplied = request.headers.get("x-intake-api-key")
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            supplied = auth_header.split(" ", 1)[1].strip()

        if supplied != settings.api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "missing or invalid Intake API key"},
            )
        return await call_next(request)
