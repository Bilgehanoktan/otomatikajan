
import sqlite3
import os

db_path = 'e:/ai_company_faz12.1/runtime/data/cortex_local.db'

def patch():
    print(f"[*] Patching SQLite: {db_path}")
    if not os.path.exists(db_path):
        print("[!] SQLite file not found, skipping.")
        return
        
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE decision_lineage ADD COLUMN outcome TEXT")
        conn.commit()
        print("[+] SQLITE SUCCESS: decision_lineage.outcome added.")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("[*] Column already exists in SQLite.")
        else:
            print(f"[!] SQLITE FAILED: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    patch()
