from __future__ import annotations


DOWNLOAD_REPO_INTEGRATIONS = {
    "Agentless-main.zip": {
        "integration": "agentless_backend",
        "mode": "implemented",
        "purpose": "Localization -> repair -> validation ayrimi ve SEARCH/REPLACE patch uretimi.",
    },
    "aider-main.zip": {
        "integration": "aider_backend",
        "mode": "safe_deferred",
        "purpose": "Diff tabanli conversational coding agent alternatifi.",
    },
    "auto-code-rover-main.zip": {
        "integration": "auto_code_rover_backend",
        "mode": "safe_deferred",
        "purpose": "Multi-agent search, selection, review ve patch-writing desenleri.",
    },
    "joycode-agent-main.zip": {
        "integration": "joycode_verifier_patterns",
        "mode": "implemented",
        "purpose": "Fail2Pass, Pass2Pass, retry ve failure attribution dogrulama desenleri.",
    },
    "live-swe-agent-main.zip": {
        "integration": "live_swe_backend",
        "mode": "safe_deferred",
        "purpose": "Canli SWE-style repair loop icin ileriki adapter noktasi.",
    },
    "mini-swe-agent-main.zip": {
        "integration": "mini_swe_adapter",
        "mode": "implemented_safe_mock",
        "purpose": "Ana repair agent adapter'i; varsayilan olarak mock/disabled.",
    },
    "RepairAgent-main.zip": {
        "integration": "repair_agent_backend",
        "mode": "safe_deferred",
        "purpose": "Klasik automated program repair stratejileri ve repair corpus desenleri.",
    },
    "software-agent-sdk-main.zip": {
        "integration": "openhands_backend",
        "mode": "safe_deferred",
        "purpose": "OpenHands SDK file editor, terminal ve workspace abstraction icin ileriki katman.",
    },
    "SWE-agent-main.zip": {
        "integration": "swe_agent_backend",
        "mode": "safe_deferred",
        "purpose": "SWE-agent task solving loop ve issue-oriented workflow referansi.",
    },
    "SWE-ReX-main.zip": {
        "integration": "swe_rex_adapter",
        "mode": "safe_deferred",
        "purpose": "local, Docker veya remote sandbox command runtime abstraction.",
    },
}


def integration_names() -> list[str]:
    return sorted(DOWNLOAD_REPO_INTEGRATIONS)


def integration_summary() -> dict:
    return DOWNLOAD_REPO_INTEGRATIONS.copy()

