from typing import List, Dict, Any, Optional
from sqlalchemy import select, and_
from libs.db.session import get_db
from libs.db.models.governance_models import QuorumRequirement, MultiPartySignoff, ProductionSignoff, PolicyProposal, SignoffStatus
from services.governance.policy_vcs_service import PolicyVCSService

class QuorumService:
    @staticmethod
    async def get_requirement(component_type: str, risk_level: str = "LOW") -> Optional[QuorumRequirement]:
        async with get_db() as session:
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
        async with get_db() as session:
            # Check if exists
            existing = await QuorumService.get_requirement(component, risk)
            if existing:
                existing.required_quorum = count
                existing.description = desc
                await session.commit()
                return existing
            
            req = QuorumRequirement(
                component_type=component,
                risk_level=risk,
                required_quorum=count,
                description=desc
            )
            session.add(req)
            await session.commit()
            await session.refresh(req)
            return req

    @staticmethod
    async def add_signoff(target_id: str, approver_id: str, note: str = None) -> MultiPartySignoff:
        """Adds an approval to a specific signoff or proposal record."""
        async with get_db() as session:
            # Determine if it's a signoff or proposal
            is_proposal = False
            res = await session.execute(select(PolicyProposal).where(PolicyProposal.id == target_id))
            if res.scalar_one_or_none():
                is_proposal = True

            signoff = MultiPartySignoff(
                signoff_id=None if is_proposal else target_id,
                proposal_id=target_id if is_proposal else None,
                approver_id=approver_id,
                note=note,
                status=SignoffStatus.SIGNED
            )
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
        async with get_db() as session:
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
                        MultiPartySignoff.status == SignoffStatus.SIGNED
                    )
                )
            )
            approvals = count_result.scalars().all()
            
            # Get requirement (mocked risk level for now, usually derived from component)
            req = await QuorumService.get_requirement(main_signoff.component_name, "HIGH") 
            required = req.required_quorum if req else 1
            
            if len(approvals) >= required:
                main_signoff.status = SignoffStatus.SIGNED
                await session.commit()

    @staticmethod
    async def check_and_update_policy_proposal(proposal_id: str):
        """Checks if enough approvals are collected and triggers Git commit if approved."""
        async with get_db() as session:
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
                        MultiPartySignoff.status == SignoffStatus.SIGNED
                    )
                )
            )
            approvals = count_result.scalars().all()
            
            # Quorum Requirement for policies is usually high
            req = await QuorumService.get_requirement("CONSTITUTION", "HIGH")
            required = req.required_quorum if req else 2 # Default 2 for policy changes
            
            if len(approvals) >= required:
                proposal.status = "APPROVED"
                await session.commit()
                
                # Trigger Git Sync
                sha = await PolicyVCSService.commit_approved_proposal(proposal)
                if sha:
                    proposal.status = "COMMITTED"
                    proposal.git_commit_sha = sha
                    await session.commit()
