# Contributing

Thanks for helping improve this Kujo ecosystem project.

This guide is intended for standalone Kujo tools and primitives. It does not
cover the core Kujo language repo, Kujo Skills, or Kujo Workflows when those
projects have their own contribution rules.

## Development Principles

- Keep changes focused, reviewable, and tied to one user-visible concern.
- Prefer deterministic, local-first behavior.
- Do not add network calls, provider calls, timestamps, or machine-specific
  output to core command paths unless the feature explicitly requires it.
- Preserve redaction, path safety, guarded cleanup, and stable output ordering.
- Add tests for behavior changes. Bug fixes should include regression coverage.
- Avoid speculative refactors unless they directly simplify the change at hand.

For Scent specifically:

- Preserve deterministic selection, bounded traversal, explicit budget
  decisions, and redaction-first output behavior.
- Keep changes focused on `scent.kujo`, documentation, and fixtures/examples
  that validate Kujo behavior unless the task explicitly widens scope.
- Keep generated pack output out of reviews unless the change specifically
  concerns artifact shape.
- Keep demonstrated Scent behavior visible; do not hide CLI examples behind
  broad abstractions.

## Local Setup

Use the Kujo runtime expected by this repository. Most repos support one of
these environment variables:

```bash
export KUJO_BIN=kujo
export KUJO=kujo
```

Scent commonly uses the installed runtime:

```bash
kujo run scent.kujo help
```

Primary script:

```text
scent.kujo
```

Check the repo README, `Makefile`, `tests/`, and `scripts/` directory for the
authoritative local commands.

## Agent And Example Hygiene

Start with `README.md`, `CONTRIBUTING.md`, relevant docs, and examples before
broad source sweeps.

Treat user-facing examples as canonical copyable surfaces. Examples should be
short, runnable, and representative of the idioms humans and agents should copy.

For Scent:

- Treat `README.md` as the canonical onboarding and example surface.
- Treat `docs/scent.md` as the reference contract for command behavior and
  artifacts.
- Treat inline tests in `scent.kujo` as behavioral smoke coverage, not tutorial
  examples.
- Treat generated pack artifacts such as `context.md`, `context.json`,
  `manifest.json`, `files.json`, `redactions.json`, and `metadata.json` as local
  output unless the task explicitly targets artifact shape.

Exclude generated and bulk paths from broad searches unless the task explicitly
targets them:

```bash
rg --files -g '!target/**' -g '!out/**' -g '!.scent/**' -g '!.git/**'
```

Document any important search exclusions in larger cleanup or audit PRs.

## Code Standards

- Match the surrounding code style before introducing a new abstraction.
- Keep command output readable and stable.
- Prefer small local helpers for repeated output, error, section, or key/value
  formatting once repetition distracts from the behavior.
- Keep CLI contracts explicit: flags, exit codes, JSON fields, artifact paths,
  and documented examples should agree with parser behavior.
- Keep config honest. A config key should either change observable behavior or
  be clearly documented as reserved.
- Preserve compatibility entrypoints and wrappers when a repo provides them.
- In `scent.kujo`, reuse `print_lines`, `print_kv`, and argument-array test
  runners before adding more ad hoc print or command blocks.
- Keep repeated flag behavior, repository-scoped path checks, and redaction
  coverage protected by inline tests when changing CLI parsing or pack
  selection.
- Reject explicit include/exclude selectors that leave the discovered repository
  root.
- Favor explicit redaction and safe defaults, while documenting that redaction
  is pattern-based rather than perfect.

## Kujo Runtime Notes

Kujo ecosystem tools often follow these defensive patterns:

- Prefer `while` loops in complex functions.
- Avoid duplicate local names across branches in the same function.
- Keep imports at the top of the file.
- Export functions that are imported by another module.
- Guard dictionary access with `has_key()` or local helper wrappers.
- Remember that some builtins return int-like `1`/`0` instead of booleans.
- Guard parsing operations such as JSON or TOML parsing and validate the result.
- Keep deep tree walks iterative where recursion risks VM stack limits.
- Be careful with byte-based string indexes versus character-based substring
  operations; use existing repo helpers when available.

Follow stricter runtime notes in the local repo when they exist.

## Validation

Before opening a pull request, run the strongest local validation available for
the repo.

Focused Scent validation:

```bash
cd /path/to/scent
kujo run scent.kujo help
kujo run scent.kujo version
kujo run scent.kujo --version
kujo check scent.kujo
kujo run scent.kujo pack --task "smoke" --dry-run --json
```

Tests should stay offline and deterministic unless the repo explicitly marks a
live-provider or network test as opt-in.

## Documentation And Changelog

Update docs when behavior, configuration, command output, flags, schemas,
examples, or security expectations change.

For Scent, update `README.md` and `docs/scent.md` for user-visible flag, format,
artifact, JSON field, or exit behavior changes. Also check:

- `SECURITY.md`
- command reference or flags docs
- examples
- `CHANGELOG.md`

User-visible behavior changes should include a changelog entry when the repo has
a changelog.

## Pull Requests

A good PR includes:

- Problem statement.
- Change summary.
- User-visible impact.
- Before/after behavior notes when behavior changes.
- Test evidence with commands and outcomes.
- Documentation or changelog updates.
- Known risks or follow-up work, if any.

Keep generated artifacts out of commits unless the artifact is the reviewed
output of the change.

## Commit Messages

Use concise, imperative commit subjects.
