# Validation status

This file is updated during the release-candidate hardening pass.

## Required checks

- [ ] lint
- [ ] unit tests
- [ ] API contract tests
- [ ] package build
- [ ] dependency audit
- [ ] static security scan
- [ ] clean database migration
- [ ] API readiness
- [ ] durable worker smoke workflow
- [ ] evidence integrity verification

The release candidate must not be merged until the automated checks are green or any environment-only limitation is explicitly documented.
