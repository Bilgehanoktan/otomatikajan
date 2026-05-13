"""Fix PostgreSQL schema for Docker mode."""
import asyncio
from libs.db.session import get_engine
from sqlalchemy import text

async def fix():
    engine = get_engine()
    async with engine.begin() as conn:
        # 1. Check if workflow_events table exists
        result = await conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'workflow_events')"
        ))
        exists = result.scalar()
        print(f"workflow_events exists: {exists}")

        if not exists:
            print("Creating all missing tables...")
            from libs.db.models.core_models import Base
            from libs.db.models.learning_models import Base as LearningBase
            from libs.db.models.governance_models import Base as GovBase
            from libs.db.models.lineage_models import Base as LineageBase
            from libs.db.models.compliance_models import Base as CompBase
            from libs.db.models.auth_models import Base as AuthBase
            for b in [Base, LearningBase, GovBase, LineageBase, CompBase, AuthBase]:
                await conn.run_sync(b.metadata.create_all)
            print("All tables created.")
        else:
            print("Base tables exist, checking for missing columns...")

        # 2. Fix agent_nodes columns
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'agent_nodes'"
        ))
        agent_cols = [row[0] for row in result.fetchall()]
        
        missing_agent_cols = {
            "success_count": "INTEGER DEFAULT 0",
            "failure_count": "INTEGER DEFAULT 0",
        }
        for col_name, col_type in missing_agent_cols.items():
            if col_name not in agent_cols:
                await conn.execute(text(f"ALTER TABLE agent_nodes ADD COLUMN {col_name} {col_type}"))
                print(f"  Added agent_nodes.{col_name}")

        # 3. Fix decision_lineage columns (CRITICAL FIX)
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'decision_lineage'"
        ))
        lineage_cols = [row[0] for row in result.fetchall()]
        print(f"decision_lineage columns found: {len(lineage_cols)}")

        missing_lineage_cols = {
            "root_id": "UUID",
            "trigger_event": "JSONB",
            "summary": "TEXT",
            "rationale": "TEXT",
            "confidence_score": "DOUBLE PRECISION DEFAULT 1.0",
            "outcome": "TEXT",
            "integrity_hash": "VARCHAR(64)",
            "meta_data": "JSONB DEFAULT '{}'::jsonb"
        }
        
        for col_name, col_type in missing_lineage_cols.items():
            if col_name not in lineage_cols:
                print(f"  Fixing: Adding missing column decision_lineage.{col_name}")
                await conn.execute(text(f"ALTER TABLE decision_lineage ADD COLUMN {col_name} {col_type}"))

    print("Schema fix complete.")

if __name__ == "__main__":
    asyncio.run(fix())
