# Design model service adapters

<!-- repo-init:managed -->

## Metadata

- ID: `TASK-004`
- Status: `done`
- Owner: `shared`
- Parent: `TASK-001`
- Created: `2026-05-29`
- Updated: `2026-05-30`

## Why

Design stable adapters around voice cloning TTS, avatar rendering, subtitle alignment, HTML/animation rendering, and final composition so model churn does not leak into product workflows.

## Scope

- In scope: adapter contracts, artifact inputs/outputs, health checks, fallback ordering, and benchmark fixtures
- Out of scope: downloading model weights or running GPU benchmarks

## Acceptance Criteria

- TTS, avatar, alignment, renderer, and composer services have explicit request/response contracts.
- Adapter contracts support local/open-source-first models with minimal third-party API dependency.
- Fallback paths are represented as first-class adapter behavior.

## Product Acceptance

- User journey: `pending`
- Evidence required: adapter spec and example contracts for at least TTS, avatar, renderer, and composer
- Acceptance owner: `yanshou`
- Acceptance status: `passed`

## Dependencies

- Files: `PROJECT.md, tasks/TASK-001-coordinate-enterprise-delivery-plan.md, tasks/TASK-002-lock-production-architecture.md, tasks/TASK-003-define-scene-dsl-and-planning-contract.md, tasks/TASK-008-design-governance-baseline-and-authorized-assets.md`
- Decisions: `DEC-002, DEC-004, DEC-005`
- External: `CosyVoice/GPT-SoVITS/F5-TTS candidates, MuseTalk/HunyuanVideo-Avatar candidates, ffmpeg, Remotion`

## Plan

1. Define model-service boundaries and artifact contracts.
2. Specify fallback and retry semantics per model class.
3. Capture benchmark and compatibility assumptions.

## Implementation Packet

- Files to inspect/change: `docs/contracts/model-service-adapters.md`, `docs/contracts/artifact-manifest.md`, `docs/security/asset-governance.md`, `docs/architecture/production-architecture.md`, `docs/architecture/artifact-lifecycle.md`, `schemas/scene-storyboard.schema.json`
- Minimal approach: define request/response contracts, artifact URIs, model/version metadata, health checks, fallback ordering, and license/capability verification notes for TTS, avatar, alignment, renderer, and composer adapters.
- Main risks: model license, GPU memory, latency, and capability assumptions leaking into product contracts; adapters omitting consent, tenant, or audit metadata required by governance.
- Validation commands: `/Users/joe/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 /Users/joe/.codex/skills/repo-init/scripts/harness.py check --repo .`
- Rollback or safety note: contract docs only; do not download weights, install runtimes, or hard-code a first-run model stack during this task.

## Parent Coordination

- Parent task: `TASK-001-coordinate-enterprise-delivery-plan.md`
- Start this task only after explicit post-initialization confirmation.

## Related Tasks

- Review `TASK-003-define-scene-dsl-and-planning-contract.md` before finalizing adapter inputs.
- Review `TASK-002-lock-production-architecture.md` for service boundaries and artifact lifecycle before finalizing adapter contracts.
- Review `TASK-008-design-governance-baseline-and-authorized-assets.md` before finalizing artifact manifest and audit fields.
- Coordinate worker scheduling with `TASK-005-design-orchestration-and-gpu-workers.md`.
- Coordinate QC metrics with `TASK-006-design-quality-gates-and-auto-repair.md`.

## Notes

- Facts: the platform should favor local/open-source model execution where practical
- Assumptions: model services should be independently containerized and replaceable
- Risks: model licenses, GPU memory requirements, and runtime variance may alter adapter priorities

## Assumption Checks

### Validated

- `2026-05-30`: Created `docs/contracts/model-service-adapters.md` and `docs/contracts/artifact-manifest.md`.
- `2026-05-30`: Adapter contracts require tenant, asset authorization, producer metadata, failure codes, audit events, and artifact manifests.

### Invalidated

- none

### Still Open

- Preferred first-run model stack and available GPU hardware are not yet confirmed.

## Downstream Impact

### Affected Tasks

- `TASK-005`: consumes adapter stage contracts and manifest/failure outputs for orchestration.
- `TASK-006`: consumes adapter failure codes and artifact/QC references.
- `TASK-007`: consumes artifact manifest and signed artifact access model.
- `TASK-009`: consumes manifest evidence for final traceability.

### Suggested Follow-up

- If model constraints change architecture or quality gates, update `TASK-001` before downstream edits.

## Execution Log

- `2026-05-29`: task created during repository initialization correction.
- `2026-05-30`: model adapter and artifact manifest contracts created; no model weights, runtimes, or benchmarks added.

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
