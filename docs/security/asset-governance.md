# Asset Governance Baseline

<!-- task: TASK-008 -->

## Purpose

This document defines the early governance baseline for identity assets and enterprise video generation. It is intentionally a product and architecture contract, not legal advice and not implementation code.

The baseline exists so downstream DSL, model adapters, orchestration, QC, and API contracts can safely reference voice and avatar assets without inventing their own authorization rules.

## Governance Principles

- Only authorized voice and likeness assets may be used.
- Tenant isolation applies to assets, jobs, artifacts, audit events, and review decisions.
- Every identity asset must have a consent evidence chain before it can be used in generation.
- Every generated video must be traceable to source input, selected assets, model versions, QC reports, and operator actions.
- Manual review is a first-class path for authorization, safety, and repeated-quality failures.
- This baseline records open legal/compliance questions for final reconciliation in `TASK-009`.

## Roles

| Role | Scope |
| --- | --- |
| Tenant admin | Manages tenant settings, retention defaults, and role assignment. |
| Asset owner | Grants or revokes consent for a voice/avatar profile. |
| Creator | Creates jobs using assets they are allowed to use. |
| Operator | Monitors jobs, retries stages, and performs allowed repair actions. |
| Reviewer | Reviews blocked, unsafe, disputed, or policy-sensitive jobs. |
| Auditor | Reads audit bundles and traceability evidence without modifying assets or jobs. |
| System worker | Executes orchestrated stages under service identity and tenant scope. |

Rule: service identities may execute workflows but may not approve consent, override review blocks, or mark a video publish-ready without recorded policy evidence.

## Asset Types

| Asset Type | Examples | Governance Requirement |
| --- | --- | --- |
| Voice profile | zero-shot reference voice, few-shot profile, default brand narrator | Consent evidence, owner, allowed use cases, expiration/revocation state. |
| Avatar profile | talking-head image/video source, digital human identity | Likeness consent, source provenance, allowed use cases, expiration/revocation state. |
| Brand kit | colors, fonts, logo, lower thirds | Tenant ownership and brand admin approval. |
| Music asset | background track, stinger, licensed loop | License/provenance evidence and allowed platform scope. |
| Template | scene layout, caption style, animation preset | Tenant/global approval and versioning. |

## Asset State Machine

```text
draft
  -> pending_consent
  -> consent_verified
  -> active
  -> suspended
  -> revoked
  -> archived
```

Allowed transitions:

- `draft -> pending_consent`: asset is uploaded or proposed.
- `pending_consent -> consent_verified`: required consent evidence is attached.
- `consent_verified -> active`: tenant admin or authorized workflow approves use.
- `active -> suspended`: temporary risk, dispute, or expired evidence.
- `active -> revoked`: owner revokes or compliance blocks use.
- `suspended -> active`: reviewer resolves the block.
- `suspended -> revoked`: reviewer or owner permanently blocks use.
- `revoked -> archived`: asset is retained for audit but cannot be used.

Rules:

- `revoked` assets are never eligible for new generation jobs.
- Existing released videos keep traceability references to historical authorization snapshots.
- A job must snapshot asset authorization at job validation time and again before release if the workflow is long-running.

## Consent Evidence

Minimum evidence fields:

```json
{
  "consent_event_id": "consent_evt_123",
  "tenant_id": "tenant_123",
  "asset_id": "voice_abc",
  "asset_type": "voice_profile",
  "subject_id": "person_456",
  "granted_by": "user_789",
  "granted_at": "2026-05-30T00:00:00Z",
  "scope": {
    "allowed_use_cases": ["talking_head_video"],
    "allowed_platforms": ["internal_review", "social_publish"],
    "allowed_languages": ["zh", "en"],
    "commercial_use": true
  },
  "expires_at": null,
  "revocation_event_id": null,
  "evidence_uri": "s3://video-factory/tenant_123/assets/voice_abc/consent/evidence.pdf",
  "review_status": "approved"
}
```

Downstream requirements:

- Scene DSL references `asset_id`, not raw media paths.
- Model adapters receive authorization snapshot IDs in artifact manifests.
- QC can block a job when authorization snapshots are missing, expired, or revoked.
- API and console show consent state before allowing generation or release.

## Tenant And RBAC Baseline

Tenant isolation:

- Asset IDs are tenant-scoped.
- Object storage keys include `tenant_id`.
- Metadata queries require tenant filter.
- Audit events include tenant, actor, and service identity.
- Signed artifact URLs are tenant-scoped and time-limited.

RBAC baseline:

| Action | Creator | Operator | Reviewer | Tenant Admin | Auditor |
| --- | --- | --- | --- | --- | --- |
| Create job | yes | no | no | yes | no |
| Select active asset | yes | no | no | yes | no |
| Upload asset draft | yes | no | no | yes | no |
| Approve consent | no | no | yes | yes | no |
| Retry failed stage | no | yes | yes | yes | no |
| Override QC block | no | no | yes | no | no |
| Release video | yes, if no blocks | yes, if delegated | yes | yes | no |
| Read audit bundle | own jobs only | operational scope | review scope | tenant scope | tenant scope |

Open question for `TASK-009`: whether release requires two-person approval for enterprise tenants.

## Audit Event Baseline

Audit events are append-only and tenant-scoped.

Required event families:

- `asset.created`
- `asset.consent_submitted`
- `asset.consent_approved`
- `asset.consent_revoked`
- `asset.activated`
- `asset.suspended`
- `job.created`
- `job.assets_bound`
- `stage.started`
- `stage.completed`
- `stage.failed`
- `qc.completed`
- `repair.requested`
- `repair.completed`
- `review.opened`
- `review.approved`
- `review.rejected`
- `release.created`
- `release.current_pointer_changed`

Event envelope:

```json
{
  "event_id": "audit_evt_123",
  "event_type": "job.assets_bound",
  "tenant_id": "tenant_123",
  "actor": {
    "type": "user",
    "id": "user_456",
    "role": "creator"
  },
  "subject": {
    "type": "job",
    "id": "job_789"
  },
  "occurred_at": "2026-05-30T00:00:00Z",
  "data": {
    "asset_ids": ["voice_abc", "avatar_def"],
    "authorization_snapshots": ["consent_evt_123", "consent_evt_456"]
  },
  "trace": {
    "workflow_id": "wf_123",
    "run_id": "run_456"
  }
}
```

Rules:

- Audit events are immutable.
- Metadata rows may cache latest state but must point back to audit events.
- Operator actions that change job state must produce audit events.
- Release pointer changes must produce audit events.

## Manual Review Triggers

Open review when:

- An identity asset is missing consent evidence.
- A consent event is expired, revoked, or disputed.
- QC detects unsafe, unauthorized, or ambiguous output.
- The same segment fails repair more than the configured threshold.
- A user requests publish-ready release after a policy-sensitive failure.
- A tenant policy requires review for identity cloning outputs.

Review outcomes:

- approve and continue
- approve with restrictions
- retry with constrained parameters
- reject output
- revoke or suspend asset
- escalate to tenant admin or external legal/compliance review

## Retention Baseline

Draft defaults for downstream use:

- Released final video and traceability bundles are retained until tenant deletion policy allows removal.
- Consent evidence must be retained at least as long as released videos that depend on it.
- Failed attempts may be pruned after tenant-defined retention unless tied to incident review.
- Raw voice/avatar enrollment media should have a shorter retention option after profile creation.
- `TASK-009` must reconcile retention with target jurisdiction and customer requirements.

## Downstream Contract Requirements

`TASK-003` Scene DSL:

- Use `asset_ref` objects with `asset_id`, `asset_type`, and optional `authorization_snapshot`.
- Do not allow raw paths or arbitrary external URLs for identity assets.
- Include `requires_review` and `policy_tags` fields where scenes request sensitive behavior.

`TASK-004` Model adapters:

- Include `tenant_id`, `asset_refs`, `authorization_snapshots`, `model_version`, and audit event IDs in manifests.
- Return policy-relevant failure codes such as `asset_not_authorized` and `consent_expired`.

`TASK-005` Orchestration:

- Emit audit events on stage attempt, repair, review, and release transitions.
- Re-check asset authorization before release.

`TASK-006` QC:

- Treat missing authorization metadata as a hard failure.
- Escalate unsafe or unauthorized identity output to review.

`TASK-007` API/Console:

- Expose asset state and consent evidence before job creation.
- Prevent operator actions from bypassing review blocks.
- Use signed tenant-scoped artifact access.

`TASK-009` Compliance completion:

- Reconcile jurisdiction, disclosure, retention, and traceability requirements after downstream contracts exist.

## Open Questions For TASK-009

- Target jurisdictions and applicable AI disclosure rules.
- Whether each generated video must include visible AI labeling.
- Whether customer contracts require exportable audit bundles.
- Whether identity asset consent must expire periodically.
- Whether release requires dual approval for enterprise tenants.
- Whether raw enrollment media must be deleted after profile creation by default.

