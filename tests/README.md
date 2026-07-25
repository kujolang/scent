# Scent Tests

Scent keeps its deterministic smoke tests inline in `scent.kujo` so they can be
run by the Kujo test runner without a separate fixture harness.

Release smoke commands:

```bash
kujo check scent.kujo
kujo run scent.kujo pack --task "smoke" --dry-run --json
```
