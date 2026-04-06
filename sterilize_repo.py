import os
import re

# THE DEFINITIVE REMEDIATOR: Phase 12.1 Final Fixes
def definitive_remediation():
    # Use accurate mappings for the newly moved modules
    fixes = {
        "from packages.persistence.repair_models": "from packages.persistence.models.repair_models",
        "import packages.persistence.repair_models": "import packages.persistence.models.repair_models",
        "from packages.persistence.repository": "from packages.persistence.repositories.repository",
        "import packages.persistence.repository": "import packages.persistence.repositories.repository",
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
                    
                    if new_content != content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        count += 1
    return count

print(f"Definitive Remediation complete. Updated {definitive_remediation()} files.")
