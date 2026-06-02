# Design governance baseline and authorized assets

<!-- repo-init:managed -->

## Metadata

- ID: `TASK-008`
- Status: `done`
- Owner: `shared`
- Parent: `TASK-001`
- Created: `2026-05-30`
- Updated: `2026-05-30`

## Why

Define the early consent, authorization, tenant, and audit baseline before DSL, model adapter, orchestration, QC, or API work can safely reference voice/avatar assets.

## Scope

- In scope: consent lifecycle, authorized voice/avatar asset states, tenant/RBAC baseline, audit event baseline, retention assumptions, and abuse-review entry points
- Out of scope: final jurisdiction-specific compliance checklist and complete risk register

## Acceptance Criteria

- Voice and avatar cloning are modeled as authorized asset workflows before downstream contracts use those assets.
- Downstream tasks have clear rules for asset references, audit events, tenant boundaries, and manual review hooks.
- Open compliance questions are captured for final completion in `TASK-009`.

## Product Acceptance

- User journey: `pending`
- Evidence required: governance baseline, consent lifecycle, asset state model, and audit-event baseline
- Acceptance owner: `yanshou`
- Acceptance status: `passed`

## Dependencies

- Files: `PROJECT.md, tasks/TASK-001-coordinate-enterprise-delivery-plan.md, tasks/TASK-002-lock-production-architecture.md`
- Decisions: `DEC-004, DEC-005`
- External: `none`

## Plan

1. Define the authorized voice/avatar asset lifecycle and consent evidence requirements.
2. Define tenant, RBAC, audit event, retention, and manual review baseline rules.
3. Publish downstream contract requirements for DSL, model adapters, orchestration, QC, and API work.

## Implementation Packet

- Files to inspect/change: `docs/security/asset-governance.md`, `docs/security/consent-audit-checklist.md`, `docs/architecture/production-architecture.md`, `docs/architecture/artifact-lifecycle.md`, `PROJECT.md`, `DECISIONS.md`
- Minimal approach: create the early governance baseline only: consent lifecycle, asset state machine, RBAC baseline, audit event vocabulary, retention assumptions, and downstream constraints.
- Main risks: making legal claims beyond the project evidence; leaving downstream contracts without enforceable asset/audit fields; blocking implementation with unresolved jurisdiction-specific questions that belong in `TASK-009`.
- Validation commands: `/Users/joe/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 /Users/joe/.codex/skills/repo-init/scripts/harness.py check --repo .`
- Rollback or safety note: governance docs only; no auth implementation or legal certification. Mark unresolved legal/compliance items for `TASK-009`.

## Parent Coordination

- Parent task: `TASK-001-coordinate-enterprise-delivery-plan.md`
- Start this task after `TASK-002` and before `TASK-003`.

## Related Tasks

- Review `TASK-002-lock-production-architecture.md` before defining tenant and audit boundaries.
- Downstream tasks `TASK-003` through `TASK-007` must consume this baseline.
- `TASK-009-complete-compliance-checklist-and-risk-register.md` completes final traceability, compliance, and risk work after downstream contracts exist.

## Notes

- Facts: only authorized voices and likenesses should be cloned or rendered.
- Assumptions: governance must be designed before cloning workflows are exposed or referenced by downstream contracts.
- Risks: weak asset governance can create legal, reputational, and safety failures even if the pipeline works technically.

## Assumption Checks

### Validated

- `2026-05-30`: Kanlu and Baguan confirmed governance must precede DSL, model adapter, API, and QC work.
- `2026-05-30`: Created `docs/security/asset-governance.md` and `docs/security/consent-audit-checklist.md`.
- `2026-05-30`: Governance baseline defines consent lifecycle, asset state machine, RBAC baseline, audit event vocabulary, retention assumptions, manual review triggers, and downstream contract requirements.

### Invalidated

- none

### Still Open

- Target jurisdictions, customer compliance expectations, and AI disclosure policy are not confirmed.

## Downstream Impact

### Affected Tasks

- `TASK-003`: must use authorized asset references.
- `TASK-004`: must include consent, tenant, model-version, and audit metadata in artifact manifests.
- `TASK-005`: must emit governance-aligned audit events and retention hooks.
- `TASK-006`: must route unsafe or unauthorized outputs to review/escalation.
- `TASK-007`: must expose consent, asset, audit, and review actions safely.

### Suggested Follow-up

- If governance changes downstream contract requirements, update `TASK-001` and the affected task before implementation continues.

## Execution Log

- `2026-05-30`: task split from the original security/compliance task after Kanlu route inspection and Baguan review.
- `2026-05-30`: governance baseline and consent/audit checklist created; no auth implementation or legal certification added.

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
