from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
UI_ROOT = ROOT / "apps" / "refine_control_plane"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase27_bilgeapi_ops_console_route_and_proxy_exist():
    page = UI_ROOT / "src" / "app" / "bilgeapi-ops" / "page.tsx"
    client = UI_ROOT / "src" / "lib" / "bilgeapiOpsClient.ts"
    next_config = UI_ROOT / "next.config.ts"

    assert page.exists()
    assert client.exists()

    page_text = read(page)
    client_text = read(client)
    config_text = read(next_config)

    assert "BilgeAPIOpsConsole" in page_text
    assert "loadBilgeApiOpsSnapshot" in page_text
    assert "createBilgeApiKey" in page_text
    assert "revokeBilgeApiKey" in page_text
    assert "createPatchRevision" in page_text
    assert "verifyPatchRevision" in page_text
    assert "getProposalAuditReport" in page_text

    assert "BILGEAPI_PROXY_BASE" in client_text
    assert "plaintext_key" in client_text
    assert "redactPlaintextKey" in client_text
    assert "X-API-Key" in client_text

    assert "bilgeapiOrigin" in config_text
    assert "source: '/bilgeapi/:path*'" in config_text
    assert "destination: `${bilgeapiOrigin}/:path*`" in config_text


def test_phase27_bilgeapi_ops_console_is_registered_in_navigation():
    providers = read(UI_ROOT / "src" / "app" / "providers.tsx")
    sidebar = read(UI_ROOT / "src" / "components" / "Sidebar.tsx")

    assert 'name: "bilgeapi-ops"' in providers
    assert 'list: "/bilgeapi-ops"' in providers
    assert "BilgeAPI Ops" in providers

    assert '"bilgeapi-ops"' in sidebar
    assert "KeyRound" in sidebar
