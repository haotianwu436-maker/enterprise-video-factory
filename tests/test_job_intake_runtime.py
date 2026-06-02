from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from video_factory_contracts import load_contract_vocabulary
from video_factory_contracts.validation import ContractDocs, load_yaml
from video_factory_runtime.api import create_app
from video_factory_runtime.cli import main as runtime_cli
from video_factory_runtime.domain import Artifact, QcReport, ReviewItem
from video_factory_runtime.seed import create_default_service, sample_create_job_request, seed_assets
from video_factory_runtime.service import (
    ACTIVE_ASSET_STATE,
    ASSET_FIELD_TYPES,
    INITIAL_JOB_STATE,
    SOURCE_INTAKE_STAGE,
    VALIDATED_JOB_STATE,
)


REPO = Path(__file__).resolve().parents[1]
AUTH_HEADERS = {
    "x-tenant-id": "tenant_123",
    "x-user-id": "user_456",
    "x-role": "creator",
}


def test_create_job_from_opinion_with_authorized_assets() -> None:
    client = TestClient(create_app(create_default_service()))

    response = client.post("/v1/jobs", headers=AUTH_HEADERS, json=sample_create_job_request())

    assert response.status_code == 202
    body = response.json()
    assert body["job_id"] == "job_000001"
    assert body["tenant_id"] == "tenant_123"
    assert body["state"] == "validated"
    assert body["active_stage"] == "source_intake"
    assert body["state_history"] == ["created", "validated"]
    assert body["progress"] == {
        "segments_total": 0,
        "segments_completed": 0,
        "repair_attempts": 0,
    }
    assert body["asset_authorization_snapshots"] == [
        "consent_evt_voice_abc_v1",
        "consent_evt_avatar_def_v1",
    ]
    assert body["links"]["self"] == "/v1/jobs/job_000001"

    get_response = client.get("/v1/jobs/job_000001", headers={"x-tenant-id": "tenant_123"})
    assert get_response.status_code == 200
    assert get_response.json()["job_id"] == "job_000001"


def test_identity_asset_without_authorization_snapshot_is_rejected() -> None:
    client = TestClient(create_app(create_default_service()))
    payload = sample_create_job_request()
    payload["asset_refs"]["voice_profile_id"] = "voice_no_consent"

    response = client.post("/v1/jobs", headers=AUTH_HEADERS, json=payload)

    assert response.status_code == 403
    assert _violations(response.json()) == [
        {
            "field": "asset_refs.voice_profile_id",
            "failure_code": "asset_not_authorized",
            "message": "identity asset is missing authorization snapshot",
        }
    ]


def test_inaccessible_identity_asset_is_rejected_without_binding() -> None:
    client = TestClient(create_app(create_default_service()))
    payload = sample_create_job_request()
    payload["asset_refs"]["voice_profile_id"] = "voice_other_tenant"

    response = client.post("/v1/jobs", headers=AUTH_HEADERS, json=payload)

    assert response.status_code == 422
    assert _violations(response.json())[0]["failure_code"] == "voice_profile_missing"


def test_invalid_output_profile_is_rejected_deterministically() -> None:
    client = TestClient(create_app(create_default_service()))
    payload = sample_create_job_request()
    payload["output_profile"]["aspect_ratio"] = "16:9"
    payload["output_profile"]["duration_target_sec"] = 15

    response = client.post("/v1/jobs", headers=AUTH_HEADERS, json=payload)

    assert response.status_code == 422
    violations = _violations(response.json())
    assert {
        "field": "output_profile.aspect_ratio",
        "failure_code": "scene_dsl_invalid",
        "message": "aspect_ratio must be one of ['9:16']",
    } in violations
    assert {
        "field": "output_profile.duration_target_sec",
        "failure_code": "scene_dsl_invalid",
        "message": "duration_target_sec must be an integer from 30 to 90",
    } in violations


def test_missing_text_and_required_assets_are_rejected_deterministically() -> None:
    client = TestClient(create_app(create_default_service()))
    payload = sample_create_job_request()
    payload["input"]["text"] = " "
    del payload["asset_refs"]["voice_profile_id"]
    del payload["asset_refs"]["avatar_profile_id"]

    response = client.post("/v1/jobs", headers=AUTH_HEADERS, json=payload)

    assert response.status_code == 422
    violations = _violations(response.json())
    assert {
        "field": "input.text",
        "failure_code": "scene_dsl_invalid",
        "message": "text must be a non-empty string",
    } in violations
    assert {
        "field": "asset_refs.voice_profile_id",
        "failure_code": "voice_profile_missing",
        "message": "voice_profile_id is required",
    } in violations
    assert {
        "field": "asset_refs.avatar_profile_id",
        "failure_code": "avatar_profile_missing",
        "message": "avatar_profile_id is required",
    } in violations


def test_top_level_non_object_body_uses_runtime_error_envelope() -> None:
    client = TestClient(create_app(create_default_service()))

    response = client.post("/v1/jobs", headers=AUTH_HEADERS, json=["not", "an", "object"])

    assert response.status_code == 422
    assert _violations(response.json()) == [
        {
            "field": "body",
            "failure_code": "scene_dsl_invalid",
            "message": "must be a JSON object",
        }
    ]


def test_runtime_vocabulary_matches_accepted_contracts() -> None:
    vocabulary = load_contract_vocabulary(REPO)
    docs = ContractDocs(REPO)
    openapi = load_yaml(REPO / "openapi/enterprise-video-factory.openapi.yaml")
    asset_type_enum = (
        openapi["components"]["schemas"]["Asset"]["properties"]["asset_type"]["enum"]
    )

    assert list(vocabulary.job_states) == docs.job_states()
    assert list(vocabulary.manifest_stages) == docs.manifest_stages()
    assert list(vocabulary.asset_states) == docs.asset_states()
    assert list(vocabulary.qc_statuses) == docs.qc_statuses()
    assert list(vocabulary.review_states) == docs.review_states()
    assert list(vocabulary.failure_codes) == docs.failure_codes()
    assert list(vocabulary.asset_types) == asset_type_enum

    assert INITIAL_JOB_STATE in vocabulary.job_states
    assert VALIDATED_JOB_STATE in vocabulary.job_states
    assert SOURCE_INTAKE_STAGE in vocabulary.manifest_stages
    assert ACTIVE_ASSET_STATE in vocabulary.asset_states
    assert set(ASSET_FIELD_TYPES.values()) <= set(vocabulary.asset_types)
    assert {asset.asset_type for asset in seed_assets()} <= set(vocabulary.asset_types)
    assert {asset.state for asset in seed_assets()} <= set(vocabulary.asset_states)


def test_future_domain_state_models_use_contract_vocabulary_terms() -> None:
    vocabulary = load_contract_vocabulary(REPO)

    artifact = Artifact(
        artifact_id="artifact_001",
        job_id="job_000001",
        stage="source_intake",
        manifest_uri="s3://video-factory/tenant_123/jobs/job_000001/source_intake/manifest.json",
        qc_status="passed",
    )
    qc_report = QcReport(
        qc_report_id="qc_001",
        job_id="job_000001",
        stage="source_intake",
        status="passed",
        failure_codes=("asset_not_authorized",),
    )
    review = ReviewItem(
        review_id="review_001",
        tenant_id="tenant_123",
        job_id="job_000001",
        state="opened",
        reason_code="missing_consent",
        opened_by="system",
        opened_at=datetime.now(timezone.utc),
        evidence_refs=("qc_001",),
    )

    assert artifact.stage in vocabulary.manifest_stages
    assert artifact.qc_status in vocabulary.qc_statuses
    assert qc_report.status in vocabulary.qc_statuses
    assert set(qc_report.failure_codes) <= set(vocabulary.failure_codes)
    assert review.state in vocabulary.review_states
    assert review.reason_code in vocabulary.review_reason_codes


def test_sample_job_cli_outputs_accepted_job(capsys) -> None:
    assert runtime_cli(["--sample-job"]) == 0

    body = json.loads(capsys.readouterr().out)

    assert body["job_id"] == "job_000001"
    assert body["state"] == "validated"
    assert body["active_stage"] == "source_intake"


def _violations(body: dict) -> list[dict]:
    return body["detail"]["violations"]
