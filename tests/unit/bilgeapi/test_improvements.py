import pytest
from datetime import datetime, timezone, timedelta
from fastapi import status

from apps.bilgeapi.services.research import SourceTrustScorer, WebResearchAdapter, MockSearchProvider
from apps.bilgeapi.services.improvement import ImprovementProposalEngine, ReleaseGateSimulator
from apps.bilgeapi.repositories.memory import InMemoryResearchRepository, InMemoryImprovementRepository


def test_source_trust_scorer():
    # 1. Official Docs Base: 95
    score_docs = SourceTrustScorer.calculate_score("https://docs.python.org/3/library/gc.html", source_type="official_docs")
    assert score_docs == 95.0

    # 2. GitHub Issue Base: 85
    score_github = SourceTrustScorer.calculate_score("https://github.com/fastapi/fastapi/issues/123")
    assert score_github == 85.0

    # 3. GitHub Comment / Maintainer comment: 80
    score_comment = SourceTrustScorer.calculate_score("https://github.com/fastapi/fastapi/issues/123#issuecomment-456")
    assert score_comment == 80.0

    # 4. StackOverflow Accepted: 70
    score_so_accepted = SourceTrustScorer.calculate_score("https://stackoverflow.com/questions/123#accepted")
    assert score_so_accepted == 70.0

    # 5. StackOverflow General: 60
    score_so = SourceTrustScorer.calculate_score("https://stackoverflow.com/questions/123")
    assert score_so == 60.0

    # 6. Blog/Medium: 35
    score_blog = SourceTrustScorer.calculate_score("https://medium.com/@dev/my-post")
    assert score_blog == 35.0

    # 7. Unknown Forum: 20
    score_forum = SourceTrustScorer.calculate_score("https://unknownforum.com/thread/1", source_type="unknown_forum")
    assert score_forum == 20.0

    # 8. Recency Adjustments
    # Age <= 1 year: +5
    score_recent = SourceTrustScorer.calculate_score("https://docs.python.org/3/library/gc.html", source_type="official_docs", recency_days=100)
    assert score_recent == 100.0

    # Age > 3 years: -10
    score_older = SourceTrustScorer.calculate_score("https://docs.python.org/3/library/gc.html", source_type="official_docs", recency_days=1200)
    assert score_older == 85.0

    # Age > 5 years: -20
    score_ancient = SourceTrustScorer.calculate_score("https://docs.python.org/3/library/gc.html", source_type="official_docs", recency_days=2000)
    assert score_ancient == 75.0

    # 9. Match Ratio adjustment (match_ratio * 10)
    score_match = SourceTrustScorer.calculate_score("https://docs.python.org/3/library/gc.html", source_type="official_docs", match_ratio=0.5)
    assert score_match == 100.0  # 95 + 5 = 100 (capped)

    score_match_low = SourceTrustScorer.calculate_score("https://medium.com/@dev/my-post", match_ratio=0.5)
    assert score_match_low == 40.0  # 35 + 5 = 40.0

    # 10. Vendor adjustment (+5)
    score_vendor = SourceTrustScorer.calculate_score("https://medium.com/@dev/my-post", is_vendor=True)
    assert score_vendor == 40.0  # 35 + 5 = 40.0


@pytest.mark.asyncio
async def test_web_research_adapter():
    repo = InMemoryResearchRepository()
    provider = MockSearchProvider()
    adapter = WebResearchAdapter(provider, repo)

    # Create a request
    req = await repo.create_request({
        "incident_id": "inc_123",
        "query": "memory leak",
        "tenant_id": "tenant_1"
    })

    assert req["status"] == "PENDING"

    # Run research
    evidences = await adapter.run_research(req["id"])

    assert len(evidences) > 0
    updated_req = await repo.get_request(req["id"])
    assert updated_req["status"] == "COMPLETED"

    # Verify evidences got trust score, summary, and hash
    for ev in evidences:
        assert ev["research_id"] == req["id"]
        assert ev["trust_score"] > 0
        assert ev["content_hash"] is not None
        assert ev["raw_content_summary"] is not None


@pytest.mark.asyncio
async def test_improvement_proposal_engine_and_simulator():
    research_repo = InMemoryResearchRepository()
    improvement_repo = InMemoryImprovementRepository()
    
    # Setup research request and evidences
    req = await research_repo.create_request({
        "incident_id": "inc_123",
        "query": "connection pool",
        "tenant_id": "tenant_1"
    })
    
    await research_repo.create_evidence({
        "research_id": req["id"],
        "source_url": "https://docs.sqlalchemy.org/en/20/core/pooling.html",
        "source_domain": "docs.sqlalchemy.org",
        "title": "Connection Pooling",
        "snippet": "SQLAlchemy connection pooling reference.",
        "content_hash": "hash123",
        "trust_score": 95.0
    })

    # Generate proposal
    engine = ImprovementProposalEngine(research_repo, improvement_repo)
    proposal = await engine.generate_proposal(req["id"])

    # Initial states
    assert proposal["research_id"] == req["id"]
    assert proposal["gate_status"] == "DRAFT"
    assert proposal["approval_status"] == "REVIEW_REQUIRED"
    assert proposal["ready_for_human_apply"] is False
    assert proposal["patch_code"] is not None
    assert proposal["risk_analysis"] is not None

    # Run gate simulation
    simulator = ReleaseGateSimulator(improvement_repo)
    report = await simulator.run_simulation(proposal["id"])

    # Verify state updated after simulation
    updated_prop = await improvement_repo.get_proposal(proposal["id"])
    assert updated_prop["gate_status"] == "GATE_PASSED"
    assert updated_prop["gate_score"] == 98.0
    assert "affected_files" in report

    # Approve proposal
    approved = await improvement_repo.approve_proposal(
        proposal_id=proposal["id"],
        approved_by="admin_user",
        approved_at=datetime.now(timezone.utc)
    )

    assert approved["approval_status"] == "APPROVED"
    assert approved["approved_by"] == "admin_user"
    assert approved["ready_for_human_apply"] is True


def test_improvements_endpoints(test_client):
    # 1. Start research via endpoint
    response = test_client.post("/v1/improvements/research", json={
        "incident_id": "inc_123",
        "query": "memory leak"
    })
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["status"] == "COMPLETED"
    research_id = data["id"]

    # 2. Get research details
    resp_get = test_client.get(f"/v1/improvements/research/{research_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == research_id

    # 3. List evidences
    resp_ev = test_client.get(f"/v1/improvements/research/{research_id}/evidences")
    assert resp_ev.status_code == 200
    evidences = resp_ev.json()
    assert len(evidences) > 0

    # 4. Generate proposal
    resp_prop = test_client.post(f"/v1/improvements/{research_id}/proposal")
    assert resp_prop.status_code == status.HTTP_201_CREATED
    prop = resp_prop.json()
    assert prop["approval_status"] == "REVIEW_REQUIRED"
    proposal_id = prop["id"]

    # 5. Generate draft PR
    resp_pr = test_client.post(f"/v1/improvements/{proposal_id}/draft-pr")
    assert resp_pr.status_code == 200
    pr_data = resp_pr.json()
    assert "patch_code" in pr_data
    assert pr_data["risk_level"] == "LOW"

    # 6. Run gate simulation
    resp_gate = test_client.post(f"/v1/improvements/{proposal_id}/run-gate")
    assert resp_gate.status_code == 200
    gate_data = resp_gate.json()
    assert gate_data["release_readiness_audit"]["status"] == "PASSED"

    # 7. Approve proposal (note: auth is disabled in conftest for test_client)
    resp_appr = test_client.post(f"/v1/improvements/{proposal_id}/approve")
    assert resp_appr.status_code == 200
    appr_data = resp_appr.json()
    assert appr_data["approval_status"] == "APPROVED"
    assert appr_data["ready_for_human_apply"] is True


def test_research_quota_limit(test_client):
    # Test client allows rate limits to be cleared or mocked.
    # In test_client, auth is disabled, so tenant_id defaults to "default_tenant".
    # Let's request research 5 times.
    for _ in range(5):
        resp = test_client.post("/v1/improvements/research", json={
            "incident_id": "inc_abc",
            "query": "something to research"
        })
        assert resp.status_code == status.HTTP_201_CREATED

    # The 6th request must fail with 429 Too Many Requests
    resp_fail = test_client.post("/v1/improvements/research", json={
        "incident_id": "inc_abc",
        "query": "something to research"
    })
    assert resp_fail.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "quota exceeded" in resp_fail.json()["detail"].lower()
