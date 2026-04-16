"""
Sovereign AGI — Phase 23
services/observability/fleet_status_api.py
Exposes global fleet metrics and project snapshots for the Fleet Hub dashboard.
"""
from fastapi import APIRouter
from typing import Dict, Any, List
from services.orchestration.fleet_manager import fleet_manager

router = APIRouter(prefix="/fleet", tags=["fleet-ops"])

@router.get("/status")
async def get_fleet_status():
    """
    Returns high-level fleet statistics.
    Used by ResourceArbitrationChart.
    """
    stats = fleet_manager.get_fleet_stats()
    
    # Enrich for the UI
    tier_labels = {
        0: "Mission Critical",
        1: "Production",
        2: "Standard",
        3: "Sandbox"
    }
    
    formatted_stats = []
    for tier, usage in stats["tier_usage"].items():
        formatted_stats.append({
            "tier": tier,
            "label": tier_labels.get(tier, "Unknown"),
            "count": 0, # In a real system, we'd count project items in this tier
            "usage_pct": min((usage / 50) * 100, 100), # Mock: usage out of pool of 50 per tier
            "limit": 50
        })
        
    return {
        "summary": stats,
        "arbitration": formatted_stats,
        "mesh_concurrency_total": sum(stats["tier_usage"].values()),
        "mesh_concurrency_limit": 200
    }

@router.get("/projects")
async def get_fleet_projects():
    """
    Returns a flat list of all projects for the Heatmap.
    """
    # Mocking 100+ projects for the Phase 23 visualization
    mock_projects = []
    import random
    
    # First, include real ones from fleet_manager if any
    # (Actually we'll just mock 100 for the 'mass-scale' demo)
    for i in range(100):
        # Deterministic random for consistent-ish polling
        random.seed(i)
        status_choice = random.choices(["healthy", "warning", "error", "idle"], weights=[80, 10, 5, 5])[0]
        load = random.randint(10, 95) if status_choice != "idle" else 0
        
        mock_projects.append({
            "id": f"proj-{i:03}",
            "name": f"Sovereign-{['A','B','X','Z'][i%4]}-{i}",
            "status": status_choice,
            "load_pct": load,
            "tier": random.randint(0, 3)
        })
        
    return mock_projects
