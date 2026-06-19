import os
import sqlite3
import shutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Dynamically resolve active project root and SQLite database file path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "runtime", "data", "cortex_local_v2.db")

class DatabaseRecoveryManager:
    @staticmethod
    def get_db_path() -> str:
        """Returns the absolute path to the active fallback SQLite database."""
        env_path = os.getenv("DATABASE_URL", "")
        if env_path.startswith("sqlite+aiosqlite:///"):
            cleaned_path = env_path.replace("sqlite+aiosqlite:///", "").split("?")[0]
            if os.path.isabs(cleaned_path):
                return cleaned_path
            return os.path.abspath(os.path.join(PROJECT_ROOT, cleaned_path))
        
        return os.path.abspath(DEFAULT_DB_PATH)

    @classmethod
    def diagnose(cls) -> dict:
        """
        Runs comprehensive integrity checks and row metrics diagnostics on the active SQLite database.
        """
        db_path = cls.get_db_path()
        result = {
            "timestamp": datetime.now().isoformat(),
            "database_path": db_path,
            "exists": os.path.exists(db_path),
            "size_bytes": 0,
            "integrity_check": "FAILED",
            "tables": {},
            "status": "HEALTHY",
            "error": None
        }

        if not result["exists"]:
            result["status"] = "DEGRADED"
            result["error"] = "Database file does not exist."
            return result

        result["size_bytes"] = os.path.getsize(db_path)

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 1. PRAGMA integrity_check
            try:
                cursor.execute("PRAGMA integrity_check")
                chk = cursor.fetchone()
                if chk and chk[0] == "ok":
                    result["integrity_check"] = "OK"
                else:
                    result["integrity_check"] = f"FAILED - {chk[0] if chk else 'Unknown'}"
                    result["status"] = "CORRUPTED"
            except Exception as e:
                result["integrity_check"] = f"ERROR - {str(e)}"
                result["status"] = "CORRUPTED"

            # 2. Schema Discovery and Row Analysis
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall() if not t[0].startswith("sqlite_")]

            for table_name in tables:
                try:
                    cursor.execute(f"SELECT count(*) FROM \"{table_name}\"")
                    count = cursor.fetchone()[0]
                    result["tables"][table_name] = {
                        "status": "OK",
                        "rows": count
                    }
                except Exception as ex:
                    result["tables"][table_name] = {
                        "status": f"ERROR: {str(ex)}",
                        "rows": 0
                    }
                    result["status"] = "CORRUPTED"

            conn.close()

        except Exception as e:
            result["status"] = "CORRUPTED"
            result["error"] = f"Diagnostics failed: {str(e)}"

        return result

    @classmethod
    def recover(cls) -> dict:
        """
        Executes a lock-resilient in-place self-healing reconstruction sweep on the active SQLite database:
        1. Backs up the database to a separate file.
        2. Dumps the schema & content safely using SQLite iterdump.
        3. Clears all existing tables in the active database.
        4. Rebuilds the schema and imports salvaged data under a single robust transaction.
        """
        db_path = cls.get_db_path()
        backup_dir = os.path.dirname(db_path)
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"cortex_backup_pre_heal_{timestamp}.db")
        temp_sql_path = os.path.join(backup_dir, f"cortex_dump_temp_{timestamp}.sql")

        result = {
            "timestamp": datetime.now().isoformat(),
            "database_path": db_path,
            "backup_created": False,
            "backup_path": backup_path,
            "status": "FAILED",
            "message": ""
        }

        if not os.path.exists(db_path):
            result["message"] = "Cannot recover database: file does not exist."
            return result

        try:
            # 1. Safely backup the raw database file
            shutil.copy2(db_path, backup_path)
            result["backup_created"] = True
            logger.info("Backup created at %s", backup_path)

            # 2. Dump SQL via iterdump to salvage all possible records
            logger.info("Dumping SQL records to temp file...")
            con = sqlite3.connect(db_path)
            with open(temp_sql_path, "w", encoding="utf-8") as f:
                for line in con.iterdump():
                    f.write(f"{line}\n")
            con.close()

            # 3. Read dump contents
            with open(temp_sql_path, "r", encoding="utf-8") as f:
                sql_script = f.read()

            # 4. Connect to active database and perform lock-resilient in-place drop and rebuild
            logger.info("Performing in-place schema drop and atomic reconstruction...")
            active_con = sqlite3.connect(db_path)
            active_cursor = active_con.cursor()

            # Temp disable foreign key constraints to drop cleanly
            active_cursor.execute("PRAGMA foreign_keys = OFF")

            # Query all table names
            active_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in active_cursor.fetchall() if not t[0].startswith("sqlite_")]

            # Drop all tables to clear schema
            for table_name in tables:
                active_cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
            
            # Execute rebuilt SQL script (creates tables & inserts data)
            active_cursor.executescript(sql_script)
            active_con.commit()

            # Re-enable foreign key constraints
            active_cursor.execute("PRAGMA foreign_keys = ON")
            active_con.close()

            # Cleanup temp SQL file
            if os.path.exists(temp_sql_path):
                os.remove(temp_sql_path)

            result["status"] = "SUCCESS"
            result["message"] = "Self-repair completed! Active fallback database reconstructed cleanly and defragmented in-place."
            logger.info(result["message"])

        except Exception as e:
            result["status"] = "FAILED"
            result["message"] = f"Recovery failed: {str(e)}"
            logger.error("Database recovery process failed: %s", e)

            # Cleanup temporary file if left
            if os.path.exists(temp_sql_path):
                try:
                    os.remove(temp_sql_path)
                except Exception:
                    pass

        return result
