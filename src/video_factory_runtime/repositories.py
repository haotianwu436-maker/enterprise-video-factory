"""Repository interfaces and in-memory implementations."""

from __future__ import annotations

from collections.abc import Iterable
from threading import Lock
from typing import Protocol

from video_factory_runtime.domain import Asset, Job


class AssetRepository(Protocol):
    """Read model for governed assets."""

    def get(self, tenant_id: str, asset_id: str) -> Asset | None:
        """Return a tenant-scoped asset by id."""


class JobRepository(Protocol):
    """Write model for jobs created by intake."""

    def next_job_id(self) -> str:
        """Return the next deterministic local job id."""

    def next_audit_event_id(self) -> str:
        """Return the next deterministic local audit event id."""

    def save(self, job: Job) -> None:
        """Persist a job."""

    def get(self, tenant_id: str, job_id: str) -> Job | None:
        """Return a tenant-scoped job."""


class InMemoryAssetRepository:
    """In-memory asset registry for TASK-011 local runtime and tests."""

    def __init__(self, assets: Iterable[Asset] = ()) -> None:
        self._assets = {(asset.tenant_id, asset.asset_id): asset for asset in assets}

    def get(self, tenant_id: str, asset_id: str) -> Asset | None:
        return self._assets.get((tenant_id, asset_id))


class InMemoryJobRepository:
    """In-memory job store with deterministic ids for local testing."""

    def __init__(self) -> None:
        self._jobs: dict[tuple[str, str], Job] = {}
        self._job_sequence = 0
        self._audit_sequence = 0
        self._lock = Lock()

    def next_job_id(self) -> str:
        with self._lock:
            self._job_sequence += 1
            return f"job_{self._job_sequence:06d}"

    def next_audit_event_id(self) -> str:
        with self._lock:
            self._audit_sequence += 1
            return f"audit_evt_{self._audit_sequence:06d}"

    def save(self, job: Job) -> None:
        with self._lock:
            self._jobs[(job.tenant_id, job.job_id)] = job

    def get(self, tenant_id: str, job_id: str) -> Job | None:
        return self._jobs.get((tenant_id, job_id))
