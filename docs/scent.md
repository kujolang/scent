# Scent Context-Pack Reference

This document describes the Kujo-runtime implementation in `scent.kujo`.

Scent packages local task context into structured artifacts that are easy for agents and humans to review before handing work off.

Canonical copyable examples live in `README.md`; this file is the reference contract.

## Goals

- Deterministic local context-pack generation
- Explicit budget control
- Pattern-based secret redaction before artifact output
- Reproducible markdown/json artifacts for downstream coding agents

## Pipeline

1. Parse CLI options (`parse_cli`)
2. Discover repository root and instruction files
3. Collect candidate files with bounded traversal
4. Score/select candidates
5. Redact sensitive lines/tokens
6. Apply budget include/truncate/exclude decisions
7. Generate artifacts and manifest metadata

## Command Surface

- `help` / `--help`: print usage
- `pack --help`: print pack-specific usage
- `version` / `--version`: print `Scent 1.0.0`
- `pack`: generate a context pack
- `pack --dry-run`: estimate the pack without writing artifacts
- `--include` / `--exclude`: may be repeated; selectors are scoped to the discovered repository root

## Artifact Contract

| Artifact | Purpose |
| --- | --- |
| `context.md` | Human-readable task pack |
| `context.json` | Machine-readable context |
| `files.json` | Discovered file inventory + selection metadata |
| `manifest.json` | Decision ledger (`include`, `truncate`, `exclude`) |
| `redactions.json` | Per-redaction audit entries |
| `metadata.json` | Run-level metadata |

### `context.json` fields

The structured context payload includes:

- task
- target
- budget
- estimated_tokens
- repo metadata
- generated_at
- instructions
- selected_files
- changed_files
- redactions
- excluded files
- artifacts
- git metadata

## Current Runtime Notes

- Candidate traversal avoids ignored directories and recursion cycles.
- Candidate traversal sorts directory entries before selection, which keeps pack selection stable across filesystems.
- Generated/bulk paths are excluded from normal review sweeps unless explicitly targeted: `.git/`, `target/`, `.scent/`, and `out/`.
- CLI parsing uses Kujo `arg_parser()` for stability.
- Git metadata reflects the current working tree at the repo root discovered from the current working directory.
- Run `scent` from the repository you want to pack; it discovers the repo root from the current working directory.
- The `--target` flag selects the downstream model target, not a repo path.
- Repeated include/exclude flags are preserved as ordered lists. Selectors cannot contain `..`, and absolute selectors must remain inside the discovered repo root.
- Selectors normalize `.` and trailing slashes. Selectors containing symlink segments are rejected, and repository traversal does not follow symlinks.
- An explicit include directory receives its own bounded traversal, so it remains effective when the baseline candidate scan reaches its cap.
- Existing output artifacts are overwritten, stale `context.md`/`context.json` files from a different requested format are removed, and an output directory inside the repository is excluded from candidate selection for that run.
- A pre-existing symlink at an artifact filename is replaced rather than followed during output writes.
- Extensionless files containing NUL bytes are treated as binary and omitted from pack contents.
- File clipping occurs after redaction and treats `--max-file-bytes` as a UTF-8 byte limit.
- `pack --dry-run` reports `estimated_tokens` and `included_files` without writing output files.
- Redaction coverage is reviewable in `redactions.json`; treat it as best-effort, pattern-based protection rather than a secrecy guarantee. Current coverage includes key/value secret lines, private-key blocks, authorization headers, JWT-shaped values, OpenAI-style `sk-` tokens, GitHub token prefixes, AWS access-key IDs, and Stripe live secret keys.
- Recognized patterns in task text are sanitized before task, command-flag, and redaction metadata are emitted.
- Git path lists use NUL-delimited porcelain output so whitespace and newline-bearing names retain exact identity across Git metadata and file selection.

## Context-Layer Positioning

- Scout maps the repository.
- Scent packages task-specific context.
- RAG retrieves grounded local knowledge.
- MCP exposes local tools and resources.

## Hardening Priorities

- Restore rich Git metadata once process primitives are fully stable
- Expand redaction patterns for provider-specific credentials beyond the current common-token coverage
- Add explicit performance baselines for very large repositories
- Add packaged fixtures for path-scope, repeated-include, and redaction regressions once the repo grows beyond inline smoke tests
