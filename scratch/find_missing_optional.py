import os
import re

def check_optional_imports(root_dir):
    missing_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if "Optional[" in content and "from typing import" not in content and "import typing" not in content:
                            # Also check if it's imported from typing in a multi-line way
                            if not re.search(r"from typing import.*Optional", content):
                                missing_files.append(path)
                except Exception:
                    pass
    return missing_files

if __name__ == "__main__":
    root = "e:\\ai_company_faz12.1"
    missing = check_optional_imports(root)
    for m in missing:
        print(m)
