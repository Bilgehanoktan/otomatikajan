"""Fix PostgreSQL schema for Docker mode."""
import asyncio
from libs.db.session import get_engine
from sqlalchemy import text

async def fix():
    engine = get_engine()
    async with engine.begin() as conn:
        # Check if workflow_events table exists
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
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'workflow_events' ORDER BY ordinal_position"
            ))
            cols = [row[0] for row in result.fetchall()]
            print(f"workflow_events columns: {cols}")

        # Check and fix agent_nodes columns
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'agent_nodes' ORDER BY ordinal_position"
        ))
        agent_cols = [row[0] for row in result.fetchall()]
        print(f"agent_nodes columns: {agent_cols}")

        missing_cols = {
            "success_count": "INTEGER DEFAULT 0",
            "failure_count": "INTEGER DEFAULT 0",
        }
        
        # SQL Injection (DDL) önlemi: col_name ve col_type güvenilir listeye (whitelist) uygun mu?
        for col_name, col_type in missing_cols.items():
            if col_name not in agent_cols:
                if not col_name.isidentifier() or " " in col_name:
                    print(f"Skipping dangerous column name: {col_name}")
                    continue
                
                # İzin verilen tipler whitelist
                allowed_types = ["INTEGER DEFAULT 0", "VARCHAR(255)", "TEXT", "BOOLEAN DEFAULT FALSE"]
                if col_type not in allowed_types:
                    print(f"Skipping dangerous column type: {col_type}")
                    continue
                    
                await conn.execute(text(f"ALTER TABLE agent_nodes ADD COLUMN {col_name} {col_type}"))
                print(f"  Added agent_nodes.{col_name}")

    print("Schema fix complete.")

asyncio.run(fix())
