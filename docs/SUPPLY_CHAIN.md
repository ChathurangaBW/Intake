# Supply-chain security

Intake 1.0 publishes verifiable build metadata for both container and Python artifacts.

## Container image

The package workflow:

1. builds the image with BuildKit,
2. embeds software-bill-of-materials metadata,
3. generates maximum-mode build provenance,
4. pushes the image to GHCR,
5. publishes a GitHub provenance attestation for the resulting digest.

CI also scans the locally built image and rejects known fixed high or critical OS/library vulnerabilities before the release branch can merge.

## Python distributions

The release workflow:

1. builds wheel and source distributions,
2. validates metadata with Twine,
3. publishes a provenance attestation for every file,
4. attaches the distributions to the GitHub release.

## Verification

Consumers should deploy immutable image digests rather than mutable tags and verify GitHub attestations before promoting artifacts into a trusted environment.

## Secrets

No registry password is stored in the repository. GitHub Actions uses scoped short-lived workflow credentials and OIDC for attestations.
