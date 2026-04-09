import os
import re

TESTS_DIR = "tests"

MAPPINGS = {
    r"from api\.skills_router": "from apps.api.routers.skills",
    r"from api\.ceo_router": "from apps.api.routers.ceo",
    r"from api\.task_write_router": "from apps.api.routers.task_write",
    r"from api\.resilience": "from apps.api.support.resilience",
    r"from api\.rate_limiter": "from apps.api.support.rate_limiter",
    r"from api\._task_shared": "from apps.api.support._task_shared",
    # Generic router fallback (if any remain)
    r"from api\.": "from apps.api.routers.",
}

def fix_imports():
    for root, dirs, files in os.walk(TESTS_DIR):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                new_content = content
                for pattern, replacement in MAPPINGS.items():
                    new_content = re.sub(pattern, replacement, new_content)
                
                if new_content != content:
                    print(f"Fixed: {path}")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)

if __name__ == "__main__":
    fix_imports()
