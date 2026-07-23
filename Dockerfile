FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY alembic.ini /app/alembic.ini
COPY migrations /app/migrations
COPY policies /app/policies
COPY scripts /app/scripts

RUN pip install --no-cache-dir -e .[dev] \
    && chmod +x /app/scripts/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["uvicorn", "intake.api:app", "--host", "0.0.0.0", "--port", "8000"]
