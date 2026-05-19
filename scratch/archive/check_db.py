import sqlite3
import os

db_path = r'e:\ai_company_faz12.1\services\workflow_api\sovereign.db'
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(decision_lineage)")
    cols = cursor.fetchall()
    for col in cols:
        print(col)
    conn.close()
