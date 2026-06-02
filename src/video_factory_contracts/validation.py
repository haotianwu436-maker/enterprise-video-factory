"""Repository contract validators.

The validators intentionally read accepted contract documents as the source of
truth and compare schema/OpenAPI/examples against those documents.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


@dataclass(frozen=True)
class ValidationIssue:
    """One validation issue."""

    check: str
    path: str
    message: str


@dataclass
class ValidationReport:
    """Aggregated validation report."""

    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)

    def error(self, check: str, path: Path | str, message: str) -> None:
        self.errors.append(ValidationIssue(check, str(path), message))

    def warning(self, check: str, path: Path | str, message: str) -> None:
        self.warnings.append(ValidationIssue(check, str(path), message))

    def pass_check(self, check: str) -> None:
        self.passed_checks.append(check)

    def extend(self, other: "ValidationReport") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.passed_checks.extend(other.passed_checks)

    def render(self) -> str:
        status = "PASS" if not self.errors else "FAIL"
        lines = [
            f"contract validation: {status}",
            f"passed checks: {len(self.passed_checks)}",
            f"errors: {len(self.errors)}",
            f"warnings: {len(self.warnings)}",
        ]
        if self.passed_checks:
            lines.append("")
            lines.append("Passed:")
            lines.extend(f"- {check}" for check in self.passed_checks)
        if self.errors:
            lines.append("")
            lines.append("Errors:")
            lines.extend(f"- [{i.check}] {i.path}: {i.message}" for i in self.errors)
        if self.warnings:
            lines.append("")
            lines.append("Warnings:")
            lines.extend(f"- [{i.check}] {i.path}: {i.message}" for i in self.warnings)
        return "\n".join(lines)


def validate_repo(repo: Path, *, skip_harness: bool = False) -> ValidationReport:
    """Validate all accepted repository contracts."""
    repo = repo.resolve()
    report = ValidationReport()
    report.extend(validate_storyboards(repo))
    report.extend(validate_openapi(repo))
    report.extend(validate_cross_contracts(repo))
    if skip_harness:
        report.warning("harness", repo, "RepoFrame harness check skipped by request.")
    else:
        report.extend(validate_harness(repo))
    return report


def validate_storyboards(repo: Path) -> ValidationReport:
    """Validate Scene Storyboard schema and examples."""
    report = ValidationReport()
    schema_path = repo / "schemas" / "scene-storyboard.schema.json"
    examples_dir = repo / "examples" / "storyboards"

    try:
        schema = load_json(schema_path)
    except Exception as exc:
        report.error("storyboard-schema", schema_path, f"cannot parse JSON schema: {exc}")
        return report

    validator = Draft202012Validator(schema)
    examples = sorted(examples_dir.glob("*.json"))
    if not examples:
        report.error("storyboard-examples", examples_dir, "no storyboard examples found")
        return report

    for path in examples:
        try:
            payload = load_json(path)
        except Exception as exc:
            report.error("storyboard-json", path, f"cannot parse JSON: {exc}")
            continue
        for err in sorted(validator.iter_errors(payload), key=lambda e: list(e.path)):
            pointer = "/".join(str(part) for part in err.path) or "$"
            report.error("storyboard-json-schema", path, f"{pointer}: {err.message}")
        for message in validate_storyboard_payload(payload):
            report.error("storyboard-semantics", path, message)

    if not report.errors:
        report.pass_check(f"storyboard schema and {len(examples)} examples")
    return report


def validate_storyboard_payload(payload: dict[str, Any]) -> list[str]:
    """Return semantic storyboard validation errors for one payload."""
    errors: list[str] = []
    asset_refs = payload.get("asset_refs", [])
    refs = {asset.get("id"): asset for asset in asset_refs}
    if len(refs) != len(asset_refs):
        errors.append("asset_refs contain duplicate ids")

    for asset in asset_refs:
        asset_type = asset.get("asset_type")
        if asset_type in {"voice_profile", "avatar_profile"} and not asset.get(
            "authorization_snapshot"
        ):
            errors.append(f"identity asset {asset.get('id')} is missing authorization_snapshot")
        asset_id = asset.get("asset_id", "")
        if "://" in asset_id or asset_id.startswith("/") or "\\" in asset_id:
            errors.append(f"asset_id {asset_id!r} looks like a path or URL")

    scene_ids: set[str] = set()
    orders: list[int] = []
    total_duration = 0.0
    for scene in payload.get("scenes", []):
        scene_id = scene.get("scene_id", "<missing>")
        if scene_id in scene_ids:
            errors.append(f"scene_id {scene_id!r} is duplicated")
        scene_ids.add(scene_id)
        orders.append(scene.get("order"))
        total_duration += float(scene.get("duration_sec", 0))

        for obj_name, field_name, expected_type in (
            ("voice", "asset_ref", "voice_profile"),
            ("avatar", "asset_ref", "avatar_profile"),
            ("layout", "template_ref", "template"),
            ("music", "asset_ref", "music_asset"),
        ):
            ref_id = scene.get(obj_name, {}).get(field_name)
            asset = refs.get(ref_id)
            if not asset:
                errors.append(f"{scene_id}: missing {obj_name}.{field_name} ref {ref_id!r}")
            elif asset.get("asset_type") != expected_type:
                errors.append(
                    f"{scene_id}: {obj_name}.{field_name} ref {ref_id!r} has "
                    f"type {asset.get('asset_type')!r}, expected {expected_type!r}"
                )

        marked_for_review = bool(
            payload.get("policy", {}).get("manual_review_tags")
            or payload.get("policy", {}).get("policy_tags")
            or scene.get("requires_review")
            or scene.get("policy_tags")
            or scene.get("qc_expectations", {}).get("manual_review_tags")
        )
        script_text = scene.get("script", {}).get("text", "")
        for item in scene.get("visuals", {}).get("emphasis", []):
            text = item.get("text", "")
            if text and text not in script_text and not marked_for_review:
                errors.append(
                    f"{scene_id}: emphasis text {text!r} is not in script and scene is not review-marked"
                )

    expected_orders = list(range(1, len(orders) + 1))
    if orders != expected_orders:
        errors.append(f"scene order must be deterministic 1..n, got {orders!r}")

    target = float(payload.get("video", {}).get("duration_target_sec", 0))
    if abs(total_duration - target) > 1.5:
        errors.append(f"scene durations total {total_duration:g}s, target is {target:g}s")

    for path, key in find_prohibited_keys(payload):
        errors.append(f"prohibited executable field {key!r} at {path}")
    return errors


def validate_openapi(repo: Path) -> ValidationReport:
    """Validate the OpenAPI contract shape against product API docs."""
    report = ValidationReport()
    openapi_path = repo / "openapi" / "enterprise-video-factory.openapi.yaml"
    api_doc = repo / "docs" / "product" / "api-console.md"
    try:
        document = load_yaml(openapi_path)
    except Exception as exc:
        report.error("openapi-yaml", openapi_path, f"cannot parse YAML: {exc}")
        return report

    endpoints = extract_api_endpoints(read_text(api_doc))
    paths = document.get("paths") or {}
    for method, path in sorted(endpoints):
        if path not in paths:
            report.error("openapi-paths", openapi_path, f"missing documented path {path}")
            continue
        if method.lower() not in paths[path]:
            report.error("openapi-methods", openapi_path, f"missing documented method {method} {path}")

    schemas = document.get("components", {}).get("schemas", {})
    required_schemas = {
        "Job",
        "Segment",
        "Artifact",
        "QcReport",
        "RepairRequest",
        "Release",
        "Asset",
        "ReviewItem",
        "AuditEvent",
        "AuditActor",
        "AuditSubject",
    }
    for name in sorted(required_schemas):
        if name not in schemas:
            report.error("openapi-schemas", openapi_path, f"missing schema {name}")

    required_fields = {
        "ReviewItem": {
            "review_id",
            "tenant_id",
            "job_id",
            "state",
            "reason_code",
            "opened_by",
            "opened_at",
            "evidence_refs",
            "decision",
            "decided_by",
            "decided_at",
        },
        "AuditEvent": {"event_id", "event_type", "tenant_id", "actor", "subject", "occurred_at"},
        "AuditActor": {"type", "id", "role"},
        "AuditSubject": {"type", "id"},
    }
    for schema_name, expected in required_fields.items():
        schema = schemas.get(schema_name, {})
        actual_required = set(schema.get("required", []))
        actual_properties = set((schema.get("properties") or {}).keys())
        missing_required = sorted(expected - actual_required)
        missing_properties = sorted(expected - actual_properties)
        if missing_required:
            report.error(
                "openapi-required-fields",
                openapi_path,
                f"{schema_name} missing required fields {missing_required!r}",
            )
        if missing_properties:
            report.error(
                "openapi-required-properties",
                openapi_path,
                f"{schema_name} missing property definitions {missing_properties!r}",
            )

    expected_refs = {
        ("Job", "state"): "#/components/schemas/JobState",
        ("Job", "active_stage"): "#/components/schemas/ManifestStage",
        ("Segment", "state"): "#/components/schemas/SegmentState",
        ("Segment", "active_stage"): "#/components/schemas/ManifestStage",
        ("Artifact", "stage"): "#/components/schemas/ManifestStage",
        ("Artifact", "qc_status"): "#/components/schemas/QcStatus",
        ("QcReport", "stage"): "#/components/schemas/ManifestStage",
        ("QcReport", "status"): "#/components/schemas/QcStatus",
        ("RepairRequest", "failure_code"): "#/components/schemas/FailureCode",
        ("Release", "state"): "#/components/schemas/ReleaseState",
        ("Asset", "state"): "#/components/schemas/AssetState",
        ("ReviewItem", "state"): "#/components/schemas/ReviewState",
        ("ReviewItem", "reason_code"): "#/components/schemas/ReviewReasonCode",
        ("AuditEvent", "event_type"): "#/components/schemas/AuditEventType",
    }
    for (schema_name, prop), ref in expected_refs.items():
        actual = schemas.get(schema_name, {}).get("properties", {}).get(prop, {}).get("$ref")
        if actual != ref:
            report.error("openapi-enum-refs", openapi_path, f"{schema_name}.{prop} must ref {ref}")

    failure_items = (
        schemas.get("QcReport", {})
        .get("properties", {})
        .get("failure_codes", {})
        .get("items", {})
        .get("$ref")
    )
    if failure_items != "#/components/schemas/FailureCode":
        report.error("openapi-enum-refs", openapi_path, "QcReport.failure_codes must ref FailureCode")

    if not report.errors:
        report.pass_check(f"OpenAPI shape ({len(paths)} paths, {len(schemas)} schemas)")
    return report


def validate_cross_contracts(repo: Path) -> ValidationReport:
    """Validate vocabulary consistency across docs and OpenAPI."""
    report = ValidationReport()
    docs = ContractDocs(repo)

    openapi_path = repo / "openapi" / "enterprise-video-factory.openapi.yaml"
    try:
        openapi = load_yaml(openapi_path)
    except Exception as exc:
        report.error("cross-contract-openapi", openapi_path, f"cannot parse OpenAPI YAML: {exc}")
        return report
    schemas = openapi.get("components", {}).get("schemas", {})
    expected_enums = {
        "ManifestStage": docs.manifest_stages(),
        "JobState": docs.job_states(),
        "SegmentState": docs.segment_states(),
        "QcStatus": docs.qc_statuses(),
        "FailureCode": docs.failure_codes(),
        "ReviewState": docs.review_states(),
        "ReviewReasonCode": docs.review_reason_codes(),
        "ReleaseState": docs.release_states(),
        "AssetState": docs.asset_states(),
        "AuditEventType": docs.audit_event_types(),
    }
    expected_enums["ReviewDecisionValue"] = [
        value
        for value in expected_enums["ReviewState"]
        if value in {"approved", "approved_with_restrictions", "rejected", "escalated"}
    ]

    for schema_name, expected in expected_enums.items():
        actual = schemas.get(schema_name, {}).get("enum", [])
        if actual != expected:
            report.error(
                "enum-consistency",
                "openapi/enterprise-video-factory.openapi.yaml",
                f"{schema_name} enum mismatch: expected {expected!r}, got {actual!r}",
            )

    canonical_failures = set(docs.failure_codes())
    for source, codes in docs.failure_code_consumers().items():
        unknown = sorted(set(codes) - canonical_failures)
        if unknown:
            report.error("failure-code-consistency", source, f"unknown failure codes {unknown!r}")

    qc_labels = set(docs.qc_stage_labels())
    for label in ("Audio Mix", "Repair", "Review"):
        if label not in qc_labels:
            report.error("stage-consistency", "docs/quality/qc-matrix.md", f"missing QC row {label}")

    mapping = docs.stage_state_mapping()
    manifest_stages = set(docs.manifest_stages())
    mapped_stages = {stage for stage, _, _ in mapping}
    missing_stages = sorted(manifest_stages - mapped_stages)
    if missing_stages:
        report.error("stage-consistency", "docs/contracts/artifact-manifest.md", f"unmapped stages {missing_stages}")

    if not report.errors:
        report.pass_check("cross-contract vocabulary consistency")
    return report


def validate_harness(repo: Path) -> ValidationReport:
    """Run the RepoFrame harness and fail on harness errors."""
    report = ValidationReport()
    codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    harness = codex_home / "skills" / "repo-init" / "scripts" / "harness.py"
    if not harness.exists():
        report.error("harness", harness, "RepoFrame harness script not found; pass --skip-harness outside Codex")
        return report
    completed = subprocess.run(
        [sys.executable, str(harness), "检查", "--repo", str(repo)],
        cwd=repo,
        text=True,
        capture_output=True,
        timeout=60,
    )
    if completed.returncode != 0:
        output = (completed.stdout + completed.stderr).strip()
        report.error("harness", harness, output or f"exited with {completed.returncode}")
    else:
        report.pass_check("RepoFrame harness errors=0")
    return report


class ContractDocs:
    """Accessors for accepted contract documents."""

    def __init__(self, repo: Path) -> None:
        self.repo = repo

    def read(self, relative: str) -> str:
        return read_text(self.repo / relative)

    def manifest_stages(self) -> list[str]:
        return extract_backtick_bullets(section(self.read("docs/contracts/artifact-manifest.md"), "Stage Enum"))

    def stage_state_mapping(self) -> list[tuple[str, list[str], str]]:
        rows = markdown_table_rows(section(self.read("docs/contracts/artifact-manifest.md"), "Stage And State Mapping"))
        parsed = []
        for row in rows:
            if len(row) >= 3:
                parsed.append((strip_ticks(row[0]), extract_backticks(row[1]), row[2]))
        return parsed

    def job_states(self) -> list[str]:
        return text_code_block_values(section(self.read("docs/contracts/job-state-machine.md"), "Job States"))

    def segment_states(self) -> list[str]:
        return text_code_block_values(section(self.read("docs/contracts/job-state-machine.md"), "Segment States"))

    def review_states(self) -> list[str]:
        return text_code_block_values(section(self.read("docs/contracts/job-state-machine.md"), "Review State"))

    def review_reason_codes(self) -> list[str]:
        return extract_backtick_bullets(
            section(self.read("docs/contracts/job-state-machine.md"), "Review State"),
            after="Review reason codes:",
        )

    def release_states(self) -> list[str]:
        return text_code_block_values(section(self.read("docs/contracts/job-state-machine.md"), "Release State"))

    def asset_states(self) -> list[str]:
        values = text_code_block_values(section(self.read("docs/security/asset-governance.md"), "Asset State Machine"))
        return [value.replace("->", "").strip() for value in values if value.replace("->", "").strip()]

    def audit_event_types(self) -> list[str]:
        return extract_backtick_bullets(section(self.read("docs/security/asset-governance.md"), "Audit Event Baseline"))

    def qc_statuses(self) -> list[str]:
        return extract_backtick_bullets(section(self.read("docs/quality/qc-matrix.md"), "QC Report Envelope"), after="Status values:")

    def qc_stage_labels(self) -> list[str]:
        rows = markdown_table_rows(section(self.read("docs/quality/qc-matrix.md"), "Stage Matrix"))
        return [row[0] for row in rows if row]

    def failure_codes(self) -> list[str]:
        rows = markdown_table_rows(section(self.read("docs/quality/failure-taxonomy.md"), "Canonical Failure Codes"))
        return [strip_ticks(row[0]) for row in rows if row]

    def failure_code_consumers(self) -> dict[str, list[str]]:
        return {
            "docs/contracts/artifact-manifest.md": extract_backtick_bullets(
                section(self.read("docs/contracts/artifact-manifest.md"), "Failure Object"),
                after="Common codes:",
            ),
            "docs/contracts/model-service-adapters.md": extract_adapter_failure_codes(
                self.read("docs/contracts/model-service-adapters.md")
            ),
            "docs/quality/qc-matrix.md": extract_qc_failure_codes(
                section(self.read("docs/quality/qc-matrix.md"), "Stage Matrix")
            ),
            "docs/quality/repair-policy.md": extract_repair_policy_failure_codes(
                self.read("docs/quality/repair-policy.md")
            ),
        }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    pattern = rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)"
    match = re.search(pattern, text)
    return match.group(1) if match else ""


def extract_backticks(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def extract_backtick_bullets(text: str, *, after: str | None = None) -> list[str]:
    if after and after in text:
        text = text.split(after, 1)[1]
    values: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\s*-\s+`([^`]+)`", line)
        if match:
            values.append(match.group(1))
        elif values and line.strip() and not line.startswith((" ", "-", "`")):
            break
    return values


def text_code_block_values(text: str) -> list[str]:
    match = re.search(r"```text\s*(.*?)```", text, flags=re.S)
    if not match:
        return []
    values = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if stripped:
            values.append(stripped)
    return values


def markdown_table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or "---" in stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and cells[0].lower() not in {"stage", "manifest stage", "code", "failure code"}:
            rows.append(cells)
    return rows


def strip_ticks(value: str) -> str:
    return value.strip().strip("`")


def extract_api_endpoints(text: str) -> set[tuple[str, str]]:
    block = text_code_block_values(section(text, "Core API Endpoints"))
    endpoints: set[tuple[str, str]] = set()
    for line in block:
        parts = line.split()
        if len(parts) >= 2 and parts[0] in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            endpoints.add((parts[0], parts[1]))
    return endpoints


def extract_adapter_failure_codes(text: str) -> list[str]:
    values: list[str] = []
    for match in re.finditer(r"Failure codes:\s*\n\n((?:- `[^`]+`\n)+)", text):
        values.extend(extract_backtick_bullets(match.group(1)))
    return values


def extract_qc_failure_codes(text: str) -> list[str]:
    values: list[str] = []
    for row in markdown_table_rows(text):
        if len(row) >= 3:
            values.extend(extract_backticks(row[2]))
    return values


def extract_repair_policy_failure_codes(text: str) -> list[str]:
    values = [strip_ticks(row[0]) for row in markdown_table_rows(section(text, "Repair Actions"))]
    values.extend(extract_backtick_bullets(section(text, "Non-Repairable Failures")))
    return values


def find_prohibited_keys(payload: Any, path: str = "$") -> list[tuple[str, str]]:
    prohibited = {"html", "javascript", "script_code", "shell", "eval"}
    found: list[tuple[str, str]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            child_path = f"{path}.{key}"
            if key in prohibited:
                found.append((path, key))
            found.extend(find_prohibited_keys(value, child_path))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            found.extend(find_prohibited_keys(value, f"{path}[{index}]"))
    return found
