from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from libs.db.session import get_db
from services.auth.jwt_auth import require_permission
from services.orchestration.ceo.repair_bridge import (
    ExternalRepairRequest,
    build_repair_case_from_finding,
    start_self_repair_from_repair_case,
)

from services.repair.ui_diagnostics import UIDiagnosticRequest
from services.repair.stagehand_adapter import (
    run_stagehand_diagnostic,
    write_diagnostic_artifact,
    map_diagnostic_to_ceo_finding,
)

router = APIRouter(tags=["CEO Findings Bridge"])

@router.post("/findings/{finding_id}/repair-case")
async def create_repair_case_from_ceo_finding(
    finding_id: str,
    body: ExternalRepairRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
    db: AsyncSession = Depends(get_db),
):
    """
    Bridges a CEO dashboard finding or recommendation to the self-repair pipeline.
    Validates identity permissions, maps finding fields, generates repair_case.json,
    and returns a structured transition payload.
    """
    if body.finding.finding_id != finding_id:
        raise HTTPException(
            status_code=400,
            detail=f"Mismatched finding_id: path has '{finding_id}' but payload has '{body.finding.finding_id}'"
        )

    try:
        # 1. Build and serialize the repair case
        result = build_repair_case_from_finding(body.finding)
        
        # 2. Trigger TaskFlow bridge according to auto_start policy
        trigger_res = await start_self_repair_from_repair_case(result.case_input, auto_start=body.auto_start, db=db)
        
        # 3. Formulate compliant response
        return {
            "status": "created",
            "finding_id": result.finding_id,
            "repair_case_id": result.repair_case_id,
            "incident_id": result.incident_id,
            "artifact_ref": result.artifact_ref,
            "recommended_agent": result.recommended_agent,
            "requested_mode": result.requested_mode,
            "next_step": "start_self_repair_taskflow" if not body.auto_start else "taskflow_running",
            "trigger_status": trigger_res
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bridge CEO finding to repair case: {e}")


@router.post("/diagnostics/stagehand")
async def post_stagehand_diagnostic(
    body: UIDiagnosticRequest,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    """
    Runs a UI diagnostic using the Stagehand adapter and translates the diagnostic results into a standard CEO Finding payload.
    """
    try:
        # 1. Run the Stagehand diagnostic
        result = run_stagehand_diagnostic(body)
        
        # 2. Persist diagnostic artifacts (diagnostic_report.json, network/console logs)
        write_diagnostic_artifact(result)
        
        # 3. Map result to CEOFindingPayload
        finding = map_diagnostic_to_ceo_finding(result)
        
        artifact_ref = f"repair_outputs/diagnostics/{result.diagnostic_id}/diagnostic_report.json"
        
        return {
            "status": "created",
            "diagnostic_id": result.diagnostic_id,
            "artifact_ref": artifact_ref,
            "finding": finding,
            "next_step": "create_repair_case"
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic run failed: {e}")



@router.get("/suggestions")
async def get_ceo_suggestions(
    force_refresh: bool = False,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves the latest audit run suggestions (classified findings).
    If no audit run exists or force_refresh is True, triggers a full audit on-demand and returns its findings.
    """
    import os
    import json
    from services.self_repair_audit.audit_orchestrator import AuditOrchestrator
    from services.self_repair_audit.suggestion_store import load_suggestion_states
    from services.self_repair_audit.suggestion_run_links import load_suggestion_run_links
    from libs.db.repositories.repository import ProjectRepository

    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    audit_runs_dir = os.path.join(workspace_root, "project_outputs", "audit_runs")

    audit_run_id = None
    findings = []

    try:
        # Check if audit directory exists and has runs
        trigger_new = True
        if not force_refresh and os.path.exists(audit_runs_dir) and os.path.isdir(audit_runs_dir):
            runs = [d for d in os.listdir(audit_runs_dir) if d.startswith("AUD-") and os.path.isdir(os.path.join(audit_runs_dir, d))]
            if runs:
                # Sort descending (alphabetical reverse) to get the latest
                runs.sort(reverse=True)
                for latest_run in runs:
                    filepath = os.path.join(audit_runs_dir, latest_run, "classified_findings.json")
                    if os.path.exists(filepath):
                        with open(filepath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            audit_run_id = latest_run
                            findings = data.get("findings", [])
                            trigger_new = False
                            break

        if trigger_new:
            # Trigger full audit on-demand
            orch = AuditOrchestrator(workspace_root)
            report = orch.execute_full_audit()
            audit_run_id = report["audit_run_id"]
            findings = report.get("findings", [])

        # Enrich findings with their current status from suggestion_state.json
        if audit_run_id:
            try:
                states = load_suggestion_states(audit_run_id, workspace_root)
                links = load_suggestion_run_links(audit_run_id, workspace_root)
                from services.self_repair_audit.project_factory_run_links import load_project_factory_run_links
                pf_links = load_project_factory_run_links(audit_run_id, workspace_root)

                # Fetch recent projects to get live status
                recent_projects = await ProjectRepository.list_recent(db, limit=100)
                project_map = {}
                for p in recent_projects:
                    ctx = p.execution_context
                    if isinstance(ctx, str):
                        try:
                            ctx = json.loads(ctx)
                        except Exception:
                            ctx = {}
                    if isinstance(ctx, dict):
                        fid = ctx.get("finding_id")
                        if fid and fid not in project_map:
                            project_map[fid] = p

                for f in findings:
                    if isinstance(f, dict) and "finding_id" in f:
                        fid = f["finding_id"]
                        f["status"] = states.get(fid, "NEW")

                        # Enrich with active run link metadata if present
                        link = links.get(fid)
                        if link:
                            live_project = project_map.get(fid)
                            proj_status = "QUEUED"
                            if live_project:
                                proj_status = (live_project.status or "QUEUED").upper()
                            else:
                                proj_status = (link.get("status") or "QUEUED").upper()

                            f["repair_run"] = {
                                "taskflow_id": link.get("taskflow_id"),
                                "job_id": link.get("job_id"),
                                "incident_id": link.get("incident_id"),
                                "workflow_template": link.get("workflow_template", "self_repair"),
                                "status": proj_status,
                                "title": f"Self Repair Case: {link.get('incident_id')}",
                                "workflow_url": f"/workflows/{link.get('taskflow_id')}"
                            }

                        # Enrich with active project factory run link if present
                        pf_link = pf_links.get(fid)
                        if pf_link:
                            pf_proj_id = pf_link.get("project_id")
                            pf_status = "REQUIREMENT_GATE_WAITING"
                            if pf_proj_id:
                                try:
                                    from services.project_factory.artifacts import load_project_factory_artifacts
                                    _, pf_gate = load_project_factory_artifacts(pf_proj_id, workspace_root)
                                    pf_status = pf_gate.status
                                    if pf_status == "WAITING_FOR_OPERATOR":
                                        pf_status = "REQUIREMENT_GATE_WAITING"
                                except Exception:
                                    pass
                            f["project_factory_run"] = {
                                "project_id": pf_proj_id,
                                "status": pf_status,
                                "title": f"Project Factory Case: {pf_proj_id}",
                                "workflow_url": f"/project-factory/{pf_proj_id}"
                            }
            except Exception as se:
                # Fallback to default NEW status if state load fails
                for f in findings:
                    if isinstance(f, dict) and "finding_id" in f:
                        f["status"] = "NEW"

        return {
            "status": "success",
            "audit_run_id": audit_run_id,
            "findings": findings
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve or trigger audit suggestions: {e}"
        )


def _resolve_audit_run_id(audit_run_id: str | None, workspace_root: str) -> str:
    if audit_run_id:
        return audit_run_id
    audit_runs_dir = os.path.join(workspace_root, "project_outputs", "audit_runs")
    if os.path.exists(audit_runs_dir) and os.path.isdir(audit_runs_dir):
        runs = [d for d in os.listdir(audit_runs_dir) if d.startswith("AUD-") and os.path.isdir(os.path.join(audit_runs_dir, d))]
        if runs:
            runs.sort(reverse=True)
            return runs[0]
    raise HTTPException(status_code=404, detail="No audit runs found to perform action on.")


from services.self_repair_audit.action_models import SuggestionActionRequest

@router.post("/suggestions/{suggestion_id}/approve-self-repair")
async def approve_self_repair(
    suggestion_id: str,
    body: SuggestionActionRequest,
    audit_run_id: str | None = None,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
    db: AsyncSession = Depends(get_db),
):
    import os
    import json
    import uuid
    from datetime import datetime
    from services.self_repair_audit.suggestion_run_links import load_suggestion_run_links, save_suggestion_run_link
    from services.self_repair_audit.suggestion_actions import get_finding_details, process_suggestion_action
    from services.orchestration.ceo.repair_bridge import (
        CEOFindingPayload,
        build_repair_case_from_finding,
        start_self_repair_from_repair_case,
    )
    from services.self_repair_audit.action_models import SuggestionActionLog
    from services.self_repair_audit.suggestion_store import record_action_log, update_suggestion_state
    from libs.db.repositories.repository import ProjectRepository

    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        resolved_run_id = _resolve_audit_run_id(audit_run_id, workspace_root)

        # 1. Check if suggestion run already exists
        links = load_suggestion_run_links(resolved_run_id, workspace_root)
        if suggestion_id in links:
            link = links[suggestion_id]
            proj_status = "QUEUED"
            try:
                # Query db project status if possible
                proj = await ProjectRepository.get(db, link["taskflow_id"])
                if proj:
                    proj_status = (proj.status or "QUEUED").upper()
            except Exception:
                pass

            return {
                "status": "already_started",
                "repair_run": {
                    "taskflow_id": link.get("taskflow_id"),
                    "job_id": link.get("job_id"),
                    "incident_id": link.get("incident_id"),
                    "workflow_template": link.get("workflow_template", "self_repair"),
                    "status": proj_status,
                    "workflow_url": f"/workflows/{link.get('taskflow_id')}"
                }
            }
        # 2. Run standard suggestion transition validation (operator_id, rationale, risk_acknowledgement, redundant, allowed)
        log = process_suggestion_action(
            audit_run_id=resolved_run_id,
            suggestion_id=suggestion_id,
            action="APPROVE_SELF_REPAIR",
            to_status="APPROVED_FOR_REPAIR",
            req=body,
            workspace_root=workspace_root
        )

        # 3. Retrieve complete finding details
        finding = get_finding_details(resolved_run_id, suggestion_id, workspace_root)
        if not finding:
            raise HTTPException(
                status_code=404,
                detail=f"Finding '{suggestion_id}' not found in audit run '{resolved_run_id}'"
            )

        # 4. Map finding to CEOFindingPayload
        affected_files = finding.get("affected_files") or []
        if isinstance(affected_files, str):
            try:
                affected_files = json.loads(affected_files)
            except Exception:
                affected_files = [affected_files]

        endpoint_val = finding.get("affected_endpoint")
        if not endpoint_val:
            endpoints = finding.get("affected_endpoints")
            if isinstance(endpoints, list) and len(endpoints) > 0:
                endpoint_val = str(endpoints[0])
            elif isinstance(endpoints, str):
                endpoint_val = endpoints
            else:
                endpoint_val = None

        rec_action = finding.get("recommended_action")
        if not rec_action:
            actions = finding.get("recommended_actions")
            if isinstance(actions, list) and len(actions) > 0:
                rec_action = ", ".join(str(a) for a in actions)
            elif isinstance(actions, str):
                rec_action = actions
            else:
                rec_action = None

        payload = CEOFindingPayload(
            finding_id=finding.get("finding_id") or suggestion_id,
            title=finding.get("title", "CEO Suggestion Repair"),
            description=finding.get("description", "Auto-generated repair flow"),
            category=finding.get("category", "security"),
            priority_score=float(finding.get("priority_score", 0.0)),
            source_signal="self_repair_audit",
            affected_endpoint=endpoint_val,
            affected_files=affected_files,
            recommended_action=rec_action,
            recommended_agent="swe_agent",
            requested_mode="local_adapter",
            can_trigger_repair=True
        )

        # 5. Build and serialize the repair case
        result = build_repair_case_from_finding(payload)

        # 6. Trigger TaskFlow active self-repair run
        trigger_res = await start_self_repair_from_repair_case(result.case_input, auto_start=True, db=db)

        # 7. Persist run link mapping in suggestion_run_links.json
        run_link = {
            "suggestion_id": suggestion_id,
            "audit_run_id": resolved_run_id,
            "taskflow_id": trigger_res["taskflow_id"],
            "job_id": trigger_res["job_id"],
            "incident_id": trigger_res["incident_id"],
            "workflow_template": "self_repair",
            "status": "QUEUED",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        save_suggestion_run_link(resolved_run_id, suggestion_id, run_link, workspace_root)

        # 8. Record second action: SELF_REPAIR_STARTED (append-only)
        action_id = f"ACT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        created_at = datetime.utcnow().isoformat() + "Z"

        start_log = SuggestionActionLog(
            action_id=action_id,
            suggestion_id=suggestion_id,
            action="SELF_REPAIR_STARTED",
            from_status="APPROVED_FOR_REPAIR",
            to_status="IN_PROGRESS",
            operator_id=body.operator_id,
            rationale=body.rationale,
            risk_acknowledgement=body.risk_acknowledgement,
            created_at=created_at,
            result={
                "repair_case_created": True,
                "taskflow_id": trigger_res["taskflow_id"],
                "job_id": trigger_res["job_id"],
                "incident_id": trigger_res["incident_id"]
            }
        )
        record_action_log(resolved_run_id, start_log, workspace_root)
        update_suggestion_state(resolved_run_id, suggestion_id, "IN_PROGRESS", workspace_root)

        return {
            "status": "success",
            "action_log": log.model_dump(),
            "repair_run": {
                "taskflow_id": trigger_res["taskflow_id"],
                "job_id": trigger_res["job_id"],
                "incident_id": trigger_res["incident_id"],
                "workflow_template": "self_repair",
                "status": "QUEUED",
                "workflow_url": f"/workflows/{trigger_res['taskflow_id']}"
            }
        }
    except KeyError as ke:
        raise HTTPException(status_code=404, detail=str(ke))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process suggestion action: {e}")


@router.post("/suggestions/{suggestion_id}/approve-project-factory")
async def approve_project_factory(
    suggestion_id: str,
    body: SuggestionActionRequest,
    audit_run_id: str | None = None,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    import os
    import uuid
    from datetime import datetime
    from services.self_repair_audit.project_factory_run_links import load_project_factory_run_links, save_project_factory_run_link
    from services.self_repair_audit.suggestion_actions import get_finding_details, process_suggestion_action
    from services.project_factory.project_factory_bridge import bridge_suggestion_to_project_factory
    from services.self_repair_audit.action_models import SuggestionActionLog
    from services.self_repair_audit.suggestion_store import record_action_log, update_suggestion_state

    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        resolved_run_id = _resolve_audit_run_id(audit_run_id, workspace_root)

        # 1. Check if suggestion run already exists
        links = load_project_factory_run_links(resolved_run_id, workspace_root)
        if suggestion_id in links:
            link = links[suggestion_id]
            return {
                "status": "already_started",
                "project_factory_run": {
                    "project_id": link.get("project_id"),
                    "status": "REQUIREMENT_GATE_WAITING",
                    "workflow_url": f"/project-factory/{link.get('project_id')}"
                }
            }

        # 2. Run standard suggestion transition validation (operator_id, rationale, risk_acknowledgement, redundant, allowed)
        log = process_suggestion_action(
            audit_run_id=resolved_run_id,
            suggestion_id=suggestion_id,
            action="APPROVE_PROJECT_FACTORY",
            to_status="APPROVED_FOR_PROJECT_FACTORY",
            req=body,
            workspace_root=workspace_root
        )

        # 3. Retrieve complete finding details
        finding = get_finding_details(resolved_run_id, suggestion_id, workspace_root)
        if not finding:
            raise HTTPException(
                status_code=404,
                detail=f"Finding '{suggestion_id}' not found in audit run '{resolved_run_id}'"
            )

        # 4. Trigger Project Factory Intake & requirement gate generation via the bridge
        bridge_res = bridge_suggestion_to_project_factory(finding, resolved_run_id, workspace_root)

        # 5. Persist run link mapping in project_factory_run_links.json
        run_link = {
            "suggestion_id": suggestion_id,
            "audit_run_id": resolved_run_id,
            "project_id": bridge_res["project_id"],
            "project_brief_ref": bridge_res["project_brief_ref"],
            "requirement_gate_ref": bridge_res["requirement_gate_ref"],
            "status": "REQUIREMENT_GATE_WAITING",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        save_project_factory_run_link(resolved_run_id, suggestion_id, run_link, workspace_root)

        # 6. Record second action: PROJECT_FACTORY_INTAKE_CREATED (append-only)
        action_id = f"ACT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        created_at = datetime.utcnow().isoformat() + "Z"

        start_log = SuggestionActionLog(
            action_id=action_id,
            suggestion_id=suggestion_id,
            action="PROJECT_FACTORY_INTAKE_CREATED",
            from_status="APPROVED_FOR_PROJECT_FACTORY",
            to_status="REQUIREMENT_GATE_WAITING",
            operator_id=body.operator_id,
            rationale=body.rationale,
            risk_acknowledgement=body.risk_acknowledgement,
            created_at=created_at,
            result={
                "project_brief_created": True,
                "project_id": bridge_res["project_id"],
                "project_brief_ref": bridge_res["project_brief_ref"],
                "requirement_gate_ref": bridge_res["requirement_gate_ref"]
            }
        )
        record_action_log(resolved_run_id, start_log, workspace_root)
        update_suggestion_state(resolved_run_id, suggestion_id, "REQUIREMENT_GATE_WAITING", workspace_root)

        return {
            "status": "success",
            "action_log": log.model_dump(),
            "project_factory_run": {
                "project_id": bridge_res["project_id"],
                "status": "REQUIREMENT_GATE_WAITING",
                "workflow_url": f"/project-factory/{bridge_res['project_id']}"
            }
        }
    except KeyError as ke:
        raise HTTPException(status_code=404, detail=str(ke))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process suggestion action: {e}")


@router.post("/suggestions/{suggestion_id}/open-war-room")
async def open_war_room(
    suggestion_id: str,
    body: SuggestionActionRequest,
    audit_run_id: str | None = None,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    import os
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        resolved_run_id = _resolve_audit_run_id(audit_run_id, workspace_root)
        from services.self_repair_audit.suggestion_actions import process_suggestion_action
        log = process_suggestion_action(
            audit_run_id=resolved_run_id,
            suggestion_id=suggestion_id,
            action="OPEN_WAR_ROOM",
            to_status="WAR_ROOM_RECOMMENDED",
            req=body,
            workspace_root=workspace_root
        )
        return {"status": "success", "action_log": log.model_dump()}
    except KeyError as ke:
        raise HTTPException(status_code=404, detail=str(ke))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process suggestion action: {e}")


@router.post("/suggestions/{suggestion_id}/defer")
async def defer_suggestion(
    suggestion_id: str,
    body: SuggestionActionRequest,
    audit_run_id: str | None = None,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    import os
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        resolved_run_id = _resolve_audit_run_id(audit_run_id, workspace_root)
        from services.self_repair_audit.suggestion_actions import process_suggestion_action
        log = process_suggestion_action(
            audit_run_id=resolved_run_id,
            suggestion_id=suggestion_id,
            action="DEFER",
            to_status="DEFERRED",
            req=body,
            workspace_root=workspace_root
        )
        return {"status": "success", "action_log": log.model_dump()}
    except KeyError as ke:
        raise HTTPException(status_code=404, detail=str(ke))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process suggestion action: {e}")


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_suggestion(
    suggestion_id: str,
    body: SuggestionActionRequest,
    audit_run_id: str | None = None,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    import os
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        resolved_run_id = _resolve_audit_run_id(audit_run_id, workspace_root)
        from services.self_repair_audit.suggestion_actions import process_suggestion_action
        log = process_suggestion_action(
            audit_run_id=resolved_run_id,
            suggestion_id=suggestion_id,
            action="REJECT",
            to_status="REJECTED",
            req=body,
            workspace_root=workspace_root
        )
        return {"status": "success", "action_log": log.model_dump()}
    except KeyError as ke:
        raise HTTPException(status_code=404, detail=str(ke))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process suggestion action: {e}")


@router.post("/suggestions/{suggestion_id}/request-more-evidence")
async def request_more_evidence(
    suggestion_id: str,
    body: SuggestionActionRequest,
    audit_run_id: str | None = None,
    identity: dict[str, Any] = Depends(require_permission("governor.override")),
):
    import os
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        resolved_run_id = _resolve_audit_run_id(audit_run_id, workspace_root)
        from services.self_repair_audit.suggestion_actions import process_suggestion_action
        log = process_suggestion_action(
            audit_run_id=resolved_run_id,
            suggestion_id=suggestion_id,
            action="REQUEST_MORE_EVIDENCE",
            to_status="MORE_EVIDENCE_REQUESTED",
            req=body,
            workspace_root=workspace_root
        )
        return {"status": "success", "action_log": log.model_dump()}
    except KeyError as ke:
        raise HTTPException(status_code=404, detail=str(ke))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process suggestion action: {e}")


@router.get("/suggestions/{suggestion_id}/actions")
async def get_suggestion_actions(
    suggestion_id: str,
    audit_run_id: str | None = None,
    identity: dict[str, Any] = Depends(require_permission("governor.view")),
):
    import os
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        resolved_run_id = _resolve_audit_run_id(audit_run_id, workspace_root)
        from services.self_repair_audit.suggestion_store import get_action_logs
        all_logs = get_action_logs(resolved_run_id, workspace_root)
        filtered_logs = [log for log in all_logs if log.get("suggestion_id") == suggestion_id]
        return {"status": "success", "actions": filtered_logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve action logs: {e}")
