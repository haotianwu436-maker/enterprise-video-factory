"""Accepted contract vocabulary accessors.

Runtime code imports this module instead of copying state strings from docs.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from video_factory_contracts.validation import ContractDocs, load_yaml


@dataclass(frozen=True)
class ContractVocabulary:
    """Vocabulary loaded from accepted repository contracts."""

    job_states: tuple[str, ...]
    segment_states: tuple[str, ...]
    manifest_stages: tuple[str, ...]
    asset_types: tuple[str, ...]
    asset_states: tuple[str, ...]
    qc_statuses: tuple[str, ...]
    review_states: tuple[str, ...]
    review_reason_codes: tuple[str, ...]
    release_states: tuple[str, ...]
    failure_codes: tuple[str, ...]
    audit_event_types: tuple[str, ...]
    create_job_input_types: tuple[str, ...]
    supported_aspect_ratios: tuple[str, ...]

    def contains(self, category: str, value: str) -> bool:
        """Return whether a value is part of a named vocabulary category."""
        values = getattr(self, category)
        return value in values


def default_repo_root() -> Path:
    """Return the source checkout root for the installed editable package."""
    return Path(__file__).resolve().parents[2]


def load_contract_vocabulary(repo: Path | None = None) -> ContractVocabulary:
    """Load vocabulary from accepted docs and OpenAPI contracts."""
    return _load_contract_vocabulary((repo or default_repo_root()).resolve())


@lru_cache(maxsize=8)
def _load_contract_vocabulary(repo: Path) -> ContractVocabulary:
    docs = ContractDocs(repo)
    schemas = _openapi_schemas(repo)
    return ContractVocabulary(
        job_states=tuple(docs.job_states()),
        segment_states=tuple(docs.segment_states()),
        manifest_stages=tuple(docs.manifest_stages()),
        asset_types=tuple(_schema_enum(schemas, "Asset", "asset_type")),
        asset_states=tuple(docs.asset_states()),
        qc_statuses=tuple(docs.qc_statuses()),
        review_states=tuple(docs.review_states()),
        review_reason_codes=tuple(docs.review_reason_codes()),
        release_states=tuple(docs.release_states()),
        failure_codes=tuple(docs.failure_codes()),
        audit_event_types=tuple(docs.audit_event_types()),
        create_job_input_types=tuple(_create_job_input_types(schemas)),
        supported_aspect_ratios=tuple(_output_profile_aspect_ratios(schemas)),
    )


def _openapi_schemas(repo: Path) -> dict[str, Any]:
    openapi = load_yaml(repo / "openapi" / "enterprise-video-factory.openapi.yaml")
    return openapi.get("components", {}).get("schemas", {})


def _schema_enum(schemas: dict[str, Any], schema_name: str, property_name: str) -> list[str]:
    values = (
        schemas.get(schema_name, {})
        .get("properties", {})
        .get(property_name, {})
        .get("enum", [])
    )
    return list(values)


def _create_job_input_types(schemas: dict[str, Any]) -> list[str]:
    return (
        schemas.get("CreateJobRequest", {})
        .get("properties", {})
        .get("input", {})
        .get("properties", {})
        .get("type", {})
        .get("enum", [])
    )


def _output_profile_aspect_ratios(schemas: dict[str, Any]) -> list[str]:
    return (
        schemas.get("CreateJobRequest", {})
        .get("properties", {})
        .get("output_profile", {})
        .get("properties", {})
        .get("aspect_ratio", {})
        .get("enum", [])
    )
