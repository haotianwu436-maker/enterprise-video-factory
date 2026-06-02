from __future__ import annotations

import base64
from pathlib import Path

from fastapi.testclient import TestClient

from video_factory_runtime.api import create_app
from video_factory_runtime.pipeline import CosyVoiceAdapter, GenerationPipeline
from video_factory_runtime.storage import SQLiteRuntimeStore


def test_login_me_asset_lifecycle_and_generation_failure_without_cosyvoice(tmp_path) -> None:
    store = SQLiteRuntimeStore(tmp_path / "runtime.sqlite3")
    client = TestClient(create_app(store=store))

    login = client.post(
        "/v1/auth/login",
        json={"email": "creator@example.local", "password": "factory-demo"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "creator"

    asset = client.post(
        "/v1/assets",
        headers=headers,
        json={
            "asset_type": "voice_profile",
            "display_name": "Uploaded voice",
            "file_name": "voice.wav",
            "content_base64": base64.b64encode(b"fake wav").decode(),
        },
    )
    assert asset.status_code == 201
    asset_id = asset.json()["asset_id"]
    assert asset.json()["state"] == "pending_consent"

    consent = client.post(
        f"/v1/assets/{asset_id}/consent",
        headers=headers,
        json={
            "scope": {"asset_id": asset_id, "purpose": "talking-head video generation"},
            "evidence_uri": "local://test-consent/voice.wav",
        },
    )
    assert consent.status_code == 201
    assert consent.json()["evidence_uri"] == "local://test-consent/voice.wav"

    activated = client.post(f"/v1/assets/{asset_id}/activate", headers=headers)
    assert activated.status_code == 200
    assert activated.json()["state"] == "active"

    assets = client.get("/v1/assets", headers=headers)
    assert assets.status_code == 200
    assert any(item["asset_id"] == asset_id for item in assets.json()["assets"])

    job = client.post(
        "/v1/jobs",
        headers=headers,
        json={
            "input": {"type": "opinion", "text": "真实生成第一步必须失败得诚实。"},
            "asset_refs": {
                "voice_profile_id": "voice_abc",
                "avatar_profile_id": "avatar_def",
                "template_id": "template_001",
            },
            "output_profile": {"duration_target_sec": 60, "aspect_ratio": "9:16"},
        },
    )
    assert job.status_code == 202
    job_id = job.json()["job_id"]

    listed = client.get("/v1/jobs", headers=headers)
    assert listed.status_code == 200
    assert any(item["job_id"] == job_id for item in listed.json()["jobs"])

    started = client.post(f"/v1/jobs/{job_id}/start", headers=headers)
    assert started.status_code == 200
    assert started.json()["state"] == "failed"
    assert started.json()["active_stage"] == "tts"

    artifacts = client.get(f"/v1/jobs/{job_id}/artifacts", headers=headers)
    assert artifacts.status_code == 200
    assert any(item["stage"] == "planning" for item in artifacts.json()["artifacts"])

    qc = client.get(f"/v1/jobs/{job_id}/qc", headers=headers)
    assert qc.status_code == 200
    assert qc.json()["qc_reports"][0]["failure_codes"] == ["model_runtime_error"]

    started_again = client.post(f"/v1/jobs/{job_id}/start", headers=headers)
    assert started_again.status_code == 200
    assert started_again.json()["state"] == "failed"
    assert len(client.get(f"/v1/jobs/{job_id}/qc", headers=headers).json()["qc_reports"]) == 1


def test_login_failure_is_unauthorized(tmp_path) -> None:
    client = TestClient(create_app(store=SQLiteRuntimeStore(tmp_path / "runtime.sqlite3")))

    response = client.post(
        "/v1/auth/login",
        json={"email": "creator@example.local", "password": "wrong"},
    )

    assert response.status_code == 401


def test_runtime_rejects_header_impersonation_for_writes(tmp_path) -> None:
    client = TestClient(create_app(store=SQLiteRuntimeStore(tmp_path / "runtime.sqlite3")))

    response = client.post(
        "/v1/assets",
        headers={"x-tenant-id": "tenant_123", "x-user-id": "attacker", "x-role": "creator"},
        json={"asset_type": "brand_kit", "display_name": "spoofed"},
    )

    assert response.status_code == 401


def test_consent_requires_evidence_payload(tmp_path) -> None:
    store = SQLiteRuntimeStore(tmp_path / "runtime.sqlite3")
    client = TestClient(create_app(store=store))
    login = client.post("/v1/auth/login", json={"email": "creator@example.local", "password": "factory-demo"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    asset = client.post(
        "/v1/assets",
        headers=headers,
        json={"asset_type": "voice_profile", "display_name": "Needs evidence"},
    )

    response = client.post(f"/v1/assets/{asset.json()['asset_id']}/consent", headers=headers, json={})

    assert response.status_code == 422


def test_asset_upload_rejects_unsupported_extension(tmp_path) -> None:
    store = SQLiteRuntimeStore(tmp_path / "runtime.sqlite3")
    client = TestClient(create_app(store=store))
    login = client.post("/v1/auth/login", json={"email": "creator@example.local", "password": "factory-demo"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.post(
        "/v1/assets",
        headers=headers,
        json={
            "asset_type": "voice_profile",
            "display_name": "Bad extension",
            "file_name": "voice.exe",
            "content_base64": base64.b64encode(b"not media").decode(),
        },
    )

    assert response.status_code == 422


def test_artifact_signed_url_serves_runtime_media(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    store = SQLiteRuntimeStore(tmp_path / "runtime.sqlite3")
    client = TestClient(create_app(store=store))
    login = client.post("/v1/auth/login", json={"email": "creator@example.local", "password": "factory-demo"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    media_path = Path("var/video_factory/tenant_123/jobs/job_test/final.mp4")
    media_path.parent.mkdir(parents=True, exist_ok=True)
    media_path.write_bytes(b"mp4-bytes")
    artifact = store.save_artifact(
        "tenant_123",
        {
            "job_id": "job_test",
            "stage": "composition",
            "manifest_uri": str(media_path),
            "qc_status": "passed",
            "file_uri": str(media_path),
        },
    )

    signed = client.get(f"/v1/artifacts/{artifact['artifact_id']}/signed-url", headers=headers)
    assert signed.status_code == 200
    media = client.get(signed.json()["url"])
    assert media.status_code == 200
    assert media.content == b"mp4-bytes"


def test_renderer_failure_records_qc(tmp_path) -> None:
    store = SQLiteRuntimeStore(tmp_path / "runtime.sqlite3")
    client = TestClient(create_app(store=store))
    login = client.post("/v1/auth/login", json={"email": "creator@example.local", "password": "factory-demo"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    job = client.post(
        "/v1/jobs",
        headers=headers,
        json={
            "input": {"type": "opinion", "text": "renderer failure should be captured"},
            "asset_refs": {
                "voice_profile_id": "voice_abc",
                "avatar_profile_id": "avatar_def",
                "template_id": "template_001",
            },
            "output_profile": {"duration_target_sec": 60, "aspect_ratio": "9:16"},
        },
    ).json()
    pipeline = GenerationPipeline(store, data_dir=tmp_path / "media", cosyvoice=StubCosyVoice())
    pipeline._render_with_remotion = failing_render  # type: ignore[method-assign]

    started = pipeline.start("tenant_123", job["job_id"])

    assert started["state"] == "failed"
    assert started["active_stage"] == "scene_render"
    qc = store.list_qc_reports("tenant_123", job["job_id"])
    assert qc[0]["failure_codes"] == ["renderer_runtime_error"]


class StubCosyVoice(CosyVoiceAdapter):
    def synthesize(self, *, job, output_dir):  # type: ignore[no-untyped-def]
        audio_path = output_dir / "voice.wav"
        audio_path.write_bytes(b"fake wav")
        return audio_path


def failing_render(*_args, **_kwargs):  # type: ignore[no-untyped-def]
    raise RuntimeError("remotion render failed")
