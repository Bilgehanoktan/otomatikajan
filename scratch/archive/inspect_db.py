
import sqlite3
import os

db_path = "./runtime/data/cortex_local.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("PRAGMA table_info(projects)")
    columns = cursor.fetchall()
    print("Columns in 'projects' table:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
except Exception as e:
    print(f"Error inspecting table: {e}")
finally:
    conn.close()
