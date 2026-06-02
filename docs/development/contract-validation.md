# Contract Validation

<!-- task: TASK-010 -->

TASK-010 turns the accepted planning contracts into repeatable local checks before model, GPU, worker, or UI code lands.

## Command

Run the full local validator from the repository root:

```bash
uv run validate-contracts --repo .
```

Run tests:

```bash
uv run pytest
```

The validator checks:

- Scene Storyboard JSON Schema and example storyboards.
- Storyboard semantic rules, including authorized identity assets, deterministic scene order, target duration, asset-ref types, prohibited executable fields, and visual-emphasis text.
- OpenAPI documented paths, required schemas, and enum references.
- Cross-contract vocabulary consistency for manifest stages, job/segment/review/release/asset states, QC statuses, failure codes, and audit events.
- RepoFrame harness health, where harness errors are fatal and warnings are non-fatal.

Outside a Codex environment, skip the local RepoFrame harness path:

```bash
uv run validate-contracts --repo . --skip-harness
```

## Source Of Truth

The validator reads the accepted contract documents as source of truth:

- `docs/contracts/artifact-manifest.md` for manifest stages and stage mapping.
- `docs/contracts/job-state-machine.md` for job, segment, review, and release states.
- `docs/security/asset-governance.md` for asset states and audit event families.
- `docs/quality/failure-taxonomy.md` for canonical failure codes.
- `docs/quality/qc-matrix.md` for QC statuses and stage failure-code usage.
- `docs/product/api-console.md` for documented API paths.

Avoid adding a second hand-maintained enum source unless a later task explicitly accepts that migration.

## Regression Rule

When review or acceptance finds a validator coverage gap, add a negative regression test for that exact gap before closing the task. For OpenAPI checks, cover both docs-derived vocabulary and structural presence: HTTP method plus path, required field plus property definition, expected enum/reference shape, and stable failure reporting for malformed YAML.
