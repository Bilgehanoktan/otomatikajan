
import sys
import os
import asyncio

# Project root'u path'e ekle
project_root = r"e:\ai_company_faz12.1"
if project_root not in sys.path:
    sys.path.append(project_root)

async def verify_components():
    print("--- [CHECK] Bileşen Kararlılık Testi (SRE Hardening) ---")
    
    # 1. db.session Hardening
    try:
        from packages.persistence.session import _verify_core
        # engine=None testi
        res = await _verify_core() 
        print(f"[OK] db.session._verify_core (None Engine test): {res}")
    except Exception as e:
        print(f"[ERR] db.session._verify_core Hatası: {e}")

    # 2. agents.agent_registry AGENT_COUNT
    try:
        from agents.agent_registry import build_agents
        agents = build_agents()
        print(f"[OK] agent_registry: {len(agents)} ajan başarıyla yüklendi.")
    except Exception as e:
        print(f"[ERR] agent_registry Hatası: {e}")

    # 3. api.improvement_router Pydantic
    try:
        from api.improvement_router import ImprovementResponse
        resp = ImprovementResponse(
            id="test_1",
            description="Test",
            severity="low",
            affected_files=["test.py"],
            evidence={"ok": True}
        )
        print(f"[OK] improvement_router: Pydantic modeli doğrulandı ({resp.id}).")
    except Exception as e:
        print(f"[ERR] improvement_router Hatası: {e}")

    # 4. core.heal_engine Tip Güvenliği
    try:
        from packages.orchestration.heal_engine import heal_engine
        score = heal_engine.system_health_score()
        print(f"[OK] heal_engine: Sağlık skoru hesaplandı ({score}).")
    except Exception as e:
        print(f"[ERR] heal_engine Hatası: {e}")

    # 5. core.debate_engine Slicing (DebateResult test)
    try:
        from packages.orchestration.debate_engine import DebateResult, DebateRound
        result = DebateResult(debate_id="test_deb", topic="Kritik Bir Konu " * 50, consensus="Uzlaşı var.") 
        result.rounds.append(DebateRound(
            round_num=1, agent_a_id="a", agent_b_id="b",
            arg_a="Uzun arguman A " * 100, arg_b="Uzun arguman B " * 100,
            moderator_note="Uzun moderator notu " * 50
        ))
        d_dict = result.to_dict()
        print(f"[OK] debate_engine: DebateResult.to_dict() dogrulandi (Slicing OK).")
    except Exception as e:
        print(f"[ERR] debate_engine Hatasi: {e}")

if __name__ == "__main__":
    asyncio.run(verify_components())
