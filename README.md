# Enterprise Talking-Head Video Factory

<!-- repo-init:managed -->

Enterprise-grade automated talking-head video generation platform. An authenticated user enters a short text, article, or opinion, then the system produces a publish-ready vertical short-form video through a controlled production pipeline.

## Repository Purpose

This repository defines and will implement a production-usable video factory for automatic口播视频 generation: script and storyboard planning, authorized voice-profile TTS, digital-human lip sync and head motion, deterministic HTML/animation rendering, subtitles, music, quality inspection, auto repair, fallback, and final MP4 composition.

## Initialization Model

- Mode: `greenfield`
- Posture: `preserve-first` by default
- Primary source: `prompt-only input`
- Source files used: `prompt-only input`
- Current confidence: sufficient to create the collaboration layer and enterprise task set

## Collaboration Contract

- `AGENT.md` defines agent operating rules and update discipline.
- `PROJECT.md` defines the project scope, constraints, assumptions, and enterprise posture.
- `STATUS.md` tracks current state, latest feedback, task impact, blockers, and next step.
- `DECISIONS.md` records durable accepted project decisions.
- `tasks/` contains the coordinating task and first-wave execution slices.
- `.repo-init/init-report.md` records initialization evidence and the post-init correction that replaced the generic scaffold task.

## Task Decomposition

RepoFrame initialized the collaboration layer, then the generic single scaffold task was corrected into an enterprise task set because the product target is explicitly not an MVP/demo.

The active coordinating task is `tasks/TASK-001-coordinate-enterprise-delivery-plan.md`.

The recommended starting child task is `tasks/TASK-002-lock-production-architecture.md`.

## Detailed Rules

- Start with `PROJECT.md`, `STATUS.md`, `DECISIONS.md`, then the active task.
- Do not begin implementation after initialization unless the user explicitly asks for post-init execution.
- Keep the product target enterprise-grade unless the user explicitly changes it.
- Use deterministic scene DSL and validated templates instead of arbitrary generated code.
- Treat voice and avatar cloning as authorized asset workflows.
- Preserve task feedback in `STATUS.md` and the coordinating task before changing downstream work.

## Contract Validation

Run the accepted contract checks before review or acceptance:

```bash
uv run validate-contracts --repo .
uv run pytest
```

See `docs/development/contract-validation.md` for the validator scope and source-of-truth documents.

## Runtime Foundation

TASK-011 adds the first product runtime slice: a FastAPI job intake API with tenant-scoped asset authorization checks, accepted contract vocabulary reuse, and deterministic `created -> validated` job creation.

Create a sample job locally:

```bash
uv run video-factory-api --sample-job
```

Start the local API:

```bash
uv run uvicorn video_factory_runtime.api:create_app --factory --host 127.0.0.1 --port 8000
```

Then create a job from the sample request:

```bash
curl -sS -X POST http://127.0.0.1:8000/v1/jobs \
  -H 'Content-Type: application/json' \
  -H 'x-tenant-id: tenant_123' \
  -H 'x-user-id: user_456' \
  -H 'x-role: creator' \
  --data @examples/jobs/create-job.json
```

See `docs/development/job-intake-runtime.md` for behavior, validation, and scope notes.

## Creative Studio Runtime

TASK-012 adds the first full product slice: a React/Vite creative Studio, seeded local login, SQLite metadata, governed asset upload/consent/activation, job list/detail/start, artifacts, QC evidence, signed local media playback, a Remotion scene renderer, ffmpeg audio muxing, and CosyVoice/MuseTalk adapter boundaries.

Start the backend:

```bash
uv run video-factory-api --host 127.0.0.1 --port 8000
```

Start the Studio:

```bash
cd web
npm install
npm run dev
```

Open `http://127.0.0.1:5173` and log in with:

```text
creator@example.local
factory-demo
```

Uploaded files and runtime metadata are stored under `var/video_factory/`, which is intentionally ignored by git. Without `COSYVOICE_BASE_URL`, starting generation fails explicitly at the TTS stage with QC evidence instead of producing a fake MP4. With a compatible CosyVoice service exposing `/v1/tts`, the local pipeline can continue into Remotion rendering and ffmpeg MP4 composition.
