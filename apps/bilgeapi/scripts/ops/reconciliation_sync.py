import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, insert, inspect, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
import uuid

# Add workspace to path for imports
sys.path.append(os.getcwd())

from libs.db.base import Base
from libs.db.session import DATABASE_URL
from libs.db.models.core_models import Project, SubTask, TaskLog, WorkflowEvent, User, ApprovalRequest, OperationalIncident
from libs.db.models.lineage_models import DecisionLineage

SQLITE_URL = "sqlite+aiosqlite:///./runtime/data/cortex_local.db"

async def reconcile_table(sqlite_session: AsyncSession, pg_session: AsyncSession, model):
    table_name = model.__tablename__
    print(f"Reconciling table: {table_name}...")
    
    # Get all records from SQLite
    result = await sqlite_session.execute(select(model))
    items = result.scalars().all()
    
    if not items:
        print(f"   No records found in SQLite for {table_name}.")
        return

    success_count = 0
    fail_count = 0
    
    for item in items:
        # Convert to dict, removing relationship attributes
        data = {}
        mapper = inspect(model).mapper
        for column in mapper.column_attrs:
            val = getattr(item, column.key)
            if val is None:
                # Check if there is a default value defined in the model
                col_obj = column.columns[0]
                if col_obj.default is not None and hasattr(col_obj.default, "arg"):
                    if not callable(col_obj.default.arg):
                        val = col_obj.default.arg
            data[column.key] = val
        
        # Special handling for SubTask: avoid self-referential FK issues on first pass
        original_parent_id = None
        if model == SubTask and data.get("parent_id"):
            original_parent_id = data["parent_id"]
            data["parent_id"] = None

        try:
            # PostgreSQL Upsert (on conflict do update)
            stmt = pg_insert(model).values(**data)
            pk_columns = [c.name for c in inspect(model).mapper.primary_key]
            
            if pk_columns:
                update_dict = {k: v for k, v in data.items() if k not in pk_columns}
                if update_dict:
                    stmt = stmt.on_conflict_do_update(
                        index_elements=pk_columns,
                        set_=update_dict
                    )
                else:
                    stmt = stmt.on_conflict_do_nothing(index_elements=pk_columns)
            
            await pg_session.execute(stmt)
            await pg_session.commit()
            
            # If it was a SubTask with a parent, we'll fix the parent_id in pass 2
            # or just try to update it immediately if we are confident the parent exists?
            # Better to do a second pass for parent_id.
            
            success_count += 1
        except Exception as e:
            await pg_session.rollback()
            print(f"   [FAIL] {table_name} ID {data.get('id')}: {str(e)}")
            fail_count += 1
    
    print(f"   Summary for {table_name}: {success_count} success, {fail_count} failed.")

async def fix_subtask_parents(sqlite_session: AsyncSession, pg_session: AsyncSession):
    print("Fixing SubTask parent_id references...")
    result = await sqlite_session.execute(select(SubTask).where(SubTask.parent_id.is_not(None)))
    items = result.scalars().all()
    
    fixed_count = 0
    for item in items:
        try:
            await pg_session.execute(
                update(SubTask)
                .where(SubTask.id == item.id)
                .values(parent_id=item.parent_id)
            )
            await pg_session.commit()
            fixed_count += 1
        except Exception:
            await pg_session.rollback()
            
    print(f"   Fixed {fixed_count} parent_id references.")

async def run_reconciliation():
    print("--- PRMR-01 Advanced Data Reconciliation Utility ---")
    
    sqlite_engine = create_async_engine(SQLITE_URL)
    pg_engine = create_async_engine(DATABASE_URL)
    
    sqlite_session_factory = sessionmaker(sqlite_engine, class_=AsyncSession, expire_on_commit=False)
    pg_session_factory = sessionmaker(pg_engine, class_=AsyncSession, expire_on_commit=False)
    
    # Order matters: Parents first
    models_to_sync = [
        User,
        Project,
        SubTask,
        TaskLog,
        WorkflowEvent,
        ApprovalRequest,
        OperationalIncident,
        DecisionLineage
    ]
    
    async with sqlite_session_factory() as sqlite_session:
        async with pg_session_factory() as pg_session:
            for model in models_to_sync:
                await reconcile_table(sqlite_session, pg_session, model)
            
            # Final pass for subtask parents
            await fix_subtask_parents(sqlite_session, pg_session)
    
    print("\nReconciliation Complete. System data is now unified in PostgreSQL.")

if __name__ == "__main__":
    asyncio.run(run_reconciliation())
