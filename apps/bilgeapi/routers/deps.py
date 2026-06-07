from typing import Any
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.session import get_db

from apps.bilgeapi.repositories.interface import (
    IncidentRepository, DiagnosticRepository, FindingRepository,
    RecommendationRepository, RepairRequestRepository, AuditRepository, WebhookDeliveryRepository,
    ReleaseCheckRepository, ApiKeyRepository, ResearchRepository, ImprovementRepository,
    PrDraftRepository, PrVerificationRepository, PrReviewFeedbackRepository, PatchRevisionRepository
)
from apps.bilgeapi.repositories.postgres import (
    PostgresIncidentRepository, PostgresDiagnosticRepository, PostgresFindingRepository,
    PostgresRecommendationRepository, PostgresRepairRequestRepository, PostgresAuditRepository, PostgresWebhookDeliveryRepository,
    PostgresReleaseCheckRepository, PostgresApiKeyRepository, PostgresResearchRepository, PostgresImprovementRepository,
    PostgresPrDraftRepository, PostgresPrVerificationRepository, PostgresPrReviewFeedbackRepository, PostgresPatchRevisionRepository
)
from apps.bilgeapi.services.audit import AuditService
from apps.bilgeapi.services.diagnostic import DiagnosticService
from apps.bilgeapi.services.risk import RiskScoringService
from apps.bilgeapi.services.webhook import WebhookDeliveryService
from apps.bilgeapi.services.release import BilgeAPIReleaseGate
from apps.bilgeapi.services.api_key import ApiKeyService
from apps.bilgeapi.services.research import WebResearchAdapter, MockSearchProvider, WebSearchProvider, SerperSearchProvider
from apps.bilgeapi.services.improvement import ImprovementProposalEngine, ReleaseGateSimulator
from apps.bilgeapi.adapters.github_pr import BaseGitHubPrAdapter


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


def get_web_search_provider() -> WebSearchProvider:
    from apps.bilgeapi.config import settings
    provider_name = settings.BILGEAPI_SEARCH_PROVIDER
    if provider_name == "serper":
        return SerperSearchProvider()
    return MockSearchProvider()


def get_web_research_adapter(
    provider: WebSearchProvider = Depends(get_web_search_provider),
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


async def get_pr_draft_repository(db: AsyncSession = Depends(get_db)) -> PrDraftRepository:
    # Check if we should return in-memory repo for testing
    # In standard app context, we return postgres repository
    from apps.bilgeapi.config import settings
    # We can default to postgres, but if testing overrides or settings suggest, we can instantiate InMemory. 
    # Actually, we can return PostgresPrDraftRepository(db) as default, just like get_improvement_repository.
    return PostgresPrDraftRepository(db)


def get_github_pr_adapter() -> BaseGitHubPrAdapter:
    from apps.bilgeapi.config import settings
    from apps.bilgeapi.adapters.github_pr import MockGitHubPrAdapter, GitHubDraftPrAdapter
    
    provider_name = settings.BILGEAPI_PR_PROVIDER
    if provider_name == "github":
        return GitHubDraftPrAdapter(
            token=settings.BILGEAPI_GITHUB_TOKEN,
            owner=settings.BILGEAPI_GITHUB_OWNER,
            repo=settings.BILGEAPI_GITHUB_REPO,
            base_branch=settings.BILGEAPI_GITHUB_BASE_BRANCH,
            allow_real=settings.BILGEAPI_ALLOW_REAL_DRAFT_PR
        )
    return MockGitHubPrAdapter()


def get_pr_draft_service(
    pr_draft_repo: PrDraftRepository = Depends(get_pr_draft_repository),
    proposal_repo: ImprovementRepository = Depends(get_improvement_repository),
    github_adapter: BaseGitHubPrAdapter = Depends(get_github_pr_adapter),
    audit_service: AuditService = Depends(get_audit_service)
) -> Any:
    from apps.bilgeapi.services.pr_draft import PrDraftService
    return PrDraftService(pr_draft_repo, proposal_repo, github_adapter, audit_service)


async def get_pr_verification_repository(db: AsyncSession = Depends(get_db)) -> PrVerificationRepository:
    return PostgresPrVerificationRepository(db)


async def get_pr_review_feedback_repository(db: AsyncSession = Depends(get_db)) -> PrReviewFeedbackRepository:
    return PostgresPrReviewFeedbackRepository(db)


async def get_patch_revision_repository(db: AsyncSession = Depends(get_db)) -> PatchRevisionRepository:
    return PostgresPatchRevisionRepository(db)


def get_pr_verification_service(
    verification_repo: PrVerificationRepository = Depends(get_pr_verification_repository),
    pr_draft_repo: PrDraftRepository = Depends(get_pr_draft_repository),
    proposal_repo: ImprovementRepository = Depends(get_improvement_repository),
    research_repo: ResearchRepository = Depends(get_research_repository),
    audit_service: AuditService = Depends(get_audit_service),
    revision_repo: PatchRevisionRepository = Depends(get_patch_revision_repository)
) -> Any:
    from apps.bilgeapi.services.pr_verification import PrVerificationService
    return PrVerificationService(
        verification_repo=verification_repo,
        pr_draft_repo=pr_draft_repo,
        proposal_repo=proposal_repo,
        research_repo=research_repo,
        audit_service=audit_service,
        revision_repo=revision_repo
    )


def get_reviewer_feedback_service(
    feedback_repo: PrReviewFeedbackRepository = Depends(get_pr_review_feedback_repository),
    pr_draft_repo: PrDraftRepository = Depends(get_pr_draft_repository),
    audit_service: AuditService = Depends(get_audit_service)
) -> Any:
    from apps.bilgeapi.services.patch_revision import ReviewerFeedbackService
    return ReviewerFeedbackService(feedback_repo, pr_draft_repo, audit_service)


def get_patch_revision_engine(
    revision_repo: PatchRevisionRepository = Depends(get_patch_revision_repository),
    pr_draft_repo: PrDraftRepository = Depends(get_pr_draft_repository),
    audit_service: AuditService = Depends(get_audit_service)
) -> Any:
    from apps.bilgeapi.services.patch_revision import PatchRevisionEngine
    return PatchRevisionEngine(revision_repo, pr_draft_repo, audit_service)




