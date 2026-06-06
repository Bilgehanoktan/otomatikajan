from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.session import get_db

from apps.bilgeapi.repositories.interface import (
    IncidentRepository, DiagnosticRepository, FindingRepository,
    RecommendationRepository, RepairRequestRepository, AuditRepository, WebhookDeliveryRepository,
    ReleaseCheckRepository, ApiKeyRepository, ResearchRepository, ImprovementRepository
)
from apps.bilgeapi.repositories.postgres import (
    PostgresIncidentRepository, PostgresDiagnosticRepository, PostgresFindingRepository,
    PostgresRecommendationRepository, PostgresRepairRequestRepository, PostgresAuditRepository, PostgresWebhookDeliveryRepository,
    PostgresReleaseCheckRepository, PostgresApiKeyRepository, PostgresResearchRepository, PostgresImprovementRepository
)
from apps.bilgeapi.services.audit import AuditService
from apps.bilgeapi.services.diagnostic import DiagnosticService
from apps.bilgeapi.services.risk import RiskScoringService
from apps.bilgeapi.services.webhook import WebhookDeliveryService
from apps.bilgeapi.services.release import BilgeAPIReleaseGate
from apps.bilgeapi.services.api_key import ApiKeyService
from apps.bilgeapi.services.research import WebResearchAdapter, MockSearchProvider
from apps.bilgeapi.services.improvement import ImprovementProposalEngine, ReleaseGateSimulator


def get_risk_scoring_service() -> RiskScoringService:
    return RiskScoringService()

async def get_incident_repository(db: AsyncSession = Depends(get_db)) -> IncidentRepository:
    return PostgresIncidentRepository(db)

async def get_diagnostic_repository(db: AsyncSession = Depends(get_db)) -> DiagnosticRepository:
    return PostgresDiagnosticRepository(db)

async def get_finding_repository(db: AsyncSession = Depends(get_db)) -> FindingRepository:
    return PostgresFindingRepository(db)

async def get_recommendation_repository(db: AsyncSession = Depends(get_db)) -> RecommendationRepository:
    return PostgresRecommendationRepository(db)

async def get_repair_repository(db: AsyncSession = Depends(get_db)) -> RepairRequestRepository:
    return PostgresRepairRequestRepository(db)

async def get_audit_repository(db: AsyncSession = Depends(get_db)) -> AuditRepository:
    return PostgresAuditRepository(db)

async def get_webhook_repository(db: AsyncSession = Depends(get_db)) -> WebhookDeliveryRepository:
    return PostgresWebhookDeliveryRepository(db)

async def get_release_repository(db: AsyncSession = Depends(get_db)) -> ReleaseCheckRepository:
    return PostgresReleaseCheckRepository(db)

async def get_api_key_repository(db: AsyncSession = Depends(get_db)) -> ApiKeyRepository:
    return PostgresApiKeyRepository(db)

def get_audit_service(repo: AuditRepository = Depends(get_audit_repository)) -> AuditService:
    return AuditService(repo)

def get_api_key_service(
    repo: ApiKeyRepository = Depends(get_api_key_repository),
    audit_service: AuditService = Depends(get_audit_service)
) -> ApiKeyService:
    return ApiKeyService(repo, audit_service)

def get_webhook_service(
    webhook_repo: WebhookDeliveryRepository = Depends(get_webhook_repository),
    repair_repo: RepairRequestRepository = Depends(get_repair_repository),
    incident_repo: IncidentRepository = Depends(get_incident_repository),
    diagnostic_repo: DiagnosticRepository = Depends(get_diagnostic_repository),
    audit_service: AuditService = Depends(get_audit_service)
) -> WebhookDeliveryService:
    return WebhookDeliveryService(
        webhook_repo=webhook_repo,
        repair_repo=repair_repo,
        incident_repo=incident_repo,
        diagnostic_repo=diagnostic_repo,
        audit_service=audit_service
    )

def get_diagnostic_service(
    incident_repo: IncidentRepository = Depends(get_incident_repository),
    diagnostic_repo: DiagnosticRepository = Depends(get_diagnostic_repository),
    finding_repo: FindingRepository = Depends(get_finding_repository),
    recommendation_repo: RecommendationRepository = Depends(get_recommendation_repository),
    audit_service: AuditService = Depends(get_audit_service)
) -> DiagnosticService:
    return DiagnosticService(
        incident_repo=incident_repo,
        diagnostic_repo=diagnostic_repo,
        finding_repo=finding_repo,
        recommendation_repo=recommendation_repo,
        audit_service=audit_service
    )

def get_release_gate_service(
    repo: ReleaseCheckRepository = Depends(get_release_repository)
) -> BilgeAPIReleaseGate:
    return BilgeAPIReleaseGate(repo)


async def get_research_repository(db: AsyncSession = Depends(get_db)) -> ResearchRepository:
    return PostgresResearchRepository(db)


async def get_improvement_repository(db: AsyncSession = Depends(get_db)) -> ImprovementRepository:
    return PostgresImprovementRepository(db)


def get_web_search_provider() -> MockSearchProvider:
    return MockSearchProvider()


def get_web_research_adapter(
    provider: MockSearchProvider = Depends(get_web_search_provider),
    repo: ResearchRepository = Depends(get_research_repository)
) -> WebResearchAdapter:
    return WebResearchAdapter(provider, repo)


def get_improvement_proposal_engine(
    research_repo: ResearchRepository = Depends(get_research_repository),
    improvement_repo: ImprovementRepository = Depends(get_improvement_repository)
) -> ImprovementProposalEngine:
    return ImprovementProposalEngine(research_repo, improvement_repo)


def get_release_gate_simulator(
    repo: ImprovementRepository = Depends(get_improvement_repository)
) -> ReleaseGateSimulator:
    return ReleaseGateSimulator(repo)


