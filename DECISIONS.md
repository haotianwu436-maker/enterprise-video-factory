# DECISIONS.md

<!-- repo-init:managed -->

This file stores durable, accepted project decisions only.

## DEC-001: Enterprise-grade target, not MVP

- Status: `accepted`
- Date: `2026-05-29`
- Decision: The project target is an enterprise-usable automated口播视频 generation platform, not a demo or MVP-only scaffold.
- Consequence: Architecture, reliability, observability, governance, quality gates, and fallback behavior must be treated as first-wave work.

## DEC-002: Segment-based generation

- Status: `accepted`
- Date: `2026-05-29`
- Decision: Videos should be generated as independently retryable scenes/segments before final composition.
- Consequence: Orchestration, artifact storage, QC, and repair flows must support partial reruns.

## DEC-003: Deterministic scene DSL over arbitrary generated code

- Status: `accepted`
- Date: `2026-05-29`
- Decision: LLMs should output validated scene/storyboard DSL rather than unrestricted HTML or code.
- Consequence: Rendering should use controlled templates and schema validation to improve reliability and safety.

## DEC-004: Authorized identity assets only

- Status: `accepted`
- Date: `2026-05-29`
- Decision: Voice cloning and avatar generation must operate on authorized voice/avatar profiles with consent and audit evidence.
- Consequence: Asset onboarding, RBAC, audit logs, safety review, and abuse controls are product requirements from the start.

## DEC-005: Split governance baseline from final compliance completion

- Status: `accepted`
- Date: `2026-05-30`
- Decision: Split the original security/compliance work into an early governance baseline (`TASK-008`) and a final compliance/risk completion pass (`TASK-009`).
- Consequence: Downstream DSL, model adapter, orchestration, QC, and API work must consume the early governance baseline, while final traceability and compliance reconciliation waits until those contracts exist.
