# Scent Enterprise Readiness Review - 2026-06-19

## Verdict

Scent is not yet something we should describe as universally enterprise ready, but it is a strong Kujo showcase candidate with a compact surface, deterministic behavior, redaction-first posture, and useful context-pack artifacts. The next step is to turn the current inline smoke coverage into a more formal release-quality validation story.

## Completed In This Pass

- Preserved repeated `--include` and `--exclude` flags as ordered selector lists.
- Rejected explicit include/exclude selectors that contain `..` or point outside the discovered repository root.
- Sorted directory traversal entries before scoring to reduce filesystem-order variance.
- Expanded redaction coverage for OpenAI-style `sk-` tokens, GitHub token prefixes, AWS access-key IDs, Stripe live secret keys, and the previously latent JWT replacement path.
- Added inline regression coverage for repeated includes, scoped path rejection, and expanded token redaction.
- Updated README, reference docs, security guidance, and contributing notes to match the current behavior.
- Confirmed tracked root files are intentional: `scent.kujo` remains the canonical Kujo entrypoint, while generated `out/`, `.scent/`, and `target/` directories are ignored.

## Current Strengths

- Small copyable CLI surface with clean help/version behavior.
- Deterministic scoring model that prioritizes instructions, explicit includes, changed files, tests, configs, and docs.
- Bounded pack generation through token, file-count, and per-file byte limits.
- Reviewable artifacts: `context.md`, `context.json`, `manifest.json`, `files.json`, `redactions.json`, and `metadata.json`.
- Pattern-based redaction metadata is exposed rather than hidden.
- Inline tests exercise help/version, dry-run, artifact writes, git dirty-state capture, redaction, repeated includes, and path-scope hardening.

## Remaining Work Before Calling It Enterprise Grade

1. Add a CI workflow that runs `kujo check scent.kujo`, `kujo test-run scent.kujo`, and the documented smoke commands on every PR.
2. Add fixture directories for redaction, path traversal, repeated selectors, symlinks, large files, binary files, and dirty git states instead of relying only on inline `/tmp` setup.
3. Define and publish JSON schemas for `context.json`, `manifest.json`, `files.json`, `redactions.json`, and `metadata.json`.
4. Add large-repository performance baselines with target thresholds for traversal time, memory use, selected-file count, and pack generation duration.
5. Respect `.gitignore` or a Scent-specific ignore file for candidate traversal while preserving explicit include behavior.
6. Harden path handling around symlinks once Kujo exposes canonical path primitives, so repository-root confinement is based on resolved real paths.
7. Add entropy-based redaction for unknown high-entropy tokens, with careful allowlisting to avoid noisy false positives.
8. Add provider-specific redaction fixtures for Anthropic, Google, Azure, npm, PyPI, Slack, Stripe, GitHub, AWS, database URLs, and private-key formats.
9. Add configurable redaction policy levels, for example `standard`, `strict`, and `audit`, while keeping the current default conservative and predictable.
10. Add a `--config` file option for durable defaults such as target, budget, include/exclude paths, max files, and redaction policy.
11. Consider moving implementation internals into a `src/` directory only when Kujo module support and project conventions make that cleaner; keep the root `scent.kujo` entrypoint or compatibility wrapper.
12. Add release packaging notes that show how Scent should be installed, versioned, and invoked outside this monorepo-style checkout.
13. Add examples for Codex, Claude, DeepSeek, and generic downstream usage with small fixture repos and expected artifact snippets.
14. Add a security review checklist for generated pack sharing, redaction audit review, and incident handling.
15. Add benchmark/report artifacts that make Scent visually impressive as a Kujo showcase, not only functionally correct.

## Next Session Starting Point

Start with CI and fixtures. The most valuable next slice is:

1. Create a `tests/fixtures/` tree for redaction and selector behavior.
2. Update inline tests to consume fixtures where possible.
3. Add a GitHub Actions workflow or equivalent local CI script.
4. Add JSON schema docs for the generated artifacts.
5. Run the full validation suite and update this review with measured results.
