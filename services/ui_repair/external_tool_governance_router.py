from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from libs.db.session import get_db
from services.ui_repair.schemas import (
    UIExternalToolSchema, UIMCPServerSchema, UIToolPermissionSchema,
    UIToolCallAuditSchema, UIProviderHealthSchema, UIThirdPartyRiskAssessmentSchema, UIToolRiskOverviewSchema,
    ToolCallEvaluationRequest, ToolCallEvaluationResponse
)
from services.ui_repair.external_tool_registry import ExternalToolRegistry
from services.ui_repair.mcp_governance_service import MCPGovernanceService
from services.ui_repair.tool_call_policy_engine import ToolCallPolicyEngine
from services.ui_repair.provider_health_monitor import ProviderHealthMonitor
from services.ui_repair.third_party_risk_scorer import ThirdPartyRiskScorer
from libs.db.models.ui_repair_models import UIToolCallAudit, UIProviderHealth, UIExternalTool, UIMCPServer, UIThirdPartyRiskAssessment
from sqlalchemy import select

router = APIRouter(prefix="/tools", tags=["Tool Governance"])

@router.get("/registry", response_model=List[UIExternalToolSchema])
async def get_tool_registry(db: AsyncSession = Depends(get_db)):
    registry = ExternalToolRegistry(db)
    await registry.initialize_default_tools()
    return await registry.list_tools()

@router.get("/mcp/servers", response_model=List[UIMCPServerSchema])
async def get_mcp_servers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UIMCPServer))
    return result.scalars().all()

@router.post("/evaluate-call", response_model=ToolCallEvaluationResponse)
async def evaluate_tool_call(
    request: ToolCallEvaluationRequest,
    db: AsyncSession = Depends(get_db)
):
    engine = ToolCallPolicyEngine(db)
    decision = await engine.evaluate_call(
        tool_key=request.tool_key,
        tenant_key=request.tenant_key,
        project_key=request.project_key,
        action_type=request.action_type,
        input_data=request.input_data
    )
    
    # Secret check simulation (simplified for router)
    from services.ui_repair.tool_secret_guard import ToolSecretGuard
    guard = ToolSecretGuard()
    _, redacted = guard.sanitize_data(request.input_data)
    
    return {
        **decision,
        "redaction_required": redacted,
        "matched_policies": decision.get("matched_policies", []),
        "required_controls": decision.get("required_controls", [])
    }

@router.get("/audit", response_model=List[UIToolCallAuditSchema])
async def get_tool_audit(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UIToolCallAudit).order_by(UIToolCallAudit.created_at.desc()).limit(100))
    return result.scalars().all()

@router.get("/provider-health", response_model=List[UIProviderHealthSchema])
async def get_provider_health(db: AsyncSession = Depends(get_db)):
    monitor = ProviderHealthMonitor(db)
    return await monitor.list_health_snapshots()

@router.get("/risk/overview", response_model=UIToolRiskOverviewSchema)
async def get_tool_risk_overview(db: AsyncSession = Depends(get_db)):
    provider_rows = list((await db.execute(select(UIProviderHealth))).scalars().all())
    tool_rows = list((await db.execute(select(UIExternalTool))).scalars().all())

    scorer = ThirdPartyRiskScorer(db)
    assessments = []
    existing = list((await db.execute(select(UIThirdPartyRiskAssessment))).scalars().all())
    if existing:
        assessments = existing
    else:
        for provider in provider_rows:
            matching_tools = [tool for tool in tool_rows if tool.provider == provider.provider]
            if matching_tools:
                for tool in matching_tools:
                    assessments.append(await scorer.assess_risk(provider.provider, tool.tool_key))
            else:
                assessments.append(await scorer.assess_risk(provider.provider))

    ordered_assessments = sorted(assessments, key=lambda item: item.risk_score, reverse=True)
    highest = ordered_assessments[0] if ordered_assessments else None
    return {
        "provider_count": len(provider_rows),
        "healthy_providers": sum(1 for provider in provider_rows if provider.status == "HEALTHY"),
        "degraded_providers": sum(1 for provider in provider_rows if provider.status == "DEGRADED"),
        "unavailable_providers": sum(1 for provider in provider_rows if provider.status == "UNAVAILABLE"),
        "tool_count": len(tool_rows),
        "assessment_count": len(ordered_assessments),
        "highest_risk_level": highest.risk_level if highest else "LOW",
        "highest_risk_score": float(highest.risk_score) if highest else 0.0,
        "critical_findings": sum(
            len(assessment.findings_json)
            for assessment in ordered_assessments
            if assessment.risk_level in {"HIGH", "CRITICAL"}
        ),
        "latest_assessments": ordered_assessments[:10],
    }
