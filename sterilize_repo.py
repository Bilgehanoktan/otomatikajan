import os
import re

# Repo Sterilization Script for Sovereign AGI (Faz 12.1)
# IMPROVED: Handles sub-imports (core.agi.world.engine -> packages.orchestration.agi.world.engine)

def get_mappings(root_core):
    mappings = {}
    for root, dirs, files in os.walk(root_core):
        for name in files:
            if name.endswith(".py"):
                file_path = os.path.join(root, name)
                rel_path = os.path.relpath(file_path, root_core)
                
                core_module = "core." + rel_path.replace("\\", ".").replace("/", ".").replace(".py", "")
                if core_module.endswith(".__init__"):
                    core_module = core_module[:-9]
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r"from (packages\.[^ ]+) import \*", content)
                    if match:
                        mappings[core_module] = match.group(1)
                    else:
                        match = re.search(r"from (packages\.[^ ]+) import", content)
                        if match:
                            mappings[core_module] = match.group(1)
    
    # Manual high-level mappings
    mappings["core.agi"] = "packages.orchestration.agi"
    mappings["core.agency"] = "packages.orchestration.agency"
    mappings["core.improvement"] = "packages.orchestration.experimental"

    return mappings

def apply_replacements(target_dir, mapping):
    # Sort mapping by length of core_module (longest first)
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
                    
                    # Pattern 1: from core.X[.Y] import Z
                    # We match core.X as a prefix
                    pattern_from = re.compile(r"from " + re.escape(core_mod) + r"(\.[a-zA-Z0-9_\.]+)? import")
                    new_content = pattern_from.sub(r"from " + target_mod + r"\1 import", new_content)
                    
                    # Pattern 2: import core.X[.Y]
                    pattern_import = re.compile(r"import " + re.escape(core_mod) + r"(\.[a-zA-Z0-9_\.]+)?")
                    new_content = pattern_import.sub(r"import " + target_mod + r"\1", new_content)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    count += 1
    return count

# EXECUTE
core_root = r"e:/ai_company_faz12.1/core"
mapping = get_mappings(core_root)

print(f"Discovered {len(mapping)} shim mappings.")

api_count = apply_replacements(r"e:/ai_company_faz12.1/apps/api/", mapping)
pkg_count = apply_replacements(r"e:/ai_company_faz12.1/packages/", mapping)
agent_count = apply_replacements(r"e:/ai_company_faz12.1/agents/", mapping)
skill_count = apply_replacements(r"e:/ai_company_faz12.1/skills/", mapping)

print(f"Sterilization complete. Updated {api_count} (api), {pkg_count} (pkg), {agent_count} (agents), {skill_count} (skills).")
