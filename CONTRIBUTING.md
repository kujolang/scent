# Contributing

Thanks for contributing to `scent`.

## Scope Of This Branch

This branch is the Kujo-runtime implementation track for the local context-pack workflow. Keep changes focused on:

- `scent.kujo`
- documentation
- fixtures/examples that validate Kujo behavior

Avoid mixing unrelated refactors.

## Development Workflow

1. Create a feature branch from `scent-kujo-build`.
2. Make focused, reviewable commits.
3. Run validation locally:

```bash
cd /path/to/scent
/path/to/kujo/target/release/kujo run scent.kujo help
/path/to/kujo/target/release/kujo run scent.kujo version
/path/to/kujo/target/release/kujo run scent.kujo --version
/path/to/kujo/target/release/kujo check scent.kujo
/path/to/kujo/target/release/kujo run scent.kujo pack --task "smoke" --dry-run --json
```

4. Include before/after behavior notes in your PR.

## Agent And Example Hygiene

Prioritize copyable examples over tests: examples should model the most token-efficient idioms we want agents to imitate.

- Treat `README.md` as the canonical onboarding/example surface.
- Treat `docs/scent.md` as the reference contract for command behavior and artifacts.
- Treat inline tests in `scent.kujo` as behavioral smoke coverage, not tutorial examples.
- Exclude generated/bulk paths from the main sweep unless the task explicitly targets them; use `rg --files -g '!target/**' -g '!out/**' -g '!.scent/**' -g '!.git/**'` for broad scans.
- Keep generated pack output out of reviews unless the change is specifically about artifact shape.
- Prefer small local helpers for repeated output formatting, but keep the demonstrated Scent behavior visible.

## Code Standards

- Prefer deterministic behavior over heuristic complexity.
- Keep operations bounded (`max_files`, `max_file_bytes`, token budget).
- Favor explicit redaction and safe defaults, while documenting that redaction is pattern-based rather than perfect.
- Document user-visible flag/format changes in `README.md`.

## Pull Request Checklist

- [ ] Kujo check passes
- [ ] Smoke run succeeds
- [ ] No secrets in repository or generated fixtures
- [ ] Docs updated for CLI or behavior changes

## Commit Message Guidance

Use concise, imperative commit subjects.

Examples:

- `stabilize candidate collection in Kujo runtime`
- `add fallback selection when strict scoring yields none`
- `update readme for Kujo branch execution flow`
