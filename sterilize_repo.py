import os
import re

# ULTIMATE Repo Sterilization Script for Sovereign AGI (Faz 12.1)
# Targets: Any legacy root-level shim module/package imports.

def get_mappings():
    # Canonical mappings for root-level modules to packages
    mappings = {
        "core": "packages.orchestration", # Usually, or more specific sub-path
        "db": "packages.persistence",
        "observability": "packages.observability",
        "llm": "packages.llm_gateway",
        "quality": "packages.quality_assurance",
        "memory": "packages.memory",
        "repair": "packages.repair_engine",
        "healing": "packages.healing",
        "improve": "packages.improvement_engine",
        "agi_engine": "packages.orchestration.agi"
    }
    
    # Specific sub-mappings for deep 'core' locations (collected earlier)
    # This ensures we don't just map core.agi to packages.orchestration.agi 
    # but handle the nested world engine etc. correctly if they shifted.
    # From previous check, mostly everything moved under orchestration/agi/
    core_root = r"e:/ai_company_faz12.1/packages/orchestration"
    # (We could dynamically build this, but simple prefixing works well with regex sub-capturing)
    
    return mappings

def apply_replacements(target_dir, mapping):
    # Sort mapping by length of key (longer first)
    sorted_prefixes = sorted(mapping.keys(), key=len, reverse=True)
    
    count = 0
    file_count = 0
    for root, dirs, files in os.walk(target_dir):
        if "__pycache__" in root or ".venv" in root or ".git" in root:
            continue
        for name in files:
            if name.endswith(".py"):
                filepath = os.path.join(root, name)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                
                # Sterilize each key prefix
                for prefix in sorted_prefixes:
                    target = mapping[prefix]
                    
                    # Pattern 1: from [prefix].[suffix] import [X]
                    # We match [prefix] as a top-level module
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

print(f"Executing sterilization for {len(mapping)} root-level prefixes.")

# target_dirs = [r"e:/ai_company_faz12.1/apps", r"e:/ai_company_faz12.1/packages", r"e:/ai_company_faz12.1/agents", r"e:/ai_company_faz12.1/skills"]
# We also include 'integrations', 'dashboard/api' etc.
# Actually, let's just scan THE WHOLE REPO except .git, packages/ (no, packages itself needs it for internal deps), apps/ etc.

full_scan_dirs = [
    r"e:/ai_company_faz12.1/apps",
    r"e:/ai_company_faz12.1/packages",
    r"e:/ai_company_faz12.1/agents",
    r"e:/ai_company_faz12.1/skills",
    r"e:/ai_company_faz12.1/integrations",
    r"e:/ai_company_faz12.1/webhooks",
    r"e:/ai_company_faz12.1/startup",
    r"e:/ai_company_faz12.1/tools"
]

total_updated = 0
for d in full_scan_dirs:
    if os.path.exists(d):
        updated, total = apply_replacements(d, mapping)
        print(f"Sterilized {d}: Updated {updated}/{total} files.")
        total_updated += updated

print(f"Ultimate Sterilization complete. Total files updated: {total_updated}")
