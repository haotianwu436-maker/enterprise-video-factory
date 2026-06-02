# Implement creative Studio and generation runtime

<!-- repo-init:managed -->

## Metadata

- ID: `TASK-012`
- Status: `done`
- Owner: `shared`
- Parent: `TASK-001`
- Created: `2026-06-03`
- Updated: `2026-06-03`

## Why

Move beyond the API-only TASK-011 slice into a product-visible creative Studio and a backend that can manage authenticated users, governed assets, job status, and a real-generation adapter path.

## Scope

- In scope: React/Vite creative Studio, JWT-style login, local SQLite runtime metadata, JSON/base64 asset upload, consent/activation, job list/detail/start, artifacts/QC endpoints, deterministic generation pipeline states, CosyVoice remote adapter, MuseTalk remote adapter placeholder, local file storage under `var/`, tests, and docs/contracts updates
- Out of scope: vendoring model weights, running MuseTalk locally on this Mac, production SSO, production object storage, Kubernetes/GPU scheduling, and guaranteed MP4 generation without a configured CosyVoice service

## Acceptance Criteria

- A local developer can start the backend and frontend Studio, log in, view/create authorized assets, create a job, start generation, and inspect status/artifacts/QC.
- The Studio is visually polished as a creator-facing tool, not a Swagger substitute or generic CRUD table.
- The backend persists users/assets/jobs/artifacts/QC in SQLite and stores uploaded files under `var/video_factory/`.
- Missing `COSYVOICE_BASE_URL` causes an explicit failed/blocked generation state and QC evidence, not a fake successful MP4.
- Contract validation and backend tests pass; frontend build/tests pass where dependencies are available.

## Product Acceptance

- User journey: `pending`
- Evidence required: local Studio login, asset authorization, job creation/start, visible failed TTS/QC evidence without CosyVoice, backend/frontend test output, contract validator output, and browser screenshot/inspection
- Acceptance owner: `yanshou`
- Acceptance status: `passed`

## Dependencies

- Files: `src/video_factory_runtime/`, `src/video_factory_contracts/`, `tests/`, `openapi/enterprise-video-factory.openapi.yaml`, `docs/product/api-console.md`, `docs/development/`, `README.md`, `STATUS.md`, `.gitignore`, `web/`
- Decisions: `DEC-001, DEC-002, DEC-003, DEC-004, DEC-005`
- External: optional remote `COSYVOICE_BASE_URL` for real TTS audio; optional remote `MUSETALK_BASE_URL` for future GPU lip-sync worker; local Node/npm and ffmpeg for Studio/build/composition

## Plan

1. Preserve TASK-011 accepted intake behavior while replacing the runtime store with a durable local SQLite implementation.
2. Add seeded local auth, bearer token verification, governed asset upload/consent/activation, job list/detail/start, artifacts, and QC endpoints.
3. Add a deterministic planner, CosyVoice remote adapter, MuseTalk remote placeholder, and ffmpeg composition path that fails honestly when required model runtime is missing.
4. Build a polished React/Vite creative Studio that consumes only `/v1/*` APIs.
5. Update docs/OpenAPI/contracts, run backend/frontend validation, then run Baguan review and Yanshou acceptance.

## Implementation Packet

- Files to inspect/change: `src/video_factory_runtime/`, `src/video_factory_contracts/`, `tests/`, `openapi/enterprise-video-factory.openapi.yaml`, `docs/product/api-console.md`, `README.md`, `STATUS.md`, `pyproject.toml`, `.gitignore`, new `web/`
- Minimal approach: keep TASK-011 intake service as the validation core; add SQLite-backed repositories and API endpoints around it; build a Vite Studio that consumes only `/v1/*`; implement generation as deterministic planning plus adapter-driven TTS/render steps
- Main risks: scope explosion, dependency/network failures, fake generation success, contract drift, and overwriting TASK-011 accepted behavior
- Validation commands: `uv run pytest`; `uv run validate-contracts --repo .`; frontend `npm test` and `npm run build` when dependencies install
- Rollback or safety note: new runtime files, `web/`, docs, and TASK-012 can be reverted without removing TASK-011 accepted foundation

## Parent Coordination

- Parent task: `TASK-001-coordinate-enterprise-delivery-plan.md`
- Start condition: TASK-011 accepted and current user request explicitly asked to implement the TASK-012 plan.

## Related Tasks

- Consumes `TASK-007-design-product-api-and-console.md` for API resource shape.
- Extends `TASK-011-implement-job-intake-api-and-domain-foundation.md` with auth, persistence, assets, Studio, and generation-start behavior.
- Consumes `TASK-004-design-model-service-adapters.md` for model adapter boundaries.
- Consumes `TASK-008-design-governance-baseline-and-authorized-assets.md` for consent and authorized identity asset semantics.

## Notes

- Facts: this Mac should not run MuseTalk locally as the product path; MuseTalk remains a remote GPU worker boundary.
- Assumptions: local Studio sessions may store a bearer token in localStorage for development only.
- Risks: dependency drift, model runtime absence, fake-success behavior, visual regression on mobile, and accidental drift between product docs/OpenAPI/runtime.

## Assumption Checks

### Validated

- Backend tests validate auth, asset lifecycle, job creation, and explicit failed TTS/QC state without `COSYVOICE_BASE_URL`.
- Frontend dependency audit is clean after upgrading Vitest.

### Invalidated

- Direct `PyJWT` dependency addition was not kept because package resolution failed earlier; local bearer tokens use a stdlib HMAC-signed JWT-style envelope instead.

### Still Open

- Real MP4 production with cloned voice requires a compatible external CosyVoice service.
- True MuseTalk lip-sync requires a remote GPU worker in a later task.

## Downstream Impact

### Affected Tasks

- Future orchestration, real model worker, artifact storage, QC repair, and release tasks should build on the TASK-012 runtime and Studio surfaces.

### Suggested Follow-up

- Define the next product slice around a real CosyVoice worker contract test or a remote generation worker integration.

## Execution Log

- `2026-06-03`: task opened from the accepted TASK-012 implementation plan.
- `2026-06-03`: implemented backend auth/assets/jobs/generation-start persistence and React/Vite Studio; validation in progress.
- `2026-06-03`: local validation passed: backend/full pytest, frontend Vitest/build/audit, contract validator, harness, and browser Studio flow for login, asset creation, job creation, generation start, and explicit TTS failure evidence.
- `2026-06-03`: Baguan found enterprise blockers in auth header bypass, consent evidence, artifact preview, renderer scope drift, start idempotency, stale job evidence, and upload limits; fixes added bearer-only product runtime auth, persisted consent evidence payloads, signed artifact media URLs, Remotion rendering, renderer failure QC, start idempotency, job-specific evidence refresh, and upload size/type controls.

## Review Notes

- Status: `reviewed with fixes applied`
- Findings: Baguan reported P1/P2 blockers on the first TASK-012 implementation: header impersonation, fabricated consent evidence, missing playable artifact URL/video preview, static renderer drift, non-idempotent start, stale selected-job evidence, and upload controls. Follow-up Baguan found no blocking findings after fixes and one remaining P2 on backend upload extension enforcement; that P2 was fixed with a server-side extension allowlist and regression test.
- Required follow-up: none blocking; future hardening should add MIME sniffing, Playwright e2e, successful CosyVoice MP4 validation, and concurrency locks.

## Acceptance Evidence

- Status: `passed`
- Evidence: `2026-06-03`: after Baguan fixes and the backend upload allowlist follow-up, `uv run pytest -q` passed 24 tests with 1 FastAPI/Starlette deprecation warning. `uv run validate-contracts --repo .` returned PASS with 4 passed checks, 0 errors, and 0 warnings. In `web/`, `npm test` passed 1 Vitest file / 2 tests, `npm run build` produced a Vite production build, and `npm audit --audit-level=critical` returned 0 vulnerabilities. Remotion smoke rendered a real 60s `FactoryVertical` MP4 at `/tmp/video-factory-remotion-smoke/out.mp4` (about 5.9MB). Header impersonation against `POST /v1/assets` returned `401 {"detail":"missing bearer token"}`. Browser acceptance against restarted backend `http://127.0.0.1:8000` and Studio `http://127.0.0.1:5173` verified bearer-backed Studio flow, local consent evidence submission, job creation showing `validated`, generation start for the newly selected job, `state=failed`, active TTS stage, and QC message `failed_terminal: COSYVOICE_BASE_URL is not configured`.
- Repro steps for failures: `none`

## Debug Notes

- Failure signal: `none`
- Minimal reproduction: `none`
- Likely root cause: `none`
- Regression test: `tests/test_runtime_studio_api.py`, `web/src/state.test.ts`

## Harness Lessons

- Durable lesson: Product slices that add UI and runtime should update task handoff sections before contract validation so RepoFrame does not fail on missing process metadata.
- Harness update: none yet.
- Future trigger: Apply this format before opening larger Studio or worker tasks.
