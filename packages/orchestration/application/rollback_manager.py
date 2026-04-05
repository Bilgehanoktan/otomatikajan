import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from observability.logging import get_logger

logger = get_logger("rollback_manager")

class RollbackManager:
    """
    Production-grade recovery system for autonomous updates.
    Uses Git to manage code snapshots and verify system health after modifications.
    """
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()

    def _run_git(self, args: list[str]) -> str:
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            raise RuntimeError(f"Git error: {e.stderr}") from e

    def create_snapshot(self, label: str) -> str:
        """Creates a pre-update snapshot using git tags."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        tag_name = f"rollback_{label}_{timestamp}"
        
        # Ensure working directory is clean or stash changes
        status = self._run_git(["status", "--porcelain"])
        if status:
            logger.info("Working directory not clean. Stashing changes before snapshot.")
            self._run_git(["stash", "save", f"Auto-stash before {label}"])
            
        self._run_git(["tag", "-a", tag_name, "-m", f"Pre-update snapshot for {label}"])
        logger.info(f"✅ Snapshot created: {tag_name}")
        return tag_name

    def verify_health(self) -> bool:
        """
        Runs critical health checks to ensure the system is operational.
        Checks internal health endpoints and basic connectivity.
        """
        import http.client
        import json

        # Check FastAPI Health Endpoint
        try:
            conn = http.client.HTTPConnection("localhost", 8000, timeout=10)
            conn.request("GET", "/health")
            response = conn.getresponse()
            if response.status != 200:
                logger.error(f"Post-update health check failed: HTTP {response.status}")
                return False
            
            data = json.loads(response.read().decode())
            if data.get("status") != "healthy":
                logger.error(f"System reported unhealthy state: {data}")
                return False
                
            logger.info("✅ Post-update health verification PASSED.")
            return True
        except Exception as e:
            logger.error(f"Health check connection failed: {e}")
            return False

    def rollback_to_tag(self, tag_name: str):
        """Reverts the system to a previous state using git reset."""
        logger.warning(f"⚠️ CALDATING ROLLBACK to {tag_name}...")
        try:
            self._run_git(["reset", "--hard", tag_name])
            # If we stashed, pop it back
            stashes = self._run_git(["stash", "list"])
            if stashes:
                 self._run_git(["stash", "pop"])
            logger.info(f"✅ Rollback to {tag_name} successful.")
        except Exception as e:
            logger.error(f"CRITICAL: Rollback failed: {e}")
            raise

    async def execute_protected_update(self, label: str, update_fn):
        """
        Executes an update function with automated rollback protection.
        """
        tag = self.create_snapshot(label)
        try:
            result = await update_fn()
            
            # Wait a few seconds for system to reload (if in dev mode with auto-reload)
            import asyncio
            await asyncio.sleep(5) 
            
            if not self.verify_health():
                logger.error(f"Health check FAILED after update '{label}'. Initiating rollback.")
                self.rollback_to_tag(tag)
                return f"Rollback triggered: System was unhealthy after update."
            
            return result
        except Exception as e:
            logger.error(f"Update '{label}' threw exception: {e}. Initiating rollback.")
            self.rollback_to_tag(tag)
            raise
