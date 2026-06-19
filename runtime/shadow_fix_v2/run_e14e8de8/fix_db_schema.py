import sqlite3
import os

def fix_sqlite():
    db_path = os.path.join("runtime", "data", "cortex_local_v2.db")
    if not os.path.exists(db_path):
        print(f"SQLite database not found at {db_path}")
        return

    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if outcome column exists in decision_lineage
        cursor.execute("PRAGMA table_info(decision_lineage)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "outcome" not in columns:
            print("Adding 'outcome' column to 'decision_lineage' table...")
            cursor.execute("ALTER TABLE decision_lineage ADD COLUMN outcome TEXT")
            conn.commit()
            print("Successfully added 'outcome' column.")
        else:
            print("'outcome' column already exists in 'decision_lineage'.")
            
    except sqlite3.OperationalError as e:
        print(f"Error checking/altering table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_sqlite()
