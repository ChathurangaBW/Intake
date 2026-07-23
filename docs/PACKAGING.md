# Package publishing

Intake publishes a container image to GitHub Container Registry (GHCR) through `.github/workflows/package.yml`.

## Image

```text
ghcr.io/chathurangabw/intake
```

## Tags

| Trigger | Image tags |
|---|---|
| Push to `main` | `main`, short SHA |
| Push tag `vX.Y.Z` | `vX.Y.Z`, `X.Y.Z`, short SHA |
| Manual workflow dispatch | short SHA |

## Pull

```bash
docker pull ghcr.io/chathurangabw/intake:main
```

## Run

```bash
docker run --rm -p 8000:8000 \
  -e INTAKE_DATABASE_URL='postgresql://intake:intake@host.docker.internal:5432/intake' \
  -e INTAKE_OBJECT_STORE_ENDPOINT='http://host.docker.internal:9000' \
  -e INTAKE_OPA_URL='http://host.docker.internal:8181/v1/data/intake/decision' \
  ghcr.io/chathurangabw/intake:main
```

For normal local development, prefer:

```bash
docker compose up --build
```

## Requirements

The workflow uses the built-in `GITHUB_TOKEN` with `packages: write` permission. No external registry secret is required.

## Safety note

The published package contains the same default safety boundary as the source repo: no unrestricted shell runner, no exploit automation, no persistence, no evasion, and no unscoped network activity.
