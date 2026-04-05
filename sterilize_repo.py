import os
import re

# THE REMEDIATOR: Fixes specific modular import errors introduced by early sterilization
def remediation():
    fixes = {
        "packages.persistence.repository": "packages.persistence.repositories.repository",
        "packages.persistence.models.repair_models": "packages.persistence.models.repair_models", # No change needed here if previous fix was manual
        # Add other common mistranslations
        "packages.orchestration.agi.world": "packages.orchestration.agi.world" # (Check if correct)
    }
    
    count = 0
    full_scan_dirs = ["apps", "packages", "agents", "skills", "tools", "startup"]
    for d_base in full_scan_dirs:
        d = os.path.join("e:/ai_company_faz12.1/", d_base)
        if not os.path.exists(d): continue
        
        for root, dirs, files in os.walk(d):
            if any(exc in root for exc in ["__pycache__", ".venv", ".git"]): continue
            for name in files:
                if name.endswith(".py"):
                    filepath = os.path.join(root, name)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = content
                    for src, target in fixes.items():
                        new_content = new_content.replace(src, target)
                        # Specific case for repository pluralization
                        if "from packages.persistence.repository import" in new_content:
                             new_content = new_content.replace("from packages.persistence.repository import", "from packages.persistence.repositories.repository import")
                    
                    if new_content != content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        count += 1
    return count

print(f"Remediation complete. Updated {remediation()} files.")
