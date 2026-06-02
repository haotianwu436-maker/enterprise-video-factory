# Complete compliance checklist and risk register

<!-- repo-init:managed -->

## Metadata

- ID: `TASK-009`
- Status: `done`
- Owner: `shared`
- Parent: `TASK-001`
- Created: `2026-05-30`
- Updated: `2026-05-30`

## Why

Complete final traceability, compliance checklist, AI disclosure, and risk-register work after DSL, model adapters, orchestration, QC, and API contracts exist.

## Scope

- In scope: final consent/audit checklist, video traceability model, risk register, disclosure policy draft, abuse controls, and manual review completion criteria
- Out of scope: legal advice, jurisdiction-specific certification, or implementing policy enforcement

## Acceptance Criteria

- Every generated video can be traced to input text, selected assets, model versions, QC report, operator actions, and final output artifacts.
- The compliance checklist reconciles governance baseline, API, QC, model, and orchestration contracts.
- Abuse prevention, disclosure, retention, and manual review residual risks are explicit.

## Product Acceptance

- User journey: `pending`
- Evidence required: final checklist, traceability matrix, and risk register
- Acceptance owner: `yanshou`
- Acceptance status: `passed`

## Dependencies

- Files: `PROJECT.md, tasks/TASK-001-coordinate-enterprise-delivery-plan.md, tasks/TASK-002-lock-production-architecture.md, tasks/TASK-003-define-scene-dsl-and-planning-contract.md, tasks/TASK-004-design-model-service-adapters.md, tasks/TASK-005-design-orchestration-and-gpu-workers.md, tasks/TASK-006-design-quality-gates-and-auto-repair.md, tasks/TASK-007-design-product-api-and-console.md, tasks/TASK-008-design-governance-baseline-and-authorized-assets.md`
- Decisions: `DEC-004, DEC-005`
- External: `none`

## Plan

1. Reconcile downstream contracts against the governance baseline.
2. Build the final compliance checklist, traceability matrix, and risk register.
3. Mark unresolved legal/compliance items as explicit launch blockers or follow-up decisions.

## Implementation Packet

- Files to inspect/change: `docs/security/consent-audit-checklist.md`, `docs/security/risk-register.md`, `docs/security/traceability-matrix.md`, `docs/product/api-console.md`, `docs/quality/qc-matrix.md`, `docs/contracts/artifact-manifest.md`, `docs/architecture/production-architecture.md`, `docs/architecture/artifact-lifecycle.md`
- Minimal approach: complete a documentation-only final pass that cross-checks all downstream contracts against consent, audit, traceability, retention, disclosure, and manual review requirements.
- Main risks: treating the checklist as legal certification; missing gaps introduced by API/QC/model contracts; leaving unresolved disclosure or jurisdiction questions hidden.
- Validation commands: `/Users/joe/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 /Users/joe/.codex/skills/repo-init/scripts/harness.py check --repo .`
- Rollback or safety note: compliance docs only; no policy enforcement implementation. Keep legal uncertainty visible as launch blockers or explicit follow-up decisions.

## Parent Coordination

- Parent task: `TASK-001-coordinate-enterprise-delivery-plan.md`
- Start this task after `TASK-007` unless a compliance blocker forces earlier replan.

## Related Tasks

- Consumes `TASK-008` governance baseline.
- Reconciles `TASK-002` production architecture and artifact lifecycle.
- Reconciles outputs from `TASK-003` through `TASK-007`.

## Notes

- Facts: final traceability depends on model, QC, orchestration, and API contracts that do not exist yet.
- Assumptions: early governance baseline is sufficient for downstream work; final compliance completion should not block all planning.
- Risks: target jurisdictions, customer compliance expectations, and AI disclosure policy may require external review before launch.

## Assumption Checks

### Validated

- `2026-05-30`: Baguan confirmed full security/compliance acceptance depends on later contracts and should be split from the early governance baseline.
- `2026-05-30`: Created `docs/security/traceability-matrix.md` and `docs/security/risk-register.md`, and updated the consent/audit checklist with final reconciliation notes.

### Invalidated

- none

### Still Open

- Target jurisdictions, customer compliance expectations, retention rules, and AI disclosure requirements remain open.

## Downstream Impact

### Affected Tasks

- `TASK-003` through `TASK-007`: final traceability and risk review may reopen any upstream contract if evidence gaps are found.

### Suggested Follow-up

- If final compliance review discovers contract gaps, update `TASK-001` and reopen or revise the affected upstream task.

## Execution Log

- `2026-05-30`: task created as the final completion half of the original security/compliance task after Baguan review.
- `2026-05-30`: traceability matrix and risk register created; unresolved legal/disclosure/model-license questions remain explicit launch blockers.

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
