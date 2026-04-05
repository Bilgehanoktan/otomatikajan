import os
import re

# THE DEFINITIVE Repo Sterilization Script for Sovereign AGI (Faz 12.1)
# Corrects all root-level shims and sub-package redirections.

def get_mappings():
    return {
        "db.repository": "packages.persistence.repositories.repository",
        "db.models": "packages.persistence.models",
        "db.session": "packages.persistence.session",
        "db": "packages.persistence",
        
        "observability.logging": "packages.observability.logging",
        "observability.metrics": "packages.observability.metrics",
        "observability": "packages.observability",
        
        "llm.model_orchestrator": "packages.llm_gateway.model_orchestrator",
        "llm.model_router": "packages.llm_gateway.model_router",
        "llm": "packages.llm_gateway",
        
        "quality.reviewer": "packages.quality_assurance.reviewer",
        "quality.output_schema": "packages.quality_assurance.output_schema",
        "quality": "packages.quality_assurance",
        
        "memory.watchdog": "packages.memory.watchdog",
        "memory.synapse": "packages.memory.synapse",
        "memory.retrieval": "packages.memory.retrieval",
        "memory": "packages.memory",
        
        "repair.core": "packages.repair_engine.core",
        "repair": "packages.repair_engine",
        
        "healing": "packages.healing",
        "improve": "packages.improvement_engine",
        "agi_engine": "packages.orchestration.agi",
        "core": "packages.orchestration"
    }

def apply_replacements(target_dir, mapping):
    sorted_prefixes = sorted(mapping.keys(), key=len, reverse=True)
    count = 0
    file_count = 0
    for root, dirs, files in os.walk(target_dir):
        if any(exc in root for exc in ["__pycache__", ".venv", ".git"]):
            continue
        for name in files:
            if name.endswith(".py"):
                filepath = os.path.join(root, name)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                
                for prefix in sorted_prefixes:
                    target = mapping[prefix]
                    
                    # Pattern 1: from [prefix].[suffix] import [X]
                    pattern_from = re.compile(r"from " + re.escape(prefix) + r"(\.[a-zA-Z0-9_\.]+)? import")
                    new_content = pattern_from.sub(r"from " + target + r"\1 import", new_content)
                    
                    # Pattern 2: import [prefix].[suffix]
                    pattern_import = re.compile(r"import " + re.escape(prefix) + r"(\.[a-zA-Z0-9_\.]+)?")
                    new_content = pattern_import.sub(r"import " + target + r"\1", new_content)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    count += 1
                file_count += 1
    return count, file_count

# EXECUTE
mapping = get_mappings()
full_scan_dirs = ["apps", "packages", "agents", "skills", "integrations", "tools", "startup"]

total_updated = 0
for d_base in full_scan_dirs:
    d = os.path.join("e:/ai_company_faz12.1/", d_base)
    if os.path.exists(d):
        updated, total = apply_replacements(d, mapping)
        print(f"Sterilized {d_base}: Updated {updated}/{total} files.")
        total_updated += updated

print(f"Definitive Sterilization complete. Total: {total_updated}")
