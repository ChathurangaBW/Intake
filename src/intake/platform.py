from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Awaitable, Callable
from uuid import uuid4

import httpx
from fastapi import APIRouter, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy import text
from starlette.middleware.trustedhost import TrustedHostMiddleware

from intake.auth import principal_from_request
from intake.config import settings
from intake.db import engine
from intake.storage import EvidenceStore

logger = logging.getLogger("intake.access")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")

HTTP_REQUESTS = Counter(
    "intake_http_requests_total",
    "HTTP requests handled by Intake",
    ["method", "path", "status"],
)
HTTP_DURATION = Histogram(
    "intake_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "path"],
)

router = APIRouter()


def _request_id(request: Request) -> str:
    supplied = request.headers.get("x-request-id", "")
    if REQUEST_ID_RE.fullmatch(supplied):
        return supplied
    return str(uuid4())


def _safe_route_path(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return str(path or request.url.path)


def install_platform(app: FastAPI) -> None:
    if settings.trusted_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-Intake-Api-Key", "X-Request-ID"],
        )

    @app.middleware("http")
    async def request_context(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = _request_id(request)
        request.state.request_id = request_id
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > settings.maximum_request_bytes:
                    return Response(
                        content=json.dumps({"detail": "request body exceeds configured limit"}),
                        media_type="application/json",
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        headers={"X-Request-ID": request_id},
                    )
            except ValueError:
                return Response(
                    content=json.dumps({"detail": "invalid content-length header"}),
                    media_type="application/json",
                    status_code=status.HTTP_400_BAD_REQUEST,
                    headers={"X-Request-ID": request_id},
                )

        started = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - started
        route_path = _safe_route_path(request)
        HTTP_REQUESTS.labels(request.method, route_path, str(response.status_code)).inc()
        HTTP_DURATION.labels(request.method, route_path).observe(duration)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store"

        if settings.structured_logging:
            principal = principal_from_request(request)
            logger.info(
                json.dumps(
                    {
                        "event": "http_request",
                        "request_id": request_id,
                        "method": request.method,
                        "path": route_path,
                        "status": response.status_code,
                        "duration_ms": round(duration * 1000, 3),
                        "principal_role": principal.role,
                        "principal_id": principal.key_id,
                    },
                    sort_keys=True,
                )
            )
        return response


@router.get("/health/live", tags=["platform"])
def liveness() -> dict[str, str]:
    return {"status": "alive"}


def dependency_status() -> dict[str, dict[str, str | bool]]:
    checks: dict[str, dict[str, str | bool]] = {}

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["database"] = {"ok": True, "detail": "connected"}
    except Exception as error:  # noqa: BLE001 - dependency boundary
        checks["database"] = {"ok": False, "detail": type(error).__name__}

    try:
        response = httpx.get(settings.opa_health_url, timeout=settings.readiness_timeout_seconds)
        checks["opa"] = {"ok": response.is_success, "detail": str(response.status_code)}
    except Exception as error:  # noqa: BLE001
        checks["opa"] = {"ok": False, "detail": type(error).__name__}

    try:
        EvidenceStore().check()
        checks["object_store"] = {"ok": True, "detail": "bucket reachable"}
    except Exception as error:  # noqa: BLE001
        checks["object_store"] = {"ok": False, "detail": type(error).__name__}

    return checks


@router.get("/health/dependencies", tags=["platform"])
def dependencies() -> dict[str, object]:
    checks = dependency_status()
    return {"status": "ok" if all(bool(item["ok"]) for item in checks.values()) else "degraded", "checks": checks}


@router.get("/health/ready", tags=["platform"])
def readiness(response: Response) -> dict[str, object]:
    checks = dependency_status()
    ready = all(bool(item["ok"]) for item in checks.values())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if ready else "not_ready", "checks": checks}


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    if not settings.metrics_enabled:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
