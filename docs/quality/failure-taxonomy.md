# Failure Taxonomy

<!-- task: TASK-006 -->

## Purpose

This taxonomy gives every pipeline stage a shared failure language. It is consumed by adapter contracts, orchestration, QC, repair policy, API, console, and final compliance.

## Failure Severity

| Severity | Meaning | Default Handling |
| --- | --- | --- |
| `info` | Non-blocking observation. | Record in QC report. |
| `warning` | Output usable but degraded. | Record and possibly repair. |
| `repairable` | Output should not release but can be repaired. | Trigger repair policy. |
| `review_required` | Human decision required. | Open review item. |
| `terminal` | Cannot proceed automatically. | Block stage/job/release. |

## Failure Categories

| Category | Examples |
| --- | --- |
| Authorization | missing consent, revoked asset, wrong tenant, expired snapshot |
| Policy | manual review required, unsafe output, disclosure missing |
| Input | invalid DSL, missing asset ref, text too long |
| Runtime | model timeout, worker crash, GPU OOM |
| Media Quality | silence, clipping, black frames, bad resolution |
| Semantic Quality | ASR mismatch, missing required words |
| Identity Quality | face missing, lip sync poor, avatar drift |
| Render Quality | blank render, text overflow, subtitle unsafe area |
| Composition | missing segment, duration mismatch, codec failure |
| Traceability | missing manifest, missing audit event, hash mismatch |

## Canonical Failure Codes

| Code | Severity | Stage |
| --- | --- | --- |
| `asset_not_authorized` | terminal | validation, TTS, avatar, release |
| `consent_expired` | terminal | validation, release |
| `tenant_scope_violation` | terminal | any |
| `scene_dsl_invalid` | repairable | planning |
| `scene_dsl_prohibited_code` | terminal | planning |
| `tts_text_too_long` | repairable | TTS |
| `voice_profile_missing` | terminal | TTS |
| `model_runtime_error` | repairable | TTS/avatar |
| `renderer_runtime_error` | repairable | render |
| `audio_unreadable` | repairable | alignment |
| `language_unsupported` | review_required | alignment |
| `audio_clipped` | repairable | audio QC |
| `audio_silence` | repairable | audio QC |
| `asr_text_mismatch` | repairable | alignment/QC |
| `alignment_failed` | repairable | alignment |
| `avatar_profile_missing` | terminal | avatar |
| `face_not_detected` | repairable | avatar/QC |
| `lip_sync_below_threshold` | repairable | avatar/QC |
| `avatar_identity_drift` | review_required | avatar/QC |
| `template_not_approved` | terminal | render |
| `render_blank` | repairable | render/QC |
| `text_overflow` | repairable | render/QC |
| `subtitle_safe_area_failed` | repairable | render/QC |
| `missing_segment` | repairable | composition |
| `duration_mismatch` | repairable | composition/QC |
| `codec_failed` | repairable | composition |
| `audio_mix_failed` | repairable | audio_mix/composition |
| `output_corrupt` | repairable | avatar/composition/QC |
| `traceability_incomplete` | terminal | final QC/release |
| `manual_review_required` | review_required | any |
| `model_license_unverified` | terminal | adapter readiness |

## Failure Object

```json
{
  "code": "lip_sync_below_threshold",
  "severity": "repairable",
  "stage": "avatar",
  "message": "Lip-sync score below release threshold.",
  "retryable": true,
  "repair_action": "retry_with_reduced_motion",
  "evidence_refs": [
    "s3://video-factory/tenant/jobs/job/qc/avatar/seg_001/report.json"
  ],
  "audit_event_ids": ["audit_evt_123"]
}
```

## Terminal Failure Rules

These never auto-repair:

- missing, expired, or revoked consent
- tenant scope violation
- prohibited executable code in DSL
- unverified production model license
- missing traceability bundle at release
- reviewer rejection

## Review Required Rules

These require human review:

- avatar identity drift
- disputed consent
- repeated repair failure
- policy-sensitive prompt or output
- manual override of QC block
- release after significant repair

## Downstream Use

- `repair-policy.md` maps failure codes to actions.
- `qc-matrix.md` defines checks that can emit these codes.
- `api-console.md` exposes failure codes to operators without leaking sensitive internals.
- `risk-register.md` tracks residual risks for unresolved failure classes.
