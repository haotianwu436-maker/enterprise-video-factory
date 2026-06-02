# Implement contract validation scaffold

<!-- repo-init:managed -->

## Metadata

- ID: `TASK-010`
- Status: `done`
- Owner: `shared`
- Parent: `TASK-001`
- Created: `2026-05-30`
- Updated: `2026-06-02`

## Why

Start product-code landing with the safest enterprise slice: machine-checkable contract validators and local CI scaffolding for the accepted planning layer before any GPU/model runtime work.

## Scope

- In scope: repository runtime scaffold, schema/example validation, OpenAPI contract checks, failure-code/stage enum consistency checks, and local test commands
- Out of scope: TTS, avatar rendering, orchestration workers, web console, deployment manifests, or GPU benchmarks

## Acceptance Criteria

- A developer can run one local command to validate Scene DSL examples, OpenAPI contract shape, canonical stage/state/failure-code vocabularies, and RepoFrame harness health.
- Contract validators are implemented as product code or test tooling, not only ad hoc shell snippets.
- The scaffold preserves the accepted docs/contracts/schema/examples and does not introduce model/runtime dependencies.

## Product Acceptance

- User journey: `pending`
- Evidence required: runnable validation command, test output, and updated developer instructions
- Acceptance owner: `yanshou`
- Acceptance status: `passed`

## Dependencies

- Files: `schemas/scene-storyboard.schema.json`, `examples/storyboards/*.json`, `openapi/enterprise-video-factory.openapi.yaml`, `docs/contracts/artifact-manifest.md`, `docs/contracts/job-state-machine.md`, `docs/quality/failure-taxonomy.md`, `STATUS.md`
- Decisions: `DEC-001, DEC-002, DEC-003, DEC-004, DEC-005`
- External: `none`

## Plan

1. Use `kanlu` to inspect repo conventions and recommend the smallest runtime/test scaffold.
2. Implement validators for storyboard semantics, OpenAPI required paths/enums, and cross-contract vocabularies.
3. Add a single local validation command and document it.
4. Run `baguan` review, then `yanshou` acceptance.

## Implementation Packet

- Files to inspect/change: `README.md`, `AGENT.md`, `STATUS.md`, `docs/development/contract-validation.md`, `pyproject.toml`, `uv.lock`, `src/video_factory_contracts/`, `tests/`, `schemas/scene-storyboard.schema.json`, `examples/storyboards/*.json`, `openapi/enterprise-video-factory.openapi.yaml`, `docs/contracts/artifact-manifest.md`, `docs/contracts/job-state-machine.md`, `docs/quality/failure-taxonomy.md`, `docs/quality/qc-matrix.md`, `docs/quality/repair-policy.md`, `docs/security/asset-governance.md`, `docs/product/api-console.md`
- Minimal approach: create a lightweight Python package run by `uv`, expose `validate-contracts`, validate storyboards, OpenAPI shape/enums, cross-document vocabularies, and RepoFrame harness health, with focused pytest coverage and no model/runtime dependencies.
- Main risks: brittle Markdown extraction, duplicating enum sources instead of reading accepted contracts, treating harness warnings as fatal, and accidentally introducing TTS/avatar/render/runtime dependencies in a validation-only slice.
- Validation commands: `uv run validate-contracts --repo .`; `uv run pytest`; `/Users/joe/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 /Users/joe/.codex/skills/repo-init/scripts/harness.py 检查 --repo .`
- Rollback or safety note: remove `pyproject.toml`, `uv.lock`, `.gitignore`, `src/video_factory_contracts/`, `tests/`, and `docs/development/contract-validation.md`; revert README/AGENT/STATUS/TASK-010 metadata updates. Do not rewrite accepted TASK-003 through TASK-009 contracts unless a validator exposes a real inconsistency and review accepts the change.

## Parent Coordination

- Parent task: `TASK-001-coordinate-enterprise-delivery-plan.md`
- Start this task only after TASK-003 through TASK-009 are accepted.

## Related Tasks

- Consumes the accepted contracts from `TASK-003` through `TASK-009`.
- Provides a guardrail before implementation tasks for API, orchestration, model adapters, QC, and console work.

## Notes

- Facts: TASK-003 through TASK-009 were accepted using targeted validation scripts and Yanshou evidence.
- Assumptions: the first code slice should turn those checks into repeatable tooling before model/runtime work.
- Risks: skipping this step would make later implementation drift harder to catch.

## Assumption Checks

### Validated

- `2026-06-02`: `uv` is available locally and can run the contract validation package.
- `2026-06-02`: Contract validators can pass against accepted storyboards, OpenAPI, cross-document vocabularies, and RepoFrame harness health.
- `2026-06-02`: Baguan found OpenAPI method and governance required-field coverage gaps; validators and negative tests were extended to cover both.
- `2026-06-02`: Baguan found required-property and malformed-YAML handling gaps; validators now check both required lists and property definitions, and malformed OpenAPI YAML returns a validation report instead of crashing.

### Invalidated

- none

### Still Open

- Full OpenAPI linting can be added later; this task implements targeted contract checks required by acceptance.

## Downstream Impact

### Affected Tasks

- Future API/orchestration/model/QC implementation tasks should consume these validators in CI.
- Future contract changes must update source-of-truth docs/schema/examples and keep `uv run validate-contracts --repo .` passing.

### Suggested Follow-up

- After this task, define the first runtime service slice with explicit ownership and tests.

## Execution Log

- `2026-05-30`: task created after TASK-003 through TASK-009 acceptance to provide a valid next implementation entry point.
- `2026-06-02`: implemented Python/uv contract validation scaffold, CLI, tests, and development documentation; no model/GPU/runtime code added.
- `2026-06-02`: addressed Baguan review findings by validating documented OpenAPI HTTP methods and required governance/review/audit fields.
- `2026-06-02`: addressed second Baguan review findings by validating required OpenAPI property definitions and stable malformed-YAML error reporting.
- `2026-06-02`: captured TASK-010 harness lesson for future contract-validator review gaps.

## Review Notes

- Status: `reviewed`
- Findings: `2026-06-02`: Baguan reviewed TASK-010 and requested fixes for OpenAPI method validation, governance required fields, required property definitions, and malformed YAML handling. Fixes were implemented and re-reviewed clean. No blocking findings remain.
- Required follow-up: accepted; open the first product implementation task after baseline commit.

## Acceptance Evidence

- Status: `passed`
- Evidence: `2026-06-02`: Yanshou acceptance passed for TASK-010. `uv run validate-contracts --repo .` returned PASS with 4 passed checks, 0 errors, and 0 warnings, covering storyboard schema/examples, OpenAPI shape, cross-contract vocabulary consistency, and RepoFrame harness errors=0. `uv run pytest` passed 8 tests. RepoFrame harness check returned errors=0 with only expected pending handoff warnings. Validators are implemented as package code and test tooling under `src/video_factory_contracts/` and `tests/`, with developer instructions in `docs/development/contract-validation.md`. Dependency scope remains validation-only: `jsonschema`, `PyYAML`, and `pytest`; no TTS, avatar rendering, orchestration, web console, GPU, media, or deployment runtime dependencies were introduced.
- Repro steps for failures: `none`

## Debug Notes

- Failure signal: `none`
- Minimal reproduction: `pending`
- Likely root cause: `pending`
- Regression test: `pending`

## Harness Lessons

- Durable lesson: Contract validators are only trustworthy when every reviewed coverage gap gets a negative regression test. For OpenAPI and similar contracts, validators must check both source-of-truth vocabulary drift and structural presence: documented HTTP method plus path, required-field membership plus property definitions, enum/reference shape, and stable failure reports for malformed input.
- Harness update: Added the regression rule to `docs/development/contract-validation.md`; keep the task-local lesson here so future implementation slices inherit it without broad global rule churn.
- Future trigger: Reuse this lesson whenever Baguan, Yanshou, Paicha, or a failing test exposes a validator blind spot in docs-derived vocabulary, OpenAPI schema shape, JSON Schema semantics, or malformed-contract handling.
