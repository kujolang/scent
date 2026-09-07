# Changelog

All notable changes to Scent are documented here.

## Unreleased

- Harden repository reads, mixed-token redaction, source-line audit provenance, selector normalization, and atomic artifact publication with private defaults and preserved existing permissions (Kujo 1.3.1+, POSIX).
- Replace pairwise candidate sorting and repeated Git-union copying; prune excluded trees and skip unnecessary redaction and artifact rendering work without changing selection order or receipt schemas.
- Add portable CLI regressions, isolated inline fixtures, a repeatable benchmark, and checksum-pinned CI verification; correct the readiness spec to execute inline tests.

- Align README version badge with the stable CLI/runtime metadata.
- Add launch readiness spec and deterministic Eval suite for prelaunch review evidence.
- Fix ten verified context-pack defects covering mandatory subcommands, selector normalization, symlink and binary traversal safety, bounded explicit includes, reusable output directories, credential-line parsing, Markdown fence containment, and budget manifest/redaction consistency.
- Fix twelve evidence-backed regressions covering redaction-before-clipping, UTF-8 byte limits, stale format artifacts, safe artifact replacement, exact and deduplicated Git path state, task-text secret redaction, cross-artifact selection state, unreadable-file decision provenance, package/Cargo command discovery, and discarded sort results in traversal/command ordering.

## [1.0.0] - 2026-08-08

- Declared bounded context-pack selection, provenance, dry-run, artifact, and redaction-reporting contracts stable.
- Aligned the CLI, VERSION file, documentation, and public badge at 1.0.0.

## [0.1.0-kujo] - 2026-06-27

- Prepared Scent for public release with bounded context-pack generation, dry-run previews, Markdown/JSON artifacts, provenance metadata, and redaction reporting.
