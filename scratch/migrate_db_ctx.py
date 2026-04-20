import os
import re

def migrate_db_usage(root_dir):
    print(f"[*] Starting migration in: {root_dir}")
    
    # Regex Patterns
    # 1. async with get_db() as ...
    # 2. from libs.db.session import get_db -> from libs.db.session import get_db, get_db_ctx
    ctx_usage_pattern = re.compile(r'async with get_db\(\)')
    import_pattern = re.compile(r'from libs\.db\.session import (.*?)get_db')

    for root, dirs, files in os.walk(root_dir):
        # Skip virtual environments and hidden dirs
        if any(x in root for x in [".venv", "node_modules", ".git", "__pycache__"]):
            continue
            
        for file in files:
            if not file.endswith(".py"):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"[!] Error reading {file_path}: {e}")
                continue

            if ctx_usage_pattern.search(content):
                print(f"[+] Migrating usage: {file_path}")
                # Replace usage
                new_content = ctx_usage_pattern.sub('async with get_db_ctx()', content)
                
                # Check for imports
                match = import_pattern.search(new_content)
                if match:
                    # If get_db_ctx is not already there
                    if 'get_db_ctx' not in match.group(0):
                        new_content = import_pattern.sub(r'from libs.db.session import \1get_db, get_db_ctx', new_content)
                    
                # Standardize spacing if needed
                new_content = new_content.replace('get_db, get_db_ctx', 'get_db, get_db_ctx')

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            
            # Special case for any Depends(get_db) left
            if 'Depends(get_db)' in content:
                print(f"[+] Migrating dependency: {file_path}")
                new_content = content.replace('Depends(get_db)', 'Depends(get_db)')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

if __name__ == "__main__":
    base_dir = r"e:\ai_company_faz12.1"
    migrate_db_usage(base_dir)
    print("[*] Migration complete.")
