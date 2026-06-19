import os
import re

TARGET_DIRS = [
    "apps", 
    "services", 
    "libs", 
    "workers", 
    "agents",
    "tests"
]

# NEW MAPPINGS FOR PHASE 13.04
MAPPINGS = {
    # Broad Hub Mappings
    r"hub_infra\.api\.main": "apps.public_api.main",
    r"hub_infra\.api\.auth": "services.auth",
    r"hub_infra\.persistence": "libs.db",
    r"hub_cortex\.llm_gateway": "libs.llm",
    r"hub_cortex\.config": "libs.config",
    r"hub_cortex\.memory": "libs.memory",
    r"hub_cortex\.orchestration\.agi\.agents": "agents.specialist_agents",
    r"services\.orchestration\.agi\.agents": "agents.specialist_agents",
    r"hub_cortex\.contracts": "libs.contracts",
    r"hub_cortex\.orchestration": "services.orchestration",
    r"hub_guardian\.healing": "services.repair", # healing became part of repair service
    r"hub_guardian\.repair_engine": "services.repair",
    r"hub_guardian\.quality_assurance": "services.governance.quality",
    r"hub_guardian\.tools": "services.integrations",
    r"hub_guardian\.observability": "services.observability",
    r"hub_infra\.worker": "workers.workflow_worker",
    r"hub_ecosystem\.integrations": "services.integrations",
    r"hub_interaction\.telegram_bot": "apps.telegram_bot", # If moved
    
    # Core Disaggregation
    r"core\.job_queue": "libs.queue_abstractions.job_queue",
    r"core\.ceo_engine": "agents.ceo_agent.ceo_engine",
    r"core\.ceo_supervisor": "agents.ceo_agent.ceo_supervisor",
    r"core\.prompts": "agents.prompts.prompts",
    r"core\.deerflow_prompts": "agents.prompts.deerflow_prompts",
    r"core\.heal_engine": "services.repair.heal_engine",
    r"core\.repair_orchestrator": "services.repair.repair_orchestrator",
    r"core\.policy_engine": "services.governance.policy.policy_engine",
    r"core\.policy_registry": "services.governance.policy.policy_registry",
    r"core\.git_ops": "libs.vcs.git_ops",
    r"core\.sandbox_runner": "services.orchestration.substrate.sandbox_runner",
    r"core\.shadow_runner": "services.orchestration.substrate.shadow_runner",
    r"core\.task_management": "services.orchestration.application.task_management",
    r"core\.task_routing": "services.orchestration.application.task_routing",
    r"core\.task_templates": "services.orchestration.application.task_templates",
    r"core\.self_updater": "services.repair.self_updater",
    r"core\.patcher": "services.repair.patcher",
    r"core\.reaper_service": "services.repair.reaper_service",
    r"core\.self_improvement_coordinator": "services.governance.evolution.self_improvement_coordinator",
    
    # Prefix-less (Shadow) Imports fallback (just in case any survived or were partially moved)
    r"(?m)^(from|import)\s+schemas\b": r"\1 libs.contracts.schemas",
    r"(?m)^(from|import)\s+persistence\b": r"\1 libs.db",
    r"(?m)^(from|import)\s+repositories\b": r"\1 libs.db.repositories",
    r"(?m)^(from|import)\s+models\b": r"\1 libs.db.models",
    r"(?m)^(from|import)\s+db\b": r"\1 libs.db",
    r"(?m)^(from|import)\s+domain\b": r"\1 services.orchestration.domain", # Adjust based on reality
    r"(?m)^(from|import)\s+auth\b": r"\1 services.auth",
    r"(?m)^(from|import)\s+memory\b": r"\1 libs.memory",
    r"(?m)^(from|import)\s+llm\b": r"\1 libs.llm",
    r"(?m)^(from|import)\s+quality\b": r"\1 services.governance.quality",
    r"(?m)^(from|import)\s+observability\b": r"\1 services.observability",
    r"(?m)^(from|import)\s+core\b": r"\1 core", # Keep core as shim for now
    
    # Specific Redundant Fixes
    r"libs\.db\.(repositories|models)": r"libs.db.\1",
}

BLACKLIST = {"node_modules", "venv", "__pycache__", ".archive", ".git"}
ROOT_DIR = os.getcwd()

def migrate_v13():
    fixed_count = 0
    file_count = 0
    
    for tdir in TARGET_DIRS:
        abs_tdir = os.path.normpath(os.path.join(ROOT_DIR, tdir))
        if not os.path.exists(abs_tdir):
            continue
            
        print(f"[MIGRATING] {tdir}")
        for root, dirs, files in os.walk(abs_tdir):
            dirs[:] = [d for d in dirs if d not in BLACKLIST]
            
            for file in files:
                if file.endswith(".py") or file.endswith(".js") or file.endswith(".tsx"):
                    file_count += 1
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        
                        new_content = content
                        for pattern, replacement in MAPPINGS.items():
                            new_content = re.sub(pattern, replacement, new_content)
                        
                        if new_content != content:
                            print(f"  [FIXED] {os.path.relpath(path, ROOT_DIR)}")
                            with open(path, "w", encoding="utf-8") as f:
                                f.write(new_content)
                            fixed_count += 1
                    except Exception as e:
                        print(f"  [ERROR] {path}: {e}")
                        
    print(f"\nMigration v13.04 complete. Files scanned: {file_count}, Files repaired: {fixed_count}")

if __name__ == "__main__":
    migrate_v13()
