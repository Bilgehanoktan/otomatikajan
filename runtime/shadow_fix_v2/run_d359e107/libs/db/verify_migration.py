import sqlite3

db_path = "e:/ai_company_faz12.1/runtime/data/cortex_local.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM operators")
count = cursor.fetchone()[0]
print(f"Total operators: {count}")

cursor.execute("SELECT id, email, role FROM operators LIMIT 5")
rows = cursor.fetchall()
for r in rows:
    print(f"Operator: {r}")

conn.close()
