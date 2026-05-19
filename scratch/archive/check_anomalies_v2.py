import asyncio
import sqlite3
import os

async def check_anomalies():
    db_path = "runtime/data/cortex_local_v2.db"
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("--- System Improvements ---")
    try:
        cursor.execute("SELECT COUNT(*) FROM system_improvements WHERE status = 'pending'")
        count = cursor.fetchone()[0]
        print(f"Pending System Improvements: {count}")

        cursor.execute("SELECT id, target_file, status, risk_score FROM system_improvements WHERE status = 'pending' LIMIT 10")
        for row in cursor.fetchall():
            print(row)
    except Exception as e:
        print(f"Error querying system_improvements: {e}")

    print("\n--- Failed Workflow Events ---")
    try:
        cursor.execute("SELECT COUNT(*) FROM workflow_events WHERE event_type = 'step_failed'")
        count = cursor.fetchone()[0]
        print(f"Failed Steps: {count}")
    except Exception as e:
        print(f"Error querying workflow_events: {e}")

    conn.close()

if __name__ == "__main__":
    asyncio.run(check_anomalies())
