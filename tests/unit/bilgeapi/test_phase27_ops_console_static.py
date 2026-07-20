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
    assert "Immutable Review Ledger" in page_text
    assert "verifyReviewLedgerChain" in page_text
    assert "exportReviewLedgerChain" in page_text
    assert "AI Patch Suggestions" in page_text
    assert "createAiPatchSuggestion" in page_text
    assert "verifyAiPatchSuggestion" in page_text
    assert "acceptAiPatchSuggestionForReview" in page_text
    assert "rejectAiPatchSuggestion" in page_text
    assert "triggerRemediation" in page_text
    assert "runEmergencyRecovery" in page_text
    assert "remediation" in page_text
    assert "Emergency Recovery (Liveness Only)" in page_text
    assert "Governor Findings" in page_text
    assert "Forbidden Governor Actions" in page_text
    assert "acknowledgeFinding" in page_text
    assert "dismissFinding" in page_text
    assert "watchdogStatus" in page_text
    assert "Agent Capabilities" in page_text
    assert "Recent Sandbox Runs" in page_text
    assert "Promotion Requests" in page_text
    assert "Execute Integration" in page_text
    assert "listAgentPromotions" in page_text

    assert "BILGEAPI_PROXY_BASE" in client_text
    assert "plaintext_key" in client_text
    assert "redactPlaintextKey" in client_text
    assert "X-API-Key" in client_text
    assert "listReviewLedgerRecent" in client_text
    assert "verifyReviewLedgerChain" in client_text
    assert "exportReviewLedgerChain" in client_text
    assert "AIPatchSuggestionRecord" in client_text
    assert "createAiPatchSuggestion" in client_text
    assert "listAiPatchSuggestions" in client_text
    assert "verifyAiPatchSuggestion" in client_text
    assert "acceptAiPatchSuggestionForReview" in client_text
    assert "rejectAiPatchSuggestion" in client_text
    assert "RemediationRunbookRecord" in client_text
    assert "RemediationAttemptRecord" in client_text
    assert "triggerRemediation" in client_text
    assert "runEmergencyRecovery" in client_text
    assert "acknowledgeFinding" in client_text
    assert "dismissFinding" in client_text
    assert "WatchdogStatusRecord" in client_text
    assert "SystemFindingRecord" in client_text
    assert "AgentCapabilityRecord" in client_text
    assert "AgentRunRecord" in client_text
    assert "AgentPromotionRecord" in client_text
    assert "listAgentCapabilities" in client_text
    assert "listAgentRuns" in client_text
    assert "listAgentPromotions" in client_text
    assert "approveAgentPromotion" in client_text
    assert "rejectAgentPromotion" in client_text
    assert "executeAgentPromotion" in client_text
    assert "simulateAgentPromotion" in client_text
    assert "enableAgent" in client_text
    assert "disableAgent" in client_text

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


def test_phase27_snapshot_rejects_invalid_auth_before_partial_data_collection():
    client_text = read(UI_ROOT / "src" / "lib" / "bilgeapiOpsClient.ts")

    assert "export class BilgeApiResponseError extends Error" in client_text
    assert "export function isBilgeApiAuthError" in client_text
    assert "async function verifyBilgeApiAccess" in client_text
    assert 'return bilgeApiFetch<JsonValue>(apiKey, "/v1/catalog")' in client_text

    snapshot_body = client_text.split(
        "export async function loadBilgeApiOpsSnapshot", 1
    )[1]
    probe_index = snapshot_body.index("await verifyBilgeApiAccess(apiKey)")
    partial_data_index = snapshot_body.index("const errors: string[] = []")
    assert probe_index < partial_data_index
    assert 'settle("proposals"' in snapshot_body


def test_phase27_console_clears_stale_key_using_typed_auth_error():
    page_text = read(UI_ROOT / "src" / "app" / "bilgeapi-ops" / "page.tsx")

    assert "isBilgeApiAuthError" in page_text
    assert "if (isBilgeApiAuthError(error))" in page_text
    assert 'sessionStorage.removeItem("bilgeapi_ops_api_key")' in page_text
    assert "setSnapshot(null)" in page_text
    assert 'lowered.includes("unauthorized")' not in page_text
