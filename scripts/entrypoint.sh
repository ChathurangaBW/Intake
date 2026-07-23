#!/usr/bin/env sh
set -eu

if [ "${INTAKE_SKIP_MIGRATIONS:-false}" != "true" ]; then
  alembic upgrade head
fi

exec "$@"
