"""Job intake application service."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from video_factory_contracts import ContractVocabulary, load_contract_vocabulary
from video_factory_runtime.domain import (
    ActorContext,
    Asset,
    AssetBinding,
    IntakeViolation,
    Job,
    JobIntakeRejected,
)
from video_factory_runtime.repositories import AssetRepository, JobRepository

INITIAL_JOB_STATE = "created"
VALIDATED_JOB_STATE = "validated"
SOURCE_INTAKE_STAGE = "source_intake"
ACTIVE_ASSET_STATE = "active"

ASSET_FIELD_TYPES = {
    "voice_profile_id": "voice_profile",
    "avatar_profile_id": "avatar_profile",
    "brand_kit_id": "brand_kit",
    "music_asset_id": "music_asset",
    "template_id": "template",
}
ASSET_FIELD_ROLES = {
    "voice_profile_id": "narrator",
    "avatar_profile_id": "presenter",
    "brand_kit_id": "brand",
    "music_asset_id": "music",
    "template_id": "layout",
}
IDENTITY_ASSET_FIELDS = {"voice_profile_id", "avatar_profile_id"}
REQUIRED_ASSET_FIELDS = ("voice_profile_id", "avatar_profile_id")
REQUEST_TOP_LEVEL_FIELDS = {"input", "asset_refs", "output_profile"}
INPUT_FIELDS = {"type", "text"}
OUTPUT_PROFILE_FIELDS = {"duration_target_sec", "aspect_ratio"}
MISSING_ASSET_FAILURES = {
    "voice_profile_id": "voice_profile_missing",
    "avatar_profile_id": "avatar_profile_missing",
}


class JobIntakeService:
    """Validate and create video-generation jobs."""

    def __init__(
        self,
        *,
        asset_repository: AssetRepository,
        job_repository: JobRepository,
        vocabulary: ContractVocabulary | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.asset_repository = asset_repository
        self.job_repository = job_repository
        self.vocabulary = vocabulary or load_contract_vocabulary()
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self._assert_runtime_terms_are_contract_terms()

    def create_job(self, payload: Any, actor: ActorContext) -> Job:
        """Create a job after deterministic request and authorization checks."""
        violations: list[IntakeViolation] = []
        if not isinstance(payload, dict):
            violations.append(self._violation("body", "must be a JSON object", "scene_dsl_invalid"))
            raise JobIntakeRejected(violations)

        self._validate_unknown_fields(payload, "", REQUEST_TOP_LEVEL_FIELDS, violations)

        input_payload = self._object(payload.get("input"), "input", violations)
        asset_refs = self._object(payload.get("asset_refs"), "asset_refs", violations)
        output_profile = self._object(payload.get("output_profile"), "output_profile", violations)

        input_type = self._validate_input(input_payload, violations)
        duration_target_sec, aspect_ratio = self._validate_output_profile(output_profile, violations)
        bindings = self._validate_asset_refs(asset_refs, actor, violations)

        if actor.role not in {"creator", "tenant_admin"}:
            violations.append(
                self._violation(
                    "actor.role",
                    "role must be creator or tenant_admin to create jobs",
                    "tenant_scope_violation",
                )
            )

        if violations:
            raise JobIntakeRejected(violations)

        now = self.clock()
        job_id = self.job_repository.next_job_id()
        audit_event_ids = (
            self.job_repository.next_audit_event_id(),
            self.job_repository.next_audit_event_id(),
        )
        authorization_snapshots = tuple(
            binding.authorization_snapshot
            for binding in bindings
            if binding.authorization_snapshot is not None
        )
        job = Job(
            job_id=job_id,
            tenant_id=actor.tenant_id,
            state=VALIDATED_JOB_STATE,
            active_stage=SOURCE_INTAKE_STAGE,
            input_type=input_type,
            input_text=str(input_payload["text"]).strip(),
            duration_target_sec=duration_target_sec,
            aspect_ratio=aspect_ratio,
            asset_bindings=tuple(bindings),
            asset_authorization_snapshots=authorization_snapshots,
            state_history=(INITIAL_JOB_STATE, VALIDATED_JOB_STATE),
            audit_event_ids=audit_event_ids,
            created_at=now,
            updated_at=now,
        )
        self.job_repository.save(job)
        return job

    def get_job(self, tenant_id: str, job_id: str) -> Job | None:
        """Return a tenant-scoped job by id."""
        return self.job_repository.get(tenant_id, job_id)

    def _validate_input(self, input_payload: dict[str, Any], violations: list[IntakeViolation]) -> str:
        self._validate_unknown_fields(input_payload, "input", INPUT_FIELDS, violations)
        input_type = input_payload.get("type")
        text = input_payload.get("text")
        if not isinstance(input_type, str) or input_type not in self.vocabulary.create_job_input_types:
            violations.append(
                self._violation(
                    "input.type",
                    f"type must be one of {list(self.vocabulary.create_job_input_types)}",
                    "scene_dsl_invalid",
                )
            )
        if not isinstance(text, str) or not text.strip():
            violations.append(
                self._violation("input.text", "text must be a non-empty string", "scene_dsl_invalid")
            )
        return input_type if isinstance(input_type, str) else ""

    def _validate_output_profile(
        self,
        output_profile: dict[str, Any],
        violations: list[IntakeViolation],
    ) -> tuple[int, str]:
        self._validate_unknown_fields(output_profile, "output_profile", OUTPUT_PROFILE_FIELDS, violations)
        duration = output_profile.get("duration_target_sec")
        aspect_ratio = output_profile.get("aspect_ratio")
        if not isinstance(duration, int) or not 30 <= duration <= 90:
            violations.append(
                self._violation(
                    "output_profile.duration_target_sec",
                    "duration_target_sec must be an integer from 30 to 90",
                    "scene_dsl_invalid",
                )
            )
        if (
            not isinstance(aspect_ratio, str)
            or aspect_ratio not in self.vocabulary.supported_aspect_ratios
        ):
            violations.append(
                self._violation(
                    "output_profile.aspect_ratio",
                    f"aspect_ratio must be one of {list(self.vocabulary.supported_aspect_ratios)}",
                    "scene_dsl_invalid",
                )
            )
        return duration if isinstance(duration, int) else 0, aspect_ratio if isinstance(aspect_ratio, str) else ""

    def _validate_asset_refs(
        self,
        asset_refs: dict[str, Any],
        actor: ActorContext,
        violations: list[IntakeViolation],
    ) -> list[AssetBinding]:
        self._validate_unknown_fields(asset_refs, "asset_refs", set(ASSET_FIELD_TYPES), violations)
        bindings: list[AssetBinding] = []
        for field in REQUIRED_ASSET_FIELDS:
            if not isinstance(asset_refs.get(field), str) or not asset_refs.get(field).strip():
                violations.append(
                    self._violation(
                        f"asset_refs.{field}",
                        f"{field} is required",
                        MISSING_ASSET_FAILURES[field],
                    )
                )
        for field, expected_type in ASSET_FIELD_TYPES.items():
            asset_id = asset_refs.get(field)
            if not isinstance(asset_id, str) or not asset_id.strip():
                continue
            asset = self.asset_repository.get(actor.tenant_id, asset_id)
            binding = self._validate_asset(field, expected_type, asset_id, asset, actor, violations)
            if binding:
                bindings.append(binding)
        return bindings

    def _validate_asset(
        self,
        field: str,
        expected_type: str,
        asset_id: str,
        asset: Asset | None,
        actor: ActorContext,
        violations: list[IntakeViolation],
    ) -> AssetBinding | None:
        if asset is None:
            violations.append(
                self._violation(
                    f"asset_refs.{field}",
                    f"asset {asset_id!r} was not found",
                    MISSING_ASSET_FAILURES.get(field, "asset_not_authorized"),
                )
            )
            return None
        if asset.asset_type != expected_type:
            violations.append(
                self._violation(
                    f"asset_refs.{field}",
                    f"asset type must be {expected_type}",
                    "asset_not_authorized",
                )
            )
            return None
        if asset.state != ACTIVE_ASSET_STATE:
            violations.append(
                self._violation(
                    f"asset_refs.{field}",
                    f"asset must be {ACTIVE_ASSET_STATE}",
                    "template_not_approved" if expected_type == "template" else "asset_not_authorized",
                )
            )
            return None
        authorization_snapshot = asset.latest_authorization_snapshot()
        if field in IDENTITY_ASSET_FIELDS and authorization_snapshot is None:
            violations.append(
                self._violation(
                    f"asset_refs.{field}",
                    "identity asset is missing authorization snapshot",
                    "asset_not_authorized",
                )
            )
            return None
        return AssetBinding(
            request_field=field,
            asset_id=asset.asset_id,
            asset_type=asset.asset_type,
            role=ASSET_FIELD_ROLES[field],
            authorization_snapshot=authorization_snapshot,
        )

    def _object(
        self,
        value: Any,
        field: str,
        violations: list[IntakeViolation],
    ) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        violations.append(self._violation(field, "must be an object", "scene_dsl_invalid"))
        return {}

    def _validate_unknown_fields(
        self,
        payload: dict[str, Any],
        prefix: str,
        allowed: set[str],
        violations: list[IntakeViolation],
    ) -> None:
        for field in sorted(set(payload) - allowed):
            dotted = f"{prefix}.{field}" if prefix else field
            violations.append(
                self._violation(dotted, "field is not part of the accepted contract", "scene_dsl_invalid")
            )

    def _violation(self, field: str, message: str, failure_code: str) -> IntakeViolation:
        if failure_code not in self.vocabulary.failure_codes:
            raise RuntimeError(f"runtime failure code {failure_code!r} is not in accepted contract")
        return IntakeViolation(field=field, message=message, failure_code=failure_code)

    def _assert_runtime_terms_are_contract_terms(self) -> None:
        required_terms = {
            "job_states": (INITIAL_JOB_STATE, VALIDATED_JOB_STATE),
            "manifest_stages": (SOURCE_INTAKE_STAGE,),
            "asset_states": (ACTIVE_ASSET_STATE,),
            "asset_types": tuple(ASSET_FIELD_TYPES.values()),
        }
        for category, values in required_terms.items():
            accepted = set(getattr(self.vocabulary, category))
            missing = sorted(set(values) - accepted)
            if missing:
                raise RuntimeError(f"runtime {category} terms missing from accepted contracts: {missing}")
