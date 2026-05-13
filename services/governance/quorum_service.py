import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from libs.db.session import get_db, get_db_ctx
from libs.db.models.governance_models import QuorumRequirement, MultiPartySignoff, ProductionSignoff, PolicyProposal, SignoffStatus
from services.governance.policy_vcs_service import PolicyVCSService

class QuorumService:
    @staticmethod
    async def get_requirement(component_type: str, risk_level: str = "LOW") -> Optional[QuorumRequirement]:
        async with get_db_ctx() as session:
            result = await session.execute(
                select(QuorumRequirement).where(
                    and_(
                        QuorumRequirement.component_type == component_type,
                        QuorumRequirement.risk_level == risk_level
                    )
                )
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def register_quorum_requirement(component: str, risk: str, count: int, desc: str = None) -> QuorumRequirement:
        async with get_db_ctx() as session:
            result = await session.execute(
                select(QuorumRequirement).where(
                    and_(
                        QuorumRequirement.component_type == component,
                        QuorumRequirement.risk_level == risk
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                existing.required_count = count
                await session.commit()
                await session.refresh(existing)
                return existing
            
            req = QuorumRequirement(
                component_type=component,
                risk_level=risk,
                required_count=count,
            )
            session.add(req)
            await session.commit()
            await session.refresh(req)
            return req

    @staticmethod
    def _operator_uuid(approver_id: str) -> uuid.UUID:
        try:
            return uuid.UUID(str(approver_id))
        except ValueError:
            return uuid.uuid5(uuid.NAMESPACE_DNS, f"sovereign-operator:{approver_id}")

    @staticmethod
    async def add_signoff(target_id: str, approver_id: str, note: str = None) -> MultiPartySignoff:
        """Adds an approval to a specific signoff or proposal record."""
        async with get_db_ctx() as session:
            # Determine if it's a signoff or proposal
            is_proposal = False
            res = await session.execute(select(PolicyProposal).where(PolicyProposal.id == target_id))
            if res.scalar_one_or_none():
                is_proposal = True

            signoff_data = {
                "operator_id": QuorumService._operator_uuid(approver_id),
                "justification": note,
                "decision": SignoffStatus.SIGNED.value,
            }
            if is_proposal and hasattr(MultiPartySignoff, "proposal_id"):
                signoff_data["proposal_id"] = target_id
            else:
                signoff_data["signoff_id"] = target_id
            signoff = MultiPartySignoff(**signoff_data)
            session.add(signoff)
            await session.commit()
            await session.refresh(signoff)
            
            # Check if quorum reached
            if is_proposal:
                await QuorumService.check_and_update_policy_proposal(target_id)
            else:
                await QuorumService.check_and_update_main_signoff(target_id)
            return signoff

    @staticmethod
    async def check_and_update_main_signoff(signoff_id: str):
        """Checks if enough approvals are collected and updates the ProductionSignoff status."""
        async with get_db_ctx() as session:
            # Get main signoff
            result = await session.execute(select(ProductionSignoff).where(ProductionSignoff.id == signoff_id))
            main_signoff = result.scalar_one_or_none()
            if not main_signoff:
                return

            # Get approvals count
            count_result = await session.execute(
                select(MultiPartySignoff).where(
                    and_(
                        MultiPartySignoff.signoff_id == signoff_id,
                        MultiPartySignoff.decision == SignoffStatus.SIGNED.value
                    )
                )
            )
            approvals = count_result.scalars().all()
            
            # Quorum Relaxation Logic (SOV-CAL-01)
            # Tier-1, low-risk, economic-only, no constitutional effect
            is_relaxed = False
            evidence = main_signoff.evidence_summary or {}
            if (main_signoff.component_name == "ECONOMIC" and 
                evidence.get("tier") == 1 and 
                evidence.get("risk_level") == "LOW" and 
                not evidence.get("constitutional_effect", False)):
                is_relaxed = True

            # Get requirement
            req = await QuorumService.get_requirement(main_signoff.component_name, "HIGH" if not is_relaxed else "LOW") 
            required = req.required_count if req else (1 if is_relaxed else 2)
            
            if len(approvals) >= required:
                main_signoff.status = SignoffStatus.SIGNED
                await session.commit()

    @staticmethod
    async def check_and_update_policy_proposal(proposal_id: str):
        """Checks if enough approvals are collected and triggers Git commit if approved."""
        if not hasattr(MultiPartySignoff, "proposal_id"):
            return

        async with get_db_ctx() as session:
            # Get proposal
            result = await session.execute(select(PolicyProposal).where(PolicyProposal.id == proposal_id))
            proposal = result.scalar_one_or_none()
            if not proposal or proposal.status != "PROPOSED":
                return

            # Get approvals count
            count_result = await session.execute(
                select(MultiPartySignoff).where(
                    and_(
                        MultiPartySignoff.proposal_id == proposal_id,
                        MultiPartySignoff.decision == SignoffStatus.SIGNED.value
                    )
                )
            )
            approvals = count_result.scalars().all()
            
            # Quorum Requirement for policies is usually high
            req = await QuorumService.get_requirement("CONSTITUTION", "HIGH")
            required = req.required_count if req else 2 # Default 2 for policy changes
            
            if len(approvals) >= required:
                proposal.status = "APPROVED"
                await session.commit()
                
                # Trigger Git Sync
                sha = await PolicyVCSService.commit_approved_proposal(proposal)
                if sha:
                    proposal.status = "COMMITTED"
                    proposal.git_commit_sha = sha
                    await session.commit()
