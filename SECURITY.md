# Security Policy

## Reporting A Vulnerability

Please report security issues privately to maintainers before public disclosure.

Include:

- impact summary
- reproduction steps
- affected commit/branch
- suggested mitigation (if available)

## Supported Surface

This Kujo branch focuses on:

- safe context packing
- deterministic file selection
- pattern-based secret redaction in generated artifacts

## Security Principles

- Least surprise defaults
- Bounded processing (file/token/size caps)
- Explicit artifact manifests
- Redaction-first output handling

## Current Hardening Areas

- token/secret redaction coverage
- path/exclude handling safety
- defensive behavior under malformed CLI input
- review `redactions.json` as the authoritative coverage report for each pack

## Operational Guidance

- Treat generated packs as sensitive if source repo contains confidential code.
- Review `redactions.json` in CI for coverage drift.
- Treat redaction as best-effort; do not assume it guarantees zero sensitive leakage.
- Never commit generated packs that include proprietary or secret material.
