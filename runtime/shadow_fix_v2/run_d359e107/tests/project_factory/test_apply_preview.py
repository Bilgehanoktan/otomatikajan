import json
from pathlib import Path

import pytest

from services.project_factory.apply_preview import run_apply_preview
from services.project_factory.models import ApplyPreviewRequest


def _write_delivery(workspace: Path, project_id: str, rel_path: str, content: str = "new") -> None:
    project_dir = workspace / "project_outputs" / "project_factory" / project_id
    files_dir = project_dir / "delivery_package" / "files" / Path(rel_path).parent
    files_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "delivery_package" / "files" / rel_path).write_text(content, encoding="utf-8")
    manifest = {
        "project_id": project_id,
        "status": "DELIVERY_PACKAGE_READY",
        "production_apply_allowed": False,
        "files": [{"path": f"files/{rel_path}", "checksum": "test"}],
    }
    (project_dir / "delivery_package").mkdir(parents=True, exist_ok=True)
    (project_dir / "delivery_package" / "delivery_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_run_apply_preview_add_and_modify_without_mutating_workspace(tmp_path):
    workspace = tmp_path
    project_id = "PF-APPLY"
    _write_delivery(workspace, project_id, "src/a.txt", "new")
    target = workspace / "src" / "a.txt"
    target.parent.mkdir(parents=True)
    target.write_text("old", encoding="utf-8")

    req = ApplyPreviewRequest(operator_id="op", rationale="review preview", risk_acknowledgement=True)
    preview = run_apply_preview(project_id, req, str(workspace))

    assert preview["production_apply_performed"] is False
    assert preview["file_changes"][0]["change_type"] == "MODIFY"
    assert target.read_text(encoding="utf-8") == "old"
    assert (workspace / "project_outputs" / "project_factory" / project_id / "apply_preview.json").exists()
    assert (workspace / "project_outputs" / "project_factory" / project_id / "diff_summary.md").exists()


def test_run_apply_preview_blocks_sensitive_delivery_file(tmp_path):
    workspace = tmp_path
    project_id = "PF-BLOCK"
    _write_delivery(workspace, project_id, ".env", "SECRET=x")

    req = ApplyPreviewRequest(operator_id="op", rationale="review preview", risk_acknowledgement=True)
    preview = run_apply_preview(project_id, req, str(workspace))

    assert preview["status"] == "APPLY_PREVIEW_BLOCKED"
    assert preview["blocking_risks"]


def test_run_apply_preview_requires_risk_ack(tmp_path):
    with pytest.raises(ValueError, match="risk_acknowledgement"):
        run_apply_preview(
            "PF-NOACK",
            ApplyPreviewRequest(operator_id="op", rationale="review preview", risk_acknowledgement=False),
            str(tmp_path),
        )
