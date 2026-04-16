
import sqlite3
import json

db_path = "/app/runtime/data/cortex_local.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check existing columns
    cursor.execute("PRAGMA table_info(projects)")
    existing_cols = [c[1] for c in cursor.fetchall()]

    new_cols = [
        ("isolation_tier", "INTEGER DEFAULT 2"),
        ("autonomy_envelope", "TEXT DEFAULT '{\"mode\": \"advisory\", \"allow_auto_patch\": false, \"max_risk_score\": 0.3, \"isolation_zone\": \"global\"}'"),
        ("concurrency_limit", "INTEGER DEFAULT 5"),
        ("current_budget_usd", "FLOAT DEFAULT 0.0"),
        ("hourly_burn_rate", "FLOAT DEFAULT 0.0"),
        ("economic_profile", "TEXT DEFAULT '{\"steering_policy\": \"cost_optimized\", \"min_budget_threshold\": 10.0, \"auto_scale_concurrency\": true}'"),
        ("metadata_", "TEXT DEFAULT '{}'"),
        ("is_pilot", "BOOLEAN DEFAULT 0")
    ]

    for col_name, col_def in new_cols:
        if col_name not in existing_cols:
            print(f"Adding column {col_name} to projects table...")
            cursor.execute(f"ALTER TABLE projects ADD COLUMN {col_name} {col_def}")
        else:
            print(f"Column {col_name} already exists.")

    conn.commit()
    print("Migration successful.")
except Exception as e:
    print(f"Error during migration: {e}")
    conn.rollback()
finally:
    conn.close()
