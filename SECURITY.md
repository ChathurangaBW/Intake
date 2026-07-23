# Security policy

## Supported versions

| Version | Supported |
|---|---|
| `1.x` | Yes |
| `<1.0` | No |

Security fixes are applied to the latest `1.x` release and the `main` development branch.

## Reporting a vulnerability

Open a private security advisory in GitHub if available, or contact the repository owner directly.

Do not open public issues for sensitive vulnerabilities, secret leaks, authorization bypasses, worker-isolation failures, evidence-integrity failures, or bypasses of the policy boundary.

A useful report should include the affected version, deployment configuration, reproduction steps, impact, and any proposed mitigation. Do not include customer artifacts, credentials, or confidential engagement evidence.

## Product security boundary

Intake intentionally does not expose:

- unrestricted shell execution
- exploit automation
- evasion
- persistence
- destructive actions
- unscoped active network operations

Reports that identify a bypass of these boundaries are treated as security issues.
