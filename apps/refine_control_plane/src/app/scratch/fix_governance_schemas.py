
import asyncio
from sqlalchemy import text
from libs.db.session import AsyncSessionLocal

async def fix_all_governance_schemas():
    async with AsyncSessionLocal() as db:
        engine_name = db.bind.dialect.name
        print(f"Engine: {engine_name}")
        
        # List of tables to check and their expected missing columns
        checks = [
            ("production_signoffs", "created_at", "DATETIME"),
            ("validation_results", "created_at", "DATETIME"),
            ("handover_events", "created_at", "DATETIME"),
            ("sovereign_goals", "completed_at", "DATETIME"),
            ("governor_runtime", "created_at", "DATETIME"),
            ("governor_drills", "created_at", "DATETIME"),
            ("governor_slo_samples", "created_at", "DATETIME"),
            ("governor_policy_evolutions", "created_at", "DATETIME"),
            ("governor_policy_snapshots", "created_at", "DATETIME"),
            ("governor_alerts", "created_at", "DATETIME"),
            ("governor_metric_aggregates", "created_at", "DATETIME"),
            ("governor_drifts", "created_at", "DATETIME"),
        ]
        
        for table, column, col_type in checks:
            try:
                # Check if column exists
                res = await db.execute(text(f"PRAGMA table_info({table})"))
                columns = [r[1] for r in res.fetchall()]
                if column in columns:
                    print(f"Column {column} already exists in {table}")
                    continue
                
                print(f"Adding {column} to {table}...")
                await db.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                await db.commit()
                print(f"Successfully added {column} to {table}")
            except Exception as e:
                print(f"Error fixing {table}: {e}")

if __name__ == "__main__":
    asyncio.run(fix_all_governance_schemas())
