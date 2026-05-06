
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy import inspect, create_engine, text
from libs.config import DATABASE_URL
from libs.db.base import Base
# Import all models to ensure they are registered in Base.metadata
import libs.db.models.core_models
import libs.db.models.learning_models
import libs.db.models.governance_models

logger = logging.getLogger("diagnostics.auditor")

class InfrastructureAuditor:
    """
    Sovereign AGI Proactive Infrastructure Auditor.
    Detects drifts between model definitions and physical infrastructure.
    """

    @staticmethod
    def audit_db_schema() -> List[Dict[str, Any]]:
        """
        Compares SQLAlchemy models with the physical database schema.
        Returns a list of diagnostic findings with suggested fixes.
        """
        findings = []
        
        # Normalize URL for sync inspection
        sync_url = DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", "")
        # Ensure postgresql scheme is correct for psycopg2 (default sync driver)
        if sync_url.startswith("postgresql"):
            if "://" in sync_url:
                prefix, rest = sync_url.split("://", 1)
                sync_url = f"postgresql://{rest}"

        try:
            engine = create_engine(sync_url)
            inspector = inspect(engine)
            
            for table_name, table_obj in Base.metadata.tables.items():
                if not inspector.has_table(table_name):
                    findings.append({
                        "type": "SCHEMA_DRIFT",
                        "subtype": "MISSING_TABLE",
                        "severity": "CRITICAL",
                        "component": f"DB: {table_name}",
                        "message": f"Table '{table_name}' is missing from the database.",
                        "diagnosis": f"The model '{table_obj.key}' is defined but the physical table does not exist.",
                        "suggested_fix": {
                            "method": "MIGRATION",
                            "command": f"Run 'alembic upgrade head' or manual DDL."
                        }
                    })
                    continue

                # Inspect columns
                existing_columns = {c["name"]: c for c in inspector.get_columns(table_name)}
                for col in table_obj.columns:
                    if col.name not in existing_columns:
                        # Construct a basic ADD COLUMN command
                        col_type = str(col.type).upper()
                        # Handle basic defaults (non-callable)
                        default_val = ""
                        if hasattr(col, "default") and col.default and not callable(col.default.arg):
                            default_val = f" DEFAULT {col.default.arg}"
                        
                        findings.append({
                            "type": "SCHEMA_DRIFT",
                            "subtype": "MISSING_COLUMN",
                            "severity": "HIGH",
                            "component": f"DB: {table_name}.{col.name}",
                            "message": f"Column '{col.name}' is missing in table '{table_name}'.",
                            "diagnosis": f"CEO Engine and Workflow routers expect this column to exist for persistence.",
                            "suggested_fix": {
                                "method": "SQL_PATCH",
                                "command": f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{default_val};"
                            }
                        })
            
            engine.dispose()
        except Exception as e:
            logger.error("Database audit failed: %s", e)
            findings.append({
                "type": "INFRA_ERROR",
                "subtype": "CONNECTION_FAILURE",
                "severity": "CRITICAL",
                "component": "Database",
                "message": "Failed to connect to database for auditing.",
                "diagnosis": str(e),
                "suggested_fix": {
                    "method": "INFRA_RESTART",
                    "command": "docker-compose restart db"
                }
            })

        return findings

    @staticmethod
    async def run_and_report():
        """
        Runs the audit and saves any findings as OperationalIncidents.
        """
        from libs.db.session import AsyncSessionLocal
        from libs.db.models.core_models import OperationalIncident
        from sqlalchemy import select
        
        findings = InfrastructureAuditor.audit_db_schema()
        if not findings:
            logger.info("Infrastructure audit passed. No drifts detected.")
            return

        async with AsyncSessionLocal() as db:
            for finding in findings:
                # Check if an open incident for this component/subtype already exists
                # to avoid spamming the dashboard
                check_q = select(OperationalIncident).where(
                    OperationalIncident.incident_type == finding["subtype"],
                    OperationalIncident.status == "open",
                    OperationalIncident.message == finding["message"]
                )
                existing = (await db.execute(check_q)).scalar_one_or_none()
                
                if not existing:
                    incident = OperationalIncident(
                        incident_type=finding["subtype"],
                        severity=finding["severity"].lower(),
                        message=finding["message"],
                        payload={
                            "diagnosis": finding["diagnosis"],
                            "suggested_fix": finding["suggested_fix"],
                            "component": finding["component"],
                            "audit_source": "InfrastructureAuditor"
                        }
                    )
                    db.add(incident)
                    logger.warning("Proactive Audit Finding: %s", finding['message'])
            
            await db.commit()
