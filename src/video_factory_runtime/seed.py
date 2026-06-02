"""Local seed data for TASK-011 runtime foundation."""

from __future__ import annotations

from copy import deepcopy

from video_factory_runtime.domain import Asset
from video_factory_runtime.repositories import InMemoryAssetRepository, InMemoryJobRepository
from video_factory_runtime.service import JobIntakeService

DEFAULT_TENANT_ID = "tenant_123"
DEFAULT_USER_ID = "user_456"

SAMPLE_CREATE_JOB_REQUEST = {
    "input": {
        "type": "opinion",
        "text": "企业级自动口播视频的关键不是一次生成，而是可恢复的流水线。",
    },
    "asset_refs": {
        "voice_profile_id": "voice_abc",
        "avatar_profile_id": "avatar_def",
        "brand_kit_id": "brand_001",
        "music_asset_id": "music_001",
        "template_id": "template_001",
    },
    "output_profile": {
        "duration_target_sec": 60,
        "aspect_ratio": "9:16",
    },
}


def sample_create_job_request() -> dict:
    """Return a mutable copy of the local sample job request."""
    return deepcopy(SAMPLE_CREATE_JOB_REQUEST)


def seed_assets() -> list[Asset]:
    """Return deterministic local assets for API smoke tests."""
    return [
        Asset(
            asset_id="voice_abc",
            tenant_id=DEFAULT_TENANT_ID,
            asset_type="voice_profile",
            state="active",
            authorization_snapshots=("consent_evt_voice_abc_v1",),
            display_name="Authorized narrator voice",
        ),
        Asset(
            asset_id="avatar_def",
            tenant_id=DEFAULT_TENANT_ID,
            asset_type="avatar_profile",
            state="active",
            authorization_snapshots=("consent_evt_avatar_def_v1",),
            display_name="Authorized presenter avatar",
        ),
        Asset(
            asset_id="brand_001",
            tenant_id=DEFAULT_TENANT_ID,
            asset_type="brand_kit",
            state="active",
            display_name="Default brand kit",
        ),
        Asset(
            asset_id="music_001",
            tenant_id=DEFAULT_TENANT_ID,
            asset_type="music_asset",
            state="active",
            display_name="Licensed background music",
        ),
        Asset(
            asset_id="template_001",
            tenant_id=DEFAULT_TENANT_ID,
            asset_type="template",
            state="active",
            display_name="Vertical talking-head template",
        ),
        Asset(
            asset_id="voice_no_consent",
            tenant_id=DEFAULT_TENANT_ID,
            asset_type="voice_profile",
            state="active",
            authorization_snapshots=(),
            display_name="Invalid voice missing consent",
        ),
        Asset(
            asset_id="avatar_revoked",
            tenant_id=DEFAULT_TENANT_ID,
            asset_type="avatar_profile",
            state="revoked",
            authorization_snapshots=("consent_evt_avatar_revoked_v1",),
            display_name="Revoked avatar",
        ),
        Asset(
            asset_id="voice_other_tenant",
            tenant_id="tenant_other",
            asset_type="voice_profile",
            state="active",
            authorization_snapshots=("consent_evt_other_tenant_v1",),
            display_name="Cross-tenant voice",
        ),
    ]


def create_default_service() -> JobIntakeService:
    """Create the default local job-intake service."""
    return JobIntakeService(
        asset_repository=InMemoryAssetRepository(seed_assets()),
        job_repository=InMemoryJobRepository(),
    )
