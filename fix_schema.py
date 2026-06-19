"""Fix PostgreSQL and SQLite schemas automatically by syncing with SQLAlchemy models."""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.schema import CreateColumn

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from libs.db.session import get_sync_engine
from libs.db.models.core_models import Base
from libs.db.models.learning_models import Base as LearningBase
from libs.db.models.governance_models import Base as GovBase
from libs.db.models.lineage_models import Base as LineageBase
from libs.db.models.compliance_models import Base as CompBase
from libs.db.models.auth_models import Base as AuthBase
from libs.db.models.repair_models import Base as RepairBase
from libs.db.models.federation_models import Base as FederationBase
from libs.db.models.ui_repair_models import Base as UIRepairBase
from apps.bilgeapi.models.database import Base as BilgeBase

def get_pg_engine():
    pg_url = "postgresql://postgres:postgres@localhost:5433/ai_company"
    try:
        engine = create_engine(pg_url)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception:
        return None

def get_sqlite_engine():
    db_path = os.path.join("runtime", "data", "cortex_local_v2.db")
    if not os.path.exists(db_path):
        return None
    abs_path = os.path.abspath(db_path).replace('\\', '/')
    sqlite_url = f"sqlite:///{abs_path}"
    try:
        engine = create_engine(sqlite_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception:
        return None

def sync_database(engine, name):
    print(f"--- Auto-Syncing {name} Database Schema ---")
    
    # 1. Create missing tables
    bases = [Base, LearningBase, GovBase, LineageBase, CompBase, AuthBase, RepairBase, FederationBase, UIRepairBase, BilgeBase]
    for b in bases:
        b.metadata.create_all(bind=engine)
    
    # Collect all table models
    all_table_models = {}
    for b in bases:
        all_table_models.update(b.metadata.tables)
        
    dialect = engine.dialect
    dialect_name = dialect.name # 'postgresql' or 'sqlite'
    
    with engine.begin() as conn:
        for table_name, table_model in all_table_models.items():
            # Get columns from DB
            if dialect_name == "postgresql":
                res = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = '{table_name}'
                """))
                db_cols = {row[0] for row in res.fetchall()}
            else:  # sqlite
                res = conn.execute(text(f"PRAGMA table_info({table_name})"))
                db_cols = {row[1] for row in res.fetchall()}
                
            if not db_cols:
                continue
                
            # Compare with model columns
            for col_name, column in table_model.columns.items():
                if col_name not in db_cols:
                    print(f"Table '{table_name}': column '{col_name}' is missing in {name} DB.")
                    
                    # Compile DDL for adding column
                    orig_nullable = column.nullable
                    column.nullable = True
                    
                    try:
                        ddl_compiler = CreateColumn(column)
                        compiled_ddl = str(ddl_compiler.compile(dialect=dialect))
                        
                        alter_query = f"ALTER TABLE {table_name} ADD COLUMN {compiled_ddl}"
                        print(f"  Executing: {alter_query}")
                        conn.execute(text(alter_query))
                        print(f"  Successfully added column '{col_name}' to '{table_name}'.")
                    except Exception as ex:
                        print(f"  Error adding column '{col_name}' to '{table_name}': {ex}")
                    finally:
                        column.nullable = orig_nullable

def run_fix():
    # 1. Fix default configured engine
    try:
        default_engine = get_sync_engine()
        sync_database(default_engine, "Default Configured")
    except Exception as e:
        print(f"Error running sync on default engine: {e}")
        
    # 2. Fix PostgreSQL specifically if available and not already sync'd
    pg_eng = get_pg_engine()
    if pg_eng:
        try:
            sync_database(pg_eng, "PostgreSQL")
        except Exception as e:
            print(f"Error running sync on PostgreSQL: {e}")
            
    # 3. Fix SQLite specifically if available and not already sync'd
    sqlite_eng = get_sqlite_engine()
    if sqlite_eng:
        try:
            sync_database(sqlite_eng, "SQLite")
        except Exception as e:
            print(f"Error running sync on SQLite: {e}")

if __name__ == "__main__":
    run_fix()
