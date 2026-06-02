# Design product API and console

<!-- repo-init:managed -->

## Metadata

- ID: `TASK-007`
- Status: `done`
- Owner: `shared`
- Parent: `TASK-001`
- Created: `2026-05-29`
- Updated: `2026-05-30`

## Why

Design the enterprise API, job state model, and operator console surface so customers and operators can create, monitor, repair, and audit video generation jobs.

## Scope

- In scope: tenant model, job API, asset API, status events, operator actions, review queue, and publish-ready output metadata
- Out of scope: frontend implementation or authentication provider wiring

## Acceptance Criteria

- The API supports text/opinion input, asset selection, job creation, status polling/events, artifact retrieval, and repair/retry actions.
- The console surfaces job progress, QC failures, audit trails, and manual review actions.
- API boundaries align with security and asset-governance requirements.

## Product Acceptance

- User journey: `pending`
- Evidence required: API surface draft and console workflow outline
- Acceptance owner: `yanshou`
- Acceptance status: `passed`

## Dependencies

- Files: `PROJECT.md, tasks/TASK-001-coordinate-enterprise-delivery-plan.md, tasks/TASK-004-design-model-service-adapters.md, tasks/TASK-005-design-orchestration-and-gpu-workers.md, tasks/TASK-006-design-quality-gates-and-auto-repair.md, tasks/TASK-008-design-governance-baseline-and-authorized-assets.md`
- Decisions: `DEC-001, DEC-004, DEC-005`
- External: `none`

## Plan

1. Define primary user and operator journeys.
2. Draft API resources and job state transitions.
3. Define console surfaces for job monitoring, QC review, and asset governance.

## Implementation Packet

- Files to inspect/change: `docs/product/api-console.md`, `openapi/enterprise-video-factory.openapi.yaml`, `docs/contracts/job-state-machine.md`, `docs/contracts/artifact-manifest.md`, `docs/security/asset-governance.md`, `docs/quality/qc-matrix.md`
- Minimal approach: define tenant, job, asset, artifact, review, retry/repair, and audit API surfaces plus operator console workflows; keep OpenAPI draft optional until the resource model stabilizes.
- Main risks: UI/API shortcuts bypassing consent, authorization, QC, or manual review; exposing implementation-specific model/runtime details to customers.
- Validation commands: `/Users/joe/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 /Users/joe/.codex/skills/repo-init/scripts/harness.py check --repo .`
- Rollback or safety note: product/API docs only; no frontend or auth-provider implementation in this slice.

## Parent Coordination

- Parent task: `TASK-001-coordinate-enterprise-delivery-plan.md`
- Start this task only after explicit post-initialization confirmation.

## Related Tasks

- Coordinate state model with `TASK-005-design-orchestration-and-gpu-workers.md`.
- Coordinate artifact retrieval with `TASK-004-design-model-service-adapters.md` and `docs/contracts/artifact-manifest.md`.
- Coordinate consent and authorization surfaces with `TASK-008-design-governance-baseline-and-authorized-assets.md`.

## Notes

- Facts: the product should feel like an enterprise production console, not a single-shot generator
- Assumptions: API and console should expose repair and audit behavior from day one
- Risks: UI convenience can accidentally bypass consent or QC controls

## Assumption Checks

### Validated

- `2026-05-30`: Created `docs/product/api-console.md` and draft `openapi/enterprise-video-factory.openapi.yaml`.
- `2026-05-30`: API/console contract uses tenant-scoped assets, signed artifact access, review decisions, repair requests, and immutable release resources.

### Invalidated

- none

### Still Open

- First customer persona, user roles, and publishing integration targets are not confirmed.

## Downstream Impact

### Affected Tasks

- `TASK-009`: consumes API, review, release, and audit surfaces for final compliance reconciliation.

### Suggested Follow-up

- If product workflows change asset-governance requirements, update `TASK-008`, `TASK-009`, and `TASK-001`.

## Execution Log

- `2026-05-29`: task created during repository initialization correction.
- `2026-05-30`: product API/console contract and OpenAPI draft created; no frontend or backend implementation added.

## Review Notes

- Status: `reviewed`
- Findings: `2026-05-30`: Baguan reviewed the TASK-003 through TASK-009 documentation/contract batch. Initial findings around risk status, OpenAPI coverage, repair/review exits, stage mapping, DSL enforcement, failure-code drift, review/audit envelopes, and policy fields were addressed. No P0/P1 blocking findings remain.
- Required follow-up: accepted; no review follow-up before TASK-010.

## Acceptance Evidence

- Status: `passed`
- Evidence: `2026-05-30`: Combined Yanshou acceptance passed for TASK-003 through TASK-009. Storyboard JSON parse passed for `30s.json`, `60s.json`, and `90s.json`; semantic checks confirmed asset refs resolve, identity assets include authorization snapshots, durations match targets, scene order is deterministic, and every visual emphasis text appears in the corresponding scene script unless explicitly review-marked. OpenAPI YAML parse passed with 19 paths and 29 schemas; expected job, asset, review, artifact, audit, repair, release, enum, ReviewItem, and AuditEvent contracts are present. Cross-document checks confirmed canonical stage mapping, failure-code vocabulary, QC/repair/review traceability, and concrete repair exits are consistent.
- Repro steps for failures: `none`

## Debug Notes

- Failure signal: `none`
- Minimal reproduction: `pending`
- Likely root cause: `pending`
- Regression test: `pending`

## Harness Lessons

- Durable lesson: `none yet`
- Harness update: `pending`
- Future trigger: `pending`
