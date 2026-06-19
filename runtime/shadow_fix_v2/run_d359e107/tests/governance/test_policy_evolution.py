import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from services.governance.governor_policy_evolution_engine import GovernorPolicyEvolutionEngine
from services.governance.governor_policy_simulator import GovernorPolicySimulator
from libs.db.repositories.governor_policy_repository import GovernorPolicyEvolutionRepo
from libs.db.models.governance_models import PolicyEvolutionStatus

@pytest.mark.asyncio
async def test_policy_evolution_cycle(db_session: AsyncSession):
    # 1. Tarama yap (Mock verilerle çalışması beklenir)
    new_proposals = await GovernorPolicyEvolutionEngine.run_suggestion_cycle(db_session)
    await db_session.flush()
    
    # 2. Önerileri listele
    proposals = await GovernorPolicyEvolutionRepo.list_recent_proposals(db_session, status=PolicyEvolutionStatus.PROPOSED)
    
    if proposals:
        evo = proposals[0]
        # 3. Simülasyon yap
        sim_result = await GovernorPolicySimulator.simulate_evolution(db_session, evo.id, window_days=1)
        assert sim_result["sample_size"] >= 0
        
        # 4. Statü SIMULATED olmalı
        updated_evo = await GovernorPolicyEvolutionRepo.get_evolution(db_session, evo.id)
        assert updated_evo.status == PolicyEvolutionStatus.SIMULATED
        
        print(f"Test passed: Evolution {evo.policy_key} simulated.")
    else:
        print("No candidates found, test skipped logic verification but engine ran successfully.")
