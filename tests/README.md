# Scent Tests

Scent keeps its deterministic smoke tests inline in `scent.kujo` so they can be
run by the Kujo test runner without a separate fixture harness.

The inline suite includes regression coverage for selector scope, symlink and
binary traversal, output reuse, redaction parsing, Markdown containment, bounded
explicit includes, and budget manifest/redaction consistency.

Release smoke commands:

```bash
kujo check scent.kujo
kujo run scent.kujo pack --task "smoke" --dry-run --json
```
