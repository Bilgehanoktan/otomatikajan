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

    print("--- Operational Incidents ---")
    try:
        cursor.execute("SELECT COUNT(*) FROM operational_incidents WHERE status != 'resolved'")
        open_incidents = cursor.fetchone()[0]
        print(f"Non-resolved Incidents: {open_incidents}")

        cursor.execute("SELECT id, incident_type, severity, status, message FROM operational_incidents WHERE status != 'resolved' LIMIT 10")
        for row in cursor.fetchall():
            print(row)
    except Exception as e:
        print(f"Error querying operational_incidents: {e}")

    print("\n--- Improvement Opportunities ---")
    try:
        cursor.execute("SELECT COUNT(*) FROM improvement_opportunities WHERE status = 'open'")
        pending_improvements = cursor.fetchone()[0]
        print(f"Open Improvements: {pending_improvements}")

        cursor.execute("SELECT id, title, category, severity, status FROM improvement_opportunities WHERE status = 'open' LIMIT 10")
        for row in cursor.fetchall():
            print(row)
    except Exception as e:
        print(f"Error querying improvement_opportunities: {e}")

    conn.close()

if __name__ == "__main__":
    asyncio.run(check_anomalies())
