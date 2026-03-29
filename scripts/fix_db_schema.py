
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
            conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS budget_limit FLOAT DEFAULT 0.0"))
            conn.commit()
            print("Successfully ensured budget_limit column exists in projects table.")
        except Exception as e:
            print(f"Error checking/adding column: {e}")

if __name__ == "__main__":
    fix_schema()
