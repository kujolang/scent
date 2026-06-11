# Scent Context-Pack Reference

This document describes the Kujo-runtime implementation in `scent.kujo`.

Scent packages local task context into structured artifacts that are easy for agents and humans to review before handing work off.

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
- `version` / `--version`: print `Scent 0.1.0-kujo`
- `pack`: generate a context pack
- `pack --dry-run`: estimate the pack without writing artifacts

## Artifact Contract

- `context.md`: human-readable task pack
- `context.json`: machine-readable context
- `files.json`: discovered file inventory + selection metadata
- `manifest.json`: decision ledger (include/truncate/exclude)
- `redactions.json`: per-redaction audit entries
- `metadata.json`: run-level metadata

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
- CLI parsing uses Kujo `arg_parser()` for stability.
- Git metadata reflects the current working tree at the repo root discovered from the current working directory.
- Run `scent` from the repository you want to pack; it discovers the repo root from the current working directory.
- The `--target` flag selects the downstream model target, not a repo path.
- `pack --dry-run` reports `estimated_tokens` and `included_files` without writing output files.
- Redaction coverage is reviewable in `redactions.json`; treat it as best-effort, pattern-based protection rather than a secrecy guarantee.

## Context-Layer Positioning

- Scout maps the repository.
- Scent packages task-specific context.
- RAG retrieves grounded local knowledge.
- MCP exposes local tools and resources.

## Hardening Priorities

- Restore rich Git metadata once process primitives are fully stable
- Expand redaction patterns and add regression fixtures
- Add explicit performance baselines for very large repositories
