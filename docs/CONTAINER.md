# Container usage

Intake can run from source with Docker Compose or from the GitHub Container Registry package.

## Development stack

```bash
cp .env.example .env
docker compose up --build
```

This starts:

- Intake API
- PostgreSQL
- OPA
- MinIO

## Published package

After the `package` workflow runs on `main`, pull:

```bash
docker pull ghcr.io/chathurangabw/intake:main
```

## Versioned image

After tagging a release:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Pull:

```bash
docker pull ghcr.io/chathurangabw/intake:v0.1.0
```

## Runtime configuration

Set these environment variables when not using Docker Compose:

```bash
INTAKE_DATABASE_URL=postgresql://...
INTAKE_OBJECT_STORE_ENDPOINT=http://...
INTAKE_OBJECT_STORE_BUCKET=intake-evidence
INTAKE_OBJECT_STORE_ACCESS_KEY=...
INTAKE_OBJECT_STORE_SECRET_KEY=...
INTAKE_OPA_URL=http://.../v1/data/intake/decision
```

Use `INTAKE_API_KEY` before exposing the API beyond localhost.
