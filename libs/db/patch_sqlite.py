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
        # Projects Table Patches
        print("Checking projects table for missing columns...")
        for col in [("last_error", "TEXT"), ("updated_at", "DATETIME")]:
            try:
                cursor.execute(f"ALTER TABLE projects ADD COLUMN {col[0]} {col[1]}")
                print(f"Added {col[0]} to projects")
            except sqlite3.OperationalError: pass

        # Subtasks Table Patches
        print("Checking subtasks table for missing columns...")
        for col in [("internal_monologue", "TEXT"), ("llm_provider", "TEXT")]:
            try:
                cursor.execute(f"ALTER TABLE subtasks ADD COLUMN {col[0]} {col[1]}")
                print(f"Added {col[0]} to subtasks")
            except sqlite3.OperationalError: pass

        # Agent Nodes Table Patches
        print("Checking agent_nodes table for missing columns...")
        for col in [("success_count", "INTEGER DEFAULT 0"), ("failure_count", "INTEGER DEFAULT 0")]:
            try:
                cursor.execute(f"ALTER TABLE agent_nodes ADD COLUMN {col[0]} {col[1]}")
                print(f"Added {col[0]} to agent_nodes")
            except sqlite3.OperationalError: pass
            
        # Decision Lineage Table Patches
        print("Checking decision_lineage table for missing columns...")
        try:
            cursor.execute("ALTER TABLE decision_lineage ADD COLUMN outcome TEXT")
            print("Added outcome to decision_lineage")
        except sqlite3.OperationalError: pass

        conn.commit()
        print("Patching completed successfully.")
    except Exception as e:
        print(f"Patching failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    patch()
