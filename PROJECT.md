# PROJECT.md

<!-- repo-init:managed -->

## Project Identity

- Name: `Enterprise Talking-Head Video Factory`
- Type: `production platform`
- Stage: `enterprise architecture planning`

## Goal

Build an enterprise-usable automated口播视频 generation platform. A user enters text, an article, or a viewpoint; the system plans a script and storyboard, generates authorized cloned voice audio, renders a digital human with lip sync and natural head motion, produces deterministic HTML/animation scenes, adds subtitles and music, runs quality gates and auto repair, and exports a publish-ready vertical MP4.

## Non-MVP Position

- This is not a demo, toy, or MVP-only scaffold.
- The first implementation work should lock production architecture before model experiments or UI scaffolding.
- Reliability, observability, asset authorization, and fallback behavior are product requirements, not later polish.

## Core Principles

- Segment-based generation: split each video into independently retryable scenes/segments.
- Deterministic planning: LLMs emit validated scene DSL, not arbitrary generated code.
- Local/open-source-first models: prefer self-hosted model adapters with minimal third-party API dependency.
- Quality gates by default: every stage emits evidence, metrics, and repair/fallback decisions.
- Authorized identity assets only: voice and avatar profiles require consent, audit trails, and tenant controls.
- Enterprise operability: resumable jobs, GPU worker scheduling, object storage, observability, RBAC, and manual review flows.

## System Capabilities

- Text/opinion intake and script planning
- Storyboard and scene DSL generation
- Authorized zero-shot or few-shot voice-profile TTS
- Digital-human rendering with lip sync and natural head motion
- HTML/Remotion-style dynamic scene rendering
- Subtitle generation and alignment
- Music, loudness, and final composition
- Quality inspection and auto repair
- Fallback paths for TTS, avatar generation, subtitle alignment, rendering, and composition
- Multi-tenant asset management, consent, audit logs, and operator review

## Preferred Technical Direction

- API layer: FastAPI or NestJS, selected after architecture lock
- Orchestration: Temporal or an equivalent durable workflow engine
- Storage: Postgres plus S3-compatible object storage
- Queue/cache: Redis or orchestration-native queues where appropriate
- Rendering: Remotion/HTML templates plus ffmpeg composition
- Model services: containerized adapters for TTS, avatar, alignment, render, and composition engines
- Infrastructure: GPU worker pool with explicit scheduling, health checks, and capacity planning
- Observability: OpenTelemetry, structured logs, metrics, traces, and per-job audit artifacts

## Initial Model Candidates

- Voice/TTS: CosyVoice, GPT-SoVITS, F5-TTS
- Avatar/lip sync: MuseTalk, HunyuanVideo-Avatar, fallback static-avatar modes
- Alignment/QC: WhisperX or equivalent ASR alignment, ffprobe/ffmpeg, face and lip-sync scoring tools
- Rendering/composition: Remotion, HTML/CSS animation templates, ffmpeg

## Assumptions

- The repository starts from an empty greenfield state.
- The first accepted deliverable should be architecture and contracts, not working demo code.
- GPU availability, latency targets, tenant count, and deployment environment still need confirmation.
- Legal/compliance details require product decisions and may need external review before launch.
