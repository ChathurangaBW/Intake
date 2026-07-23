FROM python:3.14-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY pyproject.toml README.md LICENSE /build/
COPY src /build/src

RUN python -m pip install --upgrade pip build \
    && python -m build --wheel \
    && mkdir -p /wheels \
    && python -m pip wheel --wheel-dir /wheels dist/*.whl


FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN addgroup --system intake \
    && adduser --system --ingroup intake --home /app intake

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN python -m pip install /wheels/* \
    && rm -rf /wheels

COPY alembic.ini /app/alembic.ini
COPY migrations /app/migrations
COPY policies /app/policies
COPY scripts /app/scripts
RUN chmod +x /app/scripts/entrypoint.sh \
    && mkdir -p /tmp/intake-ghidra \
    && chown -R intake:intake /app /tmp/intake-ghidra

USER intake

EXPOSE 8000

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["uvicorn", "intake.api:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "127.0.0.1"]
