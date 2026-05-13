"""
libs/db/session.py — Phase 13.04.2
Unified database session management with aggressive SQLite fallback & Auto-Seeding.
"""
from __future__ import annotations

import os
import logging
import asyncio
import threading
import uuid
from urllib.parse import urlparse
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
# SQLAlchemy imports moved to local scopes to prevent Phase 13.04 startup hangs in Python 3.14+
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
# from sqlalchemy.orm import sessionmaker, Session
# from sqlalchemy import create_engine, event, text, select, func

# Import variables directly from libs.config
try:
    from libs.config import (
        APP_ENV,
        DATABASE_URL,
        DB_POOL_SIZE,
        DB_MAX_OVERFLOW,
        DB_POOL_TIMEOUT,
        LOCAL_DEV_DB_STRATEGY,
        QUEUE_BACKEND,
        REDIS_URL
    )
except ImportError:
    APP_ENV = os.getenv("APP_ENV", "development")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/ai_company")
    DB_POOL_SIZE = 10
    DB_MAX_OVERFLOW = 20
    DB_POOL_TIMEOUT = 30
    LOCAL_DEV_DB_STRATEGY = os.getenv("LOCAL_DEV_DB_STRATEGY", "sqlite-fallback")
    QUEUE_BACKEND = os.getenv("QUEUE_BACKEND", "auto")
    REDIS_URL = os.getenv("REDIS_URL", "")

logger = logging.getLogger("db.session")

# ── Globals ───
_engine = None
_async_session_factory = None
_sync_engine = None
_sync_session_factory = None

_DB_DEGRADED = False  
_DB_CHECKED = False   
_DB_ERROR = ""
_last_loop = None
_lock = threading.Lock()
_REDIS_CLIENT = None
_REDIS_DISABLED = False
_REDIS_LOGGED = False


def _normalize_database_url(url: str) -> str:
    return (url or "").replace("+asyncpg", "").replace("+aiosqlite", "")


def _primary_db_target() -> tuple[str, int] | None:
    normalized = _normalize_database_url(DATABASE_URL)
    if not normalized or normalized.startswith("sqlite"):
        return None

    parsed = urlparse(normalized)
    host = parsed.hostname or "localhost"
    if parsed.port is not None:
        port = parsed.port
    elif parsed.scheme.startswith("postgres"):
        port = 5432
    else:
        port = 0

    return (host, port)

def check_connectivity(timeout=0.5):
    global _DB_DEGRADED, _DB_CHECKED, _DB_ERROR
    
    # SIF-01 Enhancement: Quick exit if already checked to prevent blocking loops
    if _DB_CHECKED and _DB_DEGRADED:
        return False
        
    import socket
    target = _primary_db_target()
    if target is None:
        _DB_DEGRADED = False
        _DB_ERROR = ""
        _DB_CHECKED = True
        return True

    host, port = target
    try:
        # Phase 32: Use a much tighter timeout for local connectivity check
        with socket.create_connection((host, port), timeout=timeout):
            _DB_DEGRADED = False
            _DB_ERROR = ""
    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        _DB_DEGRADED = True
        _DB_ERROR = f"Primary DB ({host}:{port}) unreachable: {exc}. SQLite fallback active."
    
    _DB_CHECKED = True
    return not _DB_DEGRADED

def is_db_degraded() -> bool:
    global _DB_DEGRADED, _DB_CHECKED
    if not _DB_CHECKED:
        check_connectivity()
    return _DB_DEGRADED

def db_error() -> str:
    global _DB_ERROR
    if not _DB_CHECKED:
        check_connectivity()
    return _DB_ERROR

async def is_db_available() -> bool:
    global _DB_ERROR
    try:
        from sqlalchemy import text
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        _DB_ERROR = ""
        return True
    except Exception as exc:
        if not _DB_ERROR:
            _DB_ERROR = str(exc)
        return False

def get_engine():
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import event, text
    global _engine, _last_loop, _DB_DEGRADED, _DB_CHECKED
    try:
        curr_active_loop = asyncio.get_running_loop()
    except RuntimeError:
        curr_active_loop = None

    # Force re-check if we are in fallback but engine was previously pointing elsewhere
    if _engine is not None and _DB_DEGRADED:
        if "sqlite" not in str(_engine.url):
             _engine = None 

    if _engine is None or (curr_active_loop is not None and _last_loop is not curr_active_loop):
        with _lock:
            # Double-check pattern
            if _engine is None or (curr_active_loop is not None and _last_loop is not curr_active_loop):
                if not _DB_CHECKED: 
                    check_connectivity()
                
                if _DB_DEGRADED:
                    _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    sqlite_path = os.path.join(_root, "runtime", "data", "cortex_local_v2.db")
                    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
                    # Use a stable file path and ensure it's absolute
                    abs_path = os.path.abspath(sqlite_path).replace('\\', '/')
                    sqlite_url = f"sqlite+aiosqlite:///{abs_path}?timeout=60"
                    
                    _engine = create_async_engine(
                        sqlite_url,
                        connect_args={"timeout": 60}
                    )
                    
                    @event.listens_for(_engine.sync_engine, "connect")
                    def set_sqlite_pragma(dbapi_connection, connection_record):
                        cursor = dbapi_connection.cursor()
                        cursor.execute("PRAGMA journal_mode=WAL")
                        cursor.execute("PRAGMA synchronous=NORMAL")
                        cursor.execute("PRAGMA busy_timeout=60000")
                        cursor.execute("PRAGMA foreign_keys=ON")
                        cursor.close()
                    
                    if not _DB_ERROR:
                        _DB_ERROR = "SQLite Fallback Active"
                else:
                    # SRE Hardening: Ensure pool params are only passed for Postgres
                    from typing import Dict, Any
                    engine_kwargs: Dict[str, Any] = {
                        "pool_pre_ping": True,
                    }
                    if not str(DATABASE_URL).startswith("sqlite"):
                        engine_kwargs["pool_timeout"] = 30
                        engine_kwargs["pool_size"] = DB_POOL_SIZE
                        engine_kwargs["max_overflow"] = DB_MAX_OVERFLOW
                        
                    _engine = create_async_engine(DATABASE_URL, **engine_kwargs)
                _last_loop = curr_active_loop
    return _engine

def _get_session_factory():
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    global _async_session_factory
    engine = get_engine()
    if _async_session_factory is None or _async_session_factory.kw["bind"] is not engine:
        _async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return _async_session_factory

class _LazySessionLocal:
    def __call__(self): return _get_session_factory()()

AsyncSessionLocal = _LazySessionLocal()

async def get_db() -> AsyncGenerator: # Type hint simplified to avoid import
    from sqlalchemy.ext.asyncio import AsyncSession
    async with AsyncSessionLocal() as session: yield session

@asynccontextmanager
async def session_scope():
    """
    Asenkron veritabanı oturumu sağlar ve otomatik commit/rollback yapar.
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

get_db_ctx = session_scope

async def init_db():
    from sqlalchemy import select, func, text
    import hashlib
    import json
    from datetime import datetime, timezone
    from libs.db.models.core_models import Base, Project, ProjectSource, ProjectStatus, SubTask, TaskPriority, ApprovalRequest
    from libs.db.models.learning_models import Base as LearningBase
    from libs.db.models.governance_models import (
        Base as GovBase,
        GovernorCaseRecord,
        GovernorDomain,
        GovernorOutcomeRecord,
        GovernorOutcomeQuality,
        GovernorOutcomeType,
        GovernanceProofEventRecord,
        GovernanceProofSnapshotRecord,
        PolicyProposal,
        ProofEventType,
        ProofSealStatus,
    )
    from libs.db.models.lineage_models import Base as LineageBase, DecisionLineage
    from libs.db.models.compliance_models import Base as CompBase
    from libs.db.models.auth_models import Base as AuthBase, Operator, SystemIdentity
    from libs.db.models.repair_models import Base as RepairBase
    from libs.db.models.federation_models import Base as FederationBase
    
    engine = get_engine()
    
    async with engine.begin() as conn:
        # All models share the same Base from libs.db.base, 
        # so one create_all would be enough if all are imported.
        # We keep the explicit calls for clarity and modularity.
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(LearningBase.metadata.create_all)
        await conn.run_sync(GovBase.metadata.create_all)
        await conn.run_sync(LineageBase.metadata.create_all)
        await conn.run_sync(CompBase.metadata.create_all)
        await conn.run_sync(AuthBase.metadata.create_all)
        await conn.run_sync(RepairBase.metadata.create_all)
        await conn.run_sync(FederationBase.metadata.create_all)
        db_label = "SQLite Fallback" if is_db_degraded() else "PostgreSQL"
        logger.info(f"OK: Veritabanı tabloları hazır ({db_label}).")

    # ── Auto-Seeding Phase 1: Critical Identity Seeds (SIF-01 Compliance) ───
    async with AsyncSessionLocal() as db:
        try:
            # 0. Seed Agent Nodes from Registry
            from agents.specialist_agents.agent_registry import build_agents
            from libs.db.models.core_models import AgentNode, AgentRole, AgentStatus, FleetCluster, FleetStatus
            
            registry_agents = build_agents()
            for agent_id, agent_obj in registry_agents.items():
                res = await db.execute(select(AgentNode).where(AgentNode.name == agent_id))
                if not res.scalar_one_or_none():
                    # Map role string to AgentRole enum safely
                    try:
                        # Try to match by ID or common roles
                        role_enum = AgentRole.EXECUTOR
                        if "architect" in agent_id: role_enum = AgentRole.PLANNER
                        elif "planner" in agent_id: role_enum = AgentRole.PLANNER
                        elif "reviewer" in agent_id: role_enum = AgentRole.REVIEWER
                        elif "auditor" in agent_id: role_enum = AgentRole.AUDITOR
                        elif "governor" in agent_id: role_enum = AgentRole.GOVERNOR
                        elif "security" in agent_id: role_enum = AgentRole.AUDITOR
                    except:
                        role_enum = AgentRole.EXECUTOR

                    node = AgentNode(
                        name=agent_id,
                        role=role_enum,
                        status=AgentStatus.IDLE,
                        trust_score=1.0,
                        capabilities={"id": agent_id, "name": agent_obj.name}
                    )
                    db.add(node)
                    logger.info(f"SEED: AgentNode '{agent_id}' oluşturuldu.")

            # 1. Seed Admin Operator
            res = await db.execute(select(Operator).where(Operator.email == "admin@sovereign.agi"))
            if not res.scalar_one_or_none():
                from bcrypt import hashpw, gensalt
                hashed = hashpw("admin1234".encode(), gensalt()).decode()
                admin = Operator(
                    email="admin@sovereign.agi",
                    username="admin",
                    hashed_password=hashed,
                    role="SOVEREIGN_PRIME",
                    is_active=True
                )
                db.add(admin)
                logger.info("SEED: 'admin@sovereign.agi' Prime Operator oluşturuldu.")

            # 2. Seed Default Governance Agent
            res = await db.execute(select(SystemIdentity).where(SystemIdentity.name == "governance_agent"))
            if not res.scalar_one_or_none():
                gov_agent = SystemIdentity(
                    name="governance_agent",
                    identity_type="agent",
                    role="GOVERNANCE_AGENT",
                    trust_score=100,
                    risk_level="LOW"
                )
                db.add(gov_agent)
                logger.info("SEED: 'governance_agent' System Identity oluşturuldu.")

            await db.commit()
            logger.info("SEED Phase 1: Kritik kimlikler kaydedildi.")
        except Exception as e:
            logger.error(f"SEED Phase 1 ERROR: {e}")
            await db.rollback()

    # ── Auto-Seeding Phase 2: Demo Data (SQLite Fallback Only) ───
    async with AsyncSessionLocal() as db:
        try:

            if is_db_degraded():
                project_count = await db.scalar(select(func.count(Project.id))) or 0
                if project_count == 0:
                    now = datetime.now(timezone.utc)

                    running_project = Project(
                        title="Pilot Intel Ingestion",
                        description="Fallback mode demo workflow for the control plane.",
                        status=ProjectStatus.RUNNING,
                        source=ProjectSource.CONTROL_PLANE,
                        priority=TaskPriority.HIGH,
                        workflow_template="intel_ingestion",
                        quality_profile="standard",
                        progress_pct=66,
                        started_at=now,
                        execution_context={},
                    )
                    queued_project = Project(
                        title="Daily Compliance Digest",
                        description="Queued governance digest generation.",
                        status=ProjectStatus.QUEUED,
                        source=ProjectSource.CONTROL_PLANE,
                        priority=TaskPriority.MEDIUM,
                        workflow_template="compliance_digest",
                        quality_profile="standard",
                        progress_pct=0,
                        execution_context={},
                    )
                    approval_project = Project(
                        title="Patch Review Gate",
                        description="Workflow waiting for operator approval.",
                        status=ProjectStatus.PENDING_APPROVAL,
                        source=ProjectSource.CONTROL_PLANE,
                        priority=TaskPriority.MEDIUM,
                        workflow_template="patch_review",
                        quality_profile="strict",
                        progress_pct=50,
                        started_at=now,
                        execution_context={},
                        review_required=True,
                    )
                    db.add_all([running_project, queued_project, approval_project])
                    await db.flush()

                    db.add_all([
                        SubTask(
                            project_id=running_project.id,
                            agent_id="planner.alpha",
                            action="plan_intel_pipeline",
                            prompt="Prepare ingestion plan for source connectors.",
                            status=ProjectStatus.COMPLETED,
                            attempts=1,
                            result="Connector plan generated.",
                            completed_at=now,
                        ),
                        SubTask(
                            project_id=running_project.id,
                            agent_id="executor.beta",
                            action="run_ingestion",
                            prompt="Execute normalized source ingestion.",
                            status=ProjectStatus.RUNNING,
                            attempts=1,
                        ),
                        SubTask(
                            project_id=running_project.id,
                            agent_id="reviewer.gamma",
                            action="validate_payloads",
                            prompt="Validate extracted payloads and quality checks.",
                            status=ProjectStatus.PENDING,
                        ),
                        SubTask(
                            project_id=queued_project.id,
                            agent_id="planner.delta",
                            action="prepare_digest",
                            prompt="Assemble daily compliance digest outline.",
                            status=ProjectStatus.PENDING,
                        ),
                        SubTask(
                            project_id=approval_project.id,
                            agent_id="governor.prime",
                            action="review_patch_bundle",
                            prompt="Review latest patch bundle for release readiness.",
                            status=ProjectStatus.COMPLETED,
                            attempts=1,
                            result="Initial review complete.",
                            completed_at=now,
                        ),
                        SubTask(
                            project_id=approval_project.id,
                            agent_id="auditor.theta",
                            action="await_operator_signoff",
                            prompt="Await operator decision for deployment gate.",
                            status=ProjectStatus.PENDING_APPROVAL,
                        ),
                    ])
                    logger.info("SEED: Demo workflows created for SQLite fallback control plane.")

                projects = (
                    await db.execute(select(Project).order_by(Project.created_at.asc()))
                ).scalars().all()

                project_by_title = {project.title: project for project in projects}
                approval_project = project_by_title.get("Patch Review Gate")
                running_project = project_by_title.get("Pilot Intel Ingestion")
                queued_project = project_by_title.get("Daily Compliance Digest")

                cluster_count = await db.scalar(select(func.count(FleetCluster.id))) or 0
                if cluster_count == 0:
                    primary_cluster = FleetCluster(
                        name="Main Intel Cluster",
                        status=FleetStatus.ACTIVE,
                        region="eu-central",
                        budget_limit=1200.0,
                        current_budget_usage=720.5,
                        max_parallel_projects=6,
                    )
                    edge_cluster = FleetCluster(
                        name="Edge Processing Node",
                        status=FleetStatus.ACTIVE,
                        region="tr-west",
                        budget_limit=800.0,
                        current_budget_usage=250.0,
                        max_parallel_projects=4,
                    )
                    db.add_all([primary_cluster, edge_cluster])
                    await db.flush()

                    seed_agents = (
                        await db.execute(select(AgentNode).order_by(AgentNode.created_at.asc()))
                    ).scalars().all()

                    for index, agent in enumerate(seed_agents):
                        target_cluster = primary_cluster if index < 7 else edge_cluster
                        agent.cluster_id = target_cluster.id
                        agent.current_load = 1 if index in (1, 2, 7, 8) else 0
                        agent.cost_rate = 12.5 + index
                        if index == 10:
                            agent.status = AgentStatus.QUARANTINED
                        elif index in (1, 2, 7, 8):
                            agent.status = AgentStatus.BUSY
                        else:
                            agent.status = AgentStatus.IDLE

                    logger.info("SEED: Fleet clusters and agent placement created for SQLite fallback.")

                if approval_project is not None:
                    approval_count = await db.scalar(select(func.count(ApprovalRequest.id))) or 0
                    if approval_count == 0:
                        db.add(
                            ApprovalRequest(
                                project_id=approval_project.id,
                                step_id="release_gate",
                                request_type="risk_score",
                                reason="Patch bundle yüksek etki alanına dokunuyor, operatör onayı gerekli.",
                                input_data={
                                    "bundle": "patch-review-gate",
                                    "risk_class": "HIGH",
                                    "requested_action": "approve_release",
                                },
                                status="pending",
                                comment="Governor gating active.",
                            )
                        )

                    case_count = await db.scalar(select(func.count(GovernorCaseRecord.id))) or 0
                    if case_count == 0:
                        db.add_all([
                            GovernorCaseRecord(
                                project_id=approval_project.id,
                                project_title=approval_project.title,
                                project_status=str(approval_project.status.value if hasattr(approval_project.status, "value") else approval_project.status),
                                pending_reason="RISK_REVIEW_REQUIRED",
                                risk_class="HIGH",
                                risk_score=87,
                                recommended_decision="REQUIRES_PRIME_APPROVAL",
                                decision_reason_codes=[
                                    "Açık approval isteği mevcut",
                                    "Release gate için PRIME onayı gerekiyor",
                                ],
                                has_open_incident=0,
                                has_safety_lock=1,
                                has_active_fingerprint=0,
                                requires_prime=1,
                                requires_quorum=0,
                                missing_context=0,
                                stale_seconds=5400,
                                snapshot_payload={"surface": "release-gate", "operator": "prime"},
                            ),
                            GovernorCaseRecord(
                                project_id=queued_project.id if queued_project is not None else approval_project.id,
                                project_title=queued_project.title if queued_project is not None else "Daily Compliance Digest",
                                project_status=str(queued_project.status.value if queued_project is not None and hasattr(queued_project.status, "value") else (queued_project.status if queued_project is not None else "QUEUED")),
                                pending_reason="CONTEXT_SYNC_PENDING",
                                risk_class="MEDIUM",
                                risk_score=41,
                                recommended_decision="AUTO_REPLAY_CANDIDATE",
                                decision_reason_codes=[
                                    "Eksik bağlam senkronizasyonu",
                                    "Tekrar deneme düşük riskli",
                                ],
                                has_open_incident=0,
                                has_safety_lock=0,
                                has_active_fingerprint=0,
                                requires_prime=0,
                                requires_quorum=0,
                                missing_context=1,
                                stale_seconds=1800,
                                snapshot_payload={"surface": "digest-sync", "retryable": True},
                            ),
                        ])

                    proposal_count = await db.scalar(select(func.count(PolicyProposal.id))) or 0
                    if proposal_count == 0:
                        db.add_all([
                            PolicyProposal(
                                title="Governor Retry Threshold Tuning",
                                description="Replay eşiğini düşük riskli iş akışları için optimize et.",
                                policy_code="governor.retry_threshold=2",
                                status="PROPOSED",
                            ),
                            PolicyProposal(
                                title="Fleet Quarantine Cooldown",
                                description="Karantina taramalarında gözlem penceresini 15 dakikaya sabitle.",
                                policy_code="fleet.quarantine.cooldown=900",
                                status="PROPOSED",
                            ),
                        ])

                    outcome_count = await db.scalar(select(func.count(GovernorOutcomeRecord.id))) or 0
                    if outcome_count == 0:
                        db.add_all([
                            GovernorOutcomeRecord(
                                project_id=approval_project.id,
                                decision="REQUIRES_PRIME_APPROVAL",
                                final_outcome=GovernorOutcomeType.SUCCESS,
                                quality=GovernorOutcomeQuality.OPTIMAL,
                                was_successful=1,
                                operator_overrode=0,
                                operator_agreed=1,
                                resolution_latency_seconds=142,
                                reason_codes=["PRIME_APPROVAL_CONFIRMED"],
                            ),
                            GovernorOutcomeRecord(
                                project_id=running_project.id if running_project is not None else approval_project.id,
                                decision="AUTO_REPLAY_CANDIDATE",
                                final_outcome=GovernorOutcomeType.IMPROVEMENT,
                                quality=GovernorOutcomeQuality.SUBOPTIMAL,
                                was_successful=1,
                                operator_overrode=0,
                                operator_agreed=1,
                                resolution_latency_seconds=96,
                                reason_codes=["RETRY_RECOVERED_EXECUTION"],
                            ),
                        ])

                    lineage_count = await db.scalar(select(func.count(DecisionLineage.id))) or 0
                    if lineage_count == 0:
                        db.add_all([
                            DecisionLineage(
                                decision_type="GOVERNOR_CASE",
                                component_name="Governor Inbox",
                                rationale="Patch Review Gate yüksek riskte kaldığı için PRIME onayına yönlendirildi.",
                                trigger_event={"project": approval_project.title, "risk_class": "HIGH"},
                                outcome="PENDING_PRIME",
                                confidence_score=0.93,
                                integrity_hash="seed-governor-case-01",
                                meta_data={"surface": "governor"},
                            ),
                            DecisionLineage(
                                decision_type="SELF_TUNING",
                                component_name="Evolution Hub",
                                rationale="Retry threshold düşük riskli tekrar denemelerde optimize edilmeli.",
                                trigger_event={"proposal": "Governor Retry Threshold Tuning"},
                                outcome="PROPOSED",
                                confidence_score=0.88,
                                integrity_hash="seed-self-tuning-01",
                                meta_data={"surface": "self-tuning"},
                            ),
                        ])

                    proof_event_count = await db.scalar(select(func.count(GovernanceProofEventRecord.id))) or 0
                    if proof_event_count == 0:
                        seed_events = [
                            (
                                ProofEventType.GOVERNOR_DECISION,
                                GovernorDomain.WORKFLOW,
                                str(approval_project.id),
                                {
                                    "summary": "Patch Review Gate PRIME onay kuyruğuna alındı.",
                                    "project": approval_project.title,
                                    "decision": "REQUIRES_PRIME_APPROVAL",
                                },
                            ),
                            (
                                ProofEventType.POLICY_EVOLUTION,
                                GovernorDomain.POLICY,
                                "Governor Retry Threshold Tuning",
                                {
                                    "summary": "Retry threshold düşük riskli tekrar denemeler için optimize önerisi aldı.",
                                    "proposal": "Governor Retry Threshold Tuning",
                                    "status": "PROPOSED",
                                },
                            ),
                            (
                                ProofEventType.ALERT_EVENT,
                                GovernorDomain.APPROVAL,
                                "approval-risk-score",
                                {
                                    "summary": "Risk score gate approval isteği canlı denetim zincirine işlendi.",
                                    "request_type": "risk_score",
                                    "status": "pending",
                                },
                            ),
                        ]

                        prev_hash = None
                        for chain_index, (event_type, domain, entity_id, payload) in enumerate(seed_events, start=1):
                            canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
                            payload_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                            event_hash = hashlib.sha256(
                                f"{chain_index}|{event_type.value}|{entity_id}|{payload_hash}|{prev_hash or ''}".encode("utf-8")
                            ).hexdigest()
                            db.add(
                                GovernanceProofEventRecord(
                                    event_type=event_type,
                                    domain=domain,
                                    entity_id=entity_id,
                                    payload_hash=payload_hash,
                                    payload_canonical=canonical,
                                    prev_event_hash=prev_hash,
                                    event_hash=event_hash,
                                    chain_index=chain_index,
                                    created_by="governance_agent",
                                )
                            )
                            prev_hash = event_hash

                    fleet_event_types = [
                        ProofEventType.AGENT_ASSIGNED,
                        ProofEventType.BUDGET_BLOCK,
                        ProofEventType.AGENT_QUARANTINED,
                        ProofEventType.CLUSTER_FROZEN,
                    ]
                    fleet_event_count = await db.scalar(
                        select(func.count(GovernanceProofEventRecord.id)).where(
                            GovernanceProofEventRecord.event_type.in_(fleet_event_types)
                        )
                    ) or 0
                    if fleet_event_count == 0:
                        max_chain = await db.scalar(select(func.max(GovernanceProofEventRecord.chain_index))) or 0
                        last_hash = await db.scalar(
                            select(GovernanceProofEventRecord.event_hash)
                            .order_by(GovernanceProofEventRecord.chain_index.desc())
                            .limit(1)
                        )
                        fleet_seed_events = [
                            (
                                ProofEventType.AGENT_ASSIGNED,
                                GovernorDomain.WORKFLOW,
                                str(running_project.id) if running_project else "fleet-seed-1",
                                {
                                    "details": "planner.alpha Main Intel Cluster üzerine atandı.",
                                    "project": running_project.title if running_project else "Pilot Intel Ingestion",
                                },
                            ),
                            (
                                ProofEventType.BUDGET_BLOCK,
                                GovernorDomain.WORKFLOW,
                                str(queued_project.id) if queued_project else "fleet-seed-2",
                                {
                                    "details": "Edge Processing Node bütçe eşiğine yaklaştığı için yeni iş alımı yavaşlatıldı.",
                                    "project": queued_project.title if queued_project else "Daily Compliance Digest",
                                },
                            ),
                            (
                                ProofEventType.AGENT_QUARANTINED,
                                GovernorDomain.INCIDENT,
                                "security.sentinel",
                                {
                                    "details": "security.sentinel düşük güven skoru nedeniyle karantinaya alındı.",
                                },
                            ),
                            (
                                ProofEventType.CLUSTER_FROZEN,
                                GovernorDomain.META,
                                "edge-processing-node",
                                {
                                    "details": "Edge Processing Node gözlem amaçlı donduruldu ve failover denetimine alındı.",
                                },
                            ),
                        ]

                        prev_hash = last_hash
                        for offset, (event_type, domain, entity_id, payload) in enumerate(fleet_seed_events, start=1):
                            canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
                            payload_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                            chain_index = max_chain + offset
                            event_hash = hashlib.sha256(
                                f"{chain_index}|{event_type.value}|{entity_id}|{payload_hash}|{prev_hash or ''}".encode("utf-8")
                            ).hexdigest()
                            db.add(
                                GovernanceProofEventRecord(
                                    event_type=event_type,
                                    domain=domain,
                                    entity_id=entity_id,
                                    payload_hash=payload_hash,
                                    payload_canonical=canonical,
                                    prev_event_hash=prev_hash,
                                    event_hash=event_hash,
                                    chain_index=chain_index,
                                    created_by="governance_agent",
                                )
                            )
                            prev_hash = event_hash

                    snapshot_count = await db.scalar(select(func.count(GovernanceProofSnapshotRecord.id))) or 0
                    if snapshot_count == 0:
                        proof_events = (
                            await db.execute(
                                select(GovernanceProofEventRecord).order_by(GovernanceProofEventRecord.chain_index.asc())
                            )
                        ).scalars().all()
                        if proof_events:
                            combined_hashes = "".join(event.event_hash for event in proof_events)
                            merkle_root = hashlib.sha256(combined_hashes.encode("utf-8")).hexdigest()
                            snapshot_hash = hashlib.sha256(
                                f"proof-seed|{merkle_root}|{len(proof_events)}".encode("utf-8")
                            ).hexdigest()
                            db.add(
                                GovernanceProofSnapshotRecord(
                                    snapshot_name="PHASE_12_FINAL_SNAP_20260427",
                                    start_chain_index=proof_events[0].chain_index,
                                    end_chain_index=proof_events[-1].chain_index,
                                    event_count=len(proof_events),
                                    merkle_root=merkle_root,
                                    snapshot_hash=snapshot_hash,
                                    seal_status=ProofSealStatus.SEALED,
                                    sealed_by="governance_agent",
                                )
                            )

            await db.commit()
        except Exception as e:
            logger.error(f"SEED ERROR: {e}")
            await db.rollback()

async def close_db():
    global _engine, _sync_engine, _REDIS_CLIENT, _REDIS_DISABLED, _REDIS_LOGGED
    if _engine: await _engine.dispose(); _engine = None
    if _sync_engine: _sync_engine.dispose(); _sync_engine = None
    if _REDIS_CLIENT is not None:
        try:
            await _REDIS_CLIENT.close()
        except Exception:
            pass
    _REDIS_CLIENT = None
    _REDIS_DISABLED = False
    _REDIS_LOGGED = False

async def get_redis_client():
    global _REDIS_CLIENT, _REDIS_DISABLED, _REDIS_LOGGED
    if _REDIS_DISABLED:
        return None
    if _REDIS_CLIENT is not None:
        return _REDIS_CLIENT
    if not REDIS_URL:
        return None
    try:
        from redis import asyncio as aioredis
        client = aioredis.from_url(REDIS_URL, decode_responses=True)
        await asyncio.wait_for(client.ping(), timeout=1.0)
        _REDIS_CLIENT = client
        return _REDIS_CLIENT
    except Exception as exc:
        if APP_ENV == "development" and (QUEUE_BACKEND or "auto").lower() != "celery":
            _REDIS_DISABLED = True
            if not _REDIS_LOGGED:
                logger.info("Redis unavailable in local development; continuing in degraded mode (%s).", exc)
                _REDIS_LOGGED = True
            return None
        return None

# ── Sync Support ───
def get_sync_engine():
    from sqlalchemy import create_engine, event
    global _sync_engine
    if _sync_engine is None:
        if is_db_degraded():
            _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            sqlite_path = os.path.join(_root, "runtime", "data", "cortex_local_v2.db")
            _sync_engine = create_engine(f"sqlite:///{sqlite_path.replace('\\', '/')}", connect_args={"check_same_thread": False, "timeout": 60})
            
            @event.listens_for(_sync_engine, "connect")
            def set_sqlite_pragma_sync(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA busy_timeout=60000")
                cursor.close()
        else:
            sync_url = DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", "")
            _sync_engine = create_engine(sync_url)
    return _sync_engine

def _get_sync_session_factory():
    from sqlalchemy.orm import sessionmaker
    global _sync_session_factory
    engine = get_sync_engine()
    if _sync_session_factory is None:
        _sync_session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return _sync_session_factory

def get_sync_session():
    return _get_sync_session_factory()()

from contextlib import contextmanager

@contextmanager
def get_sync_db_ctx():
    """Senkron DB context manager (legacy sync callers için)."""
    session = get_sync_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

class _LazySyncSessionLocal:
    def __call__(self): return _get_sync_session_factory()()

SessionLocal = _LazySyncSessionLocal()
