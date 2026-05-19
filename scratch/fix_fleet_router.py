import sys
import re

file_path = r"e:\ai_company_faz12.1\services\workflow_api\fleet_router.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Comment out top-level sqlalchemy and models imports
content = re.sub(r'^(from sqlalchemy.*)$', r'# \1', content, flags=re.MULTILINE)
content = re.sub(r'^(from libs\.db\.models.*)$', r'# \1', content, flags=re.MULTILINE)

# 2. Add 'from typing import Any' if not present
if 'from typing import Any' not in content:
    content = content.replace('from typing import', 'from typing import Any,')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed fleet_router.py")
