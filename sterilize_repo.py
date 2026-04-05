import os
import re

# Repo Sterilization Script for Sovereign AGI (Faz 12.1)
# 1. Map shims from core/ to packages/
# 2. Bulk replace in apps/api/ and packages/
# 3. Handle subdirectories correctly

def get_mappings(root_core):
    mappings = {}
    for root, dirs, files in os.walk(root_core):
        for name in files:
            if name.endswith(".py"):
                file_path = os.path.join(root, name)
                rel_path = os.path.relpath(file_path, root_core)
                
                # Module path in 'core'
                core_module = "core." + rel_path.replace("\\", ".").replace("/", ".").replace(".py", "")
                if core_module.endswith(".__init__"):
                    core_module = core_module[:-9]
                
                # Find shim destination
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Pattern: from packages... import *
                    match = re.search(r"from (packages\.[^ ]+) import \*", content)
                    if match:
                        mappings[core_module] = match.group(1)
                    else:
                        # Fallback for complex shims
                        match = re.search(r"from (packages\.[^ ]+) import", content)
                        if match:
                            mappings[core_module] = match.group(1)
    return mappings

def apply_replacements(target_dir, mapping):
    # Sort mapping by length of core_module (longest first) to prevent partial matching errors
    sorted_core_modules = sorted(mapping.keys(), key=len, reverse=True)
    
    count = 0
    for root, dirs, files in os.walk(target_dir):
        if "__pycache__" in root or ".venv" in root:
            continue
        for name in files:
            if name.endswith(".py"):
                filepath = os.path.join(root, name)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for core_mod in sorted_core_modules:
                    target_mod = mapping[core_mod]
                    
                    # Pattern 1: from core.something import X
                    new_content = new_content.replace(f"from {core_mod} import", f"from {target_mod} import")
                    new_content = new_content.replace(f"import {core_mod}", f"import {target_mod}")
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    count += 1
    return count

# EXECUTE
core_root = r"e:/ai_company_faz12.1/core"
mapping = get_mappings(core_root)

# Correct manual overrides if shim was generic
# mapping["core.agi.schemas"] = "packages.orchestration.agi.schemas"

print(f"Discovered {len(mapping)} shim mappings.")
for k, v in mapping.items():
    print(f"  {k} -> {v}")

api_count = apply_replacements(r"e:/ai_company_faz12.1/apps/api/", mapping)
pkg_count = apply_replacements(r"e:/ai_company_faz12.1/packages/", mapping)
agent_count = apply_replacements(r"e:/ai_company_faz12.1/agents/", mapping)
skill_count = apply_replacements(r"e:/ai_company_faz12.1/skills/", mapping)

print(f"Sterilization complete. Updated {api_count} (api), {pkg_count} (pkg), {agent_count} (agents), {skill_count} (skills).")
