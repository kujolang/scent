# Scent Evidence-Driven Bug Hunt — 2026-08-12

## Executive Summary

- Candidate root-cause hypotheses investigated: 30
- Confirmed bugs: 12
- Fixed bugs: 12
- Rejected hypotheses: 14
- Needs-specification findings: 4
- Regression tests added: 12 inline Kujo tests
- Baseline commit: `622ba30820e6d8728c1f87077fd38e180f561011` on `main`
- Fixed commit: `2775035b690660f8b1caa4d1858f04b80c148c07`
- Full-suite status: `kujo test-run scent.kujo` passed `16/16`; the repository-prescribed `KUJO_BIN=kujo kujo test` also exited 0 but discovered `0` fixtures because Scent's tests are inline. Eval passed 3/4 checks and retained its pre-existing 30-second timeout failure for the repository-level dry run.

The audit exercised the CLI, repository and worktree discovery, path containment, bounded traversal, selector interactions, Git state, deterministic scoring, binary/text boundaries, redaction, byte and token limits, artifact consistency, output reuse, dry-run behavior, Markdown/JSON robustness, and command discovery. Every admitted defect was reproduced before modification and received a regression test.

## Baseline

| Command | Exit | Result |
| --- | ---: | --- |
| `kujo check scent.kujo` | 0 | Passed |
| `KUJO_BIN=kujo kujo test` | 0 | Passed, but discovered 0 fixture tests |
| `KUJO_BIN=kujo kujo test-run scent.kujo -v` | 0 | 4/4 inline tests passed |
| `kujo run scent.kujo help` | 0 | Clean usage output |
| `kujo run scent.kujo version` | 0 | `Scent 1.0.0` |
| `kujo run scent.kujo --version` | 0 | `Scent 1.0.0` |
| `kujo run scent.kujo pack --task "baseline smoke" --dry-run --json` | 0 | Passed; the repository itself is slow enough that a 30-second Eval wrapper can time out under concurrent load |

## Confirmed Bugs

### BUG-001 — Secret recognition occurred after file clipping

- Severity: High
- Subsystem: Redaction / file clipping
- Contract/invariant violated: Recognized secrets must be sanitized before artifact output; documentation explicitly promises a redaction-first pipeline.
- Minimal reproduction: create `secret.txt` containing `sk-ABCDEFGHIJKLMNOPQRSTUVWXYZ123456`, then run `kujo run scent.kujo pack --task secret --include secret.txt --max-files 1 --max-file-bytes 10 --format json --out OUT --json`.
- Expected: no recognizable fragment of the token is emitted.
- Observed pre-fix: `context.json` contained `sk-ABCDEFG` because clipping destroyed the token shape before redaction.
- Root cause: `run_pack` called `clip_text` before `redact_text`.
- Files changed: `scent.kujo`.
- Fix: redact the complete text first, then UTF-8-safely clip the sanitized content; retain only redaction records whose placeholders survive final budgeting.
- Regression test: `redaction runs before file-size clipping`.
- RED evidence: baseline `622ba30`; exact command above; raw prefix survived; exit 0.
- GREEN evidence: fixed `2775035b690660f8b1caa4d1858f04b80c148c07`; same command; raw prefix absent and test passed.
- Backtest: baseline FAIL; fixed PASS.
- Related tests: redaction matrix, budget/redaction consistency, full inline suite.
- Full-suite result after fix: 16/16 passed.
- Regression risk: Low; order changed only within the documented redaction-first boundary.

### BUG-002 — `--max-file-bytes` counted characters, not UTF-8 bytes

- Severity: Medium
- Subsystem: File-size clipping
- Contract/invariant violated: A byte-named limit must cap emitted UTF-8 bytes without splitting a character.
- Minimal reproduction: write `12345678éZ` and pack it with `--max-file-bytes 10`.
- Expected: emitted content `12345678é`, marked truncated, totaling 10 UTF-8 bytes.
- Observed pre-fix: all 11 bytes were emitted and the file was not marked truncated.
- Root cause: `len()`/`substring()` operate on characters while the option is byte-based.
- Files changed: `scent.kujo`.
- Fix: compute UTF-8 byte length through base64 length and binary-search the largest character-safe prefix within the byte limit.
- Regression test: `max-file-bytes is a UTF-8 byte limit`.
- RED evidence: baseline `622ba30`; `--max-file-bytes 10`; 11 bytes emitted, `truncated=false`.
- GREEN evidence: fixed `2775035b690660f8b1caa4d1858f04b80c148c07`; 10 bytes emitted, `truncated=true`.
- Backtest: baseline FAIL; fixed PASS.
- Related tests: zero/one/exact/+1 byte fixtures, CRLF, no-final-newline, content-hash verification.
- Full-suite result after fix: 16/16 passed.
- Regression risk: Medium; clipping now performs additional bounded work proportional to log character count.

### BUG-003 — Reused output directories retained stale optional formats

- Severity: Medium
- Subsystem: Output lifecycle
- Contract/invariant violated: a fresh run must describe the current invocation and artifact list.
- Minimal reproduction: run `--format both --out OUT`, then `--format md --out OUT`.
- Expected: `OUT/context.json` no longer exists after the Markdown-only run.
- Observed pre-fix: stale `context.json` remained even though the new manifest did not list it.
- Root cause: the writer overwrote requested artifacts but never removed the mutually exclusive old context artifact.
- Files changed: `scent.kujo`.
- Fix: remove stale `context.json` for `md` runs and stale `context.md` for `json` runs.
- Regression test: `output reuse removes stale optional context artifacts` covers both directions.
- RED evidence: baseline `622ba30`; both→md and both→json; stale file remained.
- GREEN evidence: fixed `2775035b690660f8b1caa4d1858f04b80c148c07`; stale file absent in both sequences.
- Backtest: baseline FAIL; fixed PASS.
- Related tests: both→both, md→both, json→both, previous-output recursion fixture.
- Full-suite result after fix: 16/16 passed.
- Regression risk: Low; deletion is limited to the two known optional artifact filenames.

### BUG-004 — Git path parsing corrupted unusual filenames

- Severity: Medium
- Subsystem: Git-state enrichment
- Contract/invariant violated: Git metadata and candidate identity must preserve repository-relative paths exactly.
- Minimal reproduction: commit files named `odd\nname.txt` and ` leading and trailing .txt `, modify both, and pack with `--changed`.
- Expected: exact names appear in `changed_files` and match `files.json` paths.
- Observed pre-fix: the newline-bearing path was Git-quoted and the whitespace-bearing path was trimmed.
- Root cause: newline-delimited Git output plus `trim()` was used as a path protocol.
- Files changed: `scent.kujo`.
- Fix: request `-z`, split NUL records, and never trim path data.
- Regression test: `git metadata preserves unusual path names exactly`.
- RED evidence: baseline `622ba30`; paths became `"odd\\nname.txt"` and `leading and trailing .txt`.
- GREEN evidence: fixed `2775035b690660f8b1caa4d1858f04b80c148c07`; byte-exact path identities preserved.
- Backtest: baseline FAIL; fixed PASS.
- Related tests: staged, unstaged, untracked, rename, deletion, and space-bearing names.
- Full-suite result after fix: 16/16 passed.
- Regression risk: Low; NUL-delimited output is Git's unambiguous machine format.

### BUG-005 — Recognized tokens in task text leaked into artifacts

- Severity: High
- Subsystem: Redaction / metadata
- Contract/invariant violated: once Scent recognizes a supported token shape, the original value must not survive sanitized artifacts.
- Minimal reproduction: pass `--task "audit sk-ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"` and write a `both` pack.
- Expected: the token is replaced everywhere emitted.
- Observed pre-fix: it appeared in `context.md`, `context.json`, and `metadata.json` flags.
- Root cause: redaction was applied only to selected file content.
- Files changed: `scent.kujo`.
- Fix: redact task text before scoring/output and sanitize each recorded command argument.
- Regression test: `recognized secrets in task text are redacted from artifacts`.
- RED evidence: baseline `622ba30`; token present in three artifacts on two runs.
- GREEN evidence: fixed `2775035b690660f8b1caa4d1858f04b80c148c07`; token absent from all six artifacts and placeholder present.
- Backtest: baseline FAIL; fixed PASS.
- Related tests: provider-token matrix and verbose/stdout review.
- Full-suite result after fix: 16/16 passed.
- Regression risk: Medium; secret-like task terms no longer participate verbatim in relevance scoring.

### BUG-006 — `files.json` contradicted selected context files

- Severity: Medium
- Subsystem: Artifact contract
- Contract/invariant violated: artifact representations from one run must agree on selected paths and reasons.
- Minimal reproduction: pack one explicitly included `app.txt` with `--format json`.
- Expected: `context.json.selected_files[0]` and `files.json[0]` both mark `app.txt` selected with the same reason.
- Observed pre-fix: `context.json` selected the file while `files.json` reported `selected=false` and an exclusion reason.
- Root cause: candidate dictionaries were modified through copied loop values and never assigned back to the candidate array.
- Files changed: `scent.kujo`.
- Fix: persist the updated candidate and copy the final included-file reason into the inventory.
- Regression test: `files inventory agrees with selected context files`.
- RED evidence: baseline `622ba30`; selected count 1 versus inventory selected count 0.
- GREEN evidence: fixed `2775035b690660f8b1caa4d1858f04b80c148c07`; path, selected state, and reason agree.
- Backtest: baseline FAIL; fixed PASS.
- Related tests: artifact consistency across `md`, `json`, and `both`.
- Full-suite result after fix: 16/16 passed.
- Regression risk: Low; this only corrects serialized inventory state.

### BUG-007 — Unreadable selected files received a false relevance reason

- Severity: Low
- Subsystem: File reading / manifest provenance
- Contract/invariant violated: a manifest decision must state the actual reason content was excluded.
- Minimal reproduction: explicitly include a mode-`000` file and pack it.
- Expected: exclusion states that reading failed.
- Observed pre-fix: manifest said `not selected by deterministic relevance`, despite an explicit include and read failure.
- Root cause: read failures were dropped and later generic candidate finalization overwrote provenance.
- Files changed: `scent.kujo`.
- Fix: retain read failures by path and use them in the exclusion reason.
- Regression test: `selected unreadable files receive an accurate exclusion reason`.
- RED evidence: baseline `622ba30`; false relevance reason reproduced twice.
- GREEN evidence: fixed `2775035b690660f8b1caa4d1858f04b80c148c07`; reason contains `could not be read`.
- Backtest: baseline FAIL; fixed PASS.
- Related tests: no-selected-files warning and manifest uniqueness.
- Full-suite result after fix: 16/16 passed.
- Regression risk: Low; decision remains exclusion, only provenance changes.

### BUG-008 — Valid `package.json` scripts were never discovered

- Severity: Medium
- Subsystem: Command discovery
- Contract/invariant violated: validation commands should be reported when the repository explicitly defines the corresponding scripts.
- Minimal reproduction: create `{"scripts":{"test":"x","lint":"x","build":"x"}}` and pack.
- Expected: `npm test`, `npm run lint`, and `npm run build`.
- Observed pre-fix: `commands` was empty on repeated runs.
- Root cause: runtime type names are lowercase `dict`; code compared against `Dict`.
- Files changed: `scent.kujo`.
- Fix: use the runtime's correct type name and retain sorted/deduplicated output.
- Regression test: `package scripts produce justified validation commands`.
- RED evidence: baseline `622ba30`; `commands=[]` twice.
- GREEN evidence: fixed `2775035b690660f8b1caa4d1858f04b80c148c07`; three justified commands emitted alphabetically.
- Backtest: baseline FAIL; fixed PASS.
- Related tests: missing scripts, malformed JSON, unknown scripts.
- Full-suite result after fix: 16/16 passed.
- Regression risk: Low.

### BUG-009 — Changed-file union contained duplicates

- Severity: Medium
- Subsystem: Git-state enrichment
- Contract/invariant violated: `changed_files` is a union and each repository path must occur once.
- Minimal reproduction: stage a modification to `both.txt`, modify it again, then pack with `--changed`.
- Expected: `changed_files=["both.txt"]`, while staged and unstaged lists each contain the path.
- Observed pre-fix: `changed_files=["both.txt","both.txt"]`.
- Root cause: the helper mutated a copied dictionary, so the caller's seen set did not retain membership.
- Files changed: `scent.kujo`.
- Fix: update seen maps in the owning scope before pushing paths.
- Regression test: `changed-file union deduplicates staged and unstaged paths`.
- RED evidence: baseline `622ba30`; duplicate path reproduced in all flag modes.
- GREEN evidence: fixed `2775035b690660f8b1caa4d1858f04b80c148c07`; union is unique while component lists remain accurate.
- Backtest: baseline FAIL; fixed PASS.
- Related tests: staged/unstaged/untracked matrix and exact path parsing.
- Full-suite result after fix: 16/16 passed.
- Regression risk: Low.

### BUG-010 — Artifact writes followed pre-existing symlinks

- Severity: High
- Subsystem: Output path safety
- Contract/invariant violated: a reused output directory must not redirect known artifact writes to an unrelated file.
- Minimal reproduction: symlink `OUT/context.json` to `victim.json`, then run a JSON pack to `OUT`.
- Expected: victim remains unchanged; the symlink is replaced by a regular artifact.
- Observed pre-fix: victim was overwritten through the symlink on two runs.
- Root cause: `write_file(..., overwrite=true)` followed the existing symlink.
- Files changed: `scent.kujo`, `SECURITY.md`.
- Fix: detect directory entries without dereferencing, remove an artifact symlink, then write the regular file.
- Regression test: `artifact writes replace symlinks instead of following them`.
- RED evidence: baseline `622ba30`; victim contents replaced with context JSON.
- GREEN evidence: fixed `2775035b690660f8b1caa4d1858f04b80c148c07`; victim sentinel unchanged and artifact is a regular file.
- Backtest: baseline FAIL; fixed PASS.
- Related tests: output reuse and symlink selector/traversal tests.
- Full-suite result after fix: 16/16 passed.
- Regression risk: Low; scope is restricted to exact artifact filenames.

### BUG-011 — Traversal and command sorting discarded return values

- Severity: Medium
- Subsystem: Deterministic traversal / command ordering
- Contract/invariant violated: documented selection and emitted command order must be deterministic and alphabetically tie-broken.
- Minimal reproduction: create files in order `z.txt`, `a.txt`, `m.txt`; pack an unrelated task that uses fallback selection.
- Expected: `a.txt`, `m.txt`, `z.txt`.
- Observed pre-fix: `z.txt`, `m.txt`, `a.txt` (filesystem insertion order). Command discovery similarly retained insertion order.
- Root cause: Kujo `sort()` returns a sorted array rather than mutating in place; both calls discarded the return value.
- Files changed: `scent.kujo`.
- Fix: assign `entries = sort(entries)` and return `sort(uniq)`.
- Regression test: `fallback traversal uses alphabetical directory order`; package-command test protects command order.
- RED evidence: baseline `622ba30`; non-alphabetical fallback order reproduced twice.
- GREEN evidence: fixed `2775035b690660f8b1caa4d1858f04b80c148c07`; alphabetical order.
- Backtest: baseline FAIL; fixed PASS.
- Related tests: three repeated deterministic packs comparing paths, scores, reasons, and file manifest decisions.
- Full-suite result after fix: 16/16 passed.
- Regression risk: Low; behavior now matches the documented contract.

### BUG-012 — Malformed `Cargo.toml` produced unjustified commands

- Severity: Low
- Subsystem: Command discovery
- Contract/invariant violated: Scent should only report validation commands justified by a valid repository configuration.
- Minimal reproduction: create `Cargo.toml` containing `not = [valid`, then pack.
- Expected: no Cargo commands.
- Observed pre-fix: `cargo test` and `cargo fmt -- --check` were emitted on repeated runs solely because the filename existed.
- Root cause: Cargo discovery checked existence but not parseability.
- Files changed: `scent.kujo`.
- Fix: read and parse TOML successfully before suggesting Cargo commands.
- Regression test: `malformed Cargo metadata does not suggest Cargo commands`.
- RED evidence: baseline `622ba30`; both Cargo commands emitted.
- GREEN evidence: fixed `2775035b690660f8b1caa4d1858f04b80c148c07`; command list empty.
- Backtest: baseline FAIL; fixed PASS.
- Related tests: valid Cargo metadata, malformed/valid package metadata, Makefile and Justfile discovery.
- Full-suite result after fix: 16/16 passed.
- Regression risk: Low.

## Rejected Hypotheses

1. **Malformed CLI values bypass validation.** Empty/whitespace tasks, unknown commands/flags, zero/negative bounds, invalid target/format, and missing `pack` all returned exit 2. Rejected.
2. **Help/version combinations emit parser noise.** All documented forms stayed clean with exit 0. Rejected.
3. **Repository discovery fails in nested directories or worktrees.** Deep nesting, `.git` directory, `.git` worktree file, paths with spaces, and non-Git degraded mode behaved consistently. Rejected.
4. **Selector containment permits `..`, outside absolute paths, or symlink segments.** Each was rejected; repository traversal skipped symlinks. Rejected.
5. **Root and trailing-slash selector normalization breaks selection.** `.`, `./`, repeated `./`, and trailing slashes normalized correctly. Rejected.
6. **Explicit includes disappear after the 2,000-candidate baseline cap.** Existing and repeated cap fixtures selected the late explicit include. Rejected.
7. **NUL-bearing extensionless files leak binary content.** NUL at the beginning and later in an extensionless file caused omission. Rejected.
8. **Supported provider-token patterns or private keys leak in ordinary unclipped files.** OpenAI, GitHub, fine-grained GitHub, AWS, Stripe, JWT, authorization, key/value credentials, and complete private-key blocks were sanitized; benign code remained. Rejected.
9. **Content hashes describe source rather than emitted content.** Hashes matched exact JSON-decoded emitted content across empty, clipped, CRLF, and no-final-newline fixtures. Rejected.
10. **Budget arithmetic creates duplicate decisions or stale redactions.** Boundary fixtures produced one decision per path and redactions only for emitted placeholders. Rejected.
11. **Dry-run mutates the filesystem.** Hash snapshots of source and an existing output directory were unchanged; no artifacts were created. Rejected.
12. **Markdown fences or JSON encoding break on adversarial content.** Nested fences used longer delimiters and all JSON artifacts parsed. Rejected.
13. **Scoring is nondeterministic after sort repair.** Three identical runs produced byte-equivalent selected-file and file-manifest decisions after removing timestamps. Rejected.
14. **Malformed `package.json` or absent Make/Just targets generate commands.** They did not. Rejected.

## Needs Specification

1. **Include/exclude precedence.** Current behavior lets exclusion win, including when the same path is explicitly included. Documentation says both may repeat but does not define precedence.
2. **Repeated scalar flags.** Repeating `--task`, `--budget`, or other scalar options is accepted by the runtime parser, but first-versus-last behavior is not documented.
3. **Git flags as filters versus priorities.** Current `--changed`, `--staged`, and `--unstaged` behavior adds scores; it does not strictly filter candidates. The reference describes focusing but does not state a filtering invariant.
4. **Secret-shaped filenames and selectors.** Recognized secrets in task text and content are now sanitized, but repository path identity is emitted verbatim. Redacting path components would affect provenance and selector identity, so this needs an explicit metadata policy.

No production behavior was changed for these four findings.

## Validation Matrix

| Surface | Final result |
| --- | --- |
| Kujo check | PASS — `kujo check scent.kujo` |
| Full inline Kujo tests | PASS — 16/16 |
| Repository-prescribed Kujo tests | PASS — exit 0, 0 fixture tests discovered |
| CLI help | PASS |
| CLI version / `--version` | PASS |
| Dry run | PASS; no filesystem change |
| Path containment fixtures | PASS |
| Redaction fixtures | PASS |
| Budget fixtures | PASS |
| Artifact consistency | PASS |
| Output reuse | PASS |
| Determinism | PASS |
| ShipCheck gate | PASS — exit 0; warnings only |
| Concord scan | PASS — exit 0; two non-blocking repository-structure findings |
| Eval suite | FAIL — 3/4; repository dry-run command exceeds Eval's default 30-second timeout (pre-existing baseline limitation) |
| CI artifact guard | PASS |

## Change Summary

- Production files modified: `scent.kujo`
- Test files modified: inline test section of `scent.kujo`, `tests/README.md`
- Documentation modified: `README.md`, `docs/scent.md`, `SECURITY.md`, `CHANGELOG.md`
- Regression tests added: 12
- Bugs fixed by subsystem: redaction/security 3; clipping 1; Git state 2; artifact/output lifecycle 3; command discovery 2; deterministic traversal 1
- Final verification commands:
  - `kujo check scent.kujo`
  - `KUJO_BIN=kujo kujo test`
  - `KUJO_BIN=kujo kujo test-run scent.kujo -v`
  - `kujo run scent.kujo help`
  - `kujo run scent.kujo version`
  - `kujo run scent.kujo --version`
  - isolated `kujo run scent.kujo pack --task "final regression smoke" --dry-run --json`
  - ShipCheck `gate --format json`
  - Concord `scan --format json`
  - Eval `run tests/scent_eval.json`
  - `.github/scripts/check-kujo-tool-artifacts.sh`
- Remaining known limitations: the four needs-specification items above; redaction remains best-effort/pattern-based; the repository-level smoke can exceed a 30-second external timeout under concurrent CPU load; `kujo test` does not discover inline tests, so `kujo test-run scent.kujo` remains necessary.
