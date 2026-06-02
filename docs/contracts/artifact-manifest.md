# Artifact Manifest Contract

<!-- task: TASK-004 -->

## Purpose

The artifact manifest is the common evidence envelope for every generated artifact. It connects production architecture, governance, scene DSL, model adapters, orchestration, QC, API, and final compliance.

Every generated artifact must be traceable to:

- tenant and job
- segment and stage
- attempt and producer
- input hashes
- output URIs
- asset refs and authorization snapshots
- audit events
- quality evidence

## Manifest Envelope

```json
{
  "manifest_version": "0.1",
  "tenant_id": "tenant_123",
  "job_id": "job_456",
  "segment_id": "seg_001",
  "stage": "tts",
  "attempt": 1,
  "idempotency_key": "job_456:seg_001:tts:1",
  "producer": {},
  "inputs": [],
  "outputs": [],
  "asset_refs": [],
  "audit_events": [],
  "qc_refs": [],
  "timing": {},
  "trace": {},
  "status": "succeeded",
  "failure": null
}
```

## Required Fields

| Field | Required | Notes |
| --- | --- | --- |
| `manifest_version` | yes | Current version is `0.1`. |
| `tenant_id` | yes | Required for tenant isolation. |
| `job_id` | yes | Parent video job. |
| `segment_id` | stage-dependent | Required for segment stages; `null` or omitted for job-level release. |
| `stage` | yes | Controlled stage enum. |
| `attempt` | yes | Starts at `1`; increments on retry/repair. |
| `idempotency_key` | yes | Stable key for stage attempt. |
| `producer` | yes | Service, version, and model metadata. |
| `inputs` | yes | Input artifacts with hashes. |
| `outputs` | yes | Output artifacts with hashes and MIME type. |
| `asset_refs` | yes | Empty array allowed only when the stage consumes no assets. |
| `audit_events` | yes | Append-only event IDs relevant to this artifact. |
| `qc_refs` | yes | QC report refs, possibly empty before QC runs. |
| `timing` | yes | Start/end timestamps and duration. |
| `trace` | yes | Workflow/run/span IDs. |
| `status` | yes | `succeeded`, `failed`, `blocked`, or `superseded`. |
| `failure` | conditional | Required when `status` is `failed` or `blocked`. |

## Stage Enum

Allowed stages:

- `source_intake`
- `planning`
- `segment_input`
- `tts`
- `avatar`
- `alignment`
- `scene_render`
- `audio_mix`
- `composition`
- `qc`
- `repair`
- `review`
- `release`

## Stage And State Mapping

The manifest `stage` enum is canonical for artifact evidence. Job states are user-facing orchestration states, and QC matrix labels are human-facing names that must map back to a manifest stage.

| Manifest Stage | Job State(s) | QC Matrix Label |
| --- | --- | --- |
| `source_intake` | `created`, `validated` | Intake |
| `planning` | `planning`, `planned` | Planning |
| `segment_input` | `segmenting` | Segment Input |
| `tts` | `generating_audio` | TTS |
| `avatar` | `generating_avatar` | Avatar |
| `scene_render` | `rendering_scenes` | Render |
| `alignment` | `aligning_subtitles` | Alignment |
| `audio_mix` | `mixing_audio` | Audio Mix |
| `composition` | `composing` | Composition |
| `qc` | `quality_checking` | Stage QC / Final QC |
| `repair` | `repairing` | Repair |
| `review` | `review_required` | Review |
| `release` | `publish_ready` | Release |

Compatibility rules:

- Manifests must use only the canonical `stage` enum above.
- Job APIs may expose `active_stage`, but it must resolve to one of these manifest stages.
- QC reports may use readable labels, but each report must include the corresponding canonical manifest `stage`.
- Cross-contract changes to stage names require updating this table, the job state machine, QC matrix, OpenAPI resource model, and traceability matrix together.

## Producer Object

```json
{
  "service": "tts-adapter",
  "service_version": "0.1.0",
  "adapter_contract_version": "0.1",
  "model": "CosyVoice",
  "model_version": "unverified",
  "model_license": "unverified",
  "runtime": {
    "device_class": "gpu",
    "gpu_model": "unconfirmed",
    "container_image": "unbuilt"
  }
}
```

Rules:

- `model_version` and `model_license` may be `unverified` in planning docs, but production releases must use verified values.
- Renderer/composer services still provide producer metadata even when not ML models.
- Product APIs must not expose internal runtime details unless explicitly intended.

## Input Object

```json
{
  "type": "scene_segment",
  "uri": "s3://video-factory/tenant_123/jobs/job_456/segments/seg_001/input.json",
  "sha256": "hash",
  "manifest_uri": "s3://video-factory/tenant_123/jobs/job_456/segments/seg_001/input_manifest.json"
}
```

Rules:

- Inputs reference immutable objects.
- Hashes are required for all material inputs.
- Downstream stages consume manifests when available.

## Output Object

```json
{
  "type": "audio_wav",
  "uri": "s3://video-factory/tenant_123/jobs/job_456/segments/seg_001/tts/attempt-1/audio.wav",
  "sha256": "hash",
  "mime_type": "audio/wav",
  "size_bytes": 123456,
  "duration_sec": 9.8
}
```

Rules:

- Outputs use object storage URIs, not local paths.
- Released outputs are immutable and versioned.
- Candidate outputs remain candidate until QC and release checks pass.

## Asset Ref Object

```json
{
  "asset_id": "voice_abc",
  "asset_type": "voice_profile",
  "role": "narrator",
  "authorization_snapshot": "consent_evt_123",
  "asset_version": "voice_abc:v3"
}
```

Rules:

- Voice and avatar assets require `authorization_snapshot`.
- Music, brand, and template assets require provenance or approval evidence in later compliance checks.
- Adapters must fail hard if required asset governance fields are missing.

## Audit Event Ref

```json
{
  "event_id": "audit_evt_123",
  "event_type": "stage.completed",
  "occurred_at": "2026-05-30T00:00:00Z"
}
```

Rules:

- Stage attempts create `stage.started` and terminal `stage.completed` or `stage.failed`.
- Repair and review actions create explicit events.
- Release creates `release.created`; pointer changes create `release.current_pointer_changed`.

## QC Ref

```json
{
  "qc_report_uri": "s3://video-factory/tenant_123/jobs/job_456/qc/final/attempt-1/qc_report.json",
  "qc_status": "passed",
  "qc_profile": "final_publishable_v0.1"
}
```

Rules:

- Stage manifests may have empty `qc_refs` before QC runs.
- Release manifests require passing final QC ref.
- Missing authorization metadata is a hard QC failure.

## Failure Object

```json
{
  "code": "asset_not_authorized",
  "message": "Voice profile consent snapshot is missing.",
  "retryable": false,
  "repair_action": "manual_review",
  "details": {}
}
```

Common codes:

- `asset_not_authorized`
- `consent_expired`
- `model_runtime_error`
- `output_corrupt`
- `duration_mismatch`
- `face_not_detected`
- `lip_sync_below_threshold`
- `subtitle_safe_area_failed`
- `render_blank`
- `audio_mix_failed`
- `codec_failed`
- `model_license_unverified`
- `manual_review_required`

The canonical failure-code vocabulary lives in `docs/quality/failure-taxonomy.md`; this list is only the manifest contract's common subset.

## Compatibility Requirements

- `TASK-003` DSL scene IDs must map to manifest `segment_id`.
- `TASK-005` job state machine uses manifest `status` and `failure.code`.
- `TASK-006` QC reports attach via `qc_refs`.
- `TASK-007` API exposes manifests through tenant-scoped artifact resources.
- `TASK-009` traceability matrix reconciles manifests across all stages.
