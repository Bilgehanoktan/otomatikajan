import sqlite3
import os

db_path = "runtime/data/cortex_local_v2.db"
if not os.path.exists(db_path):
    print(f"File {db_path} does not exist!")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT email, role FROM operators")
        rows = cursor.fetchall()
        for row in rows:
            print(f"Email: {row[0]}, Role: {row[1]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
