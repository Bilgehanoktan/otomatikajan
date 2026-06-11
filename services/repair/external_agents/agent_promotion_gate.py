import fnmatch
import hashlib
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.models.repair_models import AgentArtifactPromotionModel, AgentRunModel
from services.repair.external_agents.agent_output_verifier import AgentOutputVerifier
from services.repair.external_agents.agent_ledger_reporter import AgentLedgerReporter
from services.repair.evidence_pack import REPO_ROOT

class AgentPromotionGate:
    ALLOWLIST_PATTERNS = [
        "apps/refine_control_plane/src/**",
        "tests/ui_repair/**",
        "docs/**"
    ]
    BLOCKLIST_PATTERNS = [
        ".env",
        "docker-compose.yml",
        "libs/db/**",
        "migrations/**",
        "apps/bilgeapi/config.py",
        "services/orchestration/agi/security/**",
        "services/repair/human_gate.py"
    ]

    @staticmethod
    def get_file_hash(path: Path) -> str:
        """Computes SHA256 hex string for a file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def compute_sha256(data: str) -> str:
        """Computes SHA256 hex string for a string."""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @classmethod
    def is_path_matching(cls, path_str: str, patterns: List[str]) -> bool:
        """Helper to match a path string against a list of glob patterns including **."""
        norm_path = path_str.replace('\\', '/').strip('/')
        for pattern in patterns:
            norm_pattern = pattern.replace('\\', '/').strip('/')
            if norm_pattern.endswith('/**'):
                base = norm_pattern[:-3]
                if norm_path.startswith(base) or norm_path == base:
                    return True
            if fnmatch.fnmatchcase(norm_path, norm_pattern):
                return True
        return False

    @classmethod
    def is_subpath(cls, child: Path, parent: Path) -> bool:
        """Helper to check if child path is strictly under parent path."""
        try:
            resolved_child = child.resolve()
            resolved_parent = parent.resolve()
            if resolved_child.drive.lower() != resolved_parent.drive.lower():
                return False
            return resolved_parent in resolved_child.parents or resolved_child == resolved_parent
        except Exception:
            return False

    @classmethod
    def validate_target_path(cls, target_repo_path: str) -> Tuple[bool, str]:
        """Validates target_repo_path using canonical resolution and allowlist/blocklist."""
        # Normalize path separators
        clean_path = target_repo_path.replace('\\', '/').strip('/')
        
        # Prevent absolute or empty path
        if clean_path.startswith('/') or ':' in clean_path or not clean_path:
            return False, f"Invalid or absolute path format: '{target_repo_path}'"

        target_abs = (REPO_ROOT / clean_path).resolve()

        # 1. Canonical subpath verification to block traversal
        if not cls.is_subpath(target_abs, REPO_ROOT):
            return False, f"Path traversal attempt: '{target_repo_path}' resolves outside repository boundary."

        # 2. Blocklist check
        if cls.is_path_matching(clean_path, cls.BLOCKLIST_PATTERNS):
            return False, f"Path '{target_repo_path}' is blocked by security policy."

        # 3. Allowlist check
        if not cls.is_path_matching(clean_path, cls.ALLOWLIST_PATTERNS):
            return False, f"Path '{target_repo_path}' is not in the allowed directories list."

        return True, ""

    @classmethod
    async def create_promotion_request(
        cls,
        db: AsyncSession,
        run_id: str,
        artifact_type: str,
        sandbox_artifact_path: str,
        target_repo_path: str,
        created_by: Optional[str] = None
    ) -> AgentArtifactPromotionModel:
        """Creates a new promotion request and runs synchronous validation."""
        # 1. Path check
        paths_ok, err_msg = cls.validate_target_path(target_repo_path)
        if not paths_ok:
            raise ValueError(err_msg)

        sandbox_file = Path(sandbox_artifact_path)
        if not sandbox_file.exists():
            raise FileNotFoundError(f"Sandbox artifact not found at: '{sandbox_artifact_path}'")

        # 2. Compute hashes
        art_hash = cls.get_file_hash(sandbox_file)
        manifest_hash = cls.compute_sha256(f"{run_id}:{target_repo_path}:{art_hash}")
        target_path_hash = cls.compute_sha256(target_repo_path)
        promotion_id = f"promo-{cls.compute_sha256(manifest_hash)[:12]}"

        # 3. Create model
        promo = AgentArtifactPromotionModel(
            id=None,
            promotion_id=promotion_id,
            run_id=run_id,
            artifact_type=artifact_type,
            sandbox_artifact_path=sandbox_artifact_path,
            target_repo_path=target_repo_path,
            artifact_hash=art_hash,
            manifest_hash=manifest_hash,
            target_path_hash=target_path_hash,
            status="PENDING_VERIFICATION",
            verification_score=0.0,
            verification_details={},
            created_at=datetime.now(timezone.utc)
        )
        db.add(promo)
        await db.commit()

        # Log event to immutable governance proof chain
        await cls._log_to_governor_chain(
            db,
            promotion_id=promotion_id,
            run_id=run_id,
            event_name="AGENT_PROMOTION_REQUESTED",
            payload={
                "promotion_id": promotion_id,
                "run_id": run_id,
                "artifact_type": artifact_type,
                "artifact_hash": art_hash,
                "target_repo_path": target_repo_path,
                "status": "PENDING_VERIFICATION"
            },
            actor=created_by
        )

        # 4. Trigger Verification
        await cls._run_verification(db, promo, created_by)
        return promo

    @classmethod
    async def _run_verification(
        cls,
        db: AsyncSession,
        promo: AgentArtifactPromotionModel,
        actor: Optional[str]
    ) -> None:
        """Runs the static and dynamic verification tests inside a temporary branch/workspace."""
        promo.status = "PENDING_VERIFICATION"
        await db.commit()
        
        await cls._log_to_governor_chain(
            db,
            promotion_id=promo.promotion_id,
            run_id=promo.run_id,
            event_name="AGENT_PROMOTION_VERIFICATION_STARTED",
            payload={
                "promotion_id": promo.promotion_id,
                "run_id": promo.run_id,
                "artifact_hash": promo.artifact_hash
            },
            actor=actor
        )

        sandbox_file = Path(promo.sandbox_artifact_path)
        
        # A. Syntax checks (static checks)
        v_score = 1.0
        v_details = {}
        
        if promo.artifact_type in ["source_file", "test_file"] and sandbox_file.suffix == ".py":
            syntax_ok, syntax_err = AgentOutputVerifier.verify_syntax(sandbox_file)
            if not syntax_ok:
                v_score = 0.0
                v_details["syntax_error"] = syntax_err
                
        # B. Structure checks for patches
        if promo.artifact_type == "patch":
            # For verification, we extract allowed / blocked lists
            struct_ok, struct_err = AgentOutputVerifier.verify_patch_structure(
                patch_path=sandbox_file,
                allowed_dirs=cls.ALLOWLIST_PATTERNS,
                blocked_dirs=cls.BLOCKLIST_PATTERNS
            )
            if not struct_ok:
                v_score = 0.0
                v_details["structure_error"] = struct_err

            # C. Dynamic checks: Dry run apply inside temporary workspace
            if v_score > 0.0:
                dry_ok, dry_err = await AgentOutputVerifier.dry_run_patch(
                    patch_path=sandbox_file,
                    test_path=None # We can run target test file if provided in run meta later
                )
                if not dry_ok:
                    v_score = 0.0
                    v_details["dry_run_error"] = dry_err

        # Update verification results
        promo.verification_score = v_score
        promo.verification_details = v_details
        promo.verified_artifact_hash = promo.artifact_hash
        
        if v_score < 1.0:
            promo.status = "VERIFICATION_FAILED"
            await db.commit()
            await cls._log_to_governor_chain(
                db,
                promotion_id=promo.promotion_id,
                run_id=promo.run_id,
                event_name="AGENT_PROMOTION_VERIFICATION_FAILED",
                payload={
                    "promotion_id": promo.promotion_id,
                    "run_id": promo.run_id,
                    "verification_details": v_details,
                    "status": "VERIFICATION_FAILED"
                },
                actor=actor
            )
        else:
            promo.status = "PENDING_APPROVAL"
            await db.commit()
            await cls._log_to_governor_chain(
                db,
                promotion_id=promo.promotion_id,
                run_id=promo.run_id,
                event_name="AGENT_PROMOTION_VERIFIED",
                payload={
                    "promotion_id": promo.promotion_id,
                    "run_id": promo.run_id,
                    "status": "PENDING_APPROVAL"
                },
                actor=actor
            )

    @classmethod
    async def approve_promotion(
        cls,
        db: AsyncSession,
        promotion_id: str,
        operator_email: str
    ) -> None:
        """Approves a verified promotion request."""
        stmt = select(AgentArtifactPromotionModel).where(AgentArtifactPromotionModel.promotion_id == promotion_id)
        res = await db.execute(stmt)
        promo = res.scalars().first()
        if not promo:
            raise ValueError(f"Promotion request '{promotion_id}' not found.")

        # State transition rule check
        if promo.status != "PENDING_APPROVAL":
            raise ValueError(f"Cannot approve promotion request in status '{promo.status}'. Must be 'PENDING_APPROVAL'.")

        # Set APPROVED state
        promo.status = "APPROVED"
        promo.approved_by = operator_email
        promo.approved_at = datetime.now(timezone.utc)
        promo.approved_artifact_hash = promo.artifact_hash
        await db.commit()

        await cls._log_to_governor_chain(
            db,
            promotion_id=promotion_id,
            run_id=promo.run_id,
            event_name="AGENT_PROMOTION_APPROVED",
            payload={
                "promotion_id": promotion_id,
                "run_id": promo.run_id,
                "approved_by": operator_email,
                "status": "APPROVED"
            },
            actor=operator_email
        )

    @classmethod
    async def reject_promotion(
        cls,
        db: AsyncSession,
        promotion_id: str,
        operator_email: str
    ) -> None:
        """Rejects a promotion request."""
        stmt = select(AgentArtifactPromotionModel).where(AgentArtifactPromotionModel.promotion_id == promotion_id)
        res = await db.execute(stmt)
        promo = res.scalars().first()
        if not promo:
            raise ValueError(f"Promotion request '{promotion_id}' not found.")

        # Terminal state check
        if promo.status in ["PROMOTED", "REJECTED"]:
            raise ValueError(f"Cannot reject promotion request in terminal status '{promo.status}'.")

        promo.status = "REJECTED"
        await db.commit()

        await cls._log_to_governor_chain(
            db,
            promotion_id=promotion_id,
            run_id=promo.run_id,
            event_name="AGENT_PROMOTION_REJECTED",
            payload={
                "promotion_id": promotion_id,
                "run_id": promo.run_id,
                "rejected_by": operator_email,
                "status": "REJECTED"
            },
            actor=operator_email
        )

    @classmethod
    async def execute_promotion(
        cls,
        db: AsyncSession,
        promotion_id: str,
        operator_email: str
    ) -> Tuple[bool, str]:
        """Executes the promotion logic, verifying hash manifest integrity and applying isolatedly by default."""
        stmt = select(AgentArtifactPromotionModel).where(AgentArtifactPromotionModel.promotion_id == promotion_id)
        res = await db.execute(stmt)
        promo = res.scalars().first()
        if not promo:
            raise ValueError(f"Promotion request '{promotion_id}' not found.")

        # State transition rule check
        if promo.status != "APPROVED":
            raise ValueError(f"Cannot execute promotion request in status '{promo.status}'. Must be 'APPROVED'.")

        # Policy simulation check (32E requirement)
        sim_hash_saved = (promo.verification_details or {}).get("simulation_result_hash")
        if not sim_hash_saved:
            raise ValueError("simulate_promotion result is required before execute_promotion.")

        from services.repair.external_agents.agent_policy_simulator import AgentPolicySimulator
        sim_fresh = await AgentPolicySimulator.simulate_promotion(db, promotion_id)
        if sim_fresh["simulation_result_hash"] != sim_hash_saved:
            raise ValueError("Policy simulation result mismatch: promotion state modified after simulation.")

        if sim_fresh["decision"] == "BLOCK":
            raise ValueError("Policy simulation blocked this promotion: decision is BLOCK.")

        # Hash integrity check
        if not (promo.artifact_hash == promo.verified_artifact_hash == promo.approved_artifact_hash):
            promo.status = "PROMOTION_FAILED"
            await db.commit()
            await cls._log_to_governor_chain(
                db,
                promotion_id=promotion_id,
                run_id=promo.run_id,
                event_name="AGENT_PROMOTION_HASH_MISMATCH",
                payload={
                    "promotion_id": promotion_id,
                    "run_id": promo.run_id,
                    "artifact_hash": promo.artifact_hash,
                    "verified_hash": promo.verified_artifact_hash,
                    "approved_hash": promo.approved_artifact_hash
                },
                actor=operator_email
            )
            return False, "Integrity check failed: HASH mismatch across promotion lifecycle states."

        promo.status = "PROMOTING"
        await db.commit()

        await cls._log_to_governor_chain(
            db,
            promotion_id=promotion_id,
            run_id=promo.run_id,
            event_name="AGENT_PROMOTION_EXECUTION_STARTED",
            payload={
                "promotion_id": promotion_id,
                "run_id": promo.run_id,
                "status": "PROMOTING"
            },
            actor=operator_email
        )

        sandbox_file = Path(promo.sandbox_artifact_path)
        if not sandbox_file.exists():
            promo.status = "PROMOTION_FAILED"
            await db.commit()
            return False, "Sandbox file vanished before execution."

        # Compute current hash
        current_hash = cls.get_file_hash(sandbox_file)
        if current_hash != promo.artifact_hash:
            promo.status = "PROMOTION_FAILED"
            await db.commit()
            return False, "Integrity check failed: Sandbox file was modified after approval."

        # Read environment flag for direct apply
        direct_apply_flag = os.environ.get("BILGEAPI_AGENT_PROMOTION_APPLY_TO_REPO", "false").lower() == "true"
        
        target_file = REPO_ROOT / promo.target_repo_path.replace('\\', '/').strip('/')
        
        try:
            if direct_apply_flag:
                # Controlled direct repository apply mode
                # Create backup
                backup_file = None
                if target_file.exists():
                    backup_file = Path(f"{target_file}.{datetime.now().timestamp()}.bak")
                    shutil.copy2(target_file, backup_file)
                
                # Copy sandbox file to target repo path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(sandbox_file, target_file)
                
                promoted_hash = cls.get_file_hash(target_file)
                if promoted_hash != promo.artifact_hash:
                    # Restore backup
                    if backup_file and backup_file.exists():
                        shutil.copy2(backup_file, target_file)
                        backup_file.unlink()
                    promo.status = "PROMOTION_FAILED"
                    await db.commit()
                    await cls._log_to_governor_chain(
                        db,
                        promotion_id=promotion_id,
                        run_id=promo.run_id,
                        event_name="AGENT_PROMOTION_FAILED",
                        payload={"promotion_id": promotion_id, "error": "Promoted file hash mismatch during direct apply"},
                        actor=operator_email
                    )
                    return False, "Direct apply failed: Promoted file hash mismatch."
                
                # Clean up backup
                if backup_file and backup_file.exists():
                    backup_file.unlink()

            else:
                # Default: Isolated workspace bundle promotion mode (no direct mutation)
                bundle_dir = REPO_ROOT / "repair_outputs" / "promoted_bundles" / promotion_id
                bundle_dir.mkdir(parents=True, exist_ok=True)
                bundle_file = bundle_dir / Path(promo.target_repo_path).name
                shutil.copy2(sandbox_file, bundle_file)
                
                promoted_hash = cls.get_file_hash(bundle_file)
                if promoted_hash != promo.artifact_hash:
                    promo.status = "PROMOTION_FAILED"
                    await db.commit()
                    return False, "Isolated bundle promotion failed: Promoted file hash mismatch."

            # Success
            promo.promoted_artifact_hash = promoted_hash
            promo.status = "PROMOTED"
            promo.promoted_at = datetime.now(timezone.utc)
            await db.commit()

            # Emit final event to governor
            await cls._log_to_governor_chain(
                db,
                promotion_id=promotion_id,
                run_id=promo.run_id,
                event_name="AGENT_PROMOTION_COMPLETED",
                payload={
                    "promotion_id": promotion_id,
                    "run_id": promo.run_id,
                    "promoted_artifact_hash": promoted_hash,
                    "direct_apply": direct_apply_flag,
                    "status": "PROMOTED"
                },
                actor=operator_email
            )
            return True, "Promotion completed successfully."

        except Exception as e:
            promo.status = "PROMOTION_FAILED"
            await db.commit()
            await cls._log_to_governor_chain(
                db,
                promotion_id=promotion_id,
                run_id=promo.run_id,
                event_name="AGENT_PROMOTION_FAILED",
                payload={"promotion_id": promotion_id, "error": str(e)},
                actor=operator_email
            )
            return False, f"Promotion execution failed: {e}"

    @classmethod
    async def _log_to_governor_chain(
        cls,
        db: AsyncSession,
        promotion_id: str,
        run_id: str,
        event_name: str,
        payload: dict,
        actor: Optional[str]
    ) -> None:
        """Wrapper to append events to the immutable governance proof chain."""
        try:
            from services.governance.proof_chain_service import ProofChainService
            from libs.db.models.governance_models import ProofEventType, GovernorDomain
            
            wrapped_payload = dict(payload)
            wrapped_payload["event_name"] = event_name
            wrapped_payload["promotion_id"] = promotion_id
            wrapped_payload["run_id"] = run_id
            wrapped_payload["timestamp"] = datetime.now(timezone.utc).isoformat()
            wrapped_payload["operator"] = actor or "operator"

            pcs = ProofChainService(db)
            event = await pcs.append_event_async(
                event_type=ProofEventType.RUNTIME_EVENT,
                domain=GovernorDomain.REPAIR,
                entity_id=promotion_id,
                payload=wrapped_payload,
                actor=actor
            )
            
            # Save chain event hash to model if available
            if event:
                stmt = select(AgentArtifactPromotionModel).where(AgentArtifactPromotionModel.promotion_id == promotion_id)
                res = await db.execute(stmt)
                promo = res.scalars().first()
                if promo:
                    promo.ledger_event_hash = event.event_hash
                    await db.commit()
        except Exception as e:
            print(f"Error logging promotion event to governor chain: {e}")
