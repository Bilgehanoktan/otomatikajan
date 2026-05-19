
import sqlite3
db_path = "/app/runtime/data/cortex_local.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables in DB:")
for t in sorted(tables):
    print(f"- {t}")
conn.close()
