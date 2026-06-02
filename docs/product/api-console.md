# Product API And Operator Console

<!-- task: TASK-007 -->

## Purpose

This document defines the enterprise API resources and operator console workflows for the automated talking-head video factory. It is a product/API contract, not an implementation.

## Product Surfaces

- Customer API for assets, jobs, artifacts, reviews, and releases.
- Operator console for job monitoring, QC evidence, repair/retry actions, manual review, and audit bundles.
- Signed artifact access for media retrieval.
- Audit/event visibility for enterprise traceability.

## API Principles

- All requests are tenant-scoped.
- Identity assets must be active and authorized before job creation.
- Artifact retrieval uses signed, tenant-scoped access.
- Repair/retry/release actions are audited.
- API exposes stage and QC evidence without exposing unnecessary runtime internals.
- Review blockers cannot be bypassed by ordinary operator actions.

## Resource Model

| Resource | Purpose |
| --- | --- |
| Tenant | Enterprise boundary for users, assets, jobs, artifacts, and audit. |
| User/Role | RBAC identity and permissions. |
| Asset | Voice, avatar, brand, music, template. |
| Consent Event | Evidence that identity asset use is authorized. |
| Job | End-to-end video generation request. |
| Segment | Retryable unit within a job. |
| Stage Attempt | One stage execution attempt. |
| Artifact | Stored output with manifest and signed access. |
| QC Report | Quality evidence and repair recommendation. |
| Review Item | Human review blocker or decision. |
| Release | Immutable final MP4 and traceability bundle. |
| Audit Event | Append-only action/event record. |

## Core API Endpoints

Draft endpoints:

```text
POST   /v1/jobs
GET    /v1/jobs/{job_id}
GET    /v1/jobs/{job_id}/segments
GET    /v1/jobs/{job_id}/artifacts
GET    /v1/jobs/{job_id}/qc
POST   /v1/jobs/{job_id}/cancel
POST   /v1/jobs/{job_id}/repair
POST   /v1/jobs/{job_id}/release

GET    /v1/assets
POST   /v1/assets
GET    /v1/assets/{asset_id}
POST   /v1/assets/{asset_id}/consent
POST   /v1/assets/{asset_id}/activate
POST   /v1/assets/{asset_id}/suspend
POST   /v1/assets/{asset_id}/revoke

GET    /v1/reviews
GET    /v1/reviews/{review_id}
POST   /v1/reviews/{review_id}/decision

GET    /v1/artifacts/{artifact_id}/signed-url
GET    /v1/audit/events
```

## Create Job Request

```json
{
  "input": {
    "type": "opinion",
    "text": "企业级自动口播视频的关键不是一次生成，而是可恢复的流水线。"
  },
  "asset_refs": {
    "voice_profile_id": "voice_abc",
    "avatar_profile_id": "avatar_def",
    "brand_kit_id": "brand_001",
    "music_asset_id": "music_001",
    "template_id": "template_001"
  },
  "output_profile": {
    "duration_target_sec": 60,
    "aspect_ratio": "9:16",
    "resolution": { "width": 1080, "height": 1920 },
    "publish_targets": ["douyin", "wechat_channels"]
  },
  "policy": {
    "allow_quality_fallback": true,
    "manual_review_required": false
  }
}
```

Validation:

- tenant and user can access assets
- voice/avatar assets are active
- consent snapshots exist
- template/music are approved
- output profile is supported

## Job Response

```json
{
  "job_id": "job_456",
  "tenant_id": "tenant_123",
  "state": "validated",
  "active_stage": "planning",
  "progress": {
    "segments_total": 0,
    "segments_completed": 0,
    "repair_attempts": 0
  },
  "asset_authorization_snapshots": ["consent_evt_123", "consent_evt_456"],
  "links": {
    "self": "/v1/jobs/job_456",
    "artifacts": "/v1/jobs/job_456/artifacts",
    "qc": "/v1/jobs/job_456/qc"
  }
}
```

## Job State Exposure

API state names mirror `docs/contracts/job-state-machine.md`.

The console should show:

- state
- active stage
- segment progress
- current blocker
- latest failure code
- repair attempts
- review state
- final release state

## Artifact API

Artifact list response:

```json
{
  "artifacts": [
    {
      "artifact_id": "art_123",
      "job_id": "job_456",
      "segment_id": "seg_001",
      "stage": "tts",
      "attempt": 1,
      "manifest_uri": "s3://video-factory/tenant_123/jobs/job_456/segments/seg_001/tts/attempt-1/manifest.json",
      "qc_status": "passed",
      "signed_url_available": true
    }
  ]
}
```

Rules:

- Signed URLs require tenant scope and RBAC.
- Console never reads object storage directly.
- Artifact manifests are visible to operators and auditors according to role.

## Repair API

```json
{
  "scope": "segment",
  "segment_id": "seg_001",
  "failure_code": "lip_sync_below_threshold",
  "requested_action": "retry_with_reduced_motion",
  "reason": "QC repair recommendation accepted by operator."
}
```

Rules:

- Repair requests must reference QC failure evidence.
- Authorization failures cannot be repaired automatically.
- Manual review decisions may be required before repair.

## Release API

Release request:

```json
{
  "candidate_artifact_id": "artifact_candidate_001",
  "acknowledge_qc_passed": true,
  "acknowledge_traceability_bundle": true
}
```

Release response:

```json
{
  "release_id": "rel_001",
  "state": "current",
  "final_video_uri": "s3://video-factory/tenant_123/jobs/job_456/release/releases/rel_001/final.mp4",
  "traceability_bundle_uri": "s3://video-factory/tenant_123/jobs/job_456/release/releases/rel_001/traceability_bundle.json",
  "current_pointer_uri": "s3://video-factory/tenant_123/jobs/job_456/release/current.json"
}
```

Rules:

- Release artifacts are immutable.
- Current pointer change is audited.
- Release is blocked if final QC, review, authorization, or traceability checks fail.

## Review API

Review decision request:

```json
{
  "decision": "approved_with_restrictions",
  "reason": "Fallback quality accepted for internal campaign draft.",
  "restrictions": ["internal_use_only"]
}
```

Decision values:

- `approved`
- `approved_with_restrictions`
- `rejected`
- `escalated`

Rules:

- Review decisions require reviewer role.
- Restrictions must flow into release policy.
- Review decisions are audit events.

## Operator Console Workflows

### Job Monitor

Shows:

- job state and progress
- segment list
- active stage
- latest stage attempts
- artifact manifest links
- QC status
- review blockers
- release status

### Failure Triage

Shows:

- failure code and severity
- stage and segment
- QC evidence
- repair recommendation
- allowed operator actions
- audit history

### Asset Governance

Shows:

- asset state
- consent evidence
- authorization snapshots
- affected jobs/releases
- revoke/suspend actions for authorized roles

### Release Review

Shows:

- candidate final video
- final QC report
- traceability bundle
- disclosure metadata
- release action or blocker reason

## Console Safety Rules

- No direct DB/object storage reads in the console.
- Console uses API and signed artifact URLs.
- Every mutating action creates an audit event.
- Review blockers are visible and cannot be hidden by a generic success state.
- Operators see enough evidence to act, but not raw tenant data outside their role.

## OpenAPI Draft

The initial OpenAPI file is `openapi/enterprise-video-factory.openapi.yaml`. It should remain a resource-model draft until downstream contracts are accepted.

## Open Questions

- First identity provider and SSO target.
- Whether release requires dual approval.
- Whether public publishing integrations belong in v1.
- Whether customer-facing API and internal operator API should be split.

