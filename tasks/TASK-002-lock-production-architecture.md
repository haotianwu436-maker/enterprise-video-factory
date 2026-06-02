# Lock production architecture

<!-- repo-init:managed -->

## Metadata

- ID: `TASK-002`
- Status: `done`
- Owner: `shared`
- Parent: `TASK-001`
- Created: `2026-05-29`
- Updated: `2026-05-30`

## Why

Lock production service boundaries, data flow, storage, and runtime assumptions before model experiments or UI work drive the platform shape.

## Scope

- In scope: architecture diagram, service boundaries, artifact lifecycle, tenancy model, and deployment assumptions
- Out of scope: implementing services or benchmarking model runtimes

## Acceptance Criteria

- The architecture distinguishes API, orchestration, model services, render/composition, storage, QC, and operator surfaces.
- The segment-based generation flow is explicit from input text to final MP4.
- Key non-functional targets are captured as assumptions or open questions.

## Product Acceptance

- User journey: `pending`
- Evidence required: architecture doc or diagram plus harness check output
- Acceptance owner: `yanshou`
- Acceptance status: `passed`

## Dependencies

- Files: `PROJECT.md, STATUS.md, tasks/TASK-001-coordinate-enterprise-delivery-plan.md`
- Decisions: `DEC-001, DEC-002, DEC-003, DEC-004, DEC-005`
- External: `none`

## Plan

1. Read the project snapshot and enterprise constraints.
2. Define the production service map and artifact flow.
3. Record architecture assumptions, open questions, and validation commands.

## Implementation Packet

Fill this before a worker changes files. This is the handoff from `kanlu` to implementation.

- Files to inspect/change: `PROJECT.md`, `DECISIONS.md`, `STATUS.md`, `docs/architecture/production-architecture.md`, `docs/architecture/artifact-lifecycle.md`, `tasks/TASK-001-coordinate-enterprise-delivery-plan.md`, `tasks/TASK-008-design-governance-baseline-and-authorized-assets.md`
- Minimal approach: create documentation-only architecture artifacts that define service boundaries, segment-based flow, artifact lifecycle, tenant boundaries, observability surfaces, and open NFR questions before any product code.
- Main risks: over-committing to Temporal, Kubernetes, or a specific GPU shape before benchmarks; missing governance hooks that `TASK-008` must define next; letting model experiments drive the platform architecture.
- Validation commands: `/Users/joe/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 /Users/joe/.codex/skills/repo-init/scripts/harness.py check --repo .`
- Rollback or safety note: docs/contracts only; no runtime scaffolding or production code in this slice. Revert only documentation files created by this task if the architecture is rejected.

## Parent Coordination

- Parent task: `TASK-001-coordinate-enterprise-delivery-plan.md`
- Start this task only after explicit post-initialization confirmation.

## Related Tasks

- Coordinate scene-contract decisions with `TASK-003-define-scene-dsl-and-planning-contract.md`.
- Coordinate governance baseline with `TASK-008-design-governance-baseline-and-authorized-assets.md` before downstream contracts.
- Coordinate runtime boundaries with `TASK-004-design-model-service-adapters.md` and `TASK-005-design-orchestration-and-gpu-workers.md`.

## Notes

- Facts: the product target is enterprise-grade, not MVP-only
- Assumptions: architecture should be accepted before product implementation starts
- Risks: missing GPU/runtime assumptions can make later work expensive to reverse

## Assumption Checks

Update these lists whenever current execution validates or invalidates the task's working assumptions.

### Validated

- `2026-05-30`: Created documentation-only production architecture and artifact lifecycle outputs without adding runtime scaffolding or product code.
- `2026-05-30`: Architecture documents explicitly distinguish API, auth/tenant/RBAC, asset registry, planner, orchestrator, model adapters, storage, QC, repair, composition, and operator console boundaries.

### Invalidated

- none

### Still Open

- Target concurrency, latency SLO, deployment target, and GPU budget are not yet confirmed.

## Downstream Impact

If execution changes downstream work, mirror that impact here instead of leaving it only in `Execution Log`.

### Affected Tasks

- `TASK-008`: must use `docs/architecture/production-architecture.md` and `docs/architecture/artifact-lifecycle.md` to define governance baseline.
- `TASK-003`: must align scene DSL asset references with the architecture artifact lifecycle.
- `TASK-004`: must formalize adapter manifests from the artifact lifecycle.
- `TASK-005`: must map architecture stages to durable orchestration states and worker ownership.
- `TASK-006`: must define QC reports for the artifact lifecycle.
- `TASK-007`: must expose job/artifact/review state according to the service boundaries.
- `TASK-009`: must reconcile traceability against the architecture and artifact lifecycle.

### Suggested Follow-up

- Use `docs/architecture/production-architecture.md` and `docs/architecture/artifact-lifecycle.md` as required inputs for downstream task execution.
- If future review changes service boundaries, update `TASK-001` and affected child tasks before implementation continues.

## Execution Log

- `2026-05-29`: task created during repository initialization correction.
- `2026-05-30`: created production architecture and artifact lifecycle documentation; no product code or runtime scaffolding added.
- `2026-05-30`: Yanshou acceptance passed for TASK-002.

## Review Notes

- Status: `reviewed`
- Findings: `2026-05-30`: Baguan reviewed TASK-002 implementation. No high-severity blocker and no product code/runtime scaffolding was added. Harness check passed with errors: 0, warnings: 9 expected pending handoff fields. Medium fixes requested: clarify that Operator Console access to DB/object storage is mediated by API/RBAC or signed tenant-scoped artifact access; add an explicit audit/event-store boundary; make released video artifacts immutable/versioned and use a separate current-release pointer instead of overwriting `release/final.mp4`.
- Required follow-up: addressed in `docs/architecture/production-architecture.md` and `docs/architecture/artifact-lifecycle.md`; rerun bundled Python harness check before Yanshou acceptance.

## Acceptance Evidence

- Status: `passed`
- Evidence: `2026-05-30`: Yanshou verified TASK-002 acceptance criteria. `docs/architecture/production-architecture.md` distinguishes API, orchestration, model services, render/composition, storage, QC, and operator surfaces; `docs/architecture/production-architecture.md` and `docs/architecture/artifact-lifecycle.md` make the segment-based flow explicit from input text to final MP4; key non-functional targets and open questions are captured. Baguan requested fixes are present: Operator Console access is mediated by API/RBAC or signed tenant-scoped artifact URLs, an append-only Audit/Event Store is an explicit architecture boundary, and release artifacts are immutable/versioned with `release/current.json` as the mutable pointer. Bundled Python harness check passed with errors: 0, warnings: 9 expected pending handoff fields.
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
