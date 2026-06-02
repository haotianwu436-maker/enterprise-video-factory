# Coordinate enterprise delivery plan

<!-- repo-init:managed -->

## Metadata

- ID: `TASK-001`
- Status: `done`
- Owner: `shared`
- Created: `2026-05-29`
- Updated: `2026-05-30`

## Why

Coordinate the first-wave task set for an enterprise-grade automated talking-head video generation platform without starting implementation during initialization.

## Scope

- In scope: sequence architecture, model integration, orchestration, quality, product, infrastructure, and governance work
- In scope: keep downstream task changes visible before implementation begins
- Out of scope: building a demo, MVP-only scaffold, or production code during initialization

## Acceptance Criteria

- The first-wave enterprise workstream is explicit and ordered.
- Cross-task assumptions, risks, and replan triggers are visible in one coordination surface.
- The recommended starting task is clear without marking any child task started.

## Product Acceptance

- User journey: `pending`
- Evidence required: command output, UI or API check, and screenshot or log evidence when relevant
- Acceptance owner: `yanshou`
- Acceptance status: `passed`

## Dependencies

- Files: `PROJECT.md, STATUS.md, prompt-only input`
- Decisions: `DEC-001, DEC-002, DEC-003, DEC-004`
- External: `none`

## Plan

1. Confirm the generated child-task order.
2. Fill the Implementation Packet for the first child task before code changes.
3. Capture cross-task feedback here before revising downstream tasks.

## Implementation Packet

Fill this before a worker changes files. This is the handoff from `kanlu` to implementation.

- Files to inspect/change: `PROJECT.md`, `STATUS.md`, `DECISIONS.md`, `tasks/*.md`, future architecture docs
- Minimal approach: inspect the collaboration layer, choose the first executable architecture slice, and avoid product implementation until architecture contracts are accepted
- Main risks: over-scoping the first implementation batch; letting model experiments define product architecture; missing consent, audit, and fallback requirements
- Validation commands: `/Users/joe/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 /Users/joe/.codex/skills/repo-init/scripts/harness.py check --repo .`
- Rollback or safety note: revert only files changed by the current task batch; preserve user-authored plans and accepted decisions

## Child Tasks

- `TASK-002-lock-production-architecture.md`: lock production service boundaries, data flow, storage, and runtime assumptions.
- `TASK-008-design-governance-baseline-and-authorized-assets.md`: define the early consent, authorization, tenant, and audit baseline that downstream contracts must follow.
- `TASK-003-define-scene-dsl-and-planning-contract.md`: define the deterministic scene DSL and LLM planning contract.
- `TASK-004-design-model-service-adapters.md`: design adapters for TTS, avatar, subtitle alignment, renderer, and composition services.
- `TASK-005-design-orchestration-and-gpu-workers.md`: design resumable orchestration, queues, GPU worker pools, and artifact lifecycles.
- `TASK-006-design-quality-gates-and-auto-repair.md`: design quality inspection, fallback, retry, and repair loops.
- `TASK-007-design-product-api-and-console.md`: design the enterprise API, job state model, and operator console surface.
- `TASK-009-complete-compliance-checklist-and-risk-register.md`: complete the final compliance checklist, traceability model, and risk register after downstream contracts exist.

## Recommended Order

1. `TASK-002-lock-production-architecture.md`
2. `TASK-008-design-governance-baseline-and-authorized-assets.md`
3. `TASK-003-define-scene-dsl-and-planning-contract.md`
4. `TASK-004-design-model-service-adapters.md`
5. `TASK-005-design-orchestration-and-gpu-workers.md`
6. `TASK-006-design-quality-gates-and-auto-repair.md`
7. `TASK-007-design-product-api-and-console.md`
8. `TASK-009-complete-compliance-checklist-and-risk-register.md`

## Replan Triggers

- blocker introduced or removed
- acceptance failed or changed
- assumption invalidated
- new dependency found
- scope clarification received
- model runtime benchmark invalidates the planned architecture
- compliance requirement changes asset onboarding or publishing behavior

## Feedback Ledger

- `Date=2026-05-30; Source Task=TASK-001; Observation=Yanshou accepted the enterprise coordination task; Impacted Tasks=TASK-002..TASK-008; Suggested Action=keep`
- `Date=2026-05-30; Source Task=kanlu; Observation=Downstream route inspection found governance must precede DSL, model adapters, API, and QC; Impacted Tasks=TASK-003..TASK-008; Suggested Action=reorder`
- `Date=2026-05-30; Source Task=baguan; Observation=Review accepted the route only if governance is split into early baseline and final compliance completion; Impacted Tasks=TASK-001..TASK-009; Suggested Action=split`
- Use: `Date=<YYYY-MM-DD>; Source Task=<task-id>; Observation=<high-signal feedback>; Impacted Tasks=<task-id or none>; Suggested Action=<keep|reorder|block|split|revise-acceptance|clarify>`

## Replan Decisions

- Accepted on `2026-05-30`: split the original security/compliance task into early `TASK-008` governance baseline and late `TASK-009` compliance/risk completion.
- Accepted on `2026-05-30`: keep `TASK-002` first, then run the governance baseline before DSL, model adapters, orchestration, QC, and product API work.
- Record only explicitly accepted task-order or task-definition changes here.

## Hold Rules

- Do not start child tasks automatically during initialization.
- Explicitly confirm `TASK-002-lock-production-architecture.md` before beginning execution.
- Do not downgrade the project to an MVP/demo objective unless the user explicitly changes the target.

## Cross-Task Risks

- Model quality, GPU cost, and latency can invalidate product promises if not benchmarked early.
- The platform must treat voice and avatar cloning as authorized asset workflows, not arbitrary user uploads.
- Fallback behavior must be designed before implementation so success-rate claims are credible.

## Notes

- Facts: initialization target is enterprise-grade automated talking-head video generation; output should be publish-ready vertical short video; no product code has been implemented
- Assumptions: initial task order starts with architecture before runtime scaffolding
- Risks: task order may still need reprioritization once explicit execution begins

## Assumption Checks

Update these lists whenever current execution validates or invalidates the task's working assumptions.

### Validated

- `2026-05-30`: Yanshou verified TASK-001 acceptance criteria.
- `2026-05-30`: Kanlu and Baguan verified that downstream work needs an explicit governance gate before implementation.

### Invalidated

- none

### Still Open

- GPU budget, target concurrency, preferred deployment environment, and first customer workflow still need confirmation.

## Downstream Impact

If execution changes downstream work, mirror that impact here instead of leaving it only in `Execution Log`.

### Affected Tasks

- `TASK-003`: now depends on `TASK-008` governance baseline for asset references and safety constraints.
- `TASK-004`: now depends on `TASK-008` governance baseline for artifact manifests, consent, and model-license evidence.
- `TASK-005`: now depends on `TASK-008` governance baseline for audit events, retention, and tenant boundaries.
- `TASK-006`: now depends on `TASK-008` governance baseline for unsafe-output escalation and review boundaries.
- `TASK-007`: now depends on `TASK-008` governance baseline for asset/API authorization surfaces.
- `TASK-009`: added as the final compliance/risk completion pass.

### Suggested Follow-up

- When a child task changes ordering, blockers, or acceptance expectations, update `STATUS.md` and this task before changing downstream work.
- Only move accepted reorder or scope changes into `Replan Decisions` before rewriting child tasks.

## Execution Log

Record milestone-level progress here. Each entry should summarize one meaningful execution batch, task-status transition, blocker change, or user-directed change of course.

Do not log every file save, every tiny edit, or every formatting-only change.

- `2026-05-29`: task created during repository initialization correction after repo-init produced an overly generic single task.
- `2026-05-29`: Baguan review completed; machine-readable repo-init metadata and validation runtime command were corrected.
- `2026-05-30`: Yanshou acceptance passed for TASK-001; next step is full downstream route inspection before child implementation.
- `2026-05-30`: Kanlu inspected the downstream child-task route; Baguan reviewed the route and required splitting governance baseline from final compliance completion.

## Review Notes

Use this section after implementation. `baguan` should record whether review completed and whether findings block progress.

- Status: `reviewed`
- Findings: Initial Baguan review found stale `.repo-init/intake.json` task metadata, stale front-loaded `.repo-init/init-report.md` decomposition fields, and a validation command that used the system Python instead of the bundled Python runtime. Route Baguan review then found governance was formally too late and required splitting early governance baseline from final compliance completion.
- Required follow-up: addressed in this task batch; rerun harness before moving to `TASK-002` implementation.

## Acceptance Evidence

Use this section after implementation. `yanshou` should record pass/fail evidence here or recommend the exact evidence to add.

- Status: `passed`
- Evidence: `2026-05-30`: Yanshou verified TASK-001 acceptance criteria. First-wave workstream is explicit and ordered in Child Tasks and Recommended Order; cross-task assumptions, risks, feedback, and replan triggers are visible in TASK-001 and STATUS.md; recommended start is TASK-002 and child tasks TASK-002 through TASK-008 remained Status: todo at verification time. Bundled Python repo-init harness check passed with errors: 0, warnings: 8 expected pending handoff fields. Post-acceptance route review added TASK-009 and recorded the split in this task's Feedback Ledger and Replan Decisions.
- Repro steps for failures: `none`

## Debug Notes

Use this section only when validation, QA, or user reports fail. `paicha` should record the minimal reproduction and likely root cause here or recommend the exact note to add.

- Failure signal: `none`
- Minimal reproduction: `pending`
- Likely root cause: `pending`
- Regression test: `pending`

## Harness Lessons

Use this section after meaningful implementation, review, QA, or debugging feedback. `chendian` should keep durable lessons short and point to any mechanical checks or docs updates.

- Durable lesson: `none yet`
- Harness update: `pending`
- Future trigger: `pending`
