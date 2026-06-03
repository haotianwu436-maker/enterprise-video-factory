"""FastAPI application for the enterprise video factory runtime."""

from __future__ import annotations

import base64
import binascii
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from video_factory_contracts.vocabulary import load_contract_vocabulary
from video_factory_runtime.auth import (
    AuthError,
    create_access_token,
    create_asset_access_token,
    create_artifact_access_token,
    verify_access_token,
    verify_asset_access_token,
    verify_artifact_access_token,
    verify_password,
)
from video_factory_runtime.copywriter import CopywriterService
from video_factory_runtime.domain import ActorContext, JobIntakeRejected
from video_factory_runtime.pipeline import GenerationPipeline
from video_factory_runtime.service import JobIntakeService
from video_factory_runtime.storage import DEFAULT_DATA_DIR, SQLiteRuntimeStore


def create_app(
    service: JobIntakeService | None = None,
    store: SQLiteRuntimeStore | None = None,
    allow_legacy_headers: bool | None = None,
) -> FastAPI:
    """Create a tenant-scoped FastAPI app for local product runtime."""
    runtime_store = store or SQLiteRuntimeStore()
    intake_service = service or JobIntakeService(
        asset_repository=runtime_store,
        job_repository=runtime_store,
    )
    app = FastAPI(title="Enterprise Video Factory Runtime", version="0.2.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.runtime_store = runtime_store
    app.state.job_intake_service = intake_service
    app.state.pipeline = GenerationPipeline(runtime_store)
    app.state.copywriter = CopywriterService()
    app.state.contract_vocabulary = load_contract_vocabulary()
    legacy_headers_enabled = (
        service is not None and store is None
        if allow_legacy_headers is None
        else allow_legacy_headers
    )
    actor_dep = _actor_dependency(runtime_store, allow_legacy_headers=legacy_headers_enabled)

    web_dist = Path("web/dist")
    if web_dist.exists():
        app.mount("/studio", StaticFiles(directory=web_dist, html=True), name="studio")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/auth/login")
    def login(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        user = runtime_store.find_user_by_email(str(payload.get("email", "")))
        if not user or not verify_password(str(payload.get("password", "")), user.password_hash, user.salt):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
        return {"access_token": create_access_token(user), "token_type": "bearer", "user": user.to_api()}

    @app.get("/v1/auth/me")
    def me(actor: ActorContext = Depends(actor_dep)) -> dict[str, str]:
        user = runtime_store.get_user(actor.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found")
        return user.to_api()

    @app.get("/v1/assets")
    def list_assets(actor: ActorContext = Depends(actor_dep)) -> dict[str, Any]:
        return {"assets": runtime_store.list_assets(actor.tenant_id)}

    @app.post("/v1/assets", status_code=status.HTTP_201_CREATED)
    def create_asset(
        payload: dict[str, Any] = Body(...),
        actor: ActorContext = Depends(actor_dep),
    ) -> dict[str, Any]:
        _require_role(actor, {"creator", "tenant_admin"})
        asset_type = str(payload.get("asset_type", ""))
        if asset_type not in app.state.contract_vocabulary.asset_types:
            raise HTTPException(status_code=422, detail="asset_type is not supported")
        file_uri = _write_base64_file(actor.tenant_id, payload) if payload.get("content_base64") else None
        return runtime_store.create_asset(
            tenant_id=actor.tenant_id,
            asset_type=asset_type,
            display_name=str(payload.get("display_name") or asset_type),
            file_uri=file_uri,
        )

    @app.post("/v1/assets/{asset_id}/consent", status_code=status.HTTP_201_CREATED)
    def attach_consent(
        asset_id: str,
        payload: dict[str, Any] = Body(...),
        actor: ActorContext = Depends(actor_dep),
    ) -> dict[str, Any]:
        _require_role(actor, {"creator", "tenant_admin"})
        _validate_consent_payload(payload)
        try:
            return runtime_store.attach_consent(
                actor.tenant_id,
                asset_id,
                payload=payload,
                actor_user_id=actor.user_id,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="asset not found") from exc

    @app.post("/v1/assets/{asset_id}/activate")
    def activate_asset(
        asset_id: str,
        actor: ActorContext = Depends(actor_dep),
    ) -> dict[str, Any]:
        _require_role(actor, {"creator", "tenant_admin"})
        try:
            return runtime_store.activate_asset(actor.tenant_id, asset_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="asset not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/v1/assets/{asset_id}/signed-url")
    def get_asset_signed_url(asset_id: str, actor: ActorContext = Depends(actor_dep)) -> dict[str, str]:
        asset = _get_asset_with_media(runtime_store, actor.tenant_id, asset_id)
        file_path = _safe_runtime_file(str(asset["file_uri"]))
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="asset media file not found")
        token = create_asset_access_token(tenant_id=actor.tenant_id, asset_id=asset_id)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=600)
        return {
            "url": f"/v1/assets/{asset_id}/media?token={token}",
            "expires_at": expires_at.isoformat(),
        }

    @app.get("/v1/assets/{asset_id}/media")
    def get_asset_media(asset_id: str, token: str = Query(...)) -> FileResponse:
        try:
            claims = verify_asset_access_token(token)
        except AuthError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        if claims["asset_id"] != asset_id:
            raise HTTPException(status_code=403, detail="asset token subject mismatch")
        asset = _get_asset_with_media(runtime_store, claims["tenant_id"], asset_id)
        file_path = _safe_runtime_file(str(asset["file_uri"]))
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="asset media file not found")
        return FileResponse(file_path, media_type=_asset_media_type(file_path))

    @app.post("/v1/jobs", status_code=status.HTTP_202_ACCEPTED)
    def create_job(
        payload: Any = Body(...),
        actor: ActorContext = Depends(actor_dep),
    ) -> dict[str, Any]:
        try:
            job = app.state.job_intake_service.create_job(payload, actor)
        except JobIntakeRejected as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.to_api()) from exc
        return job.to_api()

    @app.get("/v1/jobs")
    def list_jobs(actor: ActorContext = Depends(actor_dep)) -> dict[str, Any]:
        return {"jobs": runtime_store.list_jobs(actor.tenant_id)}

    @app.get("/v1/jobs/{job_id}")
    def get_job(
        job_id: str,
        response: Response,
        actor: ActorContext = Depends(actor_dep),
    ) -> dict[str, Any]:
        job = app.state.job_intake_service.get_job(actor.tenant_id, job_id)
        if job is None:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {"detail": "job not found"}
        return job.to_api()

    @app.post("/v1/jobs/{job_id}/start")
    def start_job(job_id: str, actor: ActorContext = Depends(actor_dep)) -> dict[str, Any]:
        _require_role(actor, {"creator", "tenant_admin"})
        try:
            return app.state.pipeline.start(actor.tenant_id, job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="job not found") from exc

    @app.get("/v1/jobs/{job_id}/artifacts")
    def list_job_artifacts(job_id: str, actor: ActorContext = Depends(actor_dep)) -> dict[str, Any]:
        return {"artifacts": runtime_store.list_artifacts(actor.tenant_id, job_id)}

    @app.get("/v1/jobs/{job_id}/qc")
    def list_job_qc(job_id: str, actor: ActorContext = Depends(actor_dep)) -> dict[str, Any]:
        return {"qc_reports": runtime_store.list_qc_reports(actor.tenant_id, job_id)}

    @app.get("/v1/copywriter/prompts")
    def get_copywriter_prompts(actor: ActorContext = Depends(actor_dep)) -> dict[str, Any]:
        _require_role(actor, {"creator", "tenant_admin"})
        return app.state.copywriter.prompts()

    @app.post("/v1/copywriter/generate")
    def generate_copy(
        payload: dict[str, Any] = Body(...),
        actor: ActorContext = Depends(actor_dep),
    ) -> dict[str, Any]:
        _require_role(actor, {"creator", "tenant_admin"})
        try:
            result = app.state.copywriter.generate(payload)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return result.to_api()

    @app.get("/v1/artifacts/{artifact_id}/signed-url")
    def get_artifact_signed_url(artifact_id: str, actor: ActorContext = Depends(actor_dep)) -> dict[str, str]:
        artifact = runtime_store.get_artifact(actor.tenant_id, artifact_id)
        if not artifact or not artifact.get("file_uri"):
            raise HTTPException(status_code=404, detail="artifact media not found")
        file_path = _safe_runtime_file(str(artifact["file_uri"]))
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="artifact media file not found")
        token = create_artifact_access_token(tenant_id=actor.tenant_id, artifact_id=artifact_id)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=600)
        return {
            "url": f"/v1/artifacts/{artifact_id}/media?token={token}",
            "expires_at": expires_at.isoformat(),
        }

    @app.get("/v1/artifacts/{artifact_id}/media")
    def get_artifact_media(artifact_id: str, token: str = Query(...)) -> FileResponse:
        try:
            claims = verify_artifact_access_token(token)
        except AuthError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        if claims["artifact_id"] != artifact_id:
            raise HTTPException(status_code=403, detail="artifact token subject mismatch")
        artifact = runtime_store.get_artifact(claims["tenant_id"], artifact_id)
        if not artifact or not artifact.get("file_uri"):
            raise HTTPException(status_code=404, detail="artifact media not found")
        file_path = _safe_runtime_file(str(artifact["file_uri"]))
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="artifact media file not found")
        media_type = "video/mp4" if file_path.suffix.lower() == ".mp4" else "application/octet-stream"
        return FileResponse(file_path, media_type=media_type)

    return app


def _actor_dependency(store: SQLiteRuntimeStore, *, allow_legacy_headers: bool):
    async def dependency(
        request: Request,
        authorization: str | None = Header(None),
        x_tenant_id: str | None = Header(None),
        x_user_id: str | None = Header(None),
        x_role: str | None = Header(None),
    ) -> ActorContext:
        if authorization and authorization.lower().startswith("bearer "):
            try:
                return verify_access_token(authorization.split(" ", 1)[1])
            except AuthError as exc:
                raise HTTPException(status_code=401, detail=str(exc)) from exc
        if allow_legacy_headers and request.method == "GET" and x_tenant_id:
            return ActorContext(tenant_id=x_tenant_id, user_id=x_user_id or "local_viewer", role=x_role or "creator")
        if allow_legacy_headers and x_tenant_id and x_user_id and x_role:
            return ActorContext(tenant_id=x_tenant_id, user_id=x_user_id, role=x_role)
        raise HTTPException(status_code=401, detail="missing bearer token")

    return dependency


def _require_role(actor: ActorContext, allowed: set[str]) -> None:
    if actor.role not in allowed:
        raise HTTPException(status_code=403, detail="role is not allowed")


def _validate_consent_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload.get("scope"), dict):
        raise HTTPException(status_code=422, detail="consent scope is required")
    evidence_uri = payload.get("evidence_uri")
    if not isinstance(evidence_uri, str) or not evidence_uri.strip():
        raise HTTPException(status_code=422, detail="consent evidence_uri is required")


def _write_base64_file(tenant_id: str, payload: dict[str, Any]) -> str:
    max_upload_bytes = int(os.environ.get("VIDEO_FACTORY_MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
    file_name = Path(str(payload.get("file_name") or "upload.bin")).name
    allowed_suffixes = {".wav", ".mp3", ".m4a", ".mp4", ".mov", ".png", ".jpg", ".jpeg", ".json", ".bin"}
    if Path(file_name).suffix.lower() not in allowed_suffixes:
        raise HTTPException(status_code=422, detail="file extension is not supported")
    target_dir = DEFAULT_DATA_DIR / tenant_id / "assets"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / file_name
    try:
        decoded = base64.b64decode(str(payload["content_base64"]), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=422, detail="content_base64 is invalid") from exc
    if len(decoded) > max_upload_bytes:
        raise HTTPException(status_code=413, detail="uploaded file exceeds local size limit")
    target.write_bytes(decoded)
    return str(target)


def _get_asset_with_media(store: SQLiteRuntimeStore, tenant_id: str, asset_id: str) -> dict[str, Any]:
    asset = next((item for item in store.list_assets(tenant_id) if item["asset_id"] == asset_id), None)
    if not asset or not asset.get("file_uri"):
        raise HTTPException(status_code=404, detail="asset media not found")
    return asset


def _asset_media_type(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".mp3":
        return "audio/mpeg"
    if suffix in {".m4a", ".mp4"}:
        return "video/mp4" if suffix == ".mp4" else "audio/mp4"
    if suffix == ".wav":
        return "audio/wav"
    if suffix == ".mov":
        return "video/quicktime"
    if suffix == ".json":
        return "application/json"
    return "application/octet-stream"


def _safe_runtime_file(file_uri: str) -> Path:
    path = Path(file_uri).resolve()
    root = DEFAULT_DATA_DIR.resolve()
    if root not in path.parents and path != root:
        raise HTTPException(status_code=403, detail="runtime media path is outside local storage")
    return path
