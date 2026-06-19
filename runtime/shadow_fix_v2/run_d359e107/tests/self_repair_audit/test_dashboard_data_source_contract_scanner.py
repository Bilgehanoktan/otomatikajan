import os

from services.self_repair_audit.dashboard_data_source_contract_scanner import DashboardDataSourceContractScanner


def _write_page(workspace, rel_path, content):
    path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def test_dashboard_data_source_contract_scanner_passes_canonical_sources(tmp_path):
    workspace = str(tmp_path)
    _write_page(
        workspace,
        os.path.join("apps", "refine_control_plane", "src", "app", "ops", "launch-gates", "page.tsx"),
        'safeFetchJson(`${getApiBaseUrl()}/governance/ops/launch-gates`);',
    )
    _write_page(
        workspace,
        os.path.join("apps", "refine_control_plane", "src", "app", "ops", "handover-status", "page.tsx"),
        'safeFetchJson(`${getApiBaseUrl()}/governance/ops/handover-status`);',
    )

    artifact = DashboardDataSourceContractScanner(workspace).scan("AUD-TEST")

    assert artifact.status == "PASSED"
    assert artifact.findings == []


def test_dashboard_data_source_contract_scanner_flags_stale_operational_sources(tmp_path):
    workspace = str(tmp_path)
    _write_page(
        workspace,
        os.path.join("apps", "refine_control_plane", "src", "app", "ops", "launch-gates", "page.tsx"),
        'useList({ resource: "governance/validations" });',
    )
    _write_page(
        workspace,
        os.path.join("apps", "refine_control_plane", "src", "app", "ops", "handover-status", "page.tsx"),
        'useList({ resource: "governance/signoffs" }); const label = "100% NOMINAL"; const active = "01 ACTIVE";',
    )

    artifact = DashboardDataSourceContractScanner(workspace).scan("AUD-TEST")

    assert artifact.status == "FAILED"
    titles = [finding.title for finding in artifact.findings]
    assert "Operational Dashboard Missing Canonical Data Source" in titles
    assert "Operational Dashboard Uses Non-Canonical Data Source" in titles
    assert "Operational Dashboard Hardcodes Success State" in titles

    descriptions = "\n".join(finding.description for finding in artifact.findings)
    assert "governance/validations" in descriptions
    assert "governance/signoffs" in descriptions
    assert "100% NOMINAL" in descriptions
