@router.post("/incidents/auto-close-missing-columns")
async def auto_close_missing_columns(
    threshold_minutes: int = 16,
    identity: dict[str, Any] = Depends(require_permission("incident.resolve"))
):
    """
    Automatically resolves all open `MISSING_COLUMN` incidents that have been
    in the system longer than ``threshold_minutes``.  This helper is useful
    for eliminating dangling incidents that slip past the monitoring loop.

    The endpoint is intentionally limited to users with ``incident.resolve``
    permission to prevent accidental bulk deletions.  The operation is
    performed in a single transaction and the affected incident IDs are
    returned for audit purposes.

    Parameters
    ----------
    threshold_minutes: int, optional
        Age threshold in minutes.  Incidents older than this value are
        considered stale and will be resolved automatically.  Defaults to
        16 minutes which matches the current recurring error criteria.
    identity: dict[str, Any]
        The authenticated identity of the caller.  Must have the
        ``incident.resolve`` scope.

    Returns
    -------
    dict[str, Any]
        ``resolved`` – list of incident IDs that were closed, and
        ``count`` – total number of incidents processed.

    Raises
    ------
    HTTPException
        If the caller lacks permission or if any database error occurs.
    """
    from datetime import timedelta

    now = datetime.now(UTC)
    threshold_delta = timedelta(minutes=threshold_minutes)

    async with AsyncSessionLocal() as db:
        # Find affected incidents
        query = (
            select(OperationalIncident)
            .where(OperationalIncident.incident_type == "MISSING_COLUMN")
            .where(OperationalIncident.status == "open")
            .where(OperationalIncident.created_at <= now - threshold_delta)
        )
        res = await db.execute(query)
        incidents = res.scalars().all()

        if not incidents:
            return {"resolved": [], "count": 0}

        resolved_ids = []

        for inc in incidents:
            inc.status = "resolved"
            inc.resolved_at = now

            # Log the automatic resolution
            await LineageService.log_decision(
                decision_type="AUTO_RESOLUTION",
                component_name="IncidentCenter",
                rationale=(
                    f"Automatic closure of stale {inc.incident_type} "
                    f"incident {inc.id}"
                ),
                outcome="RESOLVED",
                meta_data={
                    "incident_id": str(inc.id),
                    "project_id": str(inc.project_id) if inc.project_id else None,
                    "operator_id": str(identity["id"]),
                    "auto_reason": "stale_restraint",
                },
                db=db,
            )

            # Record learning for the automatic resolution event
            try:
                await LearningOrchestrator.record_incident_learning(
                    incident_data={
                        "id": str(inc.id),
                        "incident_type": inc.incident_type,
                        "severity": inc.severity,
                        "message": inc.message,
                        "project_id": str(inc.project_id) if inc.project_id else None,
                    },
                    outcome_data={
                        "final_outcome": "SUCCESS",
                        "root_cause": "AUTO_STALE_RESOLUTION",
                        "operator_override": False,
                        "strategy_used": "STALE_DRIFT",
                    },
                    db=db,
                )
            except Exception as le:
                logger.warning(
                    f"Learning record failed during auto-resolve of incident {inc.id}: {le}"
                )

            resolved_ids.append(str(inc.id))

        await db.commit()
        return {"resolved": resolved_ids, "count": len(resolved_ids)}