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
- repository-scoped include/exclude selectors

## Security Principles

- Least surprise defaults
- Bounded processing (file/token/size caps)
- Explicit artifact manifests
- Redaction-first output handling
- Repository-bound path handling for explicit selectors

## Current Hardening Areas

- token/secret redaction coverage
- path/exclude handling safety
- defensive behavior under malformed CLI input
- review `redactions.json` as the authoritative coverage report for each pack
- large-repository performance baselines and fixture coverage

## Operational Guidance

- Treat generated packs as sensitive if source repo contains confidential code.
- Review `redactions.json` in CI for coverage drift.
- Treat redaction as best-effort; do not assume it guarantees zero sensitive leakage.
- Keep `--include` and `--exclude` paths inside the repository being packed. Scent rejects parent-directory traversal and absolute selectors outside the discovered root.
- Scent rejects explicit selectors containing symlinks, skips symlinks during traversal, and omits NUL-bearing extensionless binary files.
- Scent applies its recognized token patterns before clipping selected file content and before emitting task text or command flags.
- Scent replaces symlinks found at artifact filenames before writing, preventing a reused output directory from redirecting an artifact write to another file.
- Never commit generated packs that include proprietary or secret material.
