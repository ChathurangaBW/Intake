# Intake

Intake is a policy-controlled security automation framework for authorized reverse engineering, evidence handling, and assessment workflows.

The project is intentionally built around this rule:

> The model proposes. Policy decides. Isolated workers execute. Evidence proves. A human authorizes sensitive actions.

## Current status

Initial framework skeleton.

## Core design

- **Scope-first execution**: every target, artifact, and operation must belong to an engagement manifest.
- **Policy-gated tools**: tool calls pass through schema validation and policy checks before execution.
- **Isolated workers**: static analysis runs in disposable containers; dynamic analysis should run in disposable VMs or microVMs.
- **Evidence integrity**: artifacts and outputs are stored by content hash and referenced by immutable IDs.
- **Human approval gates**: sensitive or state-changing actions require explicit approval.
- **LLM cost control**: models are used for planning, summarization, and reasoning, not for unrestricted shell execution.

## Repository layout

```text
src/intake/          Python package
src/intake/tools/    Typed tool wrappers
policies/            OPA/Rego policy examples
docs/                Architecture and roadmap
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
intake --help
```

## Safety boundary

This project is for systems, binaries, applications, and networks that you own or are explicitly authorized to assess. It is not designed to bypass authorization, evade detection, or automate unauthorized activity.
