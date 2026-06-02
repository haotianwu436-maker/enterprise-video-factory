# Job State Machine

<!-- task: TASK-005 -->

## Purpose

This contract defines job, segment, stage attempt, repair, review, and release states for the video factory. It is intentionally orchestration-agnostic: Temporal or another durable engine can implement it later.

## Job States

```text
created
validated
planning
planned
segmenting
generating_audio
generating_avatar
rendering_scenes
aligning_subtitles
mixing_audio
composing
quality_checking
repairing
review_required
publish_ready
failed
cancelled
```

## Job State Rules

- `created` jobs have raw request data but have not passed tenant/asset validation.
- `validated` jobs have authorized asset snapshots and a valid output profile.
- `planned` jobs have validated Scene DSL.
- Segment stages may run in parallel after `segmenting`.
- `review_required` blocks release until a reviewer action is recorded.
- `publish_ready` requires final QC pass, release manifest, and no unresolved review blockers.
- `failed` is terminal unless an operator explicitly creates a new job or permitted retry workflow.
- `cancelled` is terminal and should cancel queued or running stage attempts where possible.

## Segment States

```text
pending
ready
audio_generating
audio_ready
avatar_generating
avatar_ready
rendering
render_ready
subtitle_aligning
subtitle_ready
composed
qc_passed
qc_failed
repairing
review_required
failed
skipped
```

Rules:

- Segment failure does not automatically fail the job.
- A segment can be repaired without rerunning unrelated passing segments.
- `skipped` requires a planner or reviewer reason.

## Stage Attempt States

```text
queued
running
succeeded
failed_retryable
failed_terminal
blocked_policy
cancelled
superseded
```

Rules:

- Every stage attempt has an idempotency key.
- Retry attempts create new manifests and audit events.
- Superseded attempts remain traceable and are not deleted by default.
- Policy blocks are not retried automatically.

## Transition Table

| From | To | Trigger | Required Evidence |
| --- | --- | --- | --- |
| `created` | `validated` | request validation passes | asset authorization snapshots |
| `validated` | `planning` | orchestration starts planner | `stage.started` event |
| `planning` | `planned` | DSL validates | storyboard manifest |
| `planned` | `segmenting` | segment records created | segment input manifests |
| `segmenting` | `generating_audio` | audio stages queued | stage attempt records |
| `generating_audio` | `generating_avatar` | required audio segments ready | TTS manifests, audio QC |
| `generating_avatar` | `rendering_scenes` | avatar segments ready | avatar manifests, lip/face QC |
| `rendering_scenes` | `aligning_subtitles` | rendered scene artifacts ready | render manifests |
| `aligning_subtitles` | `mixing_audio` | subtitle timing ready | alignment manifests |
| `mixing_audio` | `composing` | audio mix ready | audio mix manifest |
| `composing` | `quality_checking` | candidate MP4 ready | composition manifest |
| `quality_checking` | `repairing` | QC repairable failure | QC report, repair decision |
| `quality_checking` | `review_required` | QC/policy block | QC report, review event |
| `quality_checking` | `publish_ready` | final QC pass | release manifest, traceability bundle |
| `repairing` | `planning`, `segmenting`, `generating_audio`, `generating_avatar`, `rendering_scenes`, `aligning_subtitles`, `mixing_audio`, or `composing` | approved retry or repair attempt starts | repair decision, new stage attempt record |
| `repairing` | `quality_checking` | repaired artifact candidate is ready | repair manifest, repaired artifact manifest |
| `repairing` | `review_required` | repair limit exhausted or policy requires review | repair report, review event |
| `review_required` | `repairing` | reviewer approves repair/retry | review decision, repair decision |
| `review_required` | `publish_ready` | reviewer approves release and final QC already passed | review decision, release manifest |
| `review_required` | `failed` | reviewer rejects output or asset use | review decision, failure manifest |
| any non-terminal | `failed` | terminal failure | failure manifest |
| any non-terminal | `cancelled` | user/operator cancellation | audit event |

Repair retry transitions must choose one concrete job state from the enum above. The durable orchestrator should record the original failed stage in the repair decision and the new stage attempt record rather than using a non-enum pseudo-state.

## Stage Mapping

The canonical artifact stage enum lives in `docs/contracts/artifact-manifest.md`. Job states are orchestration-facing labels that must resolve to a canonical artifact stage before a worker writes a manifest.

| Job State | Canonical Manifest Stage |
| --- | --- |
| `created`, `validated` | `source_intake` |
| `planning`, `planned` | `planning` |
| `segmenting` | `segment_input` |
| `generating_audio` | `tts` |
| `generating_avatar` | `avatar` |
| `rendering_scenes` | `scene_render` |
| `aligning_subtitles` | `alignment` |
| `mixing_audio` | `audio_mix` |
| `composing` | `composition` |
| `quality_checking` | `qc` |
| `repairing` | `repair` |
| `review_required` | `review` |
| `publish_ready` | `release` |

## Idempotency Keys

Format:

```text
{tenant_id}:{job_id}:{segment_id}:{stage}:{attempt}
```

Examples:

```text
tenant_123:job_456:seg_001:tts:1
tenant_123:job_456:seg_001:avatar:2
tenant_123:job_456:job:release:1
```

Rules:

- A worker receiving the same idempotency key must return the existing completed manifest or continue the same attempt.
- A retry increments attempt number.
- A repair creates a repair decision before the next attempt.

## Review State

Review item states:

```text
opened
assigned
approved
approved_with_restrictions
rejected
escalated
closed
```

Review item required fields:

- `review_id`
- `tenant_id`
- `job_id`
- optional `segment_id`
- `reason_code`
- `opened_by`
- `opened_at`
- `evidence_refs`
- `decision`
- `decided_by`
- `decided_at`

Review reason codes:

- `missing_consent`
- `revoked_asset`
- `unsafe_output`
- `repeated_repair_failure`
- `policy_sensitive_content`
- `manual_operator_request`

## Release State

Release states:

```text
candidate
approved
current
superseded
withdrawn
```

Rules:

- Release artifacts are immutable and versioned by `release_id`.
- `release/current.json` points to the current immutable release.
- Pointer changes require `release.current_pointer_changed`.
- Withdrawn releases remain auditable.

## Terminal Failure Rules

Terminal failure when:

- required identity asset is revoked or missing consent
- model license/capability is not verified for production lane
- scene DSL contains prohibited executable code
- stage repeatedly fails beyond policy threshold
- manual review rejects output
- final QC fails with non-repairable code

## Downstream Consumers

- `TASK-006` uses state/failure codes for QC and repair policy.
- `TASK-007` exposes job, segment, review, retry, and release states through API.
- `TASK-009` validates traceability across state transitions and audit events.
