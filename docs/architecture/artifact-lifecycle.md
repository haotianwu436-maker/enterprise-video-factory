# Artifact Lifecycle

<!-- task: TASK-002 -->

## Purpose

This document defines how artifacts move through the production video factory. It is the storage and traceability companion to `production-architecture.md`.

The main rule: every stage consumes immutable inputs and produces versioned artifacts with a manifest. Downstream stages should never depend on unnamed local files or implicit process state.

## Artifact Classes

| Class | Examples | Owner | Notes |
| --- | --- | --- | --- |
| Source | raw prompt, article text, uploaded reference files | API | Immutable after job validation |
| Asset | voice profile, avatar profile, brand kit, music, template | Asset Registry | Must be authorized before use |
| Plan | normalized script, segment list, scene DSL | Planner | Must validate before model stages |
| Segment Input | per-segment text, timing, asset refs, template refs | Orchestrator | Deterministic IDs |
| Model Output | TTS wav, avatar video, alignment data | Model Adapters | Must include model/version metadata |
| Render Output | scene layer, overlay, template render | Renderer | Must include template/version metadata |
| Composition | mixed audio, subtitle file, candidate final MP4 | Composer | Candidate until final QC passes |
| Quality Evidence | QC report, ASR backcheck, probe results, repair decision | QC | Required before release |
| Audit Evidence | consent event refs, operator actions, stage attempts | Audit/Event Store | Required for enterprise traceability |
| Release | final MP4, poster frame, publish metadata, traceability bundle | API/Console | Only after final QC and authorization pass |

## URI Layout

Use stable object keys that encode tenant, job, segment, stage, and attempt.

```text
s3://video-factory/{tenant_id}/jobs/{job_id}/source/input.json
s3://video-factory/{tenant_id}/jobs/{job_id}/plan/storyboard.v{n}.json
s3://video-factory/{tenant_id}/jobs/{job_id}/segments/{segment_id}/tts/attempt-{attempt}/audio.wav
s3://video-factory/{tenant_id}/jobs/{job_id}/segments/{segment_id}/avatar/attempt-{attempt}/avatar.mp4
s3://video-factory/{tenant_id}/jobs/{job_id}/segments/{segment_id}/render/attempt-{attempt}/scene.mp4
s3://video-factory/{tenant_id}/jobs/{job_id}/compose/attempt-{attempt}/candidate.mp4
s3://video-factory/{tenant_id}/jobs/{job_id}/qc/final/attempt-{attempt}/qc_report.json
s3://video-factory/{tenant_id}/jobs/{job_id}/release/releases/{release_id}/final.mp4
s3://video-factory/{tenant_id}/jobs/{job_id}/release/releases/{release_id}/traceability_bundle.json
s3://video-factory/{tenant_id}/jobs/{job_id}/release/current.json
```

Rules:

- Object keys are append-only for stage attempts.
- Released binaries and traceability bundles are immutable and versioned by `release_id`.
- `release/current.json` is the only mutable release pointer, and every pointer change must create an append-only release audit event.
- Manifests point to object URIs, not local worker paths.
- Deletion and retention are governed by tenant policy and `TASK-008`.

## Manifest Envelope

Every generated artifact should have a manifest with this envelope:

```json
{
  "manifest_version": "0.1",
  "tenant_id": "tenant_123",
  "job_id": "job_456",
  "segment_id": "seg_001",
  "stage": "tts",
  "attempt": 1,
  "producer": {
    "service": "tts-adapter",
    "version": "0.1.0",
    "model": "candidate-model",
    "model_version": "unverified"
  },
  "inputs": [
    {
      "type": "scene_segment",
      "uri": "s3://video-factory/tenant_123/jobs/job_456/segments/seg_001/input.json",
      "sha256": "..."
    }
  ],
  "outputs": [
    {
      "type": "audio_wav",
      "uri": "s3://video-factory/tenant_123/jobs/job_456/segments/seg_001/tts/attempt-1/audio.wav",
      "sha256": "...",
      "mime_type": "audio/wav"
    }
  ],
  "asset_refs": [
    {
      "asset_id": "voice_abc",
      "asset_type": "voice_profile",
      "authorization_snapshot": "auth_evt_789"
    }
  ],
  "timing": {
    "started_at": "2026-05-30T00:00:00Z",
    "finished_at": "2026-05-30T00:00:10Z"
  },
  "trace": {
    "workflow_id": "wf_123",
    "run_id": "run_456",
    "span_id": "span_789"
  }
}
```

Notes:

- Exact field names may move to `docs/contracts/artifact-manifest.md` in `TASK-004`.
- `authorization_snapshot` is required for identity assets once `TASK-008` defines the event model.
- `model_version` must not remain `unverified` in production releases.

## Lifecycle By Stage

### 1. Source Intake

Inputs:

- User text, article, or opinion.
- Selected voice/avatar/brand/template assets.
- Requested output profile.

Outputs:

- `source/input.json`
- `source/request_manifest.json`

Checks:

- Tenant/user authorization.
- Asset availability.
- Basic content and format validation.

### 2. Planning

Inputs:

- Source input.
- Asset and output profile references.

Outputs:

- `plan/script.v{n}.json`
- `plan/storyboard.v{n}.json`
- `plan/planner_manifest.json`

Checks:

- Scene DSL schema validation.
- Duration bounds.
- Asset references are IDs, not arbitrary paths.
- Planner repair history is preserved.

### 3. Segment Initialization

Inputs:

- Validated storyboard.

Outputs:

- `segments/{segment_id}/input.json`
- segment metadata rows.

Checks:

- Deterministic segment IDs.
- Idempotency keys.
- Downstream stage requirements.

### 4. TTS

Inputs:

- Segment text.
- Authorized voice profile.
- Voice style and timing hints.

Outputs:

- `audio.wav`
- `tts_manifest.json`
- audio QC draft.

Checks:

- Audio duration within expected bounds.
- Loudness and clipping.
- ASR backcheck where available.
- Voice authorization snapshot.

### 5. Avatar

Inputs:

- Segment audio.
- Authorized avatar profile.
- Emotion/head-motion hints.

Outputs:

- `avatar.mp4`
- `avatar_manifest.json`
- face/lip-sync QC draft.

Checks:

- Face detected.
- No black or corrupt frames.
- Lip-sync score available where supported.
- Avatar authorization snapshot.

### 6. HTML/Scene Render

Inputs:

- Scene DSL segment.
- Template version.
- Avatar segment or placeholder.

Outputs:

- `scene.mp4` or overlay artifact.
- `render_manifest.json`

Checks:

- Non-empty render.
- Correct aspect ratio and fps.
- Text safe-area checks.
- Template version recorded.

### 7. Subtitle And Audio Mix

Inputs:

- Segment audio.
- Alignment data or ASR output.
- Music asset.

Outputs:

- subtitle file.
- mixed audio.
- alignment manifest.

Checks:

- Subtitle timing.
- Two-line and safe-area constraints.
- Music license/authorization.
- Loudness target.

### 8. Composition

Inputs:

- Avatar segments.
- Rendered scene layers.
- Subtitles.
- Mixed audio.

Outputs:

- `candidate.mp4`
- `composition_manifest.json`

Checks:

- Codec, fps, dimensions.
- Duration consistency.
- No missing segments.
- All input manifests referenced.

### 9. Quality And Repair

Inputs:

- Candidate final MP4.
- Stage manifests.
- Stage QC reports.

Outputs:

- `qc_report.json`
- repair decision.
- optional repair job attempt.

Checks:

- Final video probe.
- Black frame and silence checks.
- Subtitle visibility.
- Face visibility.
- Traceability completeness.
- Governance and authorization checks.

### 10. Release

Inputs:

- Candidate MP4.
- Passing final QC report.
- Traceability bundle.

Outputs:

- `release/releases/{release_id}/final.mp4`
- `release/releases/{release_id}/poster.jpg`
- `release/releases/{release_id}/traceability_bundle.json`
- `release/current.json`
- append-only release audit event.

Checks:

- Final QC passed.
- No unresolved manual review blocker.
- Required authorization snapshots exist.
- Required disclosure metadata exists once policy is defined.

## Traceability Bundle

Every release should include a bundle that can answer:

- What source input generated this video?
- Which tenant and user requested it?
- Which voice/avatar/brand/template/music assets were used?
- What consent or authorization event allowed each identity asset?
- Which model service and model version produced each model output?
- Which QC checks passed or failed?
- Which repairs or retries happened?
- Which operator actions affected release?

Initial bundle shape:

```json
{
  "bundle_version": "0.1",
  "tenant_id": "tenant_123",
  "job_id": "job_456",
  "release_id": "rel_001",
  "final_video_uri": "s3://video-factory/tenant_123/jobs/job_456/release/releases/rel_001/final.mp4",
  "source_input": {},
  "assets": [],
  "segments": [],
  "stage_manifests": [],
  "qc_reports": [],
  "audit_events": [],
  "open_questions": []
}
```

## Retention And Deletion

Draft policy hooks:

- Source input retention may differ from final video retention.
- Identity asset references must remain traceable for released videos.
- Failed attempts may be pruned after a tenant-specific window, except when tied to abuse review, audit, or incident investigation.
- Deletion requests must consider final-video traceability requirements.

Open questions:

- Default retention window per tenant.
- Whether raw reference audio/video should be deleted after profile creation.
- Whether customers require exportable audit bundles.
- Whether `release/current.json` may be rolled back to a previous immutable release after operator review.

## Failure And Repair Rules

- A failed stage writes a failure manifest if it produced any artifact or meaningful diagnostic.
- Repair attempts must reference the failed artifact and QC report.
- Segment repair should not invalidate unrelated passing segments.
- Whole-job reruns require an explicit reason.
- Repeated failure routes to manual review or failed terminal state.

## Downstream Contract Requirements

- `TASK-003` must make scene DSL artifact references compatible with this lifecycle.
- `TASK-004` must turn the manifest envelope into formal adapter contracts.
- `TASK-005` must map lifecycle stages to orchestration states and idempotency keys.
- `TASK-006` must define QC reports that fit this traceability chain.
- `TASK-007` must expose artifact and review state without leaking cross-tenant data.
- `TASK-008` must define authorization snapshots, audit event names, and retention baseline.
- `TASK-009` must reconcile final traceability against all stage contracts.
