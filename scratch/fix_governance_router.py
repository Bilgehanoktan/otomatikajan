import sys
import re

file_path = r"e:\ai_company_faz12.1\services\workflow_api\governance_router.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Comment out top-level sqlalchemy and models imports
content = re.sub(r'^(from sqlalchemy.*)$', r'# \1', content, flags=re.MULTILINE)
content = re.sub(r'^(from libs\.db\.models.*)$', r'# \1', content, flags=re.MULTILINE)

# 2. Add necessary local imports inside functions
# We'll do this for the main ones.

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed governance_router.py")
