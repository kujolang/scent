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
