# Scent Context-Pack Reference

This document describes the Kujo-runtime implementation in `scent.kujo`. The supported verification environment is POSIX with Kujo 1.3.1 or newer, Git, and `realpath`; tests additionally use Python 3 and Bash. There are no third-party Scent runtime packages.

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
- `--changed`, `--staged`, and `--unstaged` boost selection priority; they are not strict filters.
- Git metadata reflects the current working tree at the repo root discovered from the current working directory.
- Run `scent` from the repository you want to pack; it discovers the repo root from the current working directory.
- The `--target` flag selects the downstream model target, not a repo path.
- Repeated include/exclude flags are preserved as ordered lists. Selectors cannot contain `..`, and absolute selectors must remain inside the discovered repo root.
- Exclusion wins over inclusion. Excluded trees are pruned before consuming the candidate cap. Selectors normalize repeated slashes, internal `.` segments, and trailing slashes. Selectors containing symlink segments are rejected, and repository traversal does not follow symlinks.
- An explicit include directory receives its own bounded traversal, so it remains effective when the baseline candidate scan reaches its cap.
- Existing output artifacts are overwritten, stale `context.md`/`context.json` files from a different requested format are removed, and an output directory inside the repository is excluded from candidate selection for that run.
- Default output directories include a random UUID suffix in addition to the timestamp, avoiding collisions within the runtime clock’s one-second resolution. Explicit output directories retain reuse behavior.
- Artifact publication uses a private same-directory temporary file and atomic rename. Existing artifact symlinks and hard links are replaced without writing through them. New files use mode `0600`; existing regular-file permission bits are preserved. Write failures return exit 4 and attempt temporary-file cleanup. Atomicity applies to each file, not the entire six-file pack: do not concurrently write the same output directory, and do not use a pack after a failed run.
- Extensionless files containing NUL bytes are treated as binary and omitted from pack contents.
- Selected content and command-discovery files use repository-relative, no-follow reads capped at the runtime’s existing 8 MiB limit. Oversized, non-regular, symlinked, or unreadable content is excluded with provenance.
- File clipping occurs after redaction and treats `--max-file-bytes` as a UTF-8 byte limit.
- `pack --dry-run` reports `estimated_tokens` and `included_files` without writing output files.
- Redaction coverage is reviewable in `redactions.json`; treat it as best-effort, pattern-based protection rather than a secrecy guarantee. Current coverage includes key/value secret lines, private-key blocks, authorization headers, JWT-shaped values, OpenAI-style `sk-` tokens, GitHub token prefixes, AWS access-key IDs, and Stripe live secret keys.
- Recognized patterns in task text are sanitized before task, command-flag, and redaction metadata are emitted.
- Redaction records retain source line numbers even when private-key removal shifts emitted line positions. Provider tokens and JWTs on the same line are all sanitized.
- Git commands use argument arrays without a shell; truncated process output degrades Git availability rather than being parsed as complete.
- Git path lists use NUL-delimited output so whitespace and newline-bearing names retain exact identity across Git metadata and file selection.

## Context-Layer Positioning

- Scout maps the repository.
- Scent packages task-specific context.
- RAG retrieves grounded local knowledge.
- MCP exposes local tools and resources.

## Budgets and efficiency

`estimated_tokens` remains the compatible estimate of task and selected content
(characters divided by four, plus two). Selection reserves 1,400 heuristic tokens
for framing. It does not count all serialized JSON/Markdown metadata, inventories,
or Git paths, and it is not a model tokenizer or a hard full-artifact limit.
Review actual artifact size before loading a complete pack into a model.

Dry runs compute selection, redaction, and budget decisions but skip unused
artifact rendering and command discovery. JSON-only writes skip Markdown
rendering. Candidate order remains descending score, then ascending exact path.

## Verification and remaining boundaries

Run `KUJO_BIN=kujo bash scripts/verify.sh`. Full logs live under the receipt's
`out/verification/` directory. `kujo test-run scent.kujo` runs the inline suite;
`kujo test` does not discover it. The Eval fixture uses repository-relative
paths and must be run from the repository root.

Use `KUJO_BIN=kujo python3 scripts/benchmark.py --files 24 --runs 3
--output out/benchmark.json` (on one shell line) to reproduce the audit workload.
Measurements include startup, Git inspection, selection, redaction, and output.
The benchmark records semantic fingerprints; no unstable timing threshold is
used in CI. Change its explicit file/run options to measure a different workload
and retain both receipts when comparing revisions.

Full-pack transactions, a full-artifact token budget, and path-metadata redaction
need separate compatibility design. Paths and repository metadata retain exact
identity and may themselves be sensitive. See the repository-local audit report
for evidence and prioritization.
