
import sqlite3
import json

db_path = "/app/runtime/data/cortex_local.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_col(table, col, definition):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
        print(f"  Added {col} to {table}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            pass
        else:
            print(f"  Error adding {col} to {table}: {e}")

try:
    print("Migrating projects...")
    cursor.execute("PRAGMA table_info(projects)")
    cols = [c[1] for c in cursor.fetchall()]
    if "isolation_tier" not in cols: add_col("projects", "isolation_tier", "INTEGER DEFAULT 2")
    if "autonomy_envelope" not in cols: add_col("projects", "autonomy_envelope", "TEXT DEFAULT '{\"mode\": \"advisory\"}'")
    if "concurrency_limit" not in cols: add_col("projects", "concurrency_limit", "INTEGER DEFAULT 5")
    if "current_budget_usd" not in cols: add_col("projects", "current_budget_usd", "FLOAT DEFAULT 0.0")
    if "hourly_burn_rate" not in cols: add_col("projects", "hourly_burn_rate", "FLOAT DEFAULT 0.0")
    if "economic_profile" not in cols: add_col("projects", "economic_profile", "TEXT DEFAULT '{}'")
    if "metadata_" not in cols: add_col("projects", "metadata_", "TEXT DEFAULT '{}'")
    if "is_pilot" not in cols: add_col("projects", "is_pilot", "BOOLEAN DEFAULT 0")

    print("Migrating system_improvements...")
    cursor.execute("PRAGMA table_info(system_improvements)")
    cols = [c[1] for c in cursor.fetchall()]
    if "risk_score" not in cols: add_col("system_improvements", "risk_score", "FLOAT DEFAULT 0.0")
    if "impact_rating" not in cols: add_col("system_improvements", "impact_rating", "FLOAT DEFAULT 0.0")
    if "confidence_score" not in cols: add_col("system_improvements", "confidence_score", "FLOAT DEFAULT 0.0")
    if "metadata_" not in cols: add_col("system_improvements", "metadata_", "TEXT DEFAULT '{}'")

    print("Migrating operational_incidents...")
    cursor.execute("PRAGMA table_info(operational_incidents)")
    cols = [c[1] for c in cursor.fetchall()]
    # Mapping old names to new if needed
    if "category" not in cols and "incident_type" in cols:
        try:
            cursor.execute("ALTER TABLE operational_incidents RENAME COLUMN incident_type TO category")
            print("  Renamed incident_type to category in operational_incidents")
        except: pass
    if "error_message" not in cols and "message" in cols:
        try:
            cursor.execute("ALTER TABLE operational_incidents RENAME COLUMN message TO error_message")
            print("  Renamed message to error_message in operational_incidents")
        except: pass
    
    # Re-fetch columns after renames
    cursor.execute("PRAGMA table_info(operational_incidents)")
    cols = [c[1] for c in cursor.fetchall()]
    
    if "category" not in cols: add_col("operational_incidents", "category", "TEXT")
    if "error_message" not in cols: add_col("operational_incidents", "error_message", "TEXT")
    if "stack_trace" not in cols: add_col("operational_incidents", "stack_trace", "TEXT")
    if "causal_node" not in cols: add_col("operational_incidents", "causal_node", "TEXT")
    if "root_cause" not in cols: add_col("operational_incidents", "root_cause", "TEXT")
    if "mitigation" not in cols: add_col("operational_incidents", "mitigation", "TEXT")
    if "resolution_summary" not in cols: add_col("operational_incidents", "resolution_summary", "TEXT")
    if "risk_score" not in cols: add_col("operational_incidents", "risk_score", "FLOAT DEFAULT 0.0")
    if "blast_radius" not in cols: add_col("operational_incidents", "blast_radius", "FLOAT DEFAULT 0.0")
    if "metadata_" not in cols: add_col("operational_incidents", "metadata_", "TEXT DEFAULT '{}'")

    print("Creating federation tables...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS federation_trust (
            cluster_id TEXT PRIMARY KEY,
            trust_score FLOAT DEFAULT 1.0,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            arbitration_wins INTEGER DEFAULT 0,
            last_activity_at TIMESTAMP,
            cluster_metadata TEXT DEFAULT '{}',
            updated_at TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS federation_trust_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cluster_id TEXT NOT NULL,
            trust_score FLOAT NOT NULL,
            change_reason TEXT,
            payload TEXT DEFAULT '{}',
            created_at TIMESTAMP
        )
    """)

    conn.commit()
    print("Full migration successful.")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
