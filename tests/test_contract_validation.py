from __future__ import annotations

import copy
import json
from pathlib import Path

import yaml

from video_factory_contracts.validation import (
    validate_repo,
    validate_openapi,
    validate_storyboard_payload,
)


REPO = Path(__file__).resolve().parents[1]


def test_current_repo_contracts_pass_without_harness() -> None:
    report = validate_repo(REPO, skip_harness=True)
    assert not report.errors, report.render()


def test_storyboard_rejects_unmarked_emphasis_text() -> None:
    payload = json.loads((REPO / "examples/storyboards/30s.json").read_text())
    payload = copy.deepcopy(payload)
    payload["scenes"][0]["visuals"]["emphasis"][0]["text"] = "not in the script"

    errors = validate_storyboard_payload(payload)

    assert any("emphasis text" in error for error in errors)


def test_storyboard_allows_review_marked_emphasis_exception() -> None:
    payload = json.loads((REPO / "examples/storyboards/30s.json").read_text())
    payload = copy.deepcopy(payload)
    payload["scenes"][0]["visuals"]["emphasis"][0]["text"] = "not in the script"
    payload["scenes"][0]["requires_review"] = True

    errors = validate_storyboard_payload(payload)

    assert not [error for error in errors if "emphasis text" in error]


def copy_openapi_fixture(tmp_path: Path) -> tuple[Path, dict]:
    temp_repo = tmp_path / "repo"
    temp_repo.mkdir()
    (temp_repo / "openapi").mkdir()
    (temp_repo / "docs/product").mkdir(parents=True)

    openapi = yaml.safe_load((REPO / "openapi/enterprise-video-factory.openapi.yaml").read_text())
    return temp_repo, openapi


def write_openapi_fixture(temp_repo: Path, openapi: dict) -> None:
    (temp_repo / "openapi/enterprise-video-factory.openapi.yaml").write_text(
        yaml.safe_dump(openapi, sort_keys=False),
        encoding="utf-8",
    )
    (temp_repo / "docs/product/api-console.md").write_text(
        (REPO / "docs/product/api-console.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def test_openapi_required_paths_are_checked(tmp_path: Path) -> None:
    temp_repo, openapi = copy_openapi_fixture(tmp_path)
    openapi["paths"].pop("/v1/audit/events")
    write_openapi_fixture(temp_repo, openapi)

    report = validate_openapi(temp_repo)

    assert any("missing documented path /v1/audit/events" in issue.message for issue in report.errors)


def test_openapi_required_methods_are_checked(tmp_path: Path) -> None:
    temp_repo, openapi = copy_openapi_fixture(tmp_path)
    repair_path = openapi["paths"]["/v1/jobs/{job_id}/repair"]
    repair_path["get"] = repair_path.pop("post")
    write_openapi_fixture(temp_repo, openapi)

    report = validate_openapi(temp_repo)

    assert any("missing documented method POST /v1/jobs/{job_id}/repair" in issue.message for issue in report.errors)


def test_openapi_required_governance_fields_are_checked(tmp_path: Path) -> None:
    temp_repo, openapi = copy_openapi_fixture(tmp_path)
    openapi["components"]["schemas"]["ReviewItem"]["required"].remove("tenant_id")
    openapi["components"]["schemas"]["AuditEvent"]["required"].remove("actor")
    write_openapi_fixture(temp_repo, openapi)

    report = validate_openapi(temp_repo)

    assert any("ReviewItem missing required fields ['tenant_id']" in issue.message for issue in report.errors)
    assert any("AuditEvent missing required fields ['actor']" in issue.message for issue in report.errors)


def test_openapi_required_governance_properties_are_checked(tmp_path: Path) -> None:
    temp_repo, openapi = copy_openapi_fixture(tmp_path)
    del openapi["components"]["schemas"]["ReviewItem"]["properties"]["tenant_id"]
    del openapi["components"]["schemas"]["AuditEvent"]["properties"]["actor"]
    write_openapi_fixture(temp_repo, openapi)

    report = validate_openapi(temp_repo)

    assert any("ReviewItem missing property definitions ['tenant_id']" in issue.message for issue in report.errors)
    assert any("AuditEvent missing property definitions ['actor']" in issue.message for issue in report.errors)


def test_malformed_openapi_yaml_returns_report(tmp_path: Path) -> None:
    temp_repo = tmp_path / "repo"
    temp_repo.mkdir()
    for directory in [
        "openapi",
        "docs/product",
        "docs/contracts",
        "docs/quality",
        "docs/security",
        "schemas",
        "examples/storyboards",
    ]:
        (temp_repo / directory).mkdir(parents=True, exist_ok=True)
    for relative in [
        "docs/product/api-console.md",
        "docs/contracts/artifact-manifest.md",
        "docs/contracts/job-state-machine.md",
        "docs/quality/failure-taxonomy.md",
        "docs/quality/qc-matrix.md",
        "docs/quality/repair-policy.md",
        "docs/security/asset-governance.md",
        "schemas/scene-storyboard.schema.json",
        "examples/storyboards/30s.json",
    ]:
        target = temp_repo / relative
        target.write_text((REPO / relative).read_text(encoding="utf-8"), encoding="utf-8")
    (temp_repo / "openapi/enterprise-video-factory.openapi.yaml").write_text(
        "openapi: [not valid\n",
        encoding="utf-8",
    )

    report = validate_repo(temp_repo, skip_harness=True)

    assert report.errors
    assert any(issue.check == "openapi-yaml" for issue in report.errors)
    assert any(issue.check == "cross-contract-openapi" for issue in report.errors)
