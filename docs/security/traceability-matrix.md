# Traceability Matrix

<!-- task: TASK-009 -->

## Purpose

This matrix verifies that every publish-ready video can be traced from source input through assets, model outputs, QC reports, review decisions, and immutable release artifacts.

It is a contract-level checklist, not legal certification.

## End-To-End Traceability

| Requirement | Source Document | Evidence Artifact |
| --- | --- | --- |
| Raw input is persisted. | `production-architecture.md` | `source/input.json` |
| Scene DSL is validated before model stages. | `scene-dsl.md` | `plan/storyboard.v{n}.json`, planner manifest |
| Voice/avatar assets are authorized. | `asset-governance.md` | consent event IDs, authorization snapshots |
| Every segment has deterministic ID. | `job-state-machine.md` | segment input manifest |
| TTS output has model/version metadata. | `model-service-adapters.md` | TTS artifact manifest |
| Avatar output has identity and model metadata. | `model-service-adapters.md` | avatar artifact manifest |
| Render output has template/version metadata. | `model-service-adapters.md` | render manifest |
| Audio mix has loudness and music provenance evidence. | `model-service-adapters.md` | audio mix manifest, loudness report |
| Composition has complete segment inputs. | `artifact-lifecycle.md` | composition manifest |
| QC produces stage and final reports. | `qc-matrix.md` | `qc_report.json` |
| Repair attempts reference failures. | `repair-policy.md` | repair decision and audit event |
| Review decisions are append-only. | `asset-governance.md` | review audit event |
| Final release is immutable/versioned. | `artifact-lifecycle.md` | `release/releases/{release_id}/final.mp4` |
| Current release pointer is audited. | `artifact-lifecycle.md` | `release/current.json`, release audit event |
| API exposes evidence without bypassing RBAC. | `api-console.md` | signed artifact URL and audit event |

## Release Traceability Bundle

Required fields:

```json
{
  "bundle_version": "0.1",
  "tenant_id": "tenant_123",
  "job_id": "job_456",
  "release_id": "rel_001",
  "final_video_uri": "s3://video-factory/tenant_123/jobs/job_456/release/releases/rel_001/final.mp4",
  "source_input_ref": {},
  "asset_refs": [],
  "authorization_snapshots": [],
  "scene_dsl_ref": {},
  "segment_refs": [],
  "stage_manifests": [],
  "qc_reports": [],
  "repair_decisions": [],
  "review_decisions": [],
  "audit_events": [],
  "open_compliance_items": []
}
```

## Stage-To-Evidence Matrix

| Stage | Required Manifest | Required QC | Required Audit |
| --- | --- | --- | --- |
| Source intake | request manifest | validation report | `job.created` |
| Planning | storyboard manifest | schema validation | `stage.completed` |
| Segment input | segment manifest | none | `stage.completed` |
| TTS | TTS manifest | audio QC | `stage.completed` |
| Avatar | avatar manifest | face/lip QC | `stage.completed` |
| Render | render manifest | render QC | `stage.completed` |
| Alignment | alignment manifest | text coverage QC | `stage.completed` |
| Audio Mix | audio mix manifest | loudness/mix QC | `stage.completed` |
| Composition | composition manifest | candidate QC | `stage.completed` |
| Repair | repair manifest and repair decision | repair QC or next-stage QC | `repair.requested`, `repair.completed` |
| Review | review decision record | policy/QC evidence referenced by review | `review.opened`, terminal review event |
| Final QC | final QC report | final QC | `qc.completed` |
| Release | release manifest | final pass | `release.created`, `release.current_pointer_changed` |

## Asset Traceability

Every identity asset in a final video must show:

- `asset_id`
- `asset_type`
- `asset_version`
- `authorization_snapshot`
- consent event URI/reference
- revocation status at job creation
- revocation status at release

## Model Traceability

Every model-generated artifact must show:

- adapter service
- service version
- model name
- model version
- model license status
- input manifest/hash
- output URI/hash
- failure or QC status

Open item:

- Production launch requires verified model license/capability records.

## Operator Traceability

Every mutating operator/reviewer action must show:

- actor ID and role
- tenant ID
- action type
- target job/segment/artifact/review/release
- reason
- timestamp
- audit event ID

## Gaps To Resolve Before Launch

- Legal review of consent language.
- AI disclosure policy by platform/jurisdiction.
- Default retention windows.
- Dual-approval policy for enterprise release.
- Customer audit export format.
- Verified license/capability metadata for selected models.
