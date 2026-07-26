import os
import logging
from typing import Dict, Any, List
from bilgeapi.execution.file_executor import FileExecutor
from bilgeapi.execution.command_executor import SafeCommandExecutor
from bilgeapi.execution.rollback_manager import RollbackManager

logger = logging.getLogger("bilgeapi.execution.controlled_execution")


class ControlledExecutionEngine:
    """
    Executes code modifications inside an atomic transaction.
    Runs verification test command, and rolls back all modifications if the test fails.
    """

    def __init__(
        self,
        file_executor: FileExecutor,
        command_executor: SafeCommandExecutor,
        rollback_manager: RollbackManager
    ):
        self.file_executor = file_executor
        self.command_executor = command_executor
        self.rollback_manager = rollback_manager

    def execute_transaction(
        self,
        files_to_modify: List[Dict[str, Any]],
        test_command: str,
        approved: bool = False
    ) -> Dict[str, Any]:
        """
        Applies a list of file changes, runs a test command, and commits or rolls back.
        
        Args:
            files_to_modify: List of file action descriptions.
              Format:
                [
                  {"action": "write", "filepath": "main.py", "content": "..."}
                  {"action": "patch", "filepath": "utils.py", "original_snippet": "...", "replacement_snippet": "..."}
                ]
            test_command: The verification test command to run.
            approved: Approval flag for policy engine enforcement.
            
        Returns:
            Dict containing status ("COMMIT" or "ROLLBACK"), message, and test_result.
        """
        backups = []
        applied_modifications = []

        try:
            # 1. Capture snapshots of all target files before modifying them
            for mod in files_to_modify:
                filepath = mod.get("filepath")
                if not filepath:
                    continue
                
                try:
                    target_path = self.file_executor.path_guard.validate_and_resolve(filepath)
                    if target_path.exists():
                        backup_path = self.rollback_manager.create_backup(filepath)
                        backups.append((filepath, backup_path, True))
                    else:
                        backups.append((filepath, None, False))
                except Exception as e:
                    # In case of validation error, clean any created backups and abort
                    self._cleanup_temp_backups(backups)
                    raise e

            # 2. Apply modifications in order
            for mod in files_to_modify:
                action = mod.get("action", "write").lower()
                filepath = mod.get("filepath")
                
                if action == "write":
                    res = self.file_executor.write_file(filepath, mod["content"], approved=approved)
                    applied_modifications.append(res)
                elif action == "patch":
                    res = self.file_executor.patch_file(
                        filepath,
                        mod["original_snippet"],
                        mod["replacement_snippet"],
                        approved=approved
                    )
                    applied_modifications.append(res)
                elif action == "rename":
                    res = self.file_executor.rename_file(
                        filepath,
                        mod["new_filepath"],
                        approved=approved
                    )
                    applied_modifications.append(res)
                else:
                    raise ValueError(f"Unsupported transaction action: {action}")

            # 3. Run validation test command
            test_res = self.command_executor.execute_command(test_command, approved=approved)

            if test_res["exit_code"] != 0:
                # Test failed -> Rollback!
                logger.warning(f"Transaction validation failed (code {test_res['exit_code']}). Rolling back changes...")
                self._perform_rollback(backups)
                return {
                    "status": "ROLLBACK",
                    "message": "Validation tests failed. Transaction has been rolled back.",
                    "applied_modifications": applied_modifications,
                    "test_result": test_res
                }
            else:
                # Test succeeded -> Commit!
                self._commit_backups(backups)
                return {
                    "status": "COMMIT",
                    "message": "Validation tests passed. Transaction committed successfully.",
                    "applied_modifications": applied_modifications,
                    "test_result": test_res
                }

        except Exception as e:
            # If any runtime error happens during file application, trigger rollback
            logger.error(f"Error during transaction execution: {e}. Initiating rollback...")
            self._perform_rollback(backups)
            return {
                "status": "ROLLBACK",
                "message": f"Exception raised during execution: {str(e)}. Transaction rolled back.",
                "applied_modifications": applied_modifications,
                "test_result": {
                    "status": "FAILED",
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": str(e)
                }
            }

    def _perform_rollback(self, backups: List[tuple]) -> None:
        """Restores original files from backups, and deletes any newly created files."""
        for filepath, backup_path, existed in reversed(backups):
            try:
                if existed and backup_path:
                    self.rollback_manager.restore_backup(filepath, backup_path)
                    self.rollback_manager.remove_backup(backup_path)
                else:
                    # File did not exist before: delete it if it was created
                    target_path = self.file_executor.path_guard.validate_and_resolve(filepath)
                    if target_path.exists():
                        os.remove(target_path)
            except Exception as e:
                logger.error(f"Error rolling back file '{filepath}': {e}")

    def _commit_backups(self, backups: List[tuple]) -> None:
        """Commits the transaction by removing all temporary backups."""
        for _, backup_path, existed in backups:
            if existed and backup_path:
                try:
                    self.rollback_manager.remove_backup(backup_path)
                except Exception as e:
                    logger.warning(f"Failed to remove backup file '{backup_path}': {e}")

    def _cleanup_temp_backups(self, backups: List[tuple]) -> None:
        """Removes temporary backups created before transaction was aborted."""
        self._commit_backups(backups)
