from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.social_growth.growth_plan import AccountGrowthPlanBuilder
from services.social_growth.growth_router import build_growth_plan_router

TEST_API_KEY = "growth-plan-api-key-value-at-least-32-characters"


def test_account_growth_plan_has_twelve_weeks_and_exact_content_allocation() -> None:
    plan = AccountGrowthPlanBuilder().build("@ai_gucum_")

    assert plan.duration_days == 90
    assert len(plan.weeks) == 12
    assert sum(week.main_posts for week in plan.weeks) == 36
    assert all(week.reels == 2 and week.carousels == 1 for week in plan.weeks)
    assert all((week.story_days_min, week.story_days_max) == (4, 6) for week in plan.weeks)
    assert plan.content_allocation == {
        "current_ai": 11,
        "applied_workflow": 11,
        "comparison": 7,
        "behind_the_scenes": 4,
        "safety_myth": 3,
    }
    assert plan.measurement_checkpoints_hours == (24, 72, 168)


def test_growth_plan_uses_baseline_decisions_without_follower_guarantees() -> None:
    plan = AccountGrowthPlanBuilder().build("ai_gucum_")
    payload = plan.to_dict()

    assert payload["handle"] == "@ai_gucum_"
    assert plan.baseline_rule == "first_four_quality_posts_median"
    assert plan.guaranteed_follower_target is None
    assert [phase.week_range for phase in plan.phases] == ["1-2", "3-6", "7-10", "11-12"]
    assert "provider_metrics_only" in plan.decision_rules
    assert "human_approval_before_publish" in plan.stop_the_line_rules


def test_growth_plan_router_is_authenticated_and_returns_dry_run_plan() -> None:
    app = FastAPI()
    app.include_router(
        build_growth_plan_router(AccountGrowthPlanBuilder(), api_key=TEST_API_KEY),
        prefix="/api/v1/social-growth",
    )
    client = TestClient(app)

    unauthorized = client.post(
        "/api/v1/social-growth/account-growth/plans",
        json={"handle": "@ai_gucum_"},
    )
    response = client.post(
        "/api/v1/social-growth/account-growth/plans",
        json={"handle": "@ai_gucum_"},
        headers={"X-Content-Orchestrator-Key": TEST_API_KEY},
    )

    assert unauthorized.status_code == 401
    assert response.status_code == 201
    assert response.json()["status"] == "DRY_RUN"
    assert len(response.json()["weeks"]) == 12
    assert response.json()["external_actions_performed"] is False
