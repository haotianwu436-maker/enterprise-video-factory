# Job Intake Runtime Foundation

<!-- task: TASK-011 -->

## Purpose

This document describes the first product runtime slice: a tenant-scoped job intake API that validates text/opinion input, governed asset references, accepted output profile fields, and the initial `created -> validated` state transition.

The runtime deliberately does not implement TTS, avatar rendering, HTML/video rendering, orchestration workers, queues, GPU scheduling, object storage, or deployment manifests.

## Local Commands

Run the product tests and accepted contract guardrail:

```bash
uv run pytest
uv run validate-contracts --repo .
```

Create a sample job without starting a server:

```bash
uv run video-factory-api --sample-job
```

Start the local FastAPI app:

```bash
uv run uvicorn video_factory_runtime.api:create_app --factory --host 127.0.0.1 --port 8000
```

Create a job through HTTP:

```bash
curl -sS -X POST http://127.0.0.1:8000/v1/jobs \
  -H 'Content-Type: application/json' \
  -H 'x-tenant-id: tenant_123' \
  -H 'x-user-id: user_456' \
  -H 'x-role: creator' \
  --data @examples/jobs/create-job.json
```

Read the created job:

```bash
curl -sS http://127.0.0.1:8000/v1/jobs/job_000001 \
  -H 'x-tenant-id: tenant_123'
```

## Contract Vocabulary

Runtime code loads accepted vocabulary through `video_factory_contracts.load_contract_vocabulary()` instead of maintaining a parallel state table.

The first job intake slice consumes:

- job states from `docs/contracts/job-state-machine.md`
- manifest stages from `docs/contracts/artifact-manifest.md`
- asset states and audit event types from `docs/security/asset-governance.md`
- asset types and create-job input/output enums from `openapi/enterprise-video-factory.openapi.yaml`
- QC statuses from `docs/quality/qc-matrix.md`
- review states and reason codes from `docs/contracts/job-state-machine.md`
- failure codes from `docs/quality/failure-taxonomy.md`

## Deterministic Intake Behavior

Accepted sample jobs return:

- `job_id`: starts at `job_000001` for a fresh local process
- `state`: `validated`
- `active_stage`: `source_intake`
- `state_history`: `created`, then `validated`
- `asset_authorization_snapshots`: current voice/avatar consent snapshots
- `audit_event_ids`: deterministic local audit ids for `job.created` and `job.assets_bound`

Invalid requests fail closed with deterministic violation objects:

- non-object request body: `scene_dsl_invalid`
- missing text: `scene_dsl_invalid`
- unsupported output profile: `scene_dsl_invalid`
- missing voice profile: `voice_profile_missing`
- missing avatar profile: `avatar_profile_missing`
- inaccessible cross-tenant identity assets: tenant-scoped lookup treats the asset as missing, so the request fails without binding it and returns the required missing-asset code
- revoked, wrong-type, or consent-less identity assets visible to the caller tenant: `asset_not_authorized` or the relevant contract failure code

## Storage Scope

TASK-011 uses in-memory repositories behind explicit interfaces. This keeps local startup and tests fast while preserving a clear replacement boundary for a future durable metadata store.
