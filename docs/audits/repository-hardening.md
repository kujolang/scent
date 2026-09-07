# Scent repository hardening — 2026-09-07

## Repository and scope

- Repository: `kujolang/scent`; branch: `main`.
- Starting SHA: `6e72cd06bf422a29e93148cf4edaddd98d937392`; working tree was clean.
- Ending SHA of audited implementation: `cdf6e7668824d2e52dd1155bddc5d12912fc5f2f`. This evidence report is committed separately; its own commit cannot embed its own hash.
- Purpose: local, deterministic task-context selection, redaction, and Markdown/JSON handoff generation.
- Dependencies: Kujo runtime, Git, and `realpath` in a POSIX environment. No Scent package dependencies, network/provider calls, database, server, or background workers. Python 3/Bash are verification-only dependencies.
- Integrations: Scout/RAG/MCP context workflows and downstream consumers of six documented artifacts. Readiness metadata invokes Eval, ShipCheck, and Concord. No sibling repository was modified.
- The 3,250-line entrypoint, inline suite, 16-file tracked inventory, prior audit, spec/Eval definitions, release metadata, artifact guard, and workflow were reviewed. Kujo collection, clock, process, safe-read, and file-publication implementations were inspected read-only to verify runtime contracts.
- Broad repository scans excluded `.git`, `out`, `.scent`, and `target`; generated local evidence is retained under `out/audit` and `out/verification` and is not committed.

## Baseline

The pre-change source is preserved locally at `out/audit/baseline.kujo`. Validation used the checksum-verified official Kujo **1.3.1 macOS x64** release. The previously suggested runtime location was initially unavailable at that path; the audit installed an isolated runtime under ignored `out/audit/runtime`, without changing the system runtime.

| Check | Before changes |
| --- | --- |
| `kujo check scent.kujo` | Passed |
| `KUJO_BIN=... kujo test-run scent.kujo` | **15/16**, 369.181 seconds; one pre-existing failure. The nonverbose runner did not identify the failing test; the large explicit-include subprocess reached its timeout during this run. Do not infer 16/16 from exit-only or zero-test checks. |
| New seven-case CLI harness against preserved source | 1 passed, 5 failed, 1 timed out, 214.335 seconds |
| Lint | Exit 0, 37 advisory warnings: 26 error-handling-pattern, 11 unreachable-code |
| Formatter `--check --json` | Reported existing formatting drift; no formatting churn applied |
| 24-file representative benchmark | Three runs per mode; medians below |
| 120-file exploratory benchmark | First both-format run exceeded the harness's existing 120-second bound; no latency value or percentage inferred |
| Existing Eval history | Prior audit documented 3/4 with a 30-second self-repository smoke timeout; this session also reproduced 3/4 before final smoke isolation, with another load-dependent recurrence after the implementation changes |

The five failing new cases reproduced mixed-token leakage, missing source-line redaction provenance, noncanonical exclusions, symlink-based command discovery, and inconsistent output error presentation. The timeout case exercised excluded-tree traversal. Two additional backtests both failed as predicted: artifact writes overwrote the hard-link victim, and concurrent default runs returned the same directory. Both pass on the fixed source; see local `baseline-extra.log` and current CLI tests.

## Findings

| ID | Priority | Area | Finding and evidence | Action | Status |
| --- | --- | --- | --- | --- | --- |
| SCT-01 | P1 | Security | Provider-token handling returned before JWT handling on the same line; reproduced in file/task artifacts. | Apply all token families before emitting a line; regression checks every artifact. | Fixed |
| SCT-02 | P1 | Provenance | Removing multiline private keys shifted output lines; source-line indexes were then used against output lines and discarded later audit records. | Keep an internal source-to-output map only for redacted lines; retain unchanged public source line numbers. | Fixed |
| SCT-03 | P1 | Selectors | `docs//./private.txt` did not match the walked canonical path; an excluded marker was emitted. | Normalize redundant separators and dot segments after validating scope; document exclude-wins. | Fixed |
| SCT-04 | P1 | Filesystem reads | Command discovery read a symlinked external `package.json`; traversal checks alone did not protect reads from replacement races. | Use `read_file_beneath` for selected content and configuration; omit symlinked instruction references. | Fixed |
| SCT-05 | P1 | Publication | In-place writes could alter another hard-link target, partially replace artifacts, and emit an uncaught runtime diagnostic. | Private staging plus atomic rename, preserved ordinary permission bits, cleanup, and concise exit-4 errors. | Fixed |
| SCT-06 | P1 | Selection cost | `sort_scored` compared every pair of candidate dictionaries. | Group by score and natively sort primitive score/path keys; retain exact tie order. | Fixed |
| SCT-07 | P1 | Traversal | Exclusions were applied after the 2,000-candidate cap, so excluded trees consumed capacity and work. | Prune excluded paths before descent and counting, including explicit directory scans. | Fixed |
| SCT-08 | P2 | Git/resource cost | Each Git path repeatedly copied nested result collections and duplicate membership maps. | Stable native unions, NUL-delimited bulk summary construction, native exact candidate membership, and explicit argv processes; reject truncated results as incomplete. | Fixed |
| SCT-09 | P2 | Redaction/rendering | Ordinary text traversed all credential machinery; dry runs built discarded artifacts; JSON writes built discarded Markdown. | Conservative pattern prefilter, hoisted rule tables, safe prefix guards, early dry-run return, conditional Markdown. | Fixed |
| SCT-10 | P1 | Concurrency | Test fixtures used shared fixed `/tmp` names. Default production pack names used `now()`, whose runtime implementation has one-second resolution. | Unique test roots and UUID suffixes on default pack directories; concurrent CLI regression. | Fixed |
| SCT-11 | P1 | Verification | CI only checked artifact hygiene; readiness spec invoked `kujo test`, which discovers no inline tests. | Pin/checksum runtime in CI; run static check, 16 inline tests, Python CLI regressions, artifact guard. | Fixed |
| SCT-12 | P2 | Portability/docs | Eval embedded one developer's absolute checkout; old priorities incorrectly said Git metadata needed restoration. | Relative Eval paths and an isolated three-file CLI smoke with stronger receipt/no-write assertions; correct verification command and current contracts. | Fixed |
| SCT-13 | P2 | Context budget | Full metadata/framing is outside the reported token estimate and can exceed `--budget`; measured below. | Preserve compatible schema/selection, document scope; separate full-artifact budget design needed. | Open design |
| SCT-14 | P2 | State/security | Six artifact replacements are not a transaction; directory parents must remain trusted. | Document one explicit output directory per writer and reject sharing failed packs; default directories now unique. | Explicit boundary; future transaction design |
| SCT-15 | Needs specification | Metadata privacy | Paths/Git metadata retain identity and can themselves contain secrets; Git ignore rules are not a content-selection security boundary; already captured in SignalBox as `cap_a80cbe08-3fbf-472c-9f9f-497eab72a8e1`. | Preserve identity; document sensitive metadata and untrusted packed content. | Existing policy question; no duplicate capture |
| SCT-16 | P3 | Static hygiene | Formatter drift and heuristic lint warnings predate this audit. | Preserve unrelated formatting; record warnings rather than disabling checks. | Not worth broad churn |

No demonstrated P0 defect remains. Prior unresolved selector precedence and Git-focus semantics are now documented as existing exclude-wins and priority behavior; behavior was not redesigned.

## Changes implemented and compatibility proof

### Redaction and provenance — `scent.kujo`, `tests/hardening.py`

The root causes were an early return between token families and confusion between original and emitted line numbers. Mixed tokens are now redacted together. A small internal line map preserves audit records after collapsed private-key blocks without adding fields to public redaction records. The map stores only lines with redactions, not every source line.

The prefilter is a conservative superset of every supported rule: assignments require `=`/`:`, private keys require a begin marker, provider patterns require their literal prefix, and JWTs require their exact existing shape. Ordinary text can therefore bypass processing without removing validation for any supported pattern. Existing provider, assignment, binary, Unicode, clipping, and task-secret tests remain enabled.

### Filesystem and failures — `scent.kujo`, `tests/hardening.py`, `SECURITY.md`

Safe reads use the trusted repository root, exact relative paths, no-follow component traversal, regular-file validation, and the runtime's **existing 8 MiB ceiling**. Whole source text is still redacted before clipping. Read failures retain exclusion provenance; configuration failures do not manufacture commands.

Each artifact starts as an owner-only private file in its destination directory. Existing regular-file ordinary permission bits are applied before atomic rename; fresh files remain `0600`. Final symlinks and hard links are replaced, not followed. Failed publication preserves the existing destination and cleans staging files where possible; cleanup failures are included in the error. Tests verify old hard-link targets, failed directory replacement, permissions, format reuse, failure exit 4, and exact/over-limit UTF-8 writes. The private publication API does not itself impose the original write ceiling, so Scent explicitly retains the 8 MiB per-artifact limit before staging.

This uses Kujo 1.3.1 POSIX primitives and is now an explicit minimum runtime/environment requirement. Directory parents and the repository root remain trusted. This is per-file atomic publication, not a six-file transaction or a hostile shared-directory sandbox.

### Selection, subprocesses, resources — `scent.kujo`

Native score/path sorting removes quadratic **pairwise comparisons**. No claim is made that every collection operation in the entire pipeline is linear or that every workload improves by the same factor. A separate ordering oracle checks 64 mixed-score paths, including Unicode/newlines; the end-to-end benchmark checks selected-file and decision fingerprints.

Excluded trees are pruned before the existing traversal cap. This intentionally allows later eligible files to be considered when earlier excluded trees formerly exhausted capacity. All other scoring weights, fallback rules, order, maximum-file selection, and exclusion precedence remain unchanged.

The unchanged 2,001-file regression was deliberately retained: an intermediate final run still exceeded 120 seconds, exposing residual Git-wide copying. Native delimiter operations and list joining fixed that remaining cost; the completed 14-case suite passes in 66.414 seconds without fixture reduction or a timeout increase.

Git retains the same five commands and exact NUL-delimited UTF-8 path protocol, but launches them without shell wrappers. Native stable unions retain staged/unstaged/untracked order and deduplication. Native NUL split/slice and bulk prefix construction avoid growing per-path arrays. Exact native array membership avoids building Git-wide copied dictionaries for excluded paths, while explicit integer conversion preserves existing inventory flag types. Markdown lists use native joining. Truncated process output is not parsed as complete. No retry loop, cache, network service, or new package dependency was introduced.

Three private helpers with no remaining callers were removed: `shell_quote`, `split_lines`, and `is_instruction_rel`. Test-local quoting helpers remain because the inline harness uses shell fixtures. The single-file layout and independent inline-test helpers were preserved; a broad module rewrite would add risk without evidence of benefit.

### Agent/output ergonomics and regression gates

`bash scripts/verify.sh` resolves the runtime, scopes fixtures/logs to a unique directory, preserves detailed evidence, and emits concise pass/fail receipts. `tests/hardening.py` uses only Python's standard library and supports individual named cases. The new GitHub workflow pins both the Kujo release and archive checksum; the existing artifact guard remains enabled.

The spec now invokes `test-run`; Eval commands and `VERSION` checks are repository-relative. The old exit-only Eval smoke packed the changing checkout and still sometimes exceeded its unchanged 30-second wrapper after passing once. Its replacement exercises three deterministic fixture files, parses bounded JSON, checks selected count/token fields, and proves no output was written. This separates functional smoke from the explicitly measured repository-size workload; it does not claim the entire changing repository now packs within 30 seconds. README, reference, security guidance, contributor instructions, and changelog describe the actual implementation. Reproduction commands are centralized rather than duplicating a new agent instruction file. No MCP schema, prompt package, Skill, AI provider interface, or model configuration exists in this repository to optimize.

## Performance and efficiency

Raw samples, fingerprints, checksums, and budget evidence are committed in [evidence/measurements.json](evidence/measurements.json). Benchmark: 24 deterministic Markdown files, eight ordinary context lines per file, ten selected files, three runs per mode, full CLI invocation including Git and startup.

| Dimension | Before | After |
| --- | ---: | ---: |
| Both formats, median elapsed | 49.1579 s | 28.9445 s |
| JSON only, median elapsed | 36.9744 s | 18.7078 s |
| Dry run, median elapsed | 26.1318 s | 15.6784 s |
| Selected files | 10 | 10 |
| Reported content token estimate | 525 | 525 |
| Both-format JSON context bytes | 11,601 | 11,601 |
| JSON-only context bytes | 11,583 | 11,583 |
| Stdout bytes: both / JSON / dry | 370 / 287 / 202 | 370 / 287 / 202 |
| Runtime package dependencies | 0 | 0 |
| Selection/content/decision fingerprint | `746c8ea259a7ad90d872799495d858d2fdd417721fc161b0dfb6116fbb1c3f8e` | Identical |

These wall-clock samples were collected on a **shared host with concurrent workloads**. Their spread is retained; they are evidence of the observed workload, not an isolated causal attribution, production SLA, or stable timing ratchet. The timestamp, temporary repository path, and metadata duration are excluded from semantic fingerprints. A separate Markdown comparison, including a newline-bearing filename, is byte-identical after timestamp normalization; its receipt is also preserved. No memory/RSS, CPU, binary-size, or exact-model-token improvement is claimed. Source inspection supports fewer comparisons, shell launches, temporary collections, and unused rendering, but does not measure peak RSS.

A separate 40-file fixture demonstrates the remaining token-envelope distinction:

| Requested budget | Reported estimate | Included files | Full Markdown chars/4, rounded up | Full JSON chars/4, rounded up |
| ---: | ---: | ---: | ---: | ---: |
| 1,450 | 5 | 1 | 2,591 (10,364 bytes) | 4,071 (16,282 bytes) |

Those are explicitly **character heuristics**, not measured model-token counts. Changing existing estimates or removing metadata to force a full-artifact limit would change established behavior. A future explicit full-artifact mode should retain detailed evidence separately and preserve old consumers.

## Review coverage and remaining work

| Surface | Review outcome |
| --- | --- |
| CLI/API/schema/config | Flags, six artifact names, JSON schema version and fields, target selection, numeric validation and exit categories reviewed; no new flags/config/env requirements. |
| Persistence/concurrency | No database, queue, cache or daemon. Default directories isolated; per-artifact publication atomic; whole-pack transaction remains outside the contract. |
| Resource bounds | Traversal cap 2,000 per scan, depth 20, explicit selection/file caps, 8 MiB runtime reads/writes and bounded subprocess output retained. Git/inventory metadata still has a separate footprint from the content budget. |
| Security | User arguments, selector paths, repository symlinks, source/config reads, output links, secret patterns, metadata identity, process argv and truncated output reviewed. No network/SSRF surface or automatic execution of discovered commands. |
| Dead weight/dependencies | No removable external dependencies or abandoned release workflows found. Only proven unused private helpers removed. |
| Docs/agent context | Correct commands and scope, documented failure interpretation, source ordering, budget limits, unique fixtures, concise verification receipt. |
| Releases | VERSION, CLI and badge stay 1.0.0; no package release or unrelated publication performed. |

- **P0/P1:** No known remaining demonstrated regression from this pass.
- **P2:** Design a compatible full-artifact budget; consider transactional publication if same-directory multiwriter/recovery becomes a supported requirement.
- **Needs more evidence/specification:** Metadata/path redaction policy and large, dedicated-runner resource profiles; repeated scalar flags remain runtime-parser behavior.
- **P3 / not worth changing:** Broad formatting changes, replacing independent inline helpers, reorganizing the single script, or removing runtime-bounded checks for speed.

## Compatibility

- Public API: CLI/artifact interface retained; private helper implementations/signatures changed, with no repository import consumers found.
- CLI: same flags and exit categories. Corrected exclusions and errors; default output directories gain UUID suffixes; fresh artifact permissions tighten to `0600`. Explicit output reuse remains supported.
- Files/formats/schemas: same six names, optional-format behavior, JSON field shapes and `schema_version` 1.0.0. Original redaction source line numbers retained.
- Configuration/environment: no new production configuration or required environment variable. `SCENT_TEST_ROOT` is optional, test-only; existing `KUJO_BIN`/`SCENT_SCRIPT` remain test controls.
- Runtime/platform: **Kujo 1.3.1+ on POSIX** is now explicit because safe-read/private-publication primitives are used. Consumers on older runtimes must update their runtime.
- Consumers: ordinary packs preserve content/decision fingerprints. Consumers relying on permissive new-file modes or parsing timestamp-only default directory basenames must use the returned path and explicit sharing permissions.

## Cross-repository follow-ups

No sibling code change is required for current supported operation. Install the already released Kujo 1.3.1 or newer where older runtimes are deployed. The published documentation mirrors may adopt the new minimum-version/budget wording in their normal synchronization cycle; Scent does not require that update to function.

A distinct **Kujo runtime follow-up** was reproduced during optimization: the official Kujo 1.3.1 VM exits 4 with `Maximum VM call stack depth of 256 exceeded while calling <lambda>` on a flat 2,001-item filter/map inside a function. The same no-import, nonrecursive program exits 0 with `--interpreter`. See [the minimal fixture](evidence/kujo-vm-callback.kujo) and [captured results](evidence/runtime-callback.json). The affected contract is native higher-order collection callbacks; investigate VM callback frame accounting and add a flat-large-collection regression. This is related to, but distinct from, the existing imported-callback report `cap_90b21b7f-7541-4a04-9a80-2fec712bfb30`. **Scent does not require this fix:** production code uses native delimiter/collection operations and ordinary bounded loops, without those callbacks. No runtime or sibling source was changed.

Eval still emits unrelated interpreter diagnostic noise while reporting **4/4 checks passing**. ShipCheck passes with four advisory warnings, and Concord reports two pre-existing structural findings. These external tools were not modified, and their successful gates are not represented as clean diagnostic output.

## Verification receipt

All paths below are relative to this repository unless shown otherwise. `K` was the verified `out/audit/runtime/kujo`; each log remains available locally under `out/audit/` or the verification receipt directory.

```bash
out/audit/runtime/kujo --version
out/audit/runtime/kujo check scent.kujo
KUJO_BIN="$PWD/out/audit/runtime/kujo" out/audit/runtime/kujo test-run scent.kujo
KUJO_BIN="$PWD/out/audit/runtime/kujo" out/audit/runtime/kujo test-run scent.kujo -v
KUJO_BIN="$PWD/out/audit/runtime/kujo" SCENT_SCRIPT="$PWD/out/audit/baseline.kujo" python3 tests/hardening.py
KUJO_BIN="$PWD/out/audit/runtime/kujo" python3 tests/hardening.py
KUJO_BIN="$PWD/out/audit/runtime/kujo" python3 tests/hardening.py Hardening.test_concurrent_default_outputs_are_distinct -v
KUJO_BIN="$PWD/out/audit/runtime/kujo" bash scripts/verify.sh
out/audit/runtime/kujo run scent.kujo help
out/audit/runtime/kujo run scent.kujo version
out/audit/runtime/kujo run scent.kujo --version
out/audit/runtime/kujo lint scent.kujo
out/audit/runtime/kujo format scent.kujo --check --json
KUJO_BIN="$PWD/out/audit/runtime/kujo" python3 scripts/benchmark.py --files 24 --script out/audit/baseline.kujo --output out/audit/baseline-benchmark.json
KUJO_BIN="$PWD/out/audit/runtime/kujo" python3 scripts/benchmark.py --files 24 --output out/audit/completed-benchmark.json
PATH="$PWD/out/audit/runtime:$PATH" out/audit/runtime/kujo run ../eval/main.kujo --interpreter run "$PWD/tests/scent_eval.json" --output-dir "$PWD/out/audit/eval-isolated" --json
PATH="$PWD/out/audit/runtime:$PATH" out/audit/runtime/kujo run ../shipcheck/shipcheck.kujo gate --dir "$PWD" --format json
PATH="$PWD/out/audit/runtime:$PATH" out/audit/runtime/kujo run ../concord/concord.kujo -- scan --dir "$PWD" --format json
bash -n scripts/verify.sh .github/scripts/check-kujo-tool-artifacts.sh
python3 -m py_compile tests/hardening.py scripts/benchmark.py
git diff --check
bash .github/scripts/check-kujo-tool-artifacts.sh
```

Final status: static compilation, **16/16 inline tests**, **15/15 CLI hardening tests**, and artifact guard **passed**; the complete runner receipt is `out/verification/run.5awHFJ` (inline 221.866 seconds; its then-14-case Python suite 66.414 seconds); the subsequently added isolated Eval assertion is included in the final 15-case run at `out/audit/completed-hardening.log` (15/15, 83.335 seconds). Lint exits 0 with 43 advisory warnings (27 error-pattern warnings, including literal NUL decoding, plus 16 unreachable-code heuristics; exercised early-return/write paths are not actually unreachable). Formatting still reports the same pre-existing `needs_formatting` drift (exit 4). The obsolete exit-only, self-repository Eval invocation was replaced by stronger isolated CLI assertions; no assertion was weakened and no timeout was increased. The stable gates are behavior/static compilation, ordering/receipt assertions, and artifact hygiene; wall-clock timing and formatter churn are not silently turned into passing gates.

## Durable follow-up receipt

SignalBox admitted SCT-13: capture `cap_30ca9577-5086-471b-98f5-181bf8a3ce1e`, signal `sig_42c95a87-1428-4738-aa74-44e419ce2fba` (project `scent`). Exact-ID and conceptual retrieval both succeeded. SCT-15 was an existing duplicate and was not recaptured. Resolved changes, verification successes, selector/Git documentation repairs, and routine handoff details were rejected as Capture candidates. No downstream task or disposition was created. Session state and handoff belong in Strata, with this report as the detailed evidence source.

The distinct Kujo callback finding is capture `cap_45a88542-0bd3-4bc9-bacf-f9d1ed9992bb`, signal `sig_d4e21130-a9a0-4f37-a9a3-15ec52b62ae6` (project `kujo`). Exact-ID and conceptual retrieval both succeeded; the related imported-callback report was linked as existing evidence rather than recaptured. Total: two new Captures and two Signals, with the existing metadata-privacy observation skipped as a duplicate.
