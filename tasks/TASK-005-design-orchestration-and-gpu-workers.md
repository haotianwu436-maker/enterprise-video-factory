# Design orchestration and GPU workers

<!-- repo-init:managed -->

## Metadata

- ID: `TASK-005`
- Status: `done`
- Owner: `shared`
- Parent: `TASK-001`
- Created: `2026-05-29`
- Updated: `2026-05-30`

## Why

Design resumable orchestration, queues, GPU worker pools, and artifact lifecycles so long-running video jobs can recover from partial failure instead of restarting the full pipeline.

## Scope

- In scope: job graph, segment-level execution, worker queues, idempotency, retries, storage keys, and observability events
- Out of scope: deploying Kubernetes or implementing Temporal workers

## Acceptance Criteria

- The workflow separates planning, TTS, avatar, render, compose, QC, and publishable output stages.
- Each stage has resumability, retry, timeout, and artifact ownership rules.
- GPU worker scheduling and capacity assumptions are visible.

## Product Acceptance

- User journey: `pending`
- Evidence required: workflow graph, job state machine, and worker contract notes
- Acceptance owner: `yanshou`
- Acceptance status: `passed`

## Dependencies

- Files: `PROJECT.md, tasks/TASK-001-coordinate-enterprise-delivery-plan.md, tasks/TASK-002-lock-production-architecture.md, tasks/TASK-004-design-model-service-adapters.md, tasks/TASK-008-design-governance-baseline-and-authorized-assets.md`
- Decisions: `DEC-001, DEC-002, DEC-004, DEC-005`
- External: `Temporal or equivalent durable orchestration, object storage, GPU worker pool`

## Plan

1. Define the segment-level job graph.
2. Specify stage idempotency, retry, timeout, and artifact contracts.
3. Capture observability and capacity-planning requirements.

## Implementation Packet

- Files to inspect/change: `docs/architecture/orchestration-gpu-workers.md`, `docs/contracts/job-state-machine.md`, `docs/contracts/artifact-manifest.md`, `docs/security/asset-governance.md`
- Minimal approach: define the segment job graph, idempotency keys, retry/timeout policy, queue/worker ownership, artifact retention hooks, audit events, and capacity-planning assumptions.
- Main risks: losing partial rerun capability; omitting audit/event consistency with the governance baseline; overfitting to one orchestration product before deployment constraints are confirmed.
- Validation commands: `/Users/joe/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 /Users/joe/.codex/skills/repo-init/scripts/harness.py check --repo .`
- Rollback or safety note: architecture/contracts only; no Temporal workers, Kubernetes manifests, or queue implementation in this slice.

## Parent Coordination

- Parent task: `TASK-001-coordinate-enterprise-delivery-plan.md`
- Start this task only after explicit post-initialization confirmation.

## Related Tasks

- Review `TASK-002-lock-production-architecture.md` before execution.
- Review `TASK-008-design-governance-baseline-and-authorized-assets.md` for audit, retention, tenant, and authorization boundaries.
- Coordinate stage outputs with `TASK-004-design-model-service-adapters.md`.
- Coordinate repair loops with `TASK-006-design-quality-gates-and-auto-repair.md`.

## Notes

- Facts: video generation jobs are long-running and failure-prone
- Assumptions: segment-level generation is required for enterprise-grade retries and partial repair
- Risks: naive orchestration can waste GPU time and make near-100% success claims unrealistic

## Assumption Checks

### Validated

- `2026-05-30`: Created `docs/architecture/orchestration-gpu-workers.md` and `docs/contracts/job-state-machine.md`.
- `2026-05-30`: Orchestration design preserves segment-level retry, idempotency, repair/review paths, and audit events without implementing workers.

### Invalidated

- none

### Still Open

- Queueing technology, deployment environment, and target throughput are not confirmed.

## Downstream Impact

### Affected Tasks

- `TASK-006`: consumes state/failure transitions for QC and repair policy.
- `TASK-007`: exposes job, segment, review, repair, and release states through API/console.
- `TASK-009`: reconciles traceability across stage and release states.

### Suggested Follow-up

- If orchestration changes artifact contracts or QC entry points, update `TASK-001` and downstream tasks.

## Execution Log

- `2026-05-29`: task created during repository initialization correction.
- `2026-05-30`: orchestration/GPU worker architecture and job state machine created as docs/contracts only.

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
