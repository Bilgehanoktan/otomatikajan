"""Deterministic, metric-led 90-day Instagram account growth plan."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

from services.social_growth.contracts import OperationEvidence, OperationStatus

_HANDLE_PATTERN = re.compile(r"^@?[A-Za-z0-9._]{1,30}$")


class GrowthEvidenceSink(Protocol):
    def record(self, evidence: OperationEvidence) -> None:
        """Persist a governed account-plan record."""


@dataclass(frozen=True)
class GrowthPhase:
    week_range: str
    objective: str
    exit_evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "week_range": self.week_range,
            "objective": self.objective,
            "exit_evidence": list(self.exit_evidence),
        }


@dataclass(frozen=True)
class GrowthWeek:
    week: int
    focus: str
    experiment: str
    main_posts: int = 3
    reels: int = 2
    carousels: int = 1
    story_days_min: int = 4
    story_days_max: int = 6

    def to_dict(self) -> dict[str, Any]:
        return {
            "week": self.week,
            "focus": self.focus,
            "experiment": self.experiment,
            "main_posts": self.main_posts,
            "reels": self.reels,
            "carousels": self.carousels,
            "story_days_min": self.story_days_min,
            "story_days_max": self.story_days_max,
        }


@dataclass(frozen=True)
class AccountGrowthPlan:
    plan_id: str
    handle: str
    phases: tuple[GrowthPhase, ...]
    weeks: tuple[GrowthWeek, ...]
    content_allocation: dict[str, int]
    metrics: tuple[str, ...]
    measurement_checkpoints_hours: tuple[int, ...]
    baseline_rule: str
    decision_rules: tuple[str, ...]
    stop_the_line_rules: tuple[str, ...]
    duration_days: int = 90
    guaranteed_follower_target: int | None = None
    status: str = "DRY_RUN"
    external_actions_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "handle": self.handle,
            "duration_days": self.duration_days,
            "status": self.status,
            "external_actions_performed": self.external_actions_performed,
            "phases": [phase.to_dict() for phase in self.phases],
            "weeks": [week.to_dict() for week in self.weeks],
            "content_allocation": dict(self.content_allocation),
            "metrics": list(self.metrics),
            "measurement_checkpoints_hours": list(self.measurement_checkpoints_hours),
            "baseline_rule": self.baseline_rule,
            "decision_rules": list(self.decision_rules),
            "stop_the_line_rules": list(self.stop_the_line_rules),
            "guaranteed_follower_target": self.guaranteed_follower_target,
        }


class AccountGrowthPlanBuilder:
    """Build a fixed-cadence plan whose decisions depend only on provider metrics."""

    def __init__(self, *, evidence_sink: GrowthEvidenceSink | None = None) -> None:
        self._evidence_sink = evidence_sink

    def build(self, handle: str) -> AccountGrowthPlan:
        normalized_handle = _normalize_handle(handle)
        weeks = tuple(
            GrowthWeek(week=index + 1, focus=focus, experiment=experiment)
            for index, (focus, experiment) in enumerate(_WEEK_BLUEPRINT)
        )
        plan = AccountGrowthPlan(
            plan_id=_build_plan_id(normalized_handle),
            handle=normalized_handle,
            phases=_PHASES,
            weeks=weeks,
            content_allocation={
                "current_ai": 11,
                "applied_workflow": 11,
                "comparison": 7,
                "behind_the_scenes": 4,
                "safety_myth": 3,
            },
            metrics=(
                "three_second_hold_rate",
                "completion_rate",
                "saves_per_reach",
                "shares_per_reach",
                "follows_per_profile_visit",
                "keyword_dm_conversion_rate",
            ),
            measurement_checkpoints_hours=(24, 72, 168),
            baseline_rule="first_four_quality_posts_median",
            decision_rules=(
                "provider_metrics_only",
                "compare_like_format_and_topic_strength",
                "scale_only_repeated_winners",
                "no_follower_guarantee",
            ),
            stop_the_line_rules=(
                "human_approval_before_publish",
                "official_source_required_for_verifiable_claim",
                "visual_text_gate_must_pass",
                "no_unverified_price_or_income_claim",
                "no_topic_repeat_inside_seven_days_without_new_evidence",
            ),
        )
        self._record(plan)
        return plan

    def _record(self, plan: AccountGrowthPlan) -> None:
        if self._evidence_sink is None:
            return
        self._evidence_sink.record(
            OperationEvidence(
                operation="account_growth_plan",
                status=OperationStatus.DRY_RUN,
                reason="90 günlük plan üretildi; canlı yayın veya takipçi garantisi yok",
                metadata={
                    "plan_id": plan.plan_id,
                    "handle": plan.handle,
                    "weeks": len(plan.weeks),
                    "main_posts": sum(week.main_posts for week in plan.weeks),
                    "external_actions_performed": False,
                    "tool_used": "AccountGrowthPlanBuilder",
                },
            )
        )


_PHASES = (
    GrowthPhase(
        "1-2",
        "profile_and_baseline",
        ("profile_quality_gate", "first_four_quality_posts_median"),
    ),
    GrowthPhase(
        "3-6",
        "hook_format_and_time_experiments",
        ("winning_hook_pattern", "winning_publish_window"),
    ),
    GrowthPhase(
        "7-10",
        "lead_magnet_and_dm_conversion",
        ("configured_dm_asset", "keyword_dm_conversion_rate"),
    ),
    GrowthPhase(
        "11-12",
        "scale_repeated_winners",
        ("two_repeated_winners", "next_quarter_backlog"),
    ),
)

_WEEK_BLUEPRINT = (
    ("profile_repair", "profile_visit_to_follow_baseline"),
    ("quality_baseline", "first_four_quality_posts"),
    ("proof_hooks", "result_first_vs_problem_first"),
    ("saveable_carousels", "checklist_vs_comparison"),
    ("demo_reels", "screen_recording_vs_generated_broll"),
    ("publish_window", "12_30_vs_20_30_europe_istanbul"),
    ("lead_magnet", "save_share_vs_keyword_dm"),
    ("dm_fulfilment", "asset_open_rate_and_reply_intent"),
    ("authority", "case_study_vs_news_explanation"),
    ("community_signal", "poll_question_vs_open_question"),
    ("winner_repeat", "repeat_winner_with_new_evidence"),
    ("quarter_review", "provider_metrics_only_backlog_decision"),
)


def _normalize_handle(handle: str) -> str:
    value = handle.strip()
    if not _HANDLE_PATTERN.fullmatch(value):
        raise ValueError("Instagram handle geçersiz")
    return value if value.startswith("@") else f"@{value}"


def _build_plan_id(handle: str) -> str:
    canonical = json.dumps({"handle": handle, "days": 90}, sort_keys=True)
    digest = hashlib.sha256(canonical.encode()).hexdigest()[:16]
    return f"growth-{digest}"
