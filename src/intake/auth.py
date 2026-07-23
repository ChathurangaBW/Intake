from __future__ import annotations

import hashlib
import hmac
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from intake.config import settings

PUBLIC_PREFIXES = (
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
)

ROLE_LEVEL = {
    "viewer": 10,
    "operator": 20,
    "approver": 30,
    "admin": 40,
}


@dataclass(frozen=True)
class Principal:
    key_id: str
    role: str


def _configured_keys() -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    for raw_key, role in settings.api_keys.items():
        normalized_role = role.strip().lower()
        if normalized_role not in ROLE_LEVEL:
            continue
        keys.append((raw_key, normalized_role))
    if settings.api_key:
        keys.append((settings.api_key, "admin"))
    return keys


def _key_id(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:12]


def _extract_key(request: Request) -> str | None:
    supplied = request.headers.get("x-intake-api-key")
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        supplied = auth_header.split(" ", 1)[1].strip()
    return supplied


def _authenticate(supplied: str | None) -> Principal | None:
    if supplied is None:
        return None
    matched: Principal | None = None
    for raw_key, role in _configured_keys():
        if hmac.compare_digest(supplied, raw_key):
            matched = Principal(key_id=_key_id(raw_key), role=role)
    return matched


def required_role(request: Request) -> str:
    path = request.url.path
    method = request.method.upper()
    if method in {"GET", "HEAD", "OPTIONS"}:
        return "viewer"
    if path.startswith("/approvals/") or path.endswith("/execute") or path.endswith("/cancel"):
        return "approver"
    return "operator"


def install_api_key_auth(app: FastAPI) -> None:
    """Install optional role-aware API-key authentication.

    When no key is configured the app remains open for disposable local
    development. Configured keys are compared in constant time and mapped to
    viewer, operator, approver, or admin roles.
    """

    @app.middleware("http")
    async def require_api_key(
        request: Request,
        call_next: Callable[[Request], Awaitable[object]],
    ) -> object:
        if request.url.path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)

        configured = _configured_keys()
        if not configured:
            request.state.principal = Principal(key_id="local-development", role="admin")
            return await call_next(request)

        principal = _authenticate(_extract_key(request))
        if principal is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "missing or invalid Intake API key"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        needed = required_role(request)
        if ROLE_LEVEL[principal.role] < ROLE_LEVEL[needed]:
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "insufficient Intake role",
                    "required_role": needed,
                    "principal_role": principal.role,
                },
            )

        request.state.principal = principal
        response = await call_next(request)
        response.headers["X-Intake-Principal-Role"] = principal.role
        return response


def principal_from_request(request: Request) -> Principal:
    principal = getattr(request.state, "principal", None)
    if isinstance(principal, Principal):
        return principal
    return Principal(key_id="public", role="viewer")
