# Scent

[![Version](https://img.shields.io/badge/version-1.0.0-black)](https://github.com/kujolang/scent)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)
[![built with Kujo](https://img.shields.io/badge/built%20with-Kujo-white.svg)](https://github.com/kujolang/kujo)

Scent packages local task context into structured, reviewable artifacts with provenance and redaction metadata.

Prioritize copyable examples over tests: examples should model the most token-efficient idioms we want agents to imitate.

## Status

- Kujo script entrypoint: `scent.kujo`
- Command: `scent pack`
- Help/version are clean: `help`, `--help`, `pack --help`, `version`, and `--version`
- Output formats: Markdown + JSON
- Deterministic selection and pattern-based redaction pipeline enabled
- Repeated `--include` and `--exclude` flags are preserved as ordered selector lists
- Include/exclude selectors are constrained to the discovered repository root
- Root (`.`) and trailing-slash selectors are normalized, and selectors containing symlinks are rejected
- Artifact write path verified on safe local smoke data
- Reusing an output directory overwrites current artifacts, removes stale optional context formats, and does not repack prior output
- Artifact writes publish complete files atomically, replacing symlinks and hard links without changing their targets. Default pack directory names include a unique suffix for concurrent runs. New artifacts are owner-only (`0600`); existing regular artifact permissions are preserved.
- `pack --dry-run` reports context estimates without writing files
- Source layout: the canonical Kujo entrypoint is still `scent.kujo` at the repo root; generated `out/`, `.scent/`, and `target/` directories are ignored and should not be committed.

## What It Produces

Given a task, `scent` builds a pack with:

- `context.md`
- `context.json`
- `manifest.json`
- `files.json`
- `redactions.json`
- `metadata.json`

The structured `context.json` includes the task, target, budget, estimated token count, repository metadata, generation timestamp, instructions, selected files, changed files, redactions, excluded files, emitted artifacts, and git metadata.

## Quick Start

These commands are the canonical examples for this branch. They are meant to be copied from a shell in the repository you want to pack.

1. Verify Kujo 1.3.1 or newer is installed (POSIX environment):

```bash
kujo --version
```

2. Preview the pack without writing files:

```bash
cd /path/to/target-repo
kujo run /path/to/scent/scent.kujo pack \
  --task "review security posture" \
  --dry-run \
  --json
```

Expected output is one compact JSON object with `output_dir`, `estimated_tokens`, `budget`, `included_files`, and `warnings`.

3. Write Markdown and JSON artifacts:

```bash
kujo run /path/to/scent/scent.kujo pack \
  --task "implement auth fixes and validate tests" \
  --out /private/tmp/scent-pack \
  --format both
```

Scent discovers the repo root from the current working directory, so run it inside the repository you want to pack.
The `--target` flag selects the downstream model target; it does not select a repo path.
Repeat `--include` or `--exclude` to focus multiple paths. These selectors must be relative to the discovered repository root, or absolute paths inside that root.
Scent does not follow repository symlinks, and extensionless files containing NUL bytes are treated as binary. Exclusions win over includes and are pruned before traversal; repeated slashes and `.` segments are normalized. Git focus flags boost priority rather than strictly filtering files.

## Position in Kujo

- Scout maps repository state.
- Scent packages task-specific context from that state.
- RAG retrieves grounded local knowledge.
- MCP exposes local tools and resources.

## CLI

```text
scent pack --task <text>
  [--out <path>]
  [--budget <n>]
  [--target codex|claude|deepseek|generic]
  [--include <path>]
  [--exclude <path>]
  [--changed] [--staged] [--unstaged]
  [--max-files <n>]
  [--max-file-bytes <n>]
  [--format md|json|both]
  [--verbose]
  [--json]
  [--dry-run]
```

## Notes For This Kujo Branch

- Git metadata reflects the current working tree at the repo root discovered from the current working directory.
- Selection falls back to a small baseline set when strict relevance scoring yields none.
- This branch is designed for implementation comparison and showcase quality, not historical parity with main.
- Canonical examples live in this README. `docs/scent.md` is the reference contract, and inline tests in `scent.kujo` are behavior checks rather than copyable user examples.
- Exclude generated/bulk paths from the main sweep unless the task explicitly targets them. This repo ignores `.git/`, `target/`, `.scent/`, and `out/`; those paths were excluded from the readability sweep.

## Security Model

- Redacts common secret/token patterns before pack output.
- Applies recognized secret patterns to task text as well as selected file content before emitting artifacts.
- Treat redaction as pattern-based and review `redactions.json`; it reduces exposure but does not guarantee perfect secrecy.
- Covers common key/value secret lines plus JWT-shaped values, OpenAI-style `sk-` tokens, GitHub token prefixes, AWS access-key IDs, Stripe live secret keys, private-key blocks, and authorization headers.
- Avoids shell interpolation from user-provided task text.
- Keeps output bounded by explicit byte/token heuristics and repository-scoped include/exclude selectors.
- Enforces `--max-file-bytes` as a UTF-8 byte limit without splitting a multibyte character.

The token budget governs selected content using a character heuristic; it is not a hard limit on serialized metadata or model tokens. Use a separate, privately controlled output directory per concurrent run.

See `SECURITY.md` for reporting and hardening guidance.

## Contributing

Run `KUJO_BIN=kujo bash scripts/verify.sh` for static checks, all inline and CLI regressions, and artifact hygiene. It prints concise receipts and saves logs in `out/verification/`.

See `CONTRIBUTING.md` for branch workflow, style, and PR expectations. Audit evidence and measured limitations are in [the repository hardening report](docs/audits/repository-hardening.md).

## License

Licensed under the MIT License. See `LICENSE`.
