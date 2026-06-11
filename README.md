# Scent

Scent packages local task context into structured, reviewable artifacts with provenance and redaction metadata.

## Status

- Kujo script entrypoint: `scent.kujo`
- Command: `scent pack`
- Help/version are clean: `help`, `--help`, `pack --help`, `version`, and `--version`
- Output formats: Markdown + JSON
- Deterministic selection and pattern-based redaction pipeline enabled
- Artifact write path verified on safe local smoke data
- `pack --dry-run` reports context estimates without writing files

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

1. Build Kujo (if needed):

```bash
cd /path/to/kujo
cargo build --release
```

2. Run `scent` from the repository you want to pack:

```bash
cd /path/to/target-repo
/path/to/kujo/target/release/kujo run /path/to/scent/scent.kujo pack \
  --task "implement auth fixes and validate tests" \
  --out /private/tmp/scent-pack \
  --max-files 25 \
  --max-file-bytes 50000 \
  --format both
```

Scent discovers the repo root from the current working directory, so run it inside the repository you want to pack.
The `--target` flag selects the downstream model target; it does not select a repo path.

3. Dry run (no writes):

```bash
/path/to/kujo/target/release/kujo run scent.kujo pack \
  --task "review security posture" \
  --dry-run \
  --json
```

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
- This branch is designed for implementation comparison, not historical parity with main.

## Security Model

- Redacts common secret/token patterns before pack output.
- Treat redaction as pattern-based and review `redactions.json`; it reduces exposure but does not guarantee perfect secrecy.
- Avoids shell interpolation from user-provided task text.
- Keeps output bounded by explicit byte/token heuristics.

See `SECURITY.md` for reporting and hardening guidance.

## Contributing

See `CONTRIBUTING.md` for branch workflow, style, and PR expectations.

## License

Licensed under the MIT License. See `LICENSE`.
