import sqlite3
import os

db_path = 'runtime/data/cortex_local.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Blanket Normalize all ENUM-like columns to UPPERCASE
    cursor.execute("UPDATE projects SET source = UPPER(source)")
    cursor.execute("UPDATE projects SET status = UPPER(status)")
    cursor.execute("UPDATE projects SET priority = UPPER(priority)")
    
    cursor.execute("UPDATE subtasks SET status = UPPER(status)")
    
    # Check DecisionLineage if table exists
    try:
        cursor.execute("UPDATE decision_lineage SET outcome = UPPER(outcome)")
    except:
        pass
        
    print(f"Update complete.")
    conn.commit()
    conn.close()
    print("SQLite GLOBAL UPPERCASE normalization complete.")
else:
    print("SQLite DB not found.")
