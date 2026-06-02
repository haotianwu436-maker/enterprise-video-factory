# Model Service Adapter Contracts

<!-- task: TASK-004 -->

## Purpose

Model service adapters isolate product workflows from model-specific runtimes. The product talks to stable adapter contracts; adapters hide whether a stage uses CosyVoice, GPT-SoVITS, F5-TTS, MuseTalk, HunyuanVideo-Avatar, Remotion, ffmpeg, or a later replacement.

This document defines contract expectations only. It does not select model weights, install runtimes, benchmark GPUs, or implement services.

## Shared Adapter Rules

- Every request includes `tenant_id`, `job_id`, `segment_id` when segment-scoped, and `idempotency_key`.
- Every request references object storage URIs or prior manifests, not local paths.
- Every identity asset includes an authorization snapshot.
- Every response produces an artifact manifest or a structured failure.
- Every adapter emits audit event references.
- Every adapter declares model/service version and license verification status.
- Fallback behavior is explicit and does not silently downgrade quality.

## Shared Request Envelope

```json
{
  "request_version": "0.1",
  "tenant_id": "tenant_123",
  "job_id": "job_456",
  "segment_id": "seg_001",
  "stage": "tts",
  "attempt": 1,
  "idempotency_key": "job_456:seg_001:tts:1",
  "inputs": [],
  "asset_refs": [],
  "stage_config": {},
  "trace": {
    "workflow_id": "wf_123",
    "run_id": "run_456"
  }
}
```

## Shared Response Envelope

```json
{
  "response_version": "0.1",
  "status": "succeeded",
  "manifest_uri": "s3://video-factory/tenant_123/jobs/job_456/segments/seg_001/tts/attempt-1/manifest.json",
  "manifest": {},
  "failure": null,
  "audit_events": []
}
```

Status values:

- `succeeded`
- `failed`
- `blocked`
- `retry_recommended`
- `manual_review_required`

## TTS Adapter

Purpose:

- Convert scene text and voice profile into audio.

Candidate engines:

- CosyVoice
- GPT-SoVITS
- F5-TTS

Inputs:

- Scene script text.
- Voice profile asset ref with authorization snapshot.
- Delivery hints from Scene DSL.
- Target loudness and optional target duration.

Outputs:

- WAV audio.
- Optional phoneme/word timing if supported.
- TTS manifest.

Failure codes:

- `asset_not_authorized`
- `consent_expired`
- `tts_text_too_long`
- `voice_profile_missing`
- `model_runtime_error`
- `audio_clipped`
- `duration_mismatch`

Fallback policy:

1. Retry with shorter text segment when text is too long.
2. Retry with safer pace/delivery hints.
3. Switch to a verified fallback voice only if tenant policy permits.
4. Otherwise escalate to manual review.

## Avatar Adapter

Purpose:

- Convert audio plus authorized avatar profile into talking-head video.

Candidate engines:

- MuseTalk
- HunyuanVideo-Avatar
- fallback static-avatar render mode

Inputs:

- TTS audio manifest.
- Avatar profile asset ref with authorization snapshot.
- Avatar behavior hints from Scene DSL.

Outputs:

- Avatar video segment.
- Optional alpha/foreground layer if supported.
- Avatar manifest.

Failure codes:

- `asset_not_authorized`
- `avatar_profile_missing`
- `face_not_detected`
- `lip_sync_below_threshold`
- `model_runtime_error`
- `output_corrupt`

Fallback policy:

1. Retry same segment once when runtime fails.
2. Reduce motion intensity when lip sync or face stability fails.
3. Switch to static-avatar fallback only as an explicit quality downgrade.
4. Escalate unauthorized or disputed assets to review.

## Alignment Adapter

Purpose:

- Produce word or sentence timings for subtitles and QC backchecks.

Candidate engines:

- WhisperX or equivalent ASR/alignment stack.
- TTS-native timing if reliable and verified.

Inputs:

- Audio manifest.
- Original script text.
- Language code.

Outputs:

- Word/sentence alignment JSON.
- Subtitle source timing.
- Alignment manifest.

Failure codes:

- `alignment_failed`
- `asr_text_mismatch`
- `audio_unreadable`
- `language_unsupported`

Fallback policy:

1. Use TTS-native timing when ASR alignment fails and TTS timing exists.
2. Fall back to sentence-level subtitles when word-level alignment fails.
3. Route large text mismatch to QC/manual review.

## Renderer Adapter

Purpose:

- Render deterministic HTML/Remotion-style scene layers from validated Scene DSL and templates.

Inputs:

- Scene DSL segment.
- Template asset ref.
- Brand kit asset ref.
- Avatar or placeholder manifest.

Outputs:

- Scene video or overlay artifact.
- Render manifest.

Failure codes:

- `template_not_approved`
- `render_blank`
- `subtitle_safe_area_failed`
- `text_overflow`
- `renderer_runtime_error`

Fallback policy:

1. Retry with default template parameters.
2. Reduce text density or switch to simpler layout.
3. Use approved fallback template.
4. Block if template approval or tenant authorization is missing.

## Composer Adapter

Purpose:

- Compose avatar, rendered scene layers, subtitles, music, and transitions into candidate MP4.

Inputs:

- Ordered segment manifests.
- Subtitle manifests.
- Music asset ref and mix settings.
- Render manifests.

Outputs:

- Candidate final MP4.
- Composition manifest.

Failure codes:

- `missing_segment`
- `duration_mismatch`
- `codec_failed`
- `audio_mix_failed`
- `output_corrupt`

Fallback policy:

1. Retry composition with deterministic inputs.
2. Normalize frame rate or audio sample rate.
3. Block if required segment artifacts are missing.

## Adapter Health Checks

Minimum health response:

```json
{
  "service": "tts-adapter",
  "service_version": "0.1.0",
  "ready": true,
  "models": [
    {
      "name": "CosyVoice",
      "version": "unverified",
      "license_status": "unverified",
      "capabilities": ["zh", "zero_shot_voice_clone"],
      "device_requirements": ["gpu_preferred"]
    }
  ]
}
```

Rules:

- Health checks report capability and license verification status.
- Product workflows must not assume a model is available until health checks and deployment configuration confirm it.

## License And Capability Verification

Before any model becomes production default:

- Record license name and source.
- Record allowed commercial usage.
- Record redistribution constraints.
- Record GPU memory and latency benchmark.
- Record supported languages.
- Record failure modes and fallback path.

Open issue:

- This repository has not yet verified the licenses or runtime characteristics of candidate models.

## Adapter To Manifest Mapping

Each adapter response must produce an artifact manifest that includes:

- producer service/version/model metadata
- input artifact hashes
- output artifact URI and hash
- asset refs and authorization snapshots
- audit event refs
- stage status/failure code
- trace context

The canonical envelope is defined in `docs/contracts/artifact-manifest.md`.
