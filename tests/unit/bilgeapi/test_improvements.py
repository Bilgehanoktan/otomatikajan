import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from fastapi import status

from apps.bilgeapi.services.research import SourceTrustScorer, WebResearchAdapter, MockSearchProvider, SerperSearchProvider
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
async def test_serper_search_provider():
    # Test date parsing first
    provider = SerperSearchProvider()
    assert provider._parse_date_string("3 days ago") is not None
    assert provider._parse_date_string("2 weeks ago") is not None
    assert provider._parse_date_string("1 month ago") is not None
    assert provider._parse_date_string("2 years ago") is not None
    assert provider._parse_date_string("Jan 15, 2024") is not None

    # Test HTTP request mocking
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "organic": [
            {
                "title": "Python Garbage Collection",
                "link": "https://docs.python.org/3/library/gc.html",
                "snippet": "Provides controls for python garbage collection.",
                "date": "Jan 15, 2024"
            },
            {
                "title": "Uncollectable objects in Python",
                "link": "https://github.com/python/cpython/issues/123",
                "snippet": "CPython issues regarding uncollectable garbage objects.",
                "date": "3 days ago"
            }
        ]
    }

    with patch.dict("os.environ", {"BILGEAPI_SERPER_API_KEY": "test-api-key"}):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            results = await provider.search("python memory leak", max_results=2)
            assert len(results) == 2
            assert results[0]["title"] == "Python Garbage Collection"
            assert results[0]["source_type"] == "official_docs"
            assert results[1]["source_type"] == "maintainer_comment"



@pytest.mark.asyncio
async def test_evidence_quality_gates():
    research_repo = InMemoryResearchRepository()
    improvement_repo = InMemoryImprovementRepository()
    engine = ImprovementProposalEngine(research_repo, improvement_repo)

    req = await research_repo.create_request({
        "incident_id": "inc_qg",
        "query": "low evidence query",
        "tenant_id": "tenant_1"
    })

    # Test 1: Raise ValueError if less than 3 evidences exist
    with pytest.raises(ValueError) as exc:
        await engine.generate_proposal(req["id"])
    assert "No research evidences found" in str(exc.value)

    # Add 2 reliable evidences (trust_score >= 50) and 1 unreliable evidence (trust_score = 20)
    await research_repo.create_evidence({
        "research_id": req["id"],
        "source_url": "https://docs.python.org/3/library/gc.html",
        "source_domain": "docs.python.org",
        "title": "Doc 1",
        "snippet": "snippet 1",
        "content_hash": "hash1",
        "trust_score": 95.0
    })
    await research_repo.create_evidence({
        "research_id": req["id"],
        "source_url": "https://github.com/fastapi/fastapi/issues/123",
        "source_domain": "github.com",
        "title": "Doc 2",
        "snippet": "snippet 2",
        "content_hash": "hash2",
        "trust_score": 85.0
    })
    await research_repo.create_evidence({
        "research_id": req["id"],
        "source_url": "https://unknownforum.com/thread/1",
        "source_domain": "unknownforum.com",
        "title": "Doc 3",
        "snippet": "snippet 3",
        "content_hash": "hash3",
        "trust_score": 20.0  # unreliable
    })

    # Should raise ValueError because only 2 reliable evidences exist
    with pytest.raises(ValueError) as exc:
        await engine.generate_proposal(req["id"])
    assert "Quality gate check failed" in str(exc.value)


@pytest.mark.asyncio
async def test_proposal_confidence_scoring():
    research_repo = InMemoryResearchRepository()
    improvement_repo = InMemoryImprovementRepository()
    engine = ImprovementProposalEngine(research_repo, improvement_repo)

    # Case 1: Proposal with official doc -> High confidence (score >= 85)
    req_high = await research_repo.create_request({
        "incident_id": "inc_high",
        "query": "gc memory",
        "tenant_id": "tenant_1"
    })
    for i in range(3):
        await research_repo.create_evidence({
            "research_id": req_high["id"],
            "source_url": f"https://docs.python.org/3/{i}",
            "source_domain": "docs.python.org",
            "title": "gc memory management docs",
            "snippet": "gc memory leaks and cycle references management",
            "content_hash": f"hash_high_{i}",
            "trust_score": 95.0
        })
    
    proposal_high = await engine.generate_proposal(req_high["id"])
    assert proposal_high["risk_analysis"]["confidence_level"] == "HIGH"
    assert proposal_high["risk_analysis"]["confidence_score"] >= 85.0
    assert proposal_high["approval_status"] == "REVIEW_REQUIRED"

    # Case 2: Proposal without official docs -> Clamped to MEDIUM (score < 85)
    req_med = await research_repo.create_request({
        "incident_id": "inc_med",
        "query": "some blogs",
        "tenant_id": "tenant_1"
    })
    for i in range(3):
        await research_repo.create_evidence({
            "research_id": req_med["id"],
            "source_url": f"https://medium.com/blog/{i}",
            "source_domain": "medium.com",
            "title": "some blogs about coding",
            "snippet": "blogs talk about coding best practices",
            "content_hash": f"hash_med_{i}",
            "trust_score": 80.0 # reliable but not official doc (which requires trust_score >= 90)
        })

    proposal_med = await engine.generate_proposal(req_med["id"])
    assert proposal_med["risk_analysis"]["confidence_level"] == "MEDIUM"
    assert proposal_med["risk_analysis"]["confidence_score"] < 85.0


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

    # 3. Generate proposal
    resp_prop = test_client.post(f"/v1/improvements/{research_id}/proposal")
    assert resp_prop.status_code == status.HTTP_201_CREATED
    prop = resp_prop.json()
    assert prop["approval_status"] == "REVIEW_REQUIRED"
    proposal_id = prop["id"]

    # 4. Get audit report (Markdown response)
    resp_audit = test_client.get(f"/v1/improvements/proposals/{proposal_id}/audit-report")
    assert resp_audit.status_code == 200
    assert resp_audit.headers["content-type"].startswith("text/markdown")
    assert "# Self-Improvement Audit Report" in resp_audit.text

    # 5. Generate draft PR
    resp_pr = test_client.post(f"/v1/improvements/{proposal_id}/draft-pr")
    assert resp_pr.status_code == 200
    pr_data = resp_pr.json()
    assert "patch_code" in pr_data
    assert "Problem Özeti" in pr_data["description"]
    assert "Rollback Planı" in pr_data["description"]

    # 6. Run gate simulation
    resp_gate = test_client.post(f"/v1/improvements/{proposal_id}/run-gate")
    assert resp_gate.status_code == 200
    gate_data = resp_gate.json()
    assert gate_data["release_readiness_audit"]["status"] == "PASSED"

    # 7. Approve proposal
    resp_appr = test_client.post(f"/v1/improvements/{proposal_id}/approve")
    assert resp_appr.status_code == 200
    appr_data = resp_appr.json()
    assert appr_data["approval_status"] == "APPROVED"
    assert appr_data["ready_for_human_apply"] is True


def test_research_quota_limit(test_client):
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


@pytest.mark.asyncio
async def test_low_confidence_blocking():
    # Setup a low confidence request
    research_repo = InMemoryResearchRepository()
    improvement_repo = InMemoryImprovementRepository()
    engine = ImprovementProposalEngine(research_repo, improvement_repo)

    req = await research_repo.create_request({
        "incident_id": "inc_low",
        "query": "low quality query",
        "tenant_id": "tenant_1"
    })

    # Add 3 reliable evidences but with low trust score (exactly 50) and low match ratio
    for i in range(3):
        await research_repo.create_evidence({
            "research_id": req["id"],
            "source_url": f"https://medium.com/blog/{i}",
            "source_domain": "medium.com",
            "title": f"Irrelevant Title {i}",
            "snippet": f"Irrelevant snippet {i}",
            "content_hash": f"hash_low_{i}",
            "trust_score": 50.0  # exact limit
        })

    proposal = await engine.generate_proposal(req["id"])
    assert proposal["risk_analysis"]["confidence_level"] == "LOW"
    assert proposal["approval_status"] == "REJECTED"


def test_endpoints_block_low_confidence(test_client):
    # We will trigger proposal generation via MockSearchProvider using low-confidence mock data
    # Create request
    resp_req = test_client.post("/v1/improvements/research", json={
        "incident_id": "inc_endpoint_low",
        "query": "low quality query"
    })
    research_id = resp_req.json()["id"]

    # Manually delete other evidences and create 3 low quality evidences (trust_score=50, irrelevant text)
    # But wait, endpoint tests run in TestClient which uses InMemoryResearchRepository.
    # In TestClient, auth is bypassed, and dependencies are overridden.
    # To test low confidence blocking in the API endpoints, we can manually inject low confidence evidences
    # using test client db repositories or simply test that if approval_status is REJECTED, approve endpoint throws 400.
    
    # Let's mock the ImprovementRepository.get_proposal to return a LOW confidence proposal
    # or just use the API flow to generate a LOW confidence proposal.
    # Actually, we can use the MockSearchProvider custom_results parameter to override results!
    # Wait, get_web_search_provider returns the provider. In test_client, we can override the dependency get_web_search_provider!
    # Yes! Let's override it in the app:
    from apps.bilgeapi.main import app
    from apps.bilgeapi.routers.deps import get_web_search_provider
    
    low_quality_provider = MockSearchProvider(custom_results=[
        {
            "url": f"https://blog.com/{i}",
            "title": "irrelevant info",
            "snippet": "unrelated snippet text",
            "content": "unrelated content",
            "source_type": "unknown_forum",
            "published_at": datetime.now(timezone.utc) - timedelta(days=2000), # old
            "is_vendor": False
        } for i in range(3)
    ])
    
    app.dependency_overrides[get_web_search_provider] = lambda: low_quality_provider
    try:
        # Create research (uses low_quality_provider)
        resp = test_client.post("/v1/improvements/research", json={
            "incident_id": "inc_low_end",
            "query": "irrelevant search query"
        })
        res_id = resp.json()["id"]

        # Generate proposal -> trust score should be around 20 for unknown forum, but wait,
        # we need at least 3 evidences with trust_score >= 50.
        # Let's adjust mock custom_results to have trust_score = 50 (e.g. blog_medium with date = now)
        low_quality_provider.custom_results = [
            {
                "url": f"https://medium.com/blog/{i}",
                "title": "unrelated",
                "snippet": "unrelated",
                "content": "unrelated",
                "source_type": "blog_medium",
                "published_at": datetime.now(timezone.utc), # recent -> +5
                "is_vendor": False
            } for i in range(3)
        ]
        # Blog/Medium base is 35. With recency <= 365, score is 40. Still < 50!
        # If we make is_vendor=True -> base 35 + recency 5 + vendor 5 = 45. Still < 50!
        # Let's make it stackoverflow but without accepted -> base 60. Recency <= 365 -> +5. Score 65.0. Match ratio 0 -> Score 65.
        # This will pass quality gate (> 50) but confidence score will be: (65 * 0.6) = 39.0.
        # (39.0 + 0 + 0) = 39.0 which is < 60 -> LOW confidence!
        low_quality_provider.custom_results = [
            {
                "url": f"https://stackoverflow.com/questions/{i}",
                "title": "unrelated",
                "snippet": "unrelated",
                "content": "unrelated",
                "source_type": "accepted_answer", # Wait, accepted_answer has base 70. Let's make it base 60 by using standard stackoverflow:
                "published_at": datetime.now(timezone.utc) - timedelta(days=2000), # old -> -20 -> 40.0.
                "is_vendor": False
            } for i in range(3)
        ]
        # Wait, if trust score is 40, it fails quality gate.
        # Let's make trust score exactly 50: e.g. base 60 (stackoverflow), old -> -10 (1200 days ago) -> trust score 50.
        low_quality_provider.custom_results = [
            {
                "url": f"https://stackoverflow.com/questions/{i}",
                "title": "unrelated",
                "snippet": "unrelated",
                "content": "unrelated",
                "published_at": datetime.now(timezone.utc) - timedelta(days=1200),
                "is_vendor": False
            } for i in range(3)
        ]

        # Trigger research
        resp_res = test_client.post("/v1/improvements/research", json={
            "incident_id": "inc_low_end",
            "query": "totally unrelated query"
        })
        research_id = resp_res.json()["id"]

        # Generate proposal -> should be LOW confidence and REJECTED status
        resp_proposal = test_client.post(f"/v1/improvements/{research_id}/proposal")
        assert resp_proposal.status_code == status.HTTP_201_CREATED
        prop_id = resp_proposal.json()["id"]
        assert resp_proposal.json()["approval_status"] == "REJECTED"
        assert resp_proposal.json()["risk_analysis"]["confidence_level"] == "LOW"

        # Try to approve -> should fail with 400 Bad Request
        resp_approve = test_client.post(f"/v1/improvements/{prop_id}/approve")
        assert resp_approve.status_code == status.HTTP_400_BAD_REQUEST
        assert "low-confidence proposals cannot be approved" in resp_approve.json()["detail"].lower()

    finally:
        # Clear dependency override
        app.dependency_overrides.pop(get_web_search_provider, None)
