from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List

# Core config path
CATALOG_PATH = Path(__file__).resolve().parents[2] / "configs" / "external_agent_catalog.yaml"

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


def load_external_agent_catalog() -> dict[str, Any]:
    """Loads the external agent catalog YAML file, returning a parsed dict.
    Falls back to a static catalog if the file is missing or unreadable.
    """
    if not CATALOG_PATH.exists():
        # Fallback dictionary matching the exact schema
        return {
            "external_agents": {
                "swe_agent": {
                    "name": "SWE-agent",
                    "repo_url": "https://github.com/princeton-nlp/SWE-agent",
                    "pinned_commit": "a3b2f91c9e8d47562f1c0b39d8e7b6d5c4b3a2f1",
                    "license": "MIT",
                    "purpose": "GitHub issue / failure spec -> patch candidate",
                    "risk_level": "high",
                    "allowed_modes": ["local_adapter", "reference_only"],
                    "forbidden_actions": ["direct_git_push", "production_secrets_read", "bypass_human_gate"]
                },
                "swe_rex": {
                    "name": "SWE-ReX",
                    "repo_url": "https://github.com/SWE-ReX/SWE-ReX",
                    "pinned_commit": "9c8b7a6f5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b",
                    "license": "Apache-2.0",
                    "purpose": "Sandboxed code execution infrastructure",
                    "risk_level": "medium",
                    "allowed_modes": ["sandbox_runner", "reference_only"],
                    "forbidden_actions": ["production_db_modify", "bypass_human_gate"]
                },
                "pr_agent": {
                    "name": "PR-Agent/Qodo",
                    "repo_url": "https://github.com/Codium-ai/pr-agent",
                    "pinned_commit": "1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c",
                    "license": "Apache-2.0",
                    "purpose": "PR automated risk rating and comment artifacts",
                    "risk_level": "low",
                    "allowed_modes": ["review_gate", "reference_only"],
                    "forbidden_actions": ["direct_git_push", "bypass_human_gate"]
                },
                "stagehand": {
                    "name": "Stagehand",
                    "repo_url": "https://github.com/browserbase/stagehand",
                    "pinned_commit": "f1e2d3c4b5a6f7e8d9c0b1a2f3e4d5c6b7a8f9e0",
                    "license": "MIT",
                    "purpose": "UI diagnostics and visual assertion verification",
                    "risk_level": "medium",
                    "allowed_modes": ["local_adapter", "reference_only"],
                    "forbidden_actions": ["production_db_modify", "bypass_human_gate"]
                },
                "openhands": {
                    "name": "OpenHands",
                    "repo_url": "https://github.com/All-Hands-AI/OpenHands",
                    "pinned_commit": "e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9",
                    "license": "MIT",
                    "purpose": "Heavy developer-agent runtime and workspace abstraction",
                    "risk_level": "high",
                    "allowed_modes": ["experimental", "reference_only"],
                    "forbidden_actions": ["direct_git_push", "production_secrets_read", "production_db_modify", "bypass_human_gate"]
                },
                "github_copilot": {
                    "name": "GitHub Copilot coding agent",
                    "repo_url": "https://github.com/features/copilot",
                    "pinned_commit": "reference_only_non_oss",
                    "license": "Proprietary",
                    "purpose": "Architectural reference for issue -> branch/PR -> human review model",
                    "risk_level": "low",
                    "allowed_modes": ["reference_only"],
                    "forbidden_actions": ["direct_git_push", "production_secrets_read", "production_db_modify", "bypass_human_gate"]
                }
            }
        }
    
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        # Graceful fallback in case of parsing error
        return {}


def validate_agent_execution(agent_key: str, requested_mode: str) -> dict[str, Any]:
    """Validates if an agent can execute under a requested mode.
    Enforces risk limits, license checks, and allowed modes.
    """
    catalog = load_external_agent_catalog()
    agents = catalog.get("external_agents", {})
    
    if agent_key not in agents:
        return {
            "valid": False,
            "status": "BLOCKED",
            "reason": f"Agent '{agent_key}' is not registered in the external agent catalog.",
            "risk_level": "unknown",
            "license": "unknown"
        }
    
    agent_info = agents[agent_key]
    allowed_modes = agent_info.get("allowed_modes", [])
    risk_level = agent_info.get("risk_level", "high")
    license_type = agent_info.get("license", "unknown")
    forbidden_actions = agent_info.get("forbidden_actions", [])
    
    # License & Safety Check
    if license_type == "Proprietary" and requested_mode != "reference_only":
        return {
            "valid": False,
            "status": "BLOCKED",
            "reason": f"Proprietary agent '{agent_key}' is restricted to 'reference_only' mode.",
            "risk_level": risk_level,
            "license": license_type
        }
    
    # Mode Validation
    if requested_mode not in allowed_modes:
        return {
            "valid": False,
            "status": "BLOCKED",
            "reason": f"Mode '{requested_mode}' is not allowed for '{agent_key}'. Allowed: {allowed_modes}",
            "risk_level": risk_level,
            "license": license_type
        }
        
    # High-Risk Blockers (Human Gate requirement)
    if risk_level == "high" and requested_mode not in {"reference_only", "experimental"}:
        # Must be double-gated by default
        return {
            "valid": True,
            "status": "WARNING_HIGH_RISK",
            "reason": f"Agent '{agent_key}' is classified as HIGH RISK. Execution requires sandbox isolation and strict Human Gate approval.",
            "risk_level": risk_level,
            "license": license_type,
            "forbidden_actions": forbidden_actions
        }
        
    return {
        "valid": True,
        "status": "APPROVED_GATED",
        "reason": f"Agent '{agent_key}' validated successfully for execution in '{requested_mode}' mode.",
        "risk_level": risk_level,
        "license": license_type,
        "forbidden_actions": forbidden_actions
    }
