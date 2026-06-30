import importlib.util
from pathlib import Path

import pytest


def load_page_audit_module():
    module_path = Path(__file__).resolve().parents[2] / "runtime" / "live-test" / "page_audit.py"
    spec = importlib.util.spec_from_file_location("page_audit", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_page(app_dir: Path, route: str) -> None:
    page_dir = app_dir / Path(route)
    page_dir.mkdir(parents=True)
    (page_dir / "page.tsx").write_text("export default function Page() { return null; }\n", encoding="utf-8")


def test_page_routes_replaces_named_dynamic_params(tmp_path, monkeypatch):
    module = load_page_audit_module()
    app_dir = tmp_path / "app"
    write_page(app_dir, "project-factory/[project_id]")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "APP_DIR", app_dir)

    routes = module.page_routes(
        samples={"project-factory/[project_id]": "pf-123"},
        skipped_samples={},
    )

    assert routes == [
        {
            "route_key": "project-factory/[project_id]",
            "url_path": "/project-factory/pf-123",
            "source": "app/project-factory/[project_id]/page.tsx",
            "data_note": "live-sample",
        }
    ]


def test_page_routes_skips_dynamic_route_when_no_live_sample(tmp_path, monkeypatch):
    module = load_page_audit_module()
    app_dir = tmp_path / "app"
    write_page(app_dir, "project-factory/[project_id]")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "APP_DIR", app_dir)

    routes = module.page_routes(
        samples={},
        skipped_samples={"project-factory/[project_id]": "No portfolio projects available."},
    )

    assert routes == [
        {
            "route_key": "project-factory/[project_id]",
            "url_path": None,
            "source": "app/project-factory/[project_id]/page.tsx",
            "data_note": "skipped_no_sample",
            "skip_reason": "No portfolio projects available.",
        }
    ]


def test_discover_route_samples_maps_live_api_payloads(monkeypatch):
    module = load_page_audit_module()
    payloads = {
        "/governance/approvals": [{"id": "approval-1"}],
        "/governance/incidents": [{"id": "incident-1"}],
        "/workflows": [{"id": "workflow-1"}],
        "/governance/governor/proof/snapshots": [{"id": "proof-1"}],
        "/governance/governor/alerts": [],
        "/governance/governor/drifts": [{"id": "drift-1"}],
        "/learning/fingerprints": [{"id": "fingerprint-1"}],
        "/project-factory/portfolio/search?sort=updated_at_desc&limit=1&offset=0": {
            "search_results": {"items": [{"project_id": "project-1"}]}
        },
    }

    monkeypatch.setattr(module, "api_get_json", lambda path, token: payloads[path])

    samples, skipped = module.discover_route_samples("token")

    assert samples["approvals/[id]"] == "approval-1"
    assert samples["governance/approvals/[id]"] == "approval-1"
    assert samples["incidents/[id]"] == "incident-1"
    assert samples["governance/incidents/[id]"] == "incident-1"
    assert samples["workflows/[id]"] == "workflow-1"
    assert samples["proof/snapshots/[id]"] == "proof-1"
    assert samples["governor/proof/snapshots/[id]"] == "proof-1"
    assert samples["governor/drifts/[id]"] == "drift-1"
    assert samples["learning/fingerprints/[id]"] == "fingerprint-1"
    assert samples["project-factory/[project_id]"] == "project-1"
    assert "governor/alerts/[id]" in skipped


def test_get_login_credentials_reads_password_from_env(monkeypatch):
    module = load_page_audit_module()
    monkeypatch.setattr(module, "_read_dotenv_value", lambda name: None)
    monkeypatch.setenv("AUDIT_LOGIN_EMAIL", "operator@example.test")
    monkeypatch.setenv("AUDIT_LOGIN_PASSWORD", "env-password")

    assert module.get_login_credentials() == ("operator@example.test", "env-password")


def test_get_login_credentials_requires_password(tmp_path, monkeypatch):
    module = load_page_audit_module()
    monkeypatch.setattr(module, "_read_dotenv_value", lambda name: None)
    monkeypatch.setattr(module, "DEFAULT_PASSWORD_FILE", tmp_path / "missing-password")
    for name in (
        "AUDIT_LOGIN_PASSWORD",
        "NEXT_PUBLIC_DEV_OPERATOR_PASSWORD",
        "DEV_OPERATOR_PASSWORD",
        "AUDIT_LOGIN_PASSWORD_FILE",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="AUDIT_LOGIN_PASSWORD"):
        module.get_login_credentials()


def test_get_login_credentials_reads_default_password_file(tmp_path, monkeypatch):
    module = load_page_audit_module()
    password_file = tmp_path / ".page-audit-password"
    password_file.write_text("\ufefffile-password\n", encoding="utf-8")
    monkeypatch.setattr(module, "DEFAULT_PASSWORD_FILE", password_file)
    monkeypatch.setattr(module, "_read_dotenv_value", lambda name: None)
    for name in (
        "AUDIT_LOGIN_PASSWORD",
        "NEXT_PUBLIC_DEV_OPERATOR_PASSWORD",
        "DEV_OPERATOR_PASSWORD",
        "AUDIT_LOGIN_PASSWORD_FILE",
    ):
        monkeypatch.delenv(name, raising=False)

    assert module.get_login_credentials() == ("admin@sovereign.agi", "file-password")
