# Release process

This repository uses GitHub Actions for release artifacts and container package publishing.

## Release checklist

1. Run local QA:

   ```bash
   make qa
   ```

2. Confirm the app starts:

   ```bash
   docker compose up --build
   ```

3. Create a version tag:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

4. GitHub Actions will:

   - build Python wheel and source distribution
   - build Docker image
   - publish the Docker image to GHCR
   - create release artifacts for the tag

## Versioning

Use semantic versioning:

```text
vMAJOR.MINOR.PATCH
```

Examples:

```text
v0.1.0
v0.2.0
v1.0.0
```

## First release

Recommended first tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Notes

The ChatGPT GitHub connector available in this session does not expose a direct release-publishing action. The repository therefore includes a release workflow so releases can be created reproducibly through GitHub Actions after a tag is pushed.
