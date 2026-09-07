# Scent Tests

Scent keeps its deterministic smoke tests inline in `scent.kujo` so they can be
run by the Kujo test runner without a separate fixture harness.

The inline suite includes regression coverage for selector scope, symlink and
binary traversal, output reuse, redaction parsing, Markdown containment, bounded
explicit includes, budget manifest/redaction consistency, UTF-8 byte clipping,
task-text redaction, exact and deduplicated Git path state, artifact selection consistency,
unreadable-file provenance, package/Cargo command discovery, and artifact
symlink replacement.
Fallback traversal and detected command ordering are also checked for stable
alphabetical output.

Release smoke commands:

```bash
kujo check scent.kujo
kujo run scent.kujo pack --task "smoke" --dry-run --json
```

## Complete verification

Run `KUJO_BIN=kujo bash scripts/verify.sh` from the repository root. This runs the
inline suite plus `tests/hardening.py` using Python's standard library, and the
artifact guard. Logs are saved to a unique `out/verification/run.*` directory.
Inline test fixture paths have unique IDs; the verification runner scopes them
under its evidence directory for failure inspection. Python fixtures clean up
automatically. A direct inline run may leave uniquely named `/tmp/scent_*`
fixtures for debugging.

The Python suite protects mixed JWT/provider redaction, source-line provenance,
normalized exclusions, pruning before candidate limits, no-follow command
discovery, atomic symlink/hard-link behavior, failure cleanup, permission
preservation, exact score/path ordering, dry-run receipts, and format reuse.
Additional cases enforce the 8 MiB write boundary, reject truncated process
output as complete, and verify concurrent default packs use distinct directories.
Run a named case with `python3 tests/hardening.py Hardening.test_mixed_tokens`.

Performance evidence: `KUJO_BIN=kujo python3 scripts/benchmark.py --files 24
--output out/benchmark.json` (one shell line). Runtime thresholds are deliberately
not CI gates; exact ordering, content fingerprints, and receipt size are stable
regression checks.

Eval's launch smoke calls `Hardening.test_isolated_eval_smoke`: three small
files in a temporary Git repository, the original three-file/byte limits,
parseable bounded JSON, and no output writes. This removes the old dependency
on the checkout's growing documentation without reducing assertions. Use the
benchmark separately to measure repository-size effects.
