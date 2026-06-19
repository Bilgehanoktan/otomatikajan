import sqlite3
import traceback

db_path = 'E:/Otomasyon/backend/company.db'
con = sqlite3.connect(db_path)
cursor = con.cursor()

try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]

    for table_name in tables:
        try:
            cursor.execute(f"SELECT count(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"{table_name}: OK ({count} rows)")
        except Exception as e:
            print(f"{table_name}: ERROR - {e}")
            
    # Try reading tasks one by one to see how many we can save
    if 'tasks' in tables:
        print("\n--- Testing tasks table rows ---")
        try:
            cursor.execute("SELECT id FROM tasks")
            rows = cursor.fetchall()
            print(f"Successfully retrieved {len(rows)} task IDs.")
        except Exception as e:
            print(f"Failed to retrieve task IDs: {e}")
except Exception as e:
    print(f"Global error: {e}")
