import pytest
from unittest.mock import MagicMock
from services.ui_repair.policy_as_code_engine import PolicyAsCodeEngine
from libs.db.models.ui_repair_models import UIPolicyRule
from services.ui_repair.schemas import PolicyDecision

@pytest.mark.asyncio
async def test_policy_evaluation_allow():
    # Setup a simple ALLOW rule
    rule = UIPolicyRule(
        policy_key="ALLOW_MAINTENANCE",
        rule_definition_json={"if": {"action": "AUTO_REPAIR"}, "then": {"decision": "ALLOW"}},
        enabled=True
    )
    
    engine = PolicyAsCodeEngine([rule])
    result = engine.evaluate("AUTO_REPAIR", {"env": "prod"})
    
    assert result["decision"] == PolicyDecision.ALLOW
    assert "Rule ALLOW_MAINTENANCE: ALLOW" in result["reason"]

@pytest.mark.asyncio
async def test_policy_evaluation_deny():
    # Setup a simple DENY rule
    rule = UIPolicyRule(
        policy_key="BLOCK_PROD_AUTO",
        rule_definition_json={"if": {"env": "prod"}, "then": {"decision": "DENY"}},
        enabled=True
    )
    
    engine = PolicyAsCodeEngine([rule])
    result = engine.evaluate("AUTO_REPAIR", {"env": "prod"})
    
    assert result["decision"] == PolicyDecision.DENY
    assert "Rule BLOCK_PROD_AUTO: DENY" in result["reason"]

@pytest.mark.asyncio
async def test_policy_conflict_restrictive_wins():
    # ALLOW vs DENY -> DENY should win (restrictive logic)
    rule1 = UIPolicyRule(
        policy_key="ALLOW_ALL",
        rule_definition_json={"if": {}, "then": {"decision": "ALLOW"}},
        enabled=True,
        priority=1
    )
    rule2 = UIPolicyRule(
        policy_key="DENY_SPECIFIC",
        rule_definition_json={"if": {"target": "auth"}, "then": {"decision": "DENY"}},
        enabled=True,
        priority=10
    )
    
    engine = PolicyAsCodeEngine([rule1, rule2])
    result = engine.evaluate("UPDATE", {"target": "auth"})
    
    assert result["decision"] == PolicyDecision.DENY
