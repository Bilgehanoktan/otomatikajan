import sqlite3
import os

DB_PATH = "runtime/data/cortex_local.db"

def patch_schema():
    if not os.path.exists(DB_PATH):
        print(f"SQLite DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Add missing column to decision_lineage
    try:
        cursor.execute("ALTER TABLE decision_lineage ADD COLUMN outcome TEXT;")
        print("   Added 'outcome' column to 'decision_lineage'.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("   'outcome' column already exists in 'decision_lineage'.")
        else:
            print(f"   Warning patching decision_lineage: {e}")

    # 2. Add any other missing columns if needed
    # (Future-proofing for other drift)
    
    conn.commit()
    conn.close()
    print("SQLite patching complete.")

if __name__ == "__main__":
    patch_schema()
