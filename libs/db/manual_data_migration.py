import sqlite3

db_path = "e:/ai_company_faz12.1/runtime/data/cortex_local.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("Migrating users to operators...")
    cursor.execute("""
        INSERT OR IGNORE INTO operators (id, email, username, hashed_password, role, is_active, created_at)
        SELECT id, email, email, hashed_password, 
               CASE WHEN is_admin THEN 'SOVEREIGN_PRIME' ELSE 'AUDIT_OBSERVER' END,
               is_active, created_at
        FROM users
    """)
    conn.commit()
    print("Migration successful.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
