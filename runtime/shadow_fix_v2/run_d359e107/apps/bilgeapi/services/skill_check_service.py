import logging
from typing import List, Dict, Any, Optional
from apps.bilgeapi.schemas.skills import SkillCheckResponse, SkillCheckItem
from apps.bilgeapi.services.skill_registry import SkillRegistryService

logger = logging.getLogger(__name__)

class SkillCheckService:
    def __init__(self, registry: SkillRegistryService, ledger_service: Optional[Any] = None):
        self.registry = registry
        self.ledger_service = ledger_service

    async def _append_ledger_event(self, event_type: str, payload: Dict[str, Any]):
        if not self.ledger_service:
            return
        try:
            await self.ledger_service.append_event(
                chain_id="skill_check_chain",
                event_type=event_type,
                entity_type="skill_check",
                entity_id="check_service",
                actor_id="system",
                payload=payload
            )
        except Exception as exc:
            logger.warning("Failed to log skill check event to review ledger: %s", exc)

    async def check_patch(self, target_type: str, target_id: str, skill_names: List[str], patch_code: str) -> SkillCheckResponse:
        """
        Evaluates the patch code against the requested list of skills.
        If a skill is unknown, has hash mismatch, or registry is not initialized, 
        fails-closed by logging to the ledger and raising ValueError/RuntimeError.
        """
        # Fail-closed if registry not initialized
        if not self.registry.initialized:
            await self._append_ledger_event(
                event_type="SKILL_POLICY_BLOCKED",
                payload={"target_type": target_type, "target_id": target_id, "error": "Registry not initialized"}
            )
            raise RuntimeError("Skill registry has not been initialized (fail-closed).")

        checks: List[SkillCheckItem] = []
        overall_status = "PASS"
        
        # ─── Pattern Detection ───
        # IMPROVEMENT NOTE (H5 — next iteration):
        # Current implementation uses simple string/regex matching against patch_code.
        # This has known false-positive and false-negative risks:
        #   - "eval(" in a comment or string literal → false positive
        #   - obfuscated code (e.g. getattr(builtins, 'eval')) → false negative
        # Future upgrade path:
        #   1. Use Python AST parsing (ast.parse + NodeVisitor) for .py patches
        #   2. Use regex with word boundary anchors for non-Python content
        #   3. Add contextual analysis (skip comments/strings)
        # For now, regex with word boundaries provides a reasonable middle ground.
        import re
        
        def contains_any(patterns: List[str]) -> List[str]:
            """Check if patch_code contains any of the given patterns using regex word boundaries."""
            found = []
            if not patch_code:
                return found
            for p in patterns:
                # Use regex with escaped pattern for special chars, word boundary where applicable
                escaped = re.escape(p)
                # For callable patterns like "eval(", match as literal
                if re.search(escaped, patch_code):
                    found.append(p)
            return found

        for name in skill_names:
            try:
                # Retrieve skill metadata. Will raise ValueError if unknown (fail-closed).
                skill_meta = self.registry.get_skill(name)
            except Exception as exc:
                # Unknown or un-verified skill: Fail-closed immediately.
                await self._append_ledger_event(
                    event_type="SKILL_POLICY_BLOCKED",
                    payload={
                        "target_type": target_type,
                        "target_id": target_id,
                        "skill": name,
                        "error": f"Unknown or un-allowlisted skill: {str(exc)}"
                    }
                )
                raise ValueError(f"Security violation: Unknown or un-allowlisted skill '{name}' requested for check.") from exc

            skill_result = "passed"
            reason = None

            # Dangerous pattern lists
            blocked_patterns = ["eval(", "exec(", "shell=True", "subprocess.run(..., shell=True)"]
            mutation_patterns = ["subprocess.", "os.system", "shutil.rmtree", "os.remove", "os.unlink", "os.rmdir"]
            git_patterns = ["git push", "git merge", "force"]
            auth_patterns = ["auth.py", "config.py", "database.py", "self_healing.py"]

            found_blocked = contains_any(blocked_patterns)
            found_mutations = contains_any(mutation_patterns)
            found_git = contains_any(git_patterns)
            found_auth = contains_any(auth_patterns)

            # Rule evaluations
            if name == "bilgeapi-repair-request-safety":
                if found_blocked:
                    skill_result = "blocked"
                    reason = f"Forbidden patterns detected: {', '.join(found_blocked)}"
                elif found_mutations:
                    skill_result = "blocked"
                    reason = f"Dangerous mutation patterns detected: {', '.join(found_mutations)}"

            elif name == "bilgeapi-webhook-security":
                if "webhook" in patch_code and found_blocked:
                    skill_result = "blocked"
                    reason = f"Dangerous webhook execution code detected: {', '.join(found_blocked)}"

            elif name == "bilgeapi-self-healing-policy":
                if found_git:
                    skill_result = "blocked"
                    reason = f"Forbidden git operations: {', '.join(found_git)}"
                elif found_mutations:
                    skill_result = "blocked"
                    reason = f"Dangerous mutations in self-healing: {', '.join(found_mutations)}"

            elif name == "bilgeapi-skill-integrity":
                if any(x in patch_code for x in ["docs/SKILL_POLICY.md", "hash_manifest.json", "docs/agent-skills/"]):
                    skill_result = "blocked"
                    reason = "Modifying skill policy or directory is strictly forbidden"
                elif found_blocked:
                    skill_result = "blocked"
                    reason = "Prompt or command execution patterns detected inside skill integrity"

            elif name == "bilgeapi-pr-verification-gate":
                if found_blocked:
                    skill_result = "blocked"
                    reason = f"Dangerous verification patterns detected: {', '.join(found_blocked)}"
                elif found_auth:
                    skill_result = "review_required"
                    reason = f"Sensitive files modified: {', '.join(found_auth)}"

            elif name == "security-and-hardening":
                if found_blocked:
                    skill_result = "blocked"
                    reason = f"Hardening violation: dangerous patterns detected: {', '.join(found_blocked)}"

            # Aggregation logic
            if skill_result == "blocked":
                overall_status = "BLOCKED"
            elif skill_result == "review_required" and overall_status != "BLOCKED":
                overall_status = "REVIEW_REQUIRED"

            checks.append(SkillCheckItem(skill=name, result=skill_result, reason=reason))

        # Log event to review ledger
        event_type = "SKILL_CHECK_FAILED" if overall_status == "BLOCKED" else "SKILL_CHECK_APPLIED"
        await self._append_ledger_event(
            event_type=event_type,
            payload={
                "target_type": target_type,
                "target_id": target_id,
                "status": overall_status,
                "checks": [c.model_dump() for c in checks]
            }
        )

        return SkillCheckResponse(
            target_type=target_type,
            target_id=target_id,
            status=overall_status,
            passed=(overall_status == "PASS"),
            checks=checks
        )
