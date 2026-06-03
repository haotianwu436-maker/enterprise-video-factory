"""SQLite runtime store for local product slices."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from video_factory_runtime.auth import User, hash_password
from video_factory_runtime.domain import Asset, AssetBinding, Job, JobProgress
from video_factory_runtime.repositories import AssetRepository, JobRepository
from video_factory_runtime.seed import DEFAULT_TENANT_ID, DEFAULT_USER_ID, seed_assets

DEFAULT_DATA_DIR = Path("var/video_factory")


class SQLiteRuntimeStore(AssetRepository, JobRepository):
    """SQLite-backed metadata store for local runtime use."""

    def __init__(self, path: Path | str = DEFAULT_DATA_DIR / "runtime.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate()
        self.seed_defaults()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _migrate(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                create table if not exists users (
                  user_id text primary key,
                  tenant_id text not null,
                  email text not null unique,
                  role text not null,
                  password_hash text not null,
                  salt text not null
                );
                create table if not exists assets (
                  tenant_id text not null,
                  asset_id text not null,
                  asset_type text not null,
                  state text not null,
                  display_name text,
                  authorization_snapshots text not null,
                  file_uri text,
                  created_at text not null,
                  updated_at text not null,
                  primary key (tenant_id, asset_id)
                );
                create table if not exists consent_events (
                  tenant_id text not null,
                  consent_event_id text primary key,
                  asset_id text not null,
                  scope text not null,
                  evidence_uri text not null,
                  granted_by text not null,
                  granted_at text not null
                );
                create table if not exists jobs (
                  tenant_id text not null,
                  job_id text not null,
                  payload text not null,
                  created_at text not null,
                  updated_at text not null,
                  primary key (tenant_id, job_id)
                );
                create table if not exists artifacts (
                  tenant_id text not null,
                  artifact_id text primary key,
                  job_id text not null,
                  stage text not null,
                  manifest_uri text not null,
                  qc_status text,
                  file_uri text,
                  created_at text not null
                );
                create table if not exists qc_reports (
                  tenant_id text not null,
                  qc_report_id text primary key,
                  job_id text not null,
                  stage text not null,
                  status text not null,
                  failure_codes text not null,
                  message text not null,
                  created_at text not null
                );
                create table if not exists counters (
                  name text primary key,
                  value integer not null
                );
                """
            )

    def seed_defaults(self) -> None:
        password_hash, salt = hash_password("factory-demo")
        with self._connect() as conn:
            conn.execute(
                """
                insert or ignore into users
                (user_id, tenant_id, email, role, password_hash, salt)
                values (?, ?, ?, ?, ?, ?)
                """,
                (DEFAULT_USER_ID, DEFAULT_TENANT_ID, "creator@example.local", "creator", password_hash, salt),
            )
            for asset in seed_assets():
                conn.execute(
                    """
                    insert or ignore into assets
                    (tenant_id, asset_id, asset_type, state, display_name, authorization_snapshots, file_uri, created_at, updated_at)
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        asset.tenant_id,
                        asset.asset_id,
                        asset.asset_type,
                        asset.state,
                        asset.display_name,
                        json.dumps(list(asset.authorization_snapshots)),
                        None,
                        _now(),
                        _now(),
                    ),
                )

    def find_user_by_email(self, email: str) -> User | None:
        with self._connect() as conn:
            row = conn.execute("select * from users where email = ?", (email,)).fetchone()
        return _user_from_row(row) if row else None

    def get_user(self, user_id: str) -> User | None:
        with self._connect() as conn:
            row = conn.execute("select * from users where user_id = ?", (user_id,)).fetchone()
        return _user_from_row(row) if row else None

    def get_asset(self, tenant_id: str, asset_id: str) -> Asset | None:
        with self._connect() as conn:
            row = conn.execute(
                "select * from assets where tenant_id = ? and asset_id = ?",
                (tenant_id, asset_id),
            ).fetchone()
        return _asset_from_row(row) if row else None

    def list_assets(self, tenant_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "select * from assets where tenant_id = ? order by created_at desc",
                (tenant_id,),
            ).fetchall()
        return [_asset_api(row) for row in rows]

    def create_asset(
        self,
        *,
        tenant_id: str,
        asset_type: str,
        display_name: str,
        file_uri: str | None,
    ) -> dict[str, Any]:
        asset_id = f"{asset_type}_{self._next_counter('asset'):06d}"
        state = "pending_consent" if asset_type in {"voice_profile", "avatar_profile"} else "active"
        with self._connect() as conn:
            conn.execute(
                """
                insert into assets
                (tenant_id, asset_id, asset_type, state, display_name, authorization_snapshots, file_uri, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (tenant_id, asset_id, asset_type, state, display_name, "[]", file_uri, _now(), _now()),
            )
        asset = self.get_asset(tenant_id, asset_id)
        return asset_to_api(asset, file_uri=file_uri) if asset else {}

    def attach_consent(
        self,
        tenant_id: str,
        asset_id: str,
        *,
        payload: dict[str, Any],
        actor_user_id: str,
    ) -> dict[str, Any]:
        asset = self.get_asset(tenant_id, asset_id)
        if not asset:
            raise KeyError(asset_id)
        consent_id = f"consent_evt_{self._next_counter('consent'):06d}"
        snapshots = list(asset.authorization_snapshots) + [consent_id]
        state = "consent_verified" if asset.asset_type in {"voice_profile", "avatar_profile"} else asset.state
        granted_at = _now()
        with self._connect() as conn:
            conn.execute(
                """
                insert into consent_events
                (tenant_id, consent_event_id, asset_id, scope, evidence_uri, granted_by, granted_at)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tenant_id,
                    consent_id,
                    asset_id,
                    json.dumps(payload["scope"], ensure_ascii=False),
                    str(payload["evidence_uri"]),
                    actor_user_id,
                    granted_at,
                ),
            )
            conn.execute(
                """
                update assets
                set authorization_snapshots = ?, state = ?, updated_at = ?
                where tenant_id = ? and asset_id = ?
                """,
                (json.dumps(snapshots), state, _now(), tenant_id, asset_id),
            )
        return {
            "consent_event_id": consent_id,
            "asset_id": asset_id,
            "scope": payload["scope"],
            "evidence_uri": str(payload["evidence_uri"]),
            "granted_by": actor_user_id,
            "granted_at": granted_at,
        }

    def activate_asset(self, tenant_id: str, asset_id: str) -> dict[str, Any]:
        asset = self.get_asset(tenant_id, asset_id)
        if not asset:
            raise KeyError(asset_id)
        if asset.asset_type in {"voice_profile", "avatar_profile"} and not asset.authorization_snapshots:
            raise ValueError("identity asset requires consent before activation")
        with self._connect() as conn:
            conn.execute(
                "update assets set state = ?, updated_at = ? where tenant_id = ? and asset_id = ?",
                ("active", _now(), tenant_id, asset_id),
            )
            row = conn.execute(
                "select * from assets where tenant_id = ? and asset_id = ?",
                (tenant_id, asset_id),
            ).fetchone()
        return _asset_api(row) if row else {}

    def next_job_id(self) -> str:
        return f"job_{self._next_counter('job'):06d}"

    def next_audit_event_id(self) -> str:
        return f"audit_evt_{self._next_counter('audit'):06d}"

    def save(self, job: Job) -> None:
        payload = job_to_dict(job)
        with self._connect() as conn:
            conn.execute(
                """
                insert into jobs (tenant_id, job_id, payload, created_at, updated_at)
                values (?, ?, ?, ?, ?)
                on conflict(tenant_id, job_id) do update set payload = excluded.payload, updated_at = excluded.updated_at
                """,
                (job.tenant_id, job.job_id, json.dumps(payload, ensure_ascii=False), payload["created_at"], payload["updated_at"]),
            )

    def get_job(self, tenant_id: str, job_id: str) -> Job | None:
        with self._connect() as conn:
            row = conn.execute(
                "select payload from jobs where tenant_id = ? and job_id = ?",
                (tenant_id, job_id),
            ).fetchone()
        return job_from_dict(json.loads(row["payload"])) if row else None

    def get(self, tenant_id: str, asset_or_job_id: str) -> Asset | Job | None:  # type: ignore[override]
        if asset_or_job_id.startswith("job_"):
            return self.get_job(tenant_id, asset_or_job_id)
        return self.get_asset(tenant_id, asset_or_job_id)

    def list_jobs(self, tenant_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "select payload from jobs where tenant_id = ? order by created_at desc",
                (tenant_id,),
            ).fetchall()
        return [job_from_dict(json.loads(row["payload"])).to_api() for row in rows]

    def save_artifact(self, tenant_id: str, artifact: dict[str, Any]) -> dict[str, Any]:
        artifact_id = artifact.get("artifact_id") or f"artifact_{self._next_counter('artifact'):06d}"
        record = {**artifact, "artifact_id": artifact_id}
        with self._connect() as conn:
            conn.execute(
                """
                insert or replace into artifacts
                (tenant_id, artifact_id, job_id, stage, manifest_uri, qc_status, file_uri, created_at)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tenant_id,
                    artifact_id,
                    record["job_id"],
                    record["stage"],
                    record["manifest_uri"],
                    record.get("qc_status"),
                    record.get("file_uri"),
                    _now(),
                ),
            )
        return record

    def list_artifacts(self, tenant_id: str, job_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "select * from artifacts where tenant_id = ? and job_id = ? order by created_at",
                (tenant_id, job_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_artifact(self, tenant_id: str, artifact_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "select * from artifacts where tenant_id = ? and artifact_id = ?",
                (tenant_id, artifact_id),
            ).fetchone()
        return dict(row) if row else None

    def save_qc_report(self, tenant_id: str, report: dict[str, Any]) -> dict[str, Any]:
        report_id = report.get("qc_report_id") or f"qc_{self._next_counter('qc'):06d}"
        record = {**report, "qc_report_id": report_id}
        with self._connect() as conn:
            conn.execute(
                """
                insert or replace into qc_reports
                (tenant_id, qc_report_id, job_id, stage, status, failure_codes, message, created_at)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tenant_id,
                    report_id,
                    record["job_id"],
                    record["stage"],
                    record["status"],
                    json.dumps(record.get("failure_codes", [])),
                    record.get("message", ""),
                    _now(),
                ),
            )
        return record

    def list_qc_reports(self, tenant_id: str, job_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "select * from qc_reports where tenant_id = ? and job_id = ? order by created_at",
                (tenant_id, job_id),
            ).fetchall()
        return [{**dict(row), "failure_codes": json.loads(row["failure_codes"])} for row in rows]

    def _next_counter(self, name: str) -> int:
        with self._connect() as conn:
            row = conn.execute("select value from counters where name = ?", (name,)).fetchone()
            value = int(row["value"]) + 1 if row else 1
            conn.execute(
                "insert into counters (name, value) values (?, ?) on conflict(name) do update set value = excluded.value",
                (name, value),
            )
        return value


def asset_to_api(asset: Asset | None, *, file_uri: str | None = None) -> dict[str, Any]:
    if asset is None:
        return {}
    return {
        "asset_id": asset.asset_id,
        "tenant_id": asset.tenant_id,
        "asset_type": asset.asset_type,
        "state": asset.state,
        "display_name": asset.display_name,
        "authorization_snapshots": list(asset.authorization_snapshots),
        "file_uri": file_uri,
    }


def job_to_dict(job: Job) -> dict[str, Any]:
    data = asdict(job)
    data["created_at"] = job.created_at.isoformat()
    data["updated_at"] = job.updated_at.isoformat()
    return data


def job_from_dict(data: dict[str, Any]) -> Job:
    bindings = tuple(AssetBinding(**binding) for binding in data["asset_bindings"])
    progress = JobProgress(**data.get("progress", {}))
    return Job(
        job_id=data["job_id"],
        tenant_id=data["tenant_id"],
        state=data["state"],
        active_stage=data["active_stage"],
        input_type=data["input_type"],
        input_text=data["input_text"],
        duration_target_sec=int(data["duration_target_sec"]),
        aspect_ratio=data["aspect_ratio"],
        asset_bindings=bindings,
        asset_authorization_snapshots=tuple(data["asset_authorization_snapshots"]),
        state_history=tuple(data["state_history"]),
        audit_event_ids=tuple(data["audit_event_ids"]),
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
        progress=progress,
    )


def _asset_from_row(row: sqlite3.Row | None) -> Asset | None:
    if row is None:
        return None
    return Asset(
        asset_id=row["asset_id"],
        tenant_id=row["tenant_id"],
        asset_type=row["asset_type"],
        state=row["state"],
        authorization_snapshots=tuple(json.loads(row["authorization_snapshots"])),
        display_name=row["display_name"],
    )


def _asset_api(row: sqlite3.Row) -> dict[str, Any]:
    asset = _asset_from_row(row)
    return asset_to_api(asset, file_uri=row["file_uri"])


def _user_from_row(row: sqlite3.Row) -> User:
    return User(
        user_id=row["user_id"],
        tenant_id=row["tenant_id"],
        email=row["email"],
        role=row["role"],
        password_hash=row["password_hash"],
        salt=row["salt"],
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
