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
    os.environ["BILGEAPI_DURABLE_QUEUE_ENABLED"] = "false"
    os.environ["BILGEAPI_MANAGEMENT_ACTIONS_UNLOCKED"] = "true"
    yield
    # Cancel and clear pending background tasks, clear state, and dispose DB connections
    try:
        import asyncio
        from bilgeapi.services.webhook import background_tasks as webhook_tasks
        from bilgeapi.services.diagnostic import background_tasks as diag_tasks
        from bilgeapi.libs.db.session import close_db
        from bilgeapi.main import app
        
        # Clear FastAPI dependency overrides and state
        try:
            app.dependency_overrides.clear()
            app.state._state.clear()
        except Exception:
            pass
            
        all_tasks = list(webhook_tasks) + list(diag_tasks)
        for task in all_tasks:
            if not task.done():
                task.cancel()
        webhook_tasks.clear()
        diag_tasks.clear()
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop is not None and loop.is_running():
            async def run_async_cleanup():
                if all_tasks:
                    await asyncio.gather(*all_tasks, return_exceptions=True)
                await close_db()
            loop.create_task(run_async_cleanup())
        else:
            new_loop = asyncio.new_event_loop()
            try:
                if all_tasks:
                    new_loop.run_until_complete(asyncio.gather(*all_tasks, return_exceptions=True))
                new_loop.run_until_complete(close_db())
            finally:
                new_loop.close()
    except Exception:
        pass

    # Cleanup environment variables
    if "BILGEAPI_AUTH_MODE" in os.environ:
        del os.environ["BILGEAPI_AUTH_MODE"]
    if "BILGEAPI_STATIC_KEYS" in os.environ:
        del os.environ["BILGEAPI_STATIC_KEYS"]
    if "BILGEAPI_PORT" in os.environ:
        del os.environ["BILGEAPI_PORT"]
    if "BILGEAPI_RATE_LIMIT_RPS" in os.environ:
        del os.environ["BILGEAPI_RATE_LIMIT_RPS"]
    if "BILGEAPI_DURABLE_QUEUE_ENABLED" in os.environ:
        del os.environ["BILGEAPI_DURABLE_QUEUE_ENABLED"]
    if "BILGEAPI_MANAGEMENT_ACTIONS_UNLOCKED" in os.environ:
        del os.environ["BILGEAPI_MANAGEMENT_ACTIONS_UNLOCKED"]

@pytest.fixture
def test_client():
    from bilgeapi.main import app
    from bilgeapi.routers.deps import (
        get_incident_repository,
        get_diagnostic_repository,
        get_finding_repository,
        get_recommendation_repository,
        get_repair_repository,
        get_audit_repository,
        get_webhook_repository,
        get_release_repository,
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
        get_ai_patch_provider,
        get_system_finding_repository,
        get_remediation_runbook_repository,
        get_remediation_attempt_repository,
        get_autonomy_decision_repository
    )
    from bilgeapi.repositories.memory import (
        InMemoryIncidentRepository,
        InMemoryDiagnosticRepository,
        InMemoryFindingRepository,
        InMemoryRecommendationRepository,
        InMemoryRepairRequestRepository,
        InMemoryAuditRepository,
        InMemoryWebhookDeliveryRepository,
        InMemoryReleaseCheckRepository,
        InMemoryApiKeyRepository,
        InMemoryResearchRepository,
        InMemoryImprovementRepository,
        InMemoryPrDraftRepository,
        InMemoryPrVerificationRepository,
        InMemoryPrReviewFeedbackRepository,
        InMemoryPatchRevisionRepository,
        InMemoryReviewLedgerRepository,
        InMemoryAIPatchSuggestionRepository,
        InMemorySystemFindingRepository,
        InMemoryRemediationRunbookRepository,
        InMemoryRemediationAttemptRepository,
        InMemoryAutonomyDecisionRepository,
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
    app.dependency_overrides[get_release_repository] = lambda: InMemoryReleaseCheckRepository()
    app.dependency_overrides[get_api_key_repository] = lambda: InMemoryApiKeyRepository()
    app.dependency_overrides[get_research_repository] = lambda: InMemoryResearchRepository()
    app.dependency_overrides[get_improvement_repository] = lambda: InMemoryImprovementRepository()
    app.dependency_overrides[get_pr_draft_repository] = lambda: InMemoryPrDraftRepository()
    app.dependency_overrides[get_pr_verification_repository] = lambda: InMemoryPrVerificationRepository()
    app.dependency_overrides[get_pr_review_feedback_repository] = lambda: InMemoryPrReviewFeedbackRepository()
    app.dependency_overrides[get_patch_revision_repository] = lambda: InMemoryPatchRevisionRepository()
    app.dependency_overrides[get_review_ledger_repository] = lambda: InMemoryReviewLedgerRepository()
    app.dependency_overrides[get_ai_patch_suggestion_repository] = lambda: InMemoryAIPatchSuggestionRepository()
    app.dependency_overrides[get_system_finding_repository] = lambda: InMemorySystemFindingRepository()
    app.dependency_overrides[get_remediation_runbook_repository] = lambda: InMemoryRemediationRunbookRepository()
    app.dependency_overrides[get_remediation_attempt_repository] = lambda: InMemoryRemediationAttemptRepository()
    app.dependency_overrides[get_autonomy_decision_repository] = lambda: InMemoryAutonomyDecisionRepository()
    app.dependency_overrides[get_ai_patch_provider] = lambda: __import__(
        "bilgeapi.adapters.ai_patch_provider",
        fromlist=["MockAIPatchProvider"]
    ).MockAIPatchProvider()
    app.dependency_overrides[get_review_ledger_service] = lambda: __import__(
        "bilgeapi.services.review_ledger",
        fromlist=["ReviewLedgerService"]
    ).ReviewLedgerService(InMemoryReviewLedgerRepository())
    app.dependency_overrides[get_review_ledger_verifier] = lambda: __import__(
        "bilgeapi.services.review_ledger",
        fromlist=["ReviewLedgerVerifier"]
    ).ReviewLedgerVerifier(InMemoryReviewLedgerRepository())
    
    with TestClient(app) as client:
        yield client
        
    # Clear overrides after test
    app.dependency_overrides.clear()


@pytest.fixture
def test_client_real_auth():
    from bilgeapi.main import app
    from bilgeapi.routers.deps import (
        get_incident_repository,
        get_diagnostic_repository,
        get_finding_repository,
        get_recommendation_repository,
        get_repair_repository,
        get_audit_repository,
        get_webhook_repository,
        get_release_repository,
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
        get_ai_patch_provider,
        get_system_finding_repository,
        get_remediation_runbook_repository,
        get_remediation_attempt_repository,
        get_autonomy_decision_repository
    )
    from bilgeapi.repositories.memory import (
        InMemoryIncidentRepository,
        InMemoryDiagnosticRepository,
        InMemoryFindingRepository,
        InMemoryRecommendationRepository,
        InMemoryRepairRequestRepository,
        InMemoryAuditRepository,
        InMemoryWebhookDeliveryRepository,
        InMemoryReleaseCheckRepository,
        InMemoryApiKeyRepository,
        InMemoryResearchRepository,
        InMemoryImprovementRepository,
        InMemoryPrDraftRepository,
        InMemoryPrVerificationRepository,
        InMemoryPrReviewFeedbackRepository,
        InMemoryPatchRevisionRepository,
        InMemoryReviewLedgerRepository,
        InMemoryAIPatchSuggestionRepository,
        InMemorySystemFindingRepository,
        InMemoryRemediationRunbookRepository,
        InMemoryRemediationAttemptRepository,
        InMemoryAutonomyDecisionRepository,
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
    app.dependency_overrides[get_release_repository] = lambda: InMemoryReleaseCheckRepository()
    app.dependency_overrides[get_api_key_repository] = lambda: InMemoryApiKeyRepository()
    app.dependency_overrides[get_research_repository] = lambda: InMemoryResearchRepository()
    app.dependency_overrides[get_improvement_repository] = lambda: InMemoryImprovementRepository()
    app.dependency_overrides[get_pr_draft_repository] = lambda: InMemoryPrDraftRepository()
    app.dependency_overrides[get_pr_verification_repository] = lambda: InMemoryPrVerificationRepository()
    app.dependency_overrides[get_pr_review_feedback_repository] = lambda: InMemoryPrReviewFeedbackRepository()
    app.dependency_overrides[get_patch_revision_repository] = lambda: InMemoryPatchRevisionRepository()
    app.dependency_overrides[get_review_ledger_repository] = lambda: InMemoryReviewLedgerRepository()
    app.dependency_overrides[get_ai_patch_suggestion_repository] = lambda: InMemoryAIPatchSuggestionRepository()
    app.dependency_overrides[get_system_finding_repository] = lambda: InMemorySystemFindingRepository()
    app.dependency_overrides[get_remediation_runbook_repository] = lambda: InMemoryRemediationRunbookRepository()
    app.dependency_overrides[get_remediation_attempt_repository] = lambda: InMemoryRemediationAttemptRepository()
    app.dependency_overrides[get_autonomy_decision_repository] = lambda: InMemoryAutonomyDecisionRepository()
    app.dependency_overrides[get_ai_patch_provider] = lambda: __import__(
        "bilgeapi.adapters.ai_patch_provider",
        fromlist=["MockAIPatchProvider"]
    ).MockAIPatchProvider()
    app.dependency_overrides[get_review_ledger_service] = lambda: __import__(
        "bilgeapi.services.review_ledger",
        fromlist=["ReviewLedgerService"]
    ).ReviewLedgerService(InMemoryReviewLedgerRepository())
    app.dependency_overrides[get_review_ledger_verifier] = lambda: __import__(
        "bilgeapi.services.review_ledger",
        fromlist=["ReviewLedgerVerifier"]
    ).ReviewLedgerVerifier(InMemoryReviewLedgerRepository())
    
    with TestClient(app) as client:
        yield client
        
    app.dependency_overrides.clear()
