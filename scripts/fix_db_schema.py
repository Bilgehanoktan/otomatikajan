
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Re-load env manually for safety
load_dotenv()
if os.path.exists(".env.local"):
    load_dotenv(".env.local", override=True)

def fix_schema():
    raw_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_company")
    sync_url = raw_url.replace("+asyncpg", "")
    
    print(f"Connecting to: {sync_url} (Sync)")
    engine = create_engine(sync_url)
    
    with engine.connect() as conn:
        try:
            # 1. Ensure goal_id exists for Sovereign Goals (Faz 12.1)
            # Use raw SQL as SQLite doesn't support 'IF NOT EXISTS' in some versions
            try:
                conn.execute(text("ALTER TABLE projects ADD COLUMN goal_id UUID"))
                print("Added goal_id column to projects table.")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("goal_id column already exists.")
                else:
                    raise e
            
            # 2. Ensure budget_limit exists
            try:
                conn.execute(text("ALTER TABLE projects ADD COLUMN budget_limit FLOAT DEFAULT 0.0"))
                print("Added budget_limit column to projects table.")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("budget_limit column already exists.")
                else:
                    raise e

            conn.commit()
            print("Database schema synchronization complete.")
        except Exception as e:
            print(f"Error checking/adding columns: {e}")

if __name__ == "__main__":
    fix_schema()
