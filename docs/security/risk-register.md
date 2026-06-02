# Risk Register

<!-- task: TASK-009 -->

## Purpose

This register captures residual product, engineering, compliance, and operational risks for the enterprise talking-head video factory. It is not legal certification; it identifies launch blockers and follow-up decisions.

## Risk Scale

- Severity: `low`, `medium`, `high`, `critical`
- Likelihood: `low`, `medium`, `high`
- Status: `open`, `contracted`, `planned`, `accepted`, `blocked`

## Risks

| ID | Risk | Severity | Likelihood | Mitigation | Status |
| --- | --- | --- | --- | --- | --- |
| R-001 | Unauthorized voice or likeness is used. | critical | medium | Asset governance baseline, consent snapshots, hard QC/release failure. | contracted |
| R-002 | Operator console bypasses tenant/RBAC controls. | critical | low | Console uses API/RBAC and signed tenant-scoped artifact URLs. | contracted |
| R-003 | Released artifact URI changes after audit bundle is produced. | high | low | Immutable versioned releases and `release/current.json` pointer. | contracted |
| R-004 | Model license is not valid for commercial production. | high | medium | License/capability verification required before production default. | open |
| R-005 | GPU latency/cost invalidates enterprise SLO. | high | medium | Benchmark before runtime commitment; keep architecture assumptions open. | open |
| R-006 | Scene DSL becomes too expressive and permits arbitrary code. | high | low | JSON schema, required semantic validator, prohibited code rules, controlled templates only. | contracted |
| R-007 | QC thresholds are too subjective for automated release. | medium | medium | Mark thresholds draft; require owner review and manual escalation. | open |
| R-008 | Repair loops hide quality degradation. | medium | medium | Repair/fallback is audited and visible in console. | contracted |
| R-009 | Traceability bundle misses stage evidence. | high | low | Artifact manifest and traceability matrix define required evidence. | contracted |
| R-010 | Target jurisdiction requires additional AI disclosure. | high | medium | Keep disclosure policy as launch blocker until reviewed. | open |
| R-011 | Raw enrollment media retention violates customer expectations. | high | medium | Retention policy open item; support shorter raw-media retention option. | open |
| R-012 | API exposes model/runtime internals to customers. | medium | medium | API contract exposes product state and manifests, not unnecessary runtime detail. | contracted |
| R-013 | Fallback voice/avatar changes identity expectation. | high | low | Fallback requires tenant policy and cannot replace unauthorized identity assets. | contracted |
| R-014 | Manual review becomes operational bottleneck. | medium | medium | Use review reason codes, thresholds, and role separation. | open |
| R-015 | Multi-tenant object storage keys leak data. | critical | low | Tenant-scoped keys and signed URLs; no direct console storage reads. | contracted |

## Launch Blockers

These must be resolved before production launch:

- Verify licenses and commercial usage rights for selected TTS/avatar/alignment/render models.
- Confirm target jurisdictions and AI disclosure requirements.
- Confirm retention/deletion policy for raw enrollment media and released videos.
- Confirm first enterprise RBAC roles and whether release requires dual approval.
- Confirm GPU budget, target concurrency, and latency SLO.

## Accepted Constraints

- This planning batch does not implement enforcement.
- This planning batch does not provide legal advice.
- Compliance language must be reviewed before production launch.
