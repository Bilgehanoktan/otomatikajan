import asyncio
import uuid
from libs.db.session import get_db
from libs.db.models.governance_models import PolicyProposal, MultiPartySignoff, QuorumRequirement
from services.governance.quorum_service import QuorumService
from sqlalchemy import select, delete

async def test_quorum_service_proposal():
    print("--- Testing QuorumService for PolicyProposals ---")
    async with get_db() as db:
        # 1. Cleanup old tests
        await db.execute(delete(MultiPartySignoff).where(MultiPartySignoff.approver_id == "test_approver_1"))
        await db.execute(delete(PolicyProposal).where(PolicyProposal.title == "Test Policy Change"))
        await db.commit()

        # 2. Create a proposal
        proposal = PolicyProposal(
            id=uuid.uuid4(),
            title="Test Policy Change",
            description="Testing automated git commit via quorum",
            scope="CONSTITUTION",
            status="PROPOSED",
            author_id=str(uuid.uuid4()),
            proposed_changes={"files": ["config/governance/constitutional_locks.yaml"]}
        )
        db.add(proposal)
        await db.commit()
        proposal_id = str(proposal.id)
        print(f"Created proposal: {proposal_id}")

        # 3. Add first signoff
        print("Adding signoff 1...")
        await QuorumService.add_signoff(proposal_id, "test_approver_1", "Looks good")
        
        # Check status (should still be PROPOSED if quorum > 1)
        res = await db.execute(select(PolicyProposal).where(PolicyProposal.id == proposal_id))
        p = res.scalar_one()
        print(f"Status after 1 signoff: {p.status}")

        # 4. Add second signoff (trigger quorum)
        print("Adding signoff 2 (Triggering Quorum)...")
        await QuorumService.add_signoff(proposal_id, "test_approver_2", "Approved by board")
        
        # Check status (should be APPROVED or COMMITTED)
        await db.refresh(p)
        print(f"Status after 2 signoffs: {p.status}")
        if p.status in ["APPROVED", "COMMITTED"]:
            print(f"SUCCESS: Quorum reached. Git SHA: {getattr(p, 'git_commit_sha', 'N/A')}")
        else:
            print(f"FAILURE: Status is {p.status}")

if __name__ == "__main__":
    asyncio.run(test_quorum_service_proposal())
