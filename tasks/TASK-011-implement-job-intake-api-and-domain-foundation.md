# Implement job intake API and domain foundation

<!-- repo-init:managed -->

## Metadata

- ID: `TASK-011`
- Status: `done`
- Owner: `shared`
- Parent: `TASK-001`
- Created: `2026-06-02`
- Updated: `2026-06-02`

## Why

Begin the first real product implementation slice after the accepted contract layer: a minimal but enterprise-shaped job intake and domain foundation that can create, validate, and expose video generation jobs without invoking model, GPU, avatar, render, or composition runtimes.

## Scope

- In scope: product runtime project structure, job intake API skeleton, domain models for jobs/assets/artifacts/reviews/QC state, request validation against accepted contracts, deterministic IDs/state transitions for the initial job lifecycle, and tests
- Out of scope: TTS generation, voice cloning, avatar rendering, HTML/video rendering, orchestration workers, queues, object storage integration, web console UI, GPU scheduling, and deployment manifests

## Acceptance Criteria

- A local developer can start or test the product runtime foundation and create a video-generation job from text/opinion input using authorized asset references.
- The implementation reuses accepted contract vocabulary for job states, manifest stages, asset types, QC status, review state, and failure codes instead of inventing parallel strings.
- Invalid requests fail deterministically for missing text, unsupported output profile, missing required assets, or unauthorized identity assets.
- The existing contract validator remains passing and is included in the validation path.
- Tests cover successful job creation, asset authorization failure, invalid output profile, and state/enum consistency with the accepted contracts.

## Product Acceptance

- User journey: `verified`
- Evidence required: runnable API/domain tests, sample job creation flow, and contract validator output
- Acceptance owner: `yanshou`
- Acceptance status: `passed`

## Dependencies

- Files: `pyproject.toml`, `src/video_factory_contracts/`, `tests/`, `openapi/enterprise-video-factory.openapi.yaml`, `docs/product/api-console.md`, `docs/contracts/job-state-machine.md`, `docs/security/asset-governance.md`, `docs/contracts/artifact-manifest.md`, `docs/quality/failure-taxonomy.md`, `STATUS.md`
- Decisions: `DEC-001, DEC-002, DEC-003, DEC-004, DEC-005`
- External: `none confirmed`

## Plan

1. Run `kanlu` to inspect the accepted API/domain contracts and recommend the smallest runtime foundation.
2. Choose the minimal implementation shape that fits the existing Python/uv scaffold.
3. Implement only job intake/domain behavior with tests and no media/model runtime.
4. Run contract validation and product tests.
5. Run Baguan review, then Yanshou acceptance.

## Implementation Packet

- Files to inspect/change: `STATUS.md`, this task, `pyproject.toml`, `src/video_factory_contracts/validation.py`, `openapi/enterprise-video-factory.openapi.yaml`, `docs/product/api-console.md`, `docs/contracts/job-state-machine.md`, `docs/contracts/artifact-manifest.md`, `docs/security/asset-governance.md`, `docs/quality/failure-taxonomy.md`, `docs/quality/qc-matrix.md`, existing tests, and new runtime tests. Likely changes: add shared contract vocabulary access under `src/video_factory_contracts/`, add `src/video_factory_runtime/` for domain/API/service/repositories, update `pyproject.toml` scripts/dependencies for HTTP API support, and add `tests/test_job_intake*.py`.
- Minimal approach: expose accepted contract vocabulary from docs/OpenAPI as the runtime source of truth; implement a small job-intake domain/service that validates `CreateJobRequest`, tenant scope, required voice/avatar refs, active identity assets, consent snapshots, supported `9:16` and `30-90s` output profile, and deterministic transition `created -> validated` with `active_stage=source_intake`. Provide a FastAPI `create_app()` wrapper for `POST /v1/jobs` and `GET /v1/jobs/{job_id}`. Keep storage in-memory behind repository interfaces for this task, with seeded authorized assets and no media/model/orchestration code.
- Main risks: duplicating enum strings instead of loading contract vocabulary; OpenAPI currently omits example-only fields like `resolution`, `publish_targets`, and `policy`, so runtime should not expand the accepted contract in this task; in-memory storage is not durable, so keep it explicitly scoped and interface-backed; authorization checks must fail closed for missing or unauthorized identity assets; framework-generated OpenAPI must not replace the accepted hand-authored OpenAPI contract.
- Validation commands: `uv run validate-contracts --repo .`; `uv run pytest`; `python3 /Users/joe/.codex/skills/repo-init/scripts/harness.py 检查 --repo .`; API smoke test with `uv run uvicorn video_factory_runtime.api:create_app --factory --port 8000`.
- Rollback or safety note: keep TASK-011 changes isolated to the new runtime package/tests plus minimal package metadata updates; do not alter accepted contract docs/OpenAPI except to expose vocabulary helpers. No persistent external state, no GPU/model calls, no object storage writes, so rollback is deleting the new runtime files/tests and reverting package metadata.

## Parent Coordination

- Parent task: `TASK-001-coordinate-enterprise-delivery-plan.md`
- Start this task only after the baseline commit containing TASK-001 through TASK-010.

## Related Tasks

- Consumes `TASK-007-design-product-api-and-console.md` for API resource shape.
- Consumes `TASK-005-design-orchestration-and-gpu-workers.md` for state vocabulary, but does not implement orchestration workers.
- Consumes `TASK-008-design-governance-baseline-and-authorized-assets.md` for authorized asset validation.
- Consumes `TASK-010-implement-contract-validation-scaffold.md` for contract validation guardrails.

## Notes

- Facts: the repository now has a Python/uv validation scaffold and accepted contract documents.
- Assumptions: the first product slice should prove the product boundary and domain vocabulary before model integration.
- Risks: implementing a demo-only endpoint would undermine the enterprise architecture; this slice must preserve governance, traceability, and state-machine vocabulary from the start.

## Assumption Checks

### Validated

- Kanlu confirmed the FastAPI wrapper, in-memory repository interfaces, tenant-scoped asset checks, and accepted contract vocabulary reuse as the smallest TASK-011 implementation route.
- Baguan re-review found no blocking findings after explicit actor headers, tenant-scoped asset lookup, and deterministic top-level non-object body validation were added.
- Yanshou accepted TASK-011 with API smoke evidence, contract vocabulary checks, deterministic invalid-request evidence, contract validator output, and targeted runtime test output.

### Invalidated

- none

### Still Open

- none

## Downstream Impact

### Affected Tasks

- Future orchestration, worker, asset registry, QC, and console tasks should build on this domain/API foundation.

### Suggested Follow-up

- After this task passes acceptance, define the first durable orchestration or asset-registry implementation slice.

## Execution Log

- `2026-06-02`: task created after baseline commit to open the first real product implementation route.
- `2026-06-02`: Kanlu filled the Implementation Packet for job intake API/domain foundation before code changes.
- `2026-06-02`: Implemented FastAPI job intake, domain/repository/service foundation, contract vocabulary loader, sample request, docs, and runtime tests.
- `2026-06-02`: Baguan re-reviewed the fixed TASK-011 diff and reported no blocking findings.
- `2026-06-02`: Yanshou accepted TASK-011 after validating sample job creation, HTTP create/get smoke, deterministic invalid-request envelopes, contract vocabulary reuse, contract validator output, and runtime test coverage.

## Review Notes

- Status: `reviewed`
- Findings: no blocking findings remain. Baguan's non-blocking API/header, tenant-scoped asset lookup, and deterministic non-object body validation feedback was absorbed before acceptance.
- Required follow-up: accepted; commit TASK-011 when ready, then open the next product implementation slice.

## Acceptance Evidence

- Status: `passed`
- Evidence: `2026-06-02`: Yanshou acceptance passed for TASK-011. `.venv/bin/video-factory-api --sample-job` returned `job_000001`, `state=validated`, `active_stage=source_intake`, `state_history=[created, validated]`, and the expected voice/avatar consent snapshots. An in-process HTTP smoke against `create_app()` returned `POST /v1/jobs -> 202` and `GET /v1/jobs/job_000001 -> 200`, then verified deterministic failure envelopes for missing text plus missing voice/avatar assets (`422` with `scene_dsl_invalid`, `voice_profile_missing`, and `avatar_profile_missing`), unsupported output profile (`422` with `scene_dsl_invalid`), and consent-less identity asset (`403` with `asset_not_authorized`). Runtime vocabulary is loaded through `video_factory_contracts.load_contract_vocabulary()` from accepted docs/OpenAPI and guarded by service-level contract-term assertions. `.venv/bin/validate-contracts --repo .` returned PASS with 4 passed checks, 0 errors, and 0 warnings. `.venv/bin/python -m pytest tests/test_job_intake_runtime.py -p no:cacheprovider -s` passed 9 tests with 1 FastAPI/Starlette deprecation warning. `python3 /Users/joe/.codex/skills/repo-init/scripts/harness.py 检查 --repo .` returned errors=0 with only expected pending-handoff warnings from RepoFrame task files. Read-only yanshou sandbox caveat: `uv run` and full pytest temp fixtures could not write cache/temp files there; parent-shell validation covers `uv run pytest` passing 17 tests and `uv run validate-contracts --repo .` passing.
- Repro steps for failures: `none`

## Debug Notes

- Failure signal: `none`
- Minimal reproduction: `none`
- Likely root cause: `none`
- Regression test: `tests/test_job_intake_runtime.py`

## Harness Lessons

- Durable lesson: First runtime slices should prove both an in-process service path and an HTTP/API path, while loading vocabulary from accepted contracts and failing closed on authorization checks before any model or worker code lands.
- Harness update: Captured TASK-011 evidence in this task; no global harness rule change needed yet.
- Future trigger: Reuse this lesson when opening asset registry, orchestration, QC, or worker tasks that consume job, asset, stage, review, QC, or failure-code vocabulary.
