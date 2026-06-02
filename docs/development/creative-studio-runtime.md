# Creative Studio Runtime

<!-- task: TASK-012 -->

## Purpose

This document describes the local product slice that connects the React creative Studio to the FastAPI runtime. It is intentionally runnable on a developer machine while keeping model runtimes, GPU workers, and production object storage outside this process.

## Local Accounts

The SQLite runtime seeds one local creator:

```text
email: creator@example.local
password: factory-demo
tenant_id: tenant_123
user_id: user_456
role: creator
```

The API issues a bearer token for local Studio sessions. The token is HMAC signed with a local development secret and must be replaced by production identity infrastructure before deployment.

TASK-012 product runtime requires bearer authentication by default. Legacy tenant/user/role headers are accepted only when explicitly creating the app in legacy compatibility mode for TASK-011 tests.

## Runtime Storage

Metadata is stored in `var/video_factory/runtime.sqlite3`.

Uploaded asset files and generated job files are stored under:

```text
var/video_factory/{tenant_id}/assets/
var/video_factory/{tenant_id}/jobs/{job_id}/
```

The `var/` directory is ignored by git because it contains local runtime state, uploaded identity assets, and generated media.

## Studio Flow

1. Log in through `POST /v1/auth/login`.
2. Load `GET /v1/auth/me`, `GET /v1/assets`, and `GET /v1/jobs`.
3. Upload or register governed assets with `POST /v1/assets`.
4. Attach consent and activate identity assets with `POST /v1/assets/{asset_id}/consent` and `POST /v1/assets/{asset_id}/activate`.
5. Create a 60s, 9:16 job with `POST /v1/jobs`.
6. Start generation with `POST /v1/jobs/{job_id}/start`.
7. Inspect `GET /v1/jobs/{job_id}/artifacts` and `GET /v1/jobs/{job_id}/qc`.
8. Fetch playable media through `GET /v1/artifacts/{artifact_id}/signed-url` when a composition artifact exists.

Consent events require a `scope` object and an `evidence_uri`; the runtime records the consent event separately before moving identity assets toward activation.

## Generation Semantics

The local pipeline always creates a deterministic six-scene storyboard artifact first. TTS is delegated to `CosyVoiceAdapter`, which calls `COSYVOICE_BASE_URL/v1/tts`.

If `COSYVOICE_BASE_URL` is not configured, the job transitions to:

```text
state: failed
active_stage: tts
failure_code: model_runtime_error
```

This is deliberate. The runtime must not claim a successful MP4 when the required model runtime is absent.

When CosyVoice returns either `audio_base64` or a readable `audio_uri`, the local pipeline renders a 60s, 1080x1920 Remotion composition and then uses ffmpeg to mux the rendered scene video with TTS audio into `final.mp4`. MuseTalk is represented by a remote adapter boundary and is not run locally on this Mac.

Renderer failures are captured as:

```text
state: failed
active_stage: scene_render
failure_code: renderer_runtime_error
```

## Validation

Run:

```bash
uv run pytest
uv run validate-contracts --repo .
cd web && npm test && npm run build && npm audit --audit-level=critical
```
