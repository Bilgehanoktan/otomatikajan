import sqlite3
import os

db_path = 'runtime/data/cortex_local.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
print(f"Tables in {db_path}:")
for t in sorted(tables):
    print(f" - {t}")

# Check if new tables are present
new_tables = ['error_fingerprints', 'learning_records', 'strategy_memory']
missing = [t for t in new_tables if t not in tables]

if not missing:
    print("\nSUCCESS: All new learning tables are present.")
else:
    print(f"\nFAILED: Missing tables: {missing}")
