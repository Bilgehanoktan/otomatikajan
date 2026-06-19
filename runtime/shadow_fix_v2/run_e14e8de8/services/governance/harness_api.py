from fastapi import APIRouter, HTTPException, Body
from typing import Dict, List, Any, Optional
import os
from services.orchestration.application.skill_catalog import skill_catalog
from services.orchestration.application.prompt_manager import prompt_manager
from agents.specialist_agents.agent_registry import build_agents, discover_and_build_specialists

router = APIRouter()

@router.get("/status")
async def get_harness_status():
    """Harness sağlığı ve aktif yapılandırmayı döner."""
    try:
        skills = skill_catalog.list_skills()
        governance_active = bool(prompt_manager._governance_contract)
        
        return {
            "status": "healthy",
            "active_skills_count": len(skills),
            "governance_contract_active": governance_active,
            "harness_root": os.getcwd(),
            "config_found": os.path.exists(".codex/config.toml")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/skills")
async def list_skills():
    """Sistemdeki tüm ECC skill'lerini listeler."""
    try:
        skills = skill_catalog.list_skills()
        return [
            {
                "id": s.skill_id,
                "name": s.name,
                "description": s.description,
                "path": s.path,
                "metadata": s.metadata
            }
            for s in skills
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents")
async def list_harness_agents():
    """Sistemdeki tüm ajanları (static + specialists) listeler."""
    try:
        # Merge static agents and dynamic specialists
        core_agents = build_agents()
        specialists = discover_and_build_specialists()
        
        all_agents = {**core_agents, **specialists}
        
        results = []
        for aid, agent in all_agents.items():
            results.append({
                "id": aid,
                "name": aid, # Using ID as name for compatibility with UI expectations
                "description": getattr(agent, "role_name", agent.role),
                "model": "gpt-4o", # Default placeholder
                "tool_groups": [],
                "status": "READY"
            })
        
        return {"agents": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}")
async def get_agent_detail(agent_id: str):
    """Belirli bir ajanın detaylarını ve 'soul' (patch) verisini döner."""
    try:
        core_agents = build_agents()
        specialists = discover_and_build_specialists()
        all_agents = {**core_agents, **specialists}
        
        if agent_id not in all_agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
            
        agent = all_agents[agent_id]
        patch = prompt_manager.get_agent_patch(agent_id)
        
        return {
            "name": agent_id,
            "description": getattr(agent, "role_name", agent.role),
            "model": "gpt-4o",
            "tool_groups": [],
            "soul": patch or agent.system_prompt # Fallback to base prompt if no patch exists
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/agents/{agent_id}")
async def update_agent_soul(agent_id: str, payload: Dict[str, Any] = Body(...)):
    """Ajanın 'soul' (patch) verisini günceller."""
    try:
        soul = payload.get("soul")
        if soul is None:
            raise HTTPException(status_code=400, detail="Missing 'soul' in payload")
            
        prompt_manager.set_agent_patch(agent_id, soul)
        return {"status": "success", "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def trigger_sync():
    """Skill kataloğunu manuel olarak yeniden tarar."""
    try:
        skill_catalog._load_catalog()
        return {"message": "Skill catalog reloaded successfully", "count": len(skill_catalog.skills)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
