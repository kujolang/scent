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
- Scent reads selected and command-discovery files through repository-relative no-follow handles. Symlink races beneath the repository root cannot redirect these reads. The repository root itself is trusted.
- Scent publishes each artifact atomically from a private temporary file. Final symlinks and hard links are replaced without changing other targets. New artifacts are mode `0600`; existing regular artifact permissions are retained.
- Use a privately controlled output directory and one directory per concurrent run. Parent-directory replacement by another writer is outside this boundary; six-file publication is not a transaction. A failed run may contain mixed generations and must not be shared.
- Repository paths and Git metadata retain identity and are not redacted. Packed content is untrusted source data, including any embedded instructions or control characters; it does not acquire authority merely by appearing in a pack.
- Scent traversal exclusions are independent of general Git ignore rules. Explicitly exclude confidential paths even when Git ignores them.
- Never commit generated packs that include proprietary or secret material.
