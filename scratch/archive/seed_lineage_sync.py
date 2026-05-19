
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Sync SQLite for absolute certainty
DB_PATH = r'e:\ai_company_faz12.1\runtime\data\cortex_local.db'
engine = create_engine(f"sqlite:///{DB_PATH}")

def seed_lineage():
    with engine.connect() as conn:
        print("--- Seeding Decision Lineage (Sync) ---")
        
        # Ensure table exists (though init_db should have done it)
        # DecisionLineage columns: id, decision_type, component_name, parent_id, root_id, trigger_event, rationale, confidence_score, outcome, integrity_hash, meta_data, created_at
        
        # Clean existing
        conn.execute(text("DELETE FROM decision_lineage"))
        
        # Insert
        stmt = text("""
            INSERT INTO decision_lineage (id, decision_type, component_name, rationale, outcome, confidence_score, created_at)
            VALUES (:id, :type, :comp, :rat, :out, :conf, :created)
        """)
        
        conn.execute(stmt, {
            "id": uuid.uuid4().hex,
            "type": "POLICY_CHANGE",
            "comp": "LearningEngine",
            "rat": "High error rate (8.5%) detected in API. Scaling strategy adjustment proposed.",
            "out": "PROPOSED",
            "conf": 0.95,
            "created": datetime.now(timezone.utc).isoformat()
        })
        
        conn.commit()
        print("Lineage seeded successfully.")

if __name__ == "__main__":
    seed_lineage()
