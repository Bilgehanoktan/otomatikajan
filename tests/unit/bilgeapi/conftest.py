import pytest
import os
import sys
from fastapi.testclient import TestClient

# Ensure root of the project is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

@pytest.fixture(autouse=True)
def setup_test_env():
    # Force default testing configs
    os.environ["BILGEAPI_AUTH_MODE"] = "disabled"
    os.environ["BILGEAPI_STATIC_KEYS"] = "test_key_1,test_key_2"
    os.environ["BILGEAPI_PORT"] = "8100"
    os.environ["BILGEAPI_RATE_LIMIT_RPS"] = "10000"
    yield
    # Cleanup
    if "BILGEAPI_AUTH_MODE" in os.environ:
        del os.environ["BILGEAPI_AUTH_MODE"]
    if "BILGEAPI_STATIC_KEYS" in os.environ:
        del os.environ["BILGEAPI_STATIC_KEYS"]
    if "BILGEAPI_PORT" in os.environ:
        del os.environ["BILGEAPI_PORT"]
    if "BILGEAPI_RATE_LIMIT_RPS" in os.environ:
        del os.environ["BILGEAPI_RATE_LIMIT_RPS"]

@pytest.fixture
def test_client():
    from apps.bilgeapi.main import app
    from apps.bilgeapi.routers.deps import (
        get_incident_repository,
        get_diagnostic_repository,
        get_finding_repository,
        get_recommendation_repository,
        get_repair_repository,
        get_audit_repository,
        get_webhook_repository,
        get_api_key_repository,
        get_research_repository,
        get_improvement_repository,
        get_pr_draft_repository,
        get_pr_verification_repository,
        get_pr_review_feedback_repository,
        get_patch_revision_repository,
        get_review_ledger_repository,
        get_review_ledger_service,
        get_review_ledger_verifier,
        get_ai_patch_suggestion_repository,
        get_ai_patch_provider
    )
    from apps.bilgeapi.repositories.memory import (
        InMemoryIncidentRepository,
        InMemoryDiagnosticRepository,
        InMemoryFindingRepository,
        InMemoryRecommendationRepository,
        InMemoryRepairRequestRepository,
        InMemoryAuditRepository,
        InMemoryWebhookDeliveryRepository,
        InMemoryApiKeyRepository,
        InMemoryResearchRepository,
        InMemoryImprovementRepository,
        InMemoryPrDraftRepository,
        InMemoryPrVerificationRepository,
        InMemoryPrReviewFeedbackRepository,
        InMemoryPatchRevisionRepository,
        InMemoryReviewLedgerRepository,
        InMemoryAIPatchSuggestionRepository,
        memory_repositories
    )
    
    # Reset repositories before each test
    memory_repositories.clear_all()
    
    # Setup dependency overrides for unit tests
    app.dependency_overrides[get_incident_repository] = lambda: InMemoryIncidentRepository()
    app.dependency_overrides[get_diagnostic_repository] = lambda: InMemoryDiagnosticRepository()
    app.dependency_overrides[get_finding_repository] = lambda: InMemoryFindingRepository()
    app.dependency_overrides[get_recommendation_repository] = lambda: InMemoryRecommendationRepository()
    app.dependency_overrides[get_repair_repository] = lambda: InMemoryRepairRequestRepository()
    app.dependency_overrides[get_audit_repository] = lambda: InMemoryAuditRepository()
    app.dependency_overrides[get_webhook_repository] = lambda: InMemoryWebhookDeliveryRepository()
    app.dependency_overrides[get_api_key_repository] = lambda: InMemoryApiKeyRepository()
    app.dependency_overrides[get_research_repository] = lambda: InMemoryResearchRepository()
    app.dependency_overrides[get_improvement_repository] = lambda: InMemoryImprovementRepository()
    app.dependency_overrides[get_pr_draft_repository] = lambda: InMemoryPrDraftRepository()
    app.dependency_overrides[get_pr_verification_repository] = lambda: InMemoryPrVerificationRepository()
    app.dependency_overrides[get_pr_review_feedback_repository] = lambda: InMemoryPrReviewFeedbackRepository()
    app.dependency_overrides[get_patch_revision_repository] = lambda: InMemoryPatchRevisionRepository()
    app.dependency_overrides[get_review_ledger_repository] = lambda: InMemoryReviewLedgerRepository()
    app.dependency_overrides[get_ai_patch_suggestion_repository] = lambda: InMemoryAIPatchSuggestionRepository()
    app.dependency_overrides[get_ai_patch_provider] = lambda: __import__(
        "apps.bilgeapi.adapters.ai_patch_provider",
        fromlist=["MockAIPatchProvider"]
    ).MockAIPatchProvider()
    app.dependency_overrides[get_review_ledger_service] = lambda: __import__(
        "apps.bilgeapi.services.review_ledger",
        fromlist=["ReviewLedgerService"]
    ).ReviewLedgerService(InMemoryReviewLedgerRepository())
    app.dependency_overrides[get_review_ledger_verifier] = lambda: __import__(
        "apps.bilgeapi.services.review_ledger",
        fromlist=["ReviewLedgerVerifier"]
    ).ReviewLedgerVerifier(InMemoryReviewLedgerRepository())
    
    with TestClient(app) as client:
        yield client
        
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def test_client_real_auth():
    from apps.bilgeapi.main import app
    from apps.bilgeapi.routers.deps import (
        get_incident_repository,
        get_diagnostic_repository,
        get_finding_repository,
        get_recommendation_repository,
        get_repair_repository,
        get_audit_repository,
        get_webhook_repository,
        get_api_key_repository,
        get_research_repository,
        get_improvement_repository,
        get_pr_draft_repository,
        get_pr_verification_repository,
        get_pr_review_feedback_repository,
        get_patch_revision_repository,
        get_review_ledger_repository,
        get_review_ledger_service,
        get_review_ledger_verifier,
        get_ai_patch_suggestion_repository,
        get_ai_patch_provider
    )
    from apps.bilgeapi.repositories.memory import (
        InMemoryIncidentRepository,
        InMemoryDiagnosticRepository,
        InMemoryFindingRepository,
        InMemoryRecommendationRepository,
        InMemoryRepairRequestRepository,
        InMemoryAuditRepository,
        InMemoryWebhookDeliveryRepository,
        InMemoryApiKeyRepository,
        InMemoryResearchRepository,
        InMemoryImprovementRepository,
        InMemoryPrDraftRepository,
        InMemoryPrVerificationRepository,
        InMemoryPrReviewFeedbackRepository,
        InMemoryPatchRevisionRepository,
        InMemoryReviewLedgerRepository,
        InMemoryAIPatchSuggestionRepository,
        memory_repositories
    )
    
    # Reset repositories
    memory_repositories.clear_all()
    
    app.dependency_overrides[get_incident_repository] = lambda: InMemoryIncidentRepository()
    app.dependency_overrides[get_diagnostic_repository] = lambda: InMemoryDiagnosticRepository()
    app.dependency_overrides[get_finding_repository] = lambda: InMemoryFindingRepository()
    app.dependency_overrides[get_recommendation_repository] = lambda: InMemoryRecommendationRepository()
    app.dependency_overrides[get_repair_repository] = lambda: InMemoryRepairRequestRepository()
    app.dependency_overrides[get_audit_repository] = lambda: InMemoryAuditRepository()
    app.dependency_overrides[get_webhook_repository] = lambda: InMemoryWebhookDeliveryRepository()
    app.dependency_overrides[get_api_key_repository] = lambda: InMemoryApiKeyRepository()
    app.dependency_overrides[get_research_repository] = lambda: InMemoryResearchRepository()
    app.dependency_overrides[get_improvement_repository] = lambda: InMemoryImprovementRepository()
    app.dependency_overrides[get_pr_draft_repository] = lambda: InMemoryPrDraftRepository()
    app.dependency_overrides[get_pr_verification_repository] = lambda: InMemoryPrVerificationRepository()
    app.dependency_overrides[get_pr_review_feedback_repository] = lambda: InMemoryPrReviewFeedbackRepository()
    app.dependency_overrides[get_patch_revision_repository] = lambda: InMemoryPatchRevisionRepository()
    app.dependency_overrides[get_review_ledger_repository] = lambda: InMemoryReviewLedgerRepository()
    app.dependency_overrides[get_ai_patch_suggestion_repository] = lambda: InMemoryAIPatchSuggestionRepository()
    app.dependency_overrides[get_ai_patch_provider] = lambda: __import__(
        "apps.bilgeapi.adapters.ai_patch_provider",
        fromlist=["MockAIPatchProvider"]
    ).MockAIPatchProvider()
    app.dependency_overrides[get_review_ledger_service] = lambda: __import__(
        "apps.bilgeapi.services.review_ledger",
        fromlist=["ReviewLedgerService"]
    ).ReviewLedgerService(InMemoryReviewLedgerRepository())
    app.dependency_overrides[get_review_ledger_verifier] = lambda: __import__(
        "apps.bilgeapi.services.review_ledger",
        fromlist=["ReviewLedgerVerifier"]
    ).ReviewLedgerVerifier(InMemoryReviewLedgerRepository())
    
    with TestClient(app) as client:
        yield client
        
    app.dependency_overrides.clear()
