# Define scene DSL and planning contract

<!-- repo-init:managed -->

## Metadata

- ID: `TASK-003`
- Status: `done`
- Owner: `shared`
- Parent: `TASK-001`
- Created: `2026-05-29`
- Updated: `2026-05-30`

## Why

Define a deterministic scene DSL so LLM planning can drive video generation without allowing arbitrary generated code to become a reliability or security risk.

## Scope

- In scope: storyboard schema, scene types, timing contract, validation rules, template parameters, and prompt/repair strategy
- Out of scope: implementing the renderer or final animation templates

## Acceptance Criteria

- The DSL can represent script segments, avatar behavior, subtitles, visual emphasis, music cues, and render templates.
- Invalid LLM output has deterministic validation and repair behavior.
- The DSL is stable enough for model adapters and Remotion/HTML rendering to consume.

## Product Acceptance

- User journey: `pending`
- Evidence required: schema draft, example storyboard JSON, and validation strategy
- Acceptance owner: `yanshou`
- Acceptance status: `passed`

## Dependencies

- Files: `PROJECT.md, tasks/TASK-001-coordinate-enterprise-delivery-plan.md, tasks/TASK-002-lock-production-architecture.md, tasks/TASK-008-design-governance-baseline-and-authorized-assets.md`
- Decisions: `DEC-003, DEC-004, DEC-005`
- External: `none`

## Plan

1. Define scene and segment primitives.
2. Specify LLM planning inputs, outputs, and validation failures.
3. Provide example storyboards for 30, 60, and 90 second videos.

## Implementation Packet

- Files to inspect/change: `docs/contracts/scene-dsl.md`, `schemas/scene-storyboard.schema.json`, `examples/storyboards/30s.json`, `examples/storyboards/60s.json`, `examples/storyboards/90s.json`, `docs/security/asset-governance.md`
- Minimal approach: define a v0.1 JSON schema, controlled scene primitives, asset-reference rules, validation failures, and LLM repair prompts with examples for 30, 60, and 90 second videos.
- Main risks: making the DSL too expressive and recreating arbitrary code generation; failing to encode consented asset references and safety constraints from the governance baseline.
- Validation commands: `/Users/joe/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 /Users/joe/.codex/skills/repo-init/scripts/harness.py check --repo .`; validate example storyboards against `schemas/scene-storyboard.schema.json` once schema tooling exists.
- Rollback or safety note: docs/schema/examples only; no renderer implementation. Keep backward compatibility notes if schema fields are renamed.

## Parent Coordination

- Parent task: `TASK-001-coordinate-enterprise-delivery-plan.md`
- Start this task only after explicit post-initialization confirmation.

## Related Tasks

- Review `TASK-002-lock-production-architecture.md` for service boundaries before execution.
- Review `TASK-008-design-governance-baseline-and-authorized-assets.md` for consented asset references and safety constraints before execution.
- Coordinate output contracts with `TASK-004-design-model-service-adapters.md`.

## Notes

- Facts: LLMs should emit structured data, not arbitrary HTML or code
- Assumptions: template-driven rendering is the path to high success rates
- Risks: overly expressive DSL can reduce determinism and increase QC burden

## Assumption Checks

### Validated

- `2026-05-30`: Created `docs/contracts/scene-dsl.md`, `schemas/scene-storyboard.schema.json`, and 30/60/90 second example storyboards.
- `2026-05-30`: Examples use authorized identity asset refs rather than raw file paths.

### Invalidated

- none

### Still Open

- The initial template library size and scene taxonomy are not yet confirmed.

## Downstream Impact

### Affected Tasks

- `TASK-004`: consumes scene IDs, asset refs, and DSL schema version in adapter contracts.
- `TASK-006`: consumes subtitle, safe-area, face/lip expectations, and scene constraints for QC.
- `TASK-007`: can expose storyboard/resource state without accepting arbitrary code.

### Suggested Follow-up

- If DSL scope changes renderer or QC expectations, update `TASK-001` and affected child tasks.

## Execution Log

- `2026-05-29`: task created during repository initialization correction.
- `2026-05-30`: scene DSL contract, JSON schema, and storyboard examples created as documentation/schema/examples only.

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
