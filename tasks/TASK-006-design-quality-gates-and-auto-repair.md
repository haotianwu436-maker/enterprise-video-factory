# Design quality gates and auto repair

<!-- repo-init:managed -->

## Metadata

- ID: `TASK-006`
- Status: `done`
- Owner: `shared`
- Parent: `TASK-001`
- Created: `2026-05-29`
- Updated: `2026-05-30`

## Why

Design quality inspection, fallback, retry, and repair loops as first-class product behavior so the system can be reliable instead of merely impressive when it succeeds.

## Scope

- In scope: audio QC, ASR backcheck, voice consistency, face/lip sync checks, subtitle safety, render checks, publishability checks, and fallback policy
- Out of scope: implementing individual detectors or model-specific scoring

## Acceptance Criteria

- Each pipeline stage has pass/fail metrics, repair actions, and escalation behavior.
- The system can rerun only failed segments where possible.
- Human review boundaries are explicit for unsafe, unauthorized, or repeatedly failing outputs.

## Product Acceptance

- User journey: `pending`
- Evidence required: QC matrix, repair decision tree, and failure taxonomy
- Acceptance owner: `yanshou`
- Acceptance status: `passed`

## Dependencies

- Files: `PROJECT.md, tasks/TASK-001-coordinate-enterprise-delivery-plan.md, tasks/TASK-003-define-scene-dsl-and-planning-contract.md, tasks/TASK-004-design-model-service-adapters.md, tasks/TASK-005-design-orchestration-and-gpu-workers.md, tasks/TASK-008-design-governance-baseline-and-authorized-assets.md`
- Decisions: `DEC-001, DEC-004, DEC-005`
- External: `ASR/alignment tooling, face detection, lip-sync metrics, ffmpeg/probe tooling`

## Plan

1. Define the QC matrix by stage.
2. Define repair and fallback behavior for common failure classes.
3. Define audit evidence emitted with every final video.

## Implementation Packet

- Files to inspect/change: `docs/quality/qc-matrix.md`, `docs/quality/repair-policy.md`, `docs/quality/failure-taxonomy.md`, `docs/contracts/artifact-manifest.md`, `docs/contracts/scene-dsl.md`, `schemas/scene-storyboard.schema.json`, `docs/security/asset-governance.md`
- Minimal approach: define stage-by-stage pass/fail metrics, repair/fallback actions, human-review thresholds, unsafe-output escalation, and `qc_report` evidence required for every final video.
- Main risks: subjective quality thresholds lacking a business owner; QC not receiving enough metadata from earlier stages; repair loops bypassing governance or audit requirements.
- Validation commands: `/Users/joe/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 /Users/joe/.codex/skills/repo-init/scripts/harness.py check --repo .`
- Rollback or safety note: quality docs only; no detector/model implementation. Keep all thresholds marked draft until reviewed by product/compliance owners.

## Parent Coordination

- Parent task: `TASK-001-coordinate-enterprise-delivery-plan.md`
- Start this task only after explicit post-initialization confirmation.

## Related Tasks

- Review `TASK-004-design-model-service-adapters.md` for model-stage outputs.
- Review `TASK-003-define-scene-dsl-and-planning-contract.md` for subtitle, safe-area, face/lip, and scene constraints.
- Coordinate repair-loop execution with `TASK-005-design-orchestration-and-gpu-workers.md`.
- Coordinate unsafe-output escalation with `TASK-008-design-governance-baseline-and-authorized-assets.md`.

## Notes

- Facts: enterprise success rate depends on fallback and repair, not only base model quality
- Assumptions: every generated artifact should have QC evidence
- Risks: subjective quality metrics may need human review thresholds before automation is trusted

## Assumption Checks

### Validated

- `2026-05-30`: Created `docs/quality/qc-matrix.md`, `docs/quality/repair-policy.md`, and `docs/quality/failure-taxonomy.md`.
- `2026-05-30`: QC and repair contracts distinguish repairable, review-required, and terminal failures.

### Invalidated

- none

### Still Open

- Required quality thresholds and manual review policy are not yet confirmed.

## Downstream Impact

### Affected Tasks

- `TASK-007`: consumes QC status, failure codes, repair actions, and review blockers in API/console.
- `TASK-009`: consumes QC reports and repair evidence for final traceability.

### Suggested Follow-up

- If QC requires additional artifacts from earlier stages, update `TASK-004` and `TASK-005`.

## Execution Log

- `2026-05-29`: task created during repository initialization correction.
- `2026-05-30`: QC matrix, repair policy, and failure taxonomy created; no detector/model implementation added.

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
