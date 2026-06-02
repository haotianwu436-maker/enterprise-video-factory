# Repair Policy

<!-- task: TASK-006 -->

## Purpose

Repair policy defines how the system attempts to recover from failures without hiding risk or bypassing governance. It is the main engineering mechanism behind high job success rates.

## Policy Principles

- Repair only when the failure is explicitly repairable.
- Retry the smallest affected unit, usually one segment.
- Preserve failed artifacts and QC reports.
- Emit audit events for repair decisions and outcomes.
- Never auto-repair authorization, tenant, consent, license, or reviewer rejection failures.
- Escalate repeated failures to manual review.

## Repair Decision Object

```json
{
  "repair_decision_version": "0.1",
  "tenant_id": "tenant_123",
  "job_id": "job_456",
  "segment_id": "seg_001",
  "source_failure_code": "lip_sync_below_threshold",
  "source_qc_report_uri": "s3://video-factory/tenant/jobs/job/qc/avatar/seg_001/report.json",
  "action": "retry_with_reduced_motion",
  "attempt_limit_remaining": 1,
  "requires_review": false,
  "audit_event_id": "audit_evt_repair_123"
}
```

## Repair Actions

| Failure Code | Action | Scope |
| --- | --- | --- |
| `scene_dsl_invalid` | repair DSL with bounded prompt | plan |
| `tts_text_too_long` | split scene or reduce pace | segment |
| `audio_clipped` | regenerate with lower gain | segment |
| `audio_silence` | retry TTS | segment |
| `asr_text_mismatch` | retry TTS or alignment | segment |
| `face_not_detected` | retry avatar with safer framing | segment |
| `lip_sync_below_threshold` | retry with reduced motion | segment |
| `model_runtime_error` | retry same stage on healthy worker | segment/job |
| `renderer_runtime_error` | retry renderer with safe template parameters | segment |
| `alignment_failed` | retry alignment or use verified TTS-native timing | segment |
| `render_blank` | retry renderer with fallback template | segment |
| `text_overflow` | reduce overlay density | segment |
| `subtitle_safe_area_failed` | adjust subtitle style/safe area | segment |
| `missing_segment` | rerun missing segment stage | segment |
| `duration_mismatch` | recompute timings or recompose | segment/job |
| `codec_failed` | retry composition with normalized settings | job |
| `audio_mix_failed` | remix with normalized loudness and ducking | job |
| `output_corrupt` | regenerate the producing stage artifact | segment/job |

## Non-Repairable Failures

Do not auto-repair:

- `asset_not_authorized`
- `consent_expired`
- `tenant_scope_violation`
- `scene_dsl_prohibited_code`
- `model_license_unverified`
- reviewer rejection
- missing final traceability bundle

Handling:

- Block job or release.
- Open review if a human decision is valid.
- Record launch blocker when policy/compliance is unresolved.

## Fallback Modes

Fallbacks are allowed only when explicit:

| Primary | Fallback | Conditions |
| --- | --- | --- |
| high-motion avatar | reduced-motion avatar | lip/face instability |
| avatar video | static avatar with animated scene | tenant policy allows quality downgrade |
| word subtitles | sentence subtitles | alignment unavailable |
| rich template | default simple template | text overflow/render failure |
| primary TTS model | approved fallback voice/model | tenant policy and consent allow |

Rules:

- Fallback must be recorded in manifest and QC report.
- Fallback must be visible to operator console.
- Fallback cannot replace unauthorized identity assets.

## Attempt Limits

Draft defaults:

- automatic retries per transient stage: 2
- repair loops per segment: 2
- fallback use per segment: 1
- manual review after repeated failure

Open question:

- Whether high-value tenants can configure stricter or looser thresholds.

## Manual Review Escalation

Escalate when:

- repair attempt limit is exhausted
- fallback would materially change output quality
- identity drift is detected
- consent is missing or disputed
- operator requests override
- policy-sensitive content appears

Review outcomes:

- approve retry
- approve fallback
- reject segment
- reject job
- require asset reauthorization
- mark launch blocker

## Audit Requirements

Every repair attempt emits:

- `repair.requested`
- `stage.started`
- terminal `stage.completed` or `stage.failed`
- `repair.completed` when repair produces a usable artifact

Manual review emits:

- `review.opened`
- terminal reviewer decision event

## Product Promise Boundary

High success rates are measured after:

- automatic retry
- repair
- approved fallback
- manual review where policy allows

They must not count unauthorized, unsafe, or untraceable outputs as successful.
