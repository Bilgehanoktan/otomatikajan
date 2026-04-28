import sqlite3
import os

DB_PATH = "runtime/data/cortex_local_v2.db"

def patch():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Checking agent_nodes table for missing columns...")
        # Add success_count to agent_nodes
        try:
            cursor.execute("ALTER TABLE agent_nodes ADD COLUMN success_count INTEGER DEFAULT 0")
            print("Added success_count to agent_nodes")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("Column success_count already exists.")
            else:
                print(f"Error adding success_count: {e}")

        # Add failure_count to agent_nodes
        try:
            cursor.execute("ALTER TABLE agent_nodes ADD COLUMN failure_count INTEGER DEFAULT 0")
            print("Added failure_count to agent_nodes")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("Column failure_count already exists.")
            else:
                print(f"Error adding failure_count: {e}")

        conn.commit()
        print("Patching completed successfully.")
    except Exception as e:
        print(f"Patching failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    patch()
