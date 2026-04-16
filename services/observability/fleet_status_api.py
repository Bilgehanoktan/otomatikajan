"""
Sovereign AGI — Phase 23
services/observability/fleet_status_api.py
Exposes global fleet metrics and project snapshots for the Fleet Hub dashboard.
"""
from fastapi import APIRouter
from typing import Dict, Any, List
from services.orchestration.fleet_manager import fleet_manager
from services.orchestration.economic_engine import economic_engine
from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import SovereignEvidence
from sqlalchemy import select, desc

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
        "mesh_concurrency_limit": 200,
        "global_burn_rate": sum(s.burn_rate for s in fleet_manager._active_workloads.values()),
        "forecast_window_hours": 4
    }

@router.get("/projects")
async def get_fleet_projects():
    """
    Returns a unified list of real and mock projects for the Heatmap.
    Include Phase 25 elasticity metrics (base_limit, adjustment_status).
    """
    projects = []
    
    # 1. Real Internal Workloads (Phase 24-25 Data)
    for p in fleet_manager._active_workloads.values():
        projects.append({
            "id": p.project_id,
            "name": f"Core-{p.project_id}",
            "status": "healthy" if p.health == "NOMINAL" else "error",
            "load_pct": (p.active_tasks / p.concurrency_limit * 100) if p.concurrency_limit > 0 else 0,
            "tier": p.isolation_tier,
            "burn_rate": p.burn_rate,
            "forecast_load": p.forecast_load,
            "base_limit": p.base_concurrency_limit,
            "current_limit": p.concurrency_limit,
            "adjustment_status": "Expanded" if p.concurrency_limit > p.base_concurrency_limit else "Nominal",
            "current_budget": economic_engine._project_budgets.get(p.project_id, 0.0),
            "anomaly_score": economic_engine.detect_spend_anomaly(p.project_id),
            "health_reason": p.health
        })

    # 2. Fill the rest with Mock projects for Viz (Phase 23 demo)
    import random
    start_idx = len(projects)
    for i in range(start_idx, 100):
        random.seed(i)
        status_choice = random.choices(["healthy", "warning", "error", "idle"], weights=[80, 10, 5, 5])[0]
        load = random.randint(10, 95) if status_choice != "idle" else 0
        
        projects.append({
            "id": f"proj-{i:03}",
            "name": f"Sovereign-{['A','B','X','Z'][i%4]}-{i}",
            "status": status_choice,
            "load_pct": load,
            "tier": random.randint(0, 3),
            "burn_rate": round(load * 0.15, 2),
            "forecast_load": round(load * (0.8 + random.random() * 0.4), 1),
            "base_limit": 10,
            "current_limit": 10,
            "adjustment_status": "Nominal",
            "current_budget": random.randint(10, 500),
            "anomaly_score": 0.05 if status_choice == "healthy" else 0.4,
            "health_reason": "NOMINAL" if status_choice == "healthy" else "MOCK_WARNING"
        })
        
    return projects

@router.get("/mesh/topology")
async def get_mesh_topology():
    """
    Returns high-fidelity topology data for ChaosMap.
    Simulates cross-region latency and health.
    """
    return {
        "regions": [
            {"id": "us-east-1", "name": "US-EAST (Virginia)", "status": "healthy", "health": "healthy", "role": "primary", "latency": 24},
            {"id": "eu-central-1", "name": "EU-CENTRAL (Frankfurt)", "status": "healthy", "health": "healthy", "role": "secondary", "latency": 88},
            {"id": "ap-southeast-1", "name": "AP-SOUTH (Singapore)", "status": "warning", "health": "warning", "role": "standby", "latency": 156},
            {"id": "us-west-1", "name": "US-WEST (Oregon)", "status": "healthy", "health": "healthy", "role": "primary", "latency": 42}
        ],
        "links": [
            # In a real system, these would be calculated based on real pings
            {"source": "us-east-1", "target": "eu-central-1", "latency": 85, "status": "active"},
            {"source": "eu-central-1", "target": "ap-southeast-1", "latency": 160, "status": "active"},
            {"source": "us-east-1", "target": "us-west-1", "latency": 40, "status": "active"}
        ],
        "quorum_maintained": True,
        "region_count": {"total": 4, "healthy": 3}
    }

@router.get("/evidence")
async def get_mesh_evidence(limit: int = 10):
    """
    Returns the latest deep-dive evidence from SovereignEvidence table.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SovereignEvidence).order_by(desc(SovereignEvidence.created_at)).limit(limit)
        )
        evidence_list = result.scalars().all()
        
    return [
        {
            "id": str(e.id),
            "type": e.evidence_type,
            "severity": e.severity,
            "created_at": e.created_at.isoformat(),
            "payload": e.payload
        } for e in evidence_list
    ]
