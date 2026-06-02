"""Domain objects for the runtime foundation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ActorContext:
    """Tenant-scoped caller context used by the product API."""

    tenant_id: str
    user_id: str
    role: str


@dataclass(frozen=True)
class Asset:
    """Governed asset metadata required before generation can start."""

    asset_id: str
    tenant_id: str
    asset_type: str
    state: str
    authorization_snapshots: tuple[str, ...] = ()
    display_name: str | None = None

    def latest_authorization_snapshot(self) -> str | None:
        return self.authorization_snapshots[-1] if self.authorization_snapshots else None


@dataclass(frozen=True)
class AssetBinding:
    """Asset bound to a job after tenant and authorization checks."""

    request_field: str
    asset_id: str
    asset_type: str
    role: str
    authorization_snapshot: str | None

    def to_api(self) -> dict[str, Any]:
        return {
            "request_field": self.request_field,
            "asset_id": self.asset_id,
            "asset_type": self.asset_type,
            "role": self.role,
            "authorization_snapshot": self.authorization_snapshot,
        }


@dataclass(frozen=True)
class JobProgress:
    """Initial job progress envelope exposed by the API."""

    segments_total: int = 0
    segments_completed: int = 0
    repair_attempts: int = 0

    def to_api(self) -> dict[str, int]:
        return {
            "segments_total": self.segments_total,
            "segments_completed": self.segments_completed,
            "repair_attempts": self.repair_attempts,
        }


@dataclass(frozen=True)
class Job:
    """Video generation job after intake validation."""

    job_id: str
    tenant_id: str
    state: str
    active_stage: str
    input_type: str
    input_text: str
    duration_target_sec: int
    aspect_ratio: str
    asset_bindings: tuple[AssetBinding, ...]
    asset_authorization_snapshots: tuple[str, ...]
    state_history: tuple[str, ...]
    audit_event_ids: tuple[str, ...]
    created_at: datetime
    updated_at: datetime
    progress: JobProgress = field(default_factory=JobProgress)

    def to_api(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "tenant_id": self.tenant_id,
            "state": self.state,
            "active_stage": self.active_stage,
            "progress": self.progress.to_api(),
            "asset_authorization_snapshots": list(self.asset_authorization_snapshots),
            "asset_bindings": [binding.to_api() for binding in self.asset_bindings],
            "state_history": list(self.state_history),
            "audit_event_ids": list(self.audit_event_ids),
            "links": {
                "self": f"/v1/jobs/{self.job_id}",
                "artifacts": f"/v1/jobs/{self.job_id}/artifacts",
                "qc": f"/v1/jobs/{self.job_id}/qc",
            },
        }


@dataclass(frozen=True)
class Artifact:
    """Stored output metadata exposed by artifact APIs in later tasks."""

    artifact_id: str
    job_id: str
    stage: str
    manifest_uri: str
    qc_status: str | None = None
    segment_id: str | None = None
    attempt: int = 1
    signed_url_available: bool = False


@dataclass(frozen=True)
class QcReport:
    """Quality report envelope for future QC implementation."""

    qc_report_id: str
    job_id: str
    stage: str
    status: str
    failure_codes: tuple[str, ...] = ()
    segment_id: str | None = None


@dataclass(frozen=True)
class ReviewItem:
    """Manual review item state exposed by review APIs in later tasks."""

    review_id: str
    tenant_id: str
    job_id: str
    state: str
    reason_code: str
    opened_by: str
    opened_at: datetime
    evidence_refs: tuple[str, ...]
    decision: str | None = None
    decided_by: str | None = None
    decided_at: datetime | None = None


@dataclass(frozen=True)
class IntakeViolation:
    """Deterministic intake validation error."""

    field: str
    message: str
    failure_code: str

    def to_api(self) -> dict[str, str]:
        return {
            "field": self.field,
            "message": self.message,
            "failure_code": self.failure_code,
        }


class JobIntakeRejected(ValueError):
    """Raised when an intake request cannot be accepted."""

    def __init__(self, violations: list[IntakeViolation]) -> None:
        self.violations = violations
        super().__init__("job intake request rejected")

    @property
    def status_code(self) -> int:
        authorization_codes = {
            "asset_not_authorized",
            "consent_expired",
            "tenant_scope_violation",
        }
        if any(violation.failure_code in authorization_codes for violation in self.violations):
            return 403
        return 422

    def to_api(self) -> dict[str, Any]:
        return {"violations": [violation.to_api() for violation in self.violations]}
