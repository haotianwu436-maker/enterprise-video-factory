# Quality Control Matrix

<!-- task: TASK-006 -->

## Purpose

This matrix defines stage-level quality gates for the automated talking-head video pipeline. Quality gates produce evidence, not just pass/fail booleans.

## QC Report Envelope

```json
{
  "qc_report_version": "0.1",
  "tenant_id": "tenant_123",
  "job_id": "job_456",
  "segment_id": "seg_001",
  "stage": "tts",
  "status": "passed",
  "checks": [],
  "failures": [],
  "repair_recommendation": null,
  "audit_event_ids": [],
  "created_at": "2026-05-30T00:00:00Z"
}
```

Status values:

- `passed`
- `warning`
- `failed_repairable`
- `review_required`
- `failed_terminal`

## Stage Matrix

| Stage | Checks | Failure Codes | Evidence |
| --- | --- | --- | --- |
| Intake | tenant scope, asset active, consent snapshot exists | `asset_not_authorized`, `tenant_scope_violation` | validation report, audit event |
| Planning | schema valid, no prohibited code, duration bounds | `scene_dsl_invalid`, `scene_dsl_prohibited_code` | validation errors, repaired payload hash |
| TTS | non-silent, no clipping, duration bounds, ASR backcheck | `audio_silence`, `audio_clipped`, `duration_mismatch`, `asr_text_mismatch` | audio probe, ASR transcript |
| Avatar | face detected, lip sync score, output not corrupt | `face_not_detected`, `lip_sync_below_threshold`, `output_corrupt` | sampled frames, lip score |
| Render | nonblank, safe area, text fit, correct fps/resolution | `render_blank`, `text_overflow`, `subtitle_safe_area_failed` | screenshots/probe |
| Alignment | timing exists, text coverage, subtitle density | `alignment_failed`, `asr_text_mismatch` | alignment JSON |
| Audio Mix | voice/music loudness, ducking, clipping, duration | `audio_mix_failed`, `audio_clipped`, `duration_mismatch` | loudness report, mix manifest |
| Composition | all segments present, duration/fps/codec, complete audio mix | `missing_segment`, `duration_mismatch`, `codec_failed`, `output_corrupt` | ffprobe, composition manifest |
| Repair | repair decision references source failure and attempt budget | `manual_review_required`, `traceability_incomplete` | repair decision, repair manifest |
| Review | reviewer decision recorded with evidence and reason | `manual_review_required`, `asset_not_authorized`, `consent_expired` | review item, review audit event |
| Final QC | traceability complete, no blockers, release format | `traceability_incomplete`, `manual_review_required` | final QC report, traceability bundle |

## Release Gates

Final release requires:

- all required stage manifests exist
- final MP4 probe passes
- no unresolved review item
- authorization snapshots exist for identity assets
- immutable release URI and traceability bundle exist
- `release.created` audit event exists
- `release/current.json` pointer change is audited

## Draft Thresholds

These values are placeholders until benchmark/product owners confirm them:

| Check | Draft Threshold |
| --- | --- |
| Target loudness | -16 LUFS voice, -20 LUFS music bed |
| Subtitle max lines | 2 |
| Subtitle safe area | bottom 10-30 percent depending template |
| Segment duration | 2-20 seconds |
| Final duration tolerance | +/- 1.5 seconds |
| Repair attempts per segment | 2 |
| Automatic retries per transient stage | 2 |

## Governance Checks

Hard failures:

- missing authorization snapshot
- revoked identity asset
- cross-tenant artifact reference
- unsigned or expired artifact URL for console access
- missing audit event for review or release action

Review-required:

- identity drift
- disputed consent
- repeated repair failure
- policy-sensitive output

## QC Evidence Requirements

Every QC report should include:

- checked artifact URI and hash
- manifest URI
- check names and results
- failure codes
- repair recommendation
- audit event IDs
- trace context

## Downstream Requirements

- `TASK-005` must route repairable failures to repair workflow.
- `TASK-007` must show QC status and evidence in console.
- `TASK-009` must verify final traceability from QC reports to release.
