import os
import sqlite3

db_path = "e:/ai_company_faz12.1/runtime/data/cortex_local.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in DB:")
    for t in tables:
        print(f" - {t[0]}")
    conn.close()
