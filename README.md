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
