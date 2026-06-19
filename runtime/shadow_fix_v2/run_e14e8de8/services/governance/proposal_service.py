from typing import List, Dict, Any, Optional
from sqlalchemy import select
from libs.db.session import get_db, get_db_ctx
from libs.db.models.governance_models import PolicyProposal

class ProposalService:
    @staticmethod
    async def create_proposal(title: str, description: str, scope: str, changes: Dict[str, Any], author: str) -> PolicyProposal:
        async with get_db_ctx() as session:
            proposal = PolicyProposal(
                title=title,
                description=description,
                scope=scope,
                proposed_changes=changes,
                author_id=author,
                status="PROPOSED"
            )
            session.add(proposal)
            await session.commit()
            await session.refresh(proposal)
            return proposal

    @staticmethod
    async def get_proposal(proposal_id: str) -> Optional[PolicyProposal]:
        async with get_session() as session:
            result = await session.execute(select(PolicyProposal).where(PolicyProposal.id == proposal_id))
            return result.scalar_one_or_none()

    @staticmethod
    async def list_proposals(scope: str = None) -> List[PolicyProposal]:
        async with get_session() as session:
            query = select(PolicyProposal).order_by(PolicyProposal.created_at.desc())
            if scope:
                query = query.where(PolicyProposal.scope == scope)
            result = await session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    async def update_status(proposal_id: str, status: str, commit_sha: str = None) -> Optional[PolicyProposal]:
        async with get_session() as session:
            proposal = await ProposalService.get_proposal(proposal_id)
            if not proposal:
                return None
            
            proposal.status = status
            if commit_sha:
                proposal.git_commit_sha = commit_sha
            
            await session.commit()
            await session.refresh(proposal)
            return proposal
