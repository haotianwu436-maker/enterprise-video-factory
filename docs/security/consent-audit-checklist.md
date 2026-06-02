# Consent And Audit Checklist

<!-- tasks: TASK-008, TASK-009 -->

## Purpose

This checklist is the working control list for consent, audit, traceability, and review. `TASK-008` defines the early baseline; `TASK-009` completes final reconciliation after DSL, model, orchestration, QC, and API contracts exist.

Status values:

- `baseline`: required by early governance.
- `downstream`: must be consumed by later contracts.
- `final`: complete in `TASK-009`.

## Asset Consent Controls

| Control | Status | Evidence |
| --- | --- | --- |
| Voice profile has owner/subject identity. | baseline | `asset.subject_id` |
| Avatar profile has owner/subject identity. | baseline | `asset.subject_id` |
| Consent evidence has immutable event ID. | baseline | `consent_event_id` |
| Consent scope includes use case. | baseline | `allowed_use_cases` |
| Consent scope includes platform scope. | baseline | `allowed_platforms` |
| Consent can expire or be revoked. | baseline | `expires_at`, `revocation_event_id` |
| Active asset requires verified consent. | baseline | asset state machine |
| Revoked asset is blocked from new generation. | baseline | job validation rule |
| Long-running job re-checks authorization before release. | downstream | orchestration release guard |
| Released video keeps historical authorization snapshot. | final | traceability bundle |

## Tenant And RBAC Controls

| Control | Status | Evidence |
| --- | --- | --- |
| Asset IDs are tenant-scoped. | baseline | `tenant_id`, `asset_id` |
| Job and artifact queries require tenant scope. | downstream | API/resource contract |
| Signed artifact URLs are tenant-scoped and time-limited. | downstream | API/console contract |
| Review actions are role-restricted. | baseline | RBAC matrix |
| Operator retries cannot override consent failure. | downstream | repair/review policy |
| Auditor can read evidence but not mutate jobs. | baseline | RBAC matrix |
| Service identities cannot approve consent. | baseline | service role rule |

## Audit Event Controls

| Control | Status | Evidence |
| --- | --- | --- |
| Audit events are append-only. | baseline | Audit/Event Store boundary |
| Asset lifecycle events are audited. | baseline | `asset.*` events |
| Job lifecycle events are audited. | downstream | `job.*`, `stage.*` events |
| QC decisions are audited. | downstream | `qc.completed` |
| Repair decisions are audited. | downstream | `repair.*` |
| Review decisions are audited. | downstream | `review.*` |
| Release and current pointer changes are audited. | downstream | `release.*` |
| Traceability bundle references audit events. | final | `traceability_bundle.json` |

## Artifact Traceability Controls

| Control | Status | Evidence |
| --- | --- | --- |
| Generated artifacts have manifests. | downstream | artifact manifest contract |
| Manifests include tenant, job, segment, stage, attempt. | downstream | manifest envelope |
| Manifests include input hashes and output URIs. | downstream | manifest envelope |
| Manifests include model/service version. | downstream | model adapter contract |
| Manifests include identity asset authorization snapshots. | downstream | adapter manifest |
| Released binaries are immutable and versioned. | baseline | release URI layout |
| `release/current.json` is the mutable pointer. | baseline | release pointer rule |
| Traceability bundle can reconstruct the final MP4 lineage. | final | traceability matrix |

## Review Controls

| Trigger | Required Action | Status |
| --- | --- | --- |
| Missing or expired consent | Block job or release | baseline |
| Revoked identity asset | Block new generation | baseline |
| QC unsafe output | Open review | downstream |
| Repeated repair failure | Open review | downstream |
| Disputed identity asset | Suspend asset and open review | baseline |
| Policy-sensitive content | Open review according to tenant policy | final |
| Release after manual override | Audit reviewer and reason | downstream |

## Open Items For Final Completion

- Target jurisdictions and applicable disclosure law.
- Required AI labeling policy.
- Default retention windows.
- Raw enrollment media deletion policy.
- Whether enterprise release requires dual approval.
- External legal/compliance review owner.
- Customer export requirements for audit bundles.

## Final Reconciliation Notes

- `docs/security/traceability-matrix.md` defines the current evidence chain required for a publish-ready video.
- `docs/security/risk-register.md` captures launch blockers and residual risks.
- The checklist is not a legal certification; unresolved jurisdiction and disclosure questions remain launch blockers.
