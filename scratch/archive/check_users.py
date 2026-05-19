
import sqlite3
import os

db_path = "runtime/data/cortex_local.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Tables ---")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print(tables)

for table in ["users", "operators"]:
    if table in tables:
        print(f"\n--- {table} ---")
        try:
            cursor.execute(f"SELECT * FROM {table}")
            cols = [description[0] for description in cursor.description]
            print(f"Columns: {cols}")
            rows = cursor.fetchall()
            for row in rows:
                print(row)
        except Exception as e:
            print(f"Error reading {table}: {e}")

conn.close()
