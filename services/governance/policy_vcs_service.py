
"""
services/governance/policy_vcs_service.py
Service for committing approved PolicyProposals to Git.
"""
from typing import Optional
from libs.vcs.git_ops import GitOps
from libs.db.models.governance_models import PolicyProposal
from services.observability.logging import get_logger

logger = get_logger("governance.vcs")

class PolicyVCSService:
    @staticmethod
    async def commit_approved_proposal(proposal: PolicyProposal) -> Optional[str]:
        """
        Commits an approved policy proposal to the repository.
        If the proposal contains a patch, it applies it first.
        """
        git = GitOps()
        
        # 1. Check Git availability
        if not git.is_git_repo():
            logger.error("System is not running in a Git repository. Commit failed.")
            return None
            
        try:
            # 2. Apply patch if present in proposed_changes
            changes = proposal.proposed_changes
            if isinstance(changes, dict) and "patch" in changes:
                patch_content = changes["patch"]
                success = git.apply_patch(patch_content)
                if not success:
                    logger.error(f"Failed to apply patch for proposal: {proposal.id}")
                    return None
            
            # 3. Commit changes (for simplicity we commit all modified files that match the scope or a specific path)
            # In a real scenario, we would parse the patch to find which files were modified.
            # Here we just commit with the proposal title as the message.
            commit_msg = f"POLICY-SYNC: [{proposal.scope}] {proposal.title} (ID: {proposal.id})"
            
            # For now, we assume the changes are already applied to the disk (either by apply_patch or by previous logic)
            # We use a broad 'add .' for the simplicity of the prototype, but in production we'd be specific.
            # We'll re-use GitOps.commit_file but we need a 'commit_all' if multiple files changed.
            
            # Temporary: using subprocess directly for multi-file commit if needed, or calling commit_file for known paths.
            # Let's assume 'proposed_changes' mentions files.
            files_to_commit = changes.get("files", [])
            last_sha = None
            
            if not files_to_commit:
                # Fallback to general commit if no specific files listed
                # git._run_git(["add", "."])
                # commit_res = git._run_git(["commit", "-m", commit_msg])
                # ... 
                logger.warning(f"No specific files listed in proposal {proposal.id}. Manual sync might be needed.")
                # For Phase 30, we'll just try to commit common config paths if we know them
                pass
            else:
                for f in files_to_commit:
                    sha = git.commit_file(f, commit_msg)
                    if sha: last_sha = sha
            
            return last_sha

        except Exception as e:
            logger.error(f"Git commit failed for proposal {proposal.id}: {e}")
            return None
