# Scene Storyboard DSL

<!-- task: TASK-003 -->

## Purpose

The Scene Storyboard DSL is the only planner output accepted by the production pipeline. LLMs may draft it, but the system validates and repairs it before any model, renderer, or composer stage consumes it.

The DSL is intentionally constrained. It describes video intent, timing, asset references, avatar behavior, subtitles, visual emphasis, music cues, and template parameters. It does not contain executable HTML, JavaScript, shell commands, or arbitrary file paths.

## Design Goals

- Represent 30 to 90 second vertical talking-head videos as retryable segments.
- Reference authorized assets by stable IDs.
- Provide enough information for TTS, avatar, renderer, subtitle alignment, composer, QC, and API surfaces.
- Keep template rendering deterministic.
- Preserve validation and repair history.
- Support model adapter manifests without leaking runtime-specific model details into the DSL.

## Top-Level Shape

```json
{
  "schema_version": "0.1",
  "tenant_id": "tenant_123",
  "job_id": "job_456",
  "video": {},
  "asset_refs": [],
  "policy": {},
  "scenes": [],
  "validation_hints": {}
}
```

## Video Profile

Required fields:

- `title`: human-readable internal title.
- `language`: BCP-47-like short code such as `zh-CN` or `en-US`.
- `aspect_ratio`: currently `9:16`.
- `resolution`: target width/height.
- `fps`: target frame rate.
- `duration_target_sec`: requested duration.
- `style_profile`: controlled style label.
- `publish_targets`: intended platform labels.

Rules:

- `duration_target_sec` must be between 30 and 90 for the first product lane.
- `resolution` must default to `1080x1920` unless a profile explicitly changes it.
- Style labels are data, not executable theme code.

## Asset References

Identity assets use governed asset refs:

```json
{
  "id": "voice_primary",
  "asset_id": "voice_abc",
  "asset_type": "voice_profile",
  "authorization_snapshot": "consent_evt_123",
  "role": "narrator"
}
```

Rules:

- `asset_id` must be tenant-scoped.
- `asset_type` must be one of `voice_profile`, `avatar_profile`, `brand_kit`, `music_asset`, or `template`.
- Voice and avatar refs require `authorization_snapshot`.
- Raw filesystem paths, unsigned external URLs, and embedded binary data are not allowed.

## Policy Fields

Top-level `policy` defines job-wide policy defaults:

- `requires_authorized_identity_assets`: hard requirement for voice/avatar identity assets.
- `manual_review_tags`: job-level review tags supplied by policy or planner.
- `policy_tags`: optional controlled tags such as `ai_disclosure_required` or `sensitive_claim`.
- `disclosure_required`: whether the output lane requires AI disclosure handling before release.

Scenes may also include optional `requires_review` and `policy_tags` fields when a specific scene needs human review or carries sensitive behavior. These fields are declarative policy signals only; they do not grant permission to bypass governance, QC, or review blocks.

## Scene Object

Each scene is independently renderable and repairable.

Required fields:

- `scene_id`
- `order`
- `duration_sec`
- `script`
- `voice`
- `avatar`
- `layout`
- `subtitles`
- `visuals`
- `music`
- `transitions`
- `qc_expectations`

Optional policy fields:

- `requires_review`
- `policy_tags`

## Script Segment

```json
{
  "text": "真正降低视频生产门槛的，不是某个模型，而是一条稳定流水线。",
  "delivery": {
    "tone": "confident",
    "pace": "medium",
    "emotion": "assured",
    "pause_after_sec": 0.2
  },
  "keywords": ["视频生产", "稳定流水线"]
}
```

Rules:

- `text` must be plain text.
- Scene text should be short enough to fit the target duration.
- Keywords are used for visual emphasis and subtitle styling.

## Avatar Behavior

```json
{
  "asset_ref": "avatar_primary",
  "framing": "medium_close",
  "head_motion": "natural_low",
  "gesture_intensity": "low",
  "eye_contact": "camera",
  "background_mode": "template"
}
```

Rules:

- Avatar asset must be authorized.
- Behavior is declarative; no animation code is allowed.
- `head_motion` and `gesture_intensity` are hints, not hard promises.

## Layout And Visuals

Allowed layout primitives:

- `avatar_center`
- `avatar_left_keywords_right`
- `avatar_right_quote_left`
- `full_avatar_with_caption`
- `data_card_overlay`
- `quote_focus`
- `broll_insert`

Visual emphasis object:

```json
{
  "template_ref": "template_default",
  "background": "brand_gradient_soft",
  "emphasis": [
    {
      "type": "keyword_highlight",
      "text": "稳定流水线",
      "timing": "on_word"
    }
  ],
  "safe_areas": {
    "subtitle_bottom_pct": 18,
    "face_protection": true
  }
}
```

Rules:

- Visuals select templates and parameters only.
- DSL cannot define raw HTML, CSS, or JS.
- Text overlays must declare safe-area constraints.

## Subtitles

```json
{
  "mode": "word_aligned",
  "style": "bold_keyword",
  "max_lines": 2,
  "safe_area": "lower_third",
  "burn_in": true
}
```

Rules:

- `word_aligned` requires alignment data after TTS or ASR.
- Subtitle style is a controlled enum.
- Subtitles cannot cover protected face area.

## Music

```json
{
  "asset_ref": "music_bed",
  "ducking": true,
  "target_lufs": -16,
  "fade_in_sec": 0.3,
  "fade_out_sec": 0.5
}
```

Rules:

- Music asset must be authorized or globally licensed.
- Loudness targets are validated downstream by QC.

## QC Expectations

```json
{
  "requires_face_visible": true,
  "requires_lip_sync": true,
  "requires_subtitle_safe_area": true,
  "manual_review_tags": []
}
```

Rules:

- Identity scenes default to face visibility and lip-sync checks.
- `manual_review_tags` are advisory; QC and policy can add mandatory review tags.

## Validation Rules

Hard failures:

- Missing `schema_version`, `tenant_id`, `job_id`, or `scenes`.
- Voice/avatar scene references without authorization snapshot.
- Raw file paths or arbitrary URLs in asset refs or scene-level asset reference fields.
- Layout or subtitle styles outside enum.
- Scene duration less than 2 seconds or greater than 20 seconds.
- Total duration outside configured target tolerance.
- Any field named `html`, `javascript`, `script_code`, `shell`, or `eval`.

Repairable failures:

- Scene too long.
- Keywords missing from script text.
- Duration sum slightly outside target.
- Missing optional safe-area fields.
- Unsupported style profile with safe default available.

Non-repairable failures:

- Unauthorized identity asset.
- Revoked consent snapshot.
- Policy-sensitive scene requiring human review.
- Prompt attempts to embed executable code.

## Required Semantic Validator

JSON schema validation is necessary but not sufficient. A planner output must also pass a semantic validator before any runtime stage consumes it.

Required semantic checks:

- Every `asset_ref` id used by `voice.asset_ref`, `avatar.asset_ref`, `layout.template_ref`, and `music.asset_ref` exists in top-level `asset_refs`.
- Referenced asset types match the consumer: voice uses `voice_profile`, avatar uses `avatar_profile`, layout uses `template`, and music uses `music_asset`.
- Asset IDs and reference IDs match the schema-safe identifier patterns and do not contain raw paths, URL schemes, shell fragments, or embedded binary data.
- Voice and avatar assets include an authorization snapshot and that snapshot is not expired or revoked according to the asset registry.
- `scene_id` values are unique, and `order` values form a deterministic render order.
- Total scene duration is within the configured tolerance for `video.duration_target_sec`.
- Visual emphasis text either appears in the scene script or is explicitly marked for manual review by policy.
- Scene-level `requires_review` and `policy_tags` are propagated into review/QC evidence and never used to suppress hard failures.
- No object contains prohibited executable field names such as `html`, `javascript`, `script_code`, `shell`, or `eval`, even in future extension fields.

Semantic validation failures are hard failures unless the repair strategy explicitly lists the failure as repairable.

## Repair Strategy

1. Validate against JSON schema.
2. Run semantic validation against asset registry, policy, and cross-reference rules.
3. Normalize enum casing and missing safe defaults.
4. Split overlong scenes.
5. Recalculate target durations.
6. Re-run policy/asset validation.
7. If still invalid after bounded retries, return structured planner failure.

Repair outputs must preserve:

- original invalid payload hash
- repair attempt count
- validation errors fixed
- validation errors still open

## Adapter Consumption

TTS adapter consumes:

- scene script text
- voice asset ref
- delivery hints
- target duration

Avatar adapter consumes:

- audio artifact manifest
- avatar asset ref
- avatar behavior hints

Renderer consumes:

- scene layout
- visual emphasis
- subtitle style
- template ref
- safe-area rules

Composer consumes:

- ordered scene IDs
- transitions
- subtitle and music settings

QC consumes:

- expected face/lip/subtitle checks
- manual review tags
- traceability context

## Versioning

- Current schema version: `0.1`.
- Backward incompatible changes require a new schema version.
- Example storyboards must be updated with schema changes.
- `TASK-004` adapter contracts should record the DSL schema version in artifact manifests.
