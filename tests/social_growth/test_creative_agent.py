from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from services.social_growth.content_orchestrator import (
    Claim,
    ContentBrief,
    ContentFormat,
    ContentMode,
    ContentOrchestrator,
    ContentTemplate,
    CTAMode,
    VideoProvider,
)
from services.social_growth.creative_planner import (
    CreativeDraft,
    CreativePlanningError,
    CreativeProductionAgent,
    OpenAICreativePlanner,
    UngroundedCreativeDraftError,
)
from services.social_growth.video_providers import (
    HumanApproval,
    ProviderExecutionRegistry,
    VideoJob,
    VideoJobStatus,
)


def make_brief() -> ContentBrief:
    return ContentBrief(
        topic="Veo ile dikey kısa video üretimi",
        audience="Türkçe konuşan freelancerlar",
        mode=ContentMode.LEAD,
        format=ContentFormat.REEL,
        template=ContentTemplate.ONE_PROMPT_DEMO,
        cta_mode=CTAMode.KEYWORD_DM,
        keyword="VIDEO",
        claims=(
            Claim(
                text="Veo 9:16 video üretebilir.",
                source_urls=("https://ai.google.dev/gemini-api/docs/veo",),
            ),
        ),
    )


def make_draft(*, source_urls: list[str] | None = None) -> CreativeDraft:
    return CreativeDraft(
        hook="Tek promptla dikey bir ürün demosu ürettim.",
        script_beats=["Sonucu göster", "Promptu göster", "Sınırlamayı belirt"],
        caption="Kaynaklı demo; sonuçlar prompta göre değişebilir.",
        video_prompt="Portrait 9:16 product demo, readable safe-area composition.",
        cta="VIDEO yaz, doğrulanmış rehberi gönderelim.",
        source_urls=source_urls or ["https://ai.google.dev/gemini-api/docs/veo"],
        safety_notes=["İnsan onayı olmadan üretme veya yayınlama."],
    )


class FakeResponses:
    def __init__(self, output: CreativeDraft | None = None, error: Exception | None = None) -> None:
        self.output = output
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def parse(self, **kwargs: Any) -> object:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(output_parsed=self.output)


class FakeOpenAIClient:
    def __init__(self, responses: FakeResponses) -> None:
        self.responses = responses


def test_openai_creative_planner_uses_structured_output_and_grounded_sources() -> None:
    responses = FakeResponses(make_draft())
    planner = OpenAICreativePlanner(FakeOpenAIClient(responses), model="gpt-test")
    brief = make_brief()
    plan = ContentOrchestrator().plan(brief)

    draft = planner.create_draft(brief, plan)

    assert draft.video_prompt.startswith("Portrait 9:16")
    assert responses.calls[0]["model"] == "gpt-test"
    assert responses.calls[0]["text_format"] is CreativeDraft
    assert responses.calls[0]["input"][0]["role"] == "system"
    assert "veri" in responses.calls[0]["input"][0]["content"]


def test_openai_creative_planner_blocks_invented_sources() -> None:
    planner = OpenAICreativePlanner(
        FakeOpenAIClient(FakeResponses(make_draft(source_urls=["https://invented.example/x"])))
    )
    brief = make_brief()

    with pytest.raises(UngroundedCreativeDraftError, match="source_url"):
        planner.create_draft(brief, ContentOrchestrator().plan(brief))


@pytest.mark.parametrize(
    "responses",
    [
        FakeResponses(None),
        FakeResponses(error=RuntimeError("Bearer sk-do-not-leak-this-value")),
    ],
)
def test_openai_creative_planner_fails_closed_without_leaking_provider_error(
    responses: FakeResponses,
) -> None:
    planner = OpenAICreativePlanner(FakeOpenAIClient(responses))
    brief = make_brief()

    with pytest.raises(CreativePlanningError) as exc_info:
        planner.create_draft(brief, ContentOrchestrator().plan(brief))

    assert "sk-do-not-leak" not in str(exc_info.value)


def test_creative_production_agent_prepares_but_does_not_execute_external_actions() -> None:
    agent = CreativeProductionAgent(
        ContentOrchestrator(),
        OpenAICreativePlanner(FakeOpenAIClient(FakeResponses(make_draft()))),
    )

    package = agent.prepare(make_brief())

    assert package.status == "AWAITING_HUMAN_APPROVAL"
    assert package.external_actions_performed is False
    assert package.content_plan.plan_id.startswith("content-")
    assert package.draft.source_urls == ["https://ai.google.dev/gemini-api/docs/veo"]
    assert package.artifact_hash.startswith("sha256:")
    assert package.to_dict()["artifact_hash"] == package.artifact_hash


class FakeVideoAdapter:
    def __init__(self) -> None:
        self.requests: list[object] = []

    def submit(self, request: object) -> VideoJob:
        self.requests.append(request)
        return VideoJob(
            provider=VideoProvider.SEEDANCE,
            plan_id=getattr(request, "plan_id"),
            status=VideoJobStatus.SUBMITTED,
            task_id="configured-seedance-task-1",
            external_actions_performed=True,
        )

    def poll(self, job: VideoJob) -> VideoJob:
        return job


def test_creative_production_agent_connects_selected_provider_only_after_approval() -> None:
    adapter = FakeVideoAdapter()
    agent = CreativeProductionAgent(
        ContentOrchestrator(),
        OpenAICreativePlanner(FakeOpenAIClient(FakeResponses(make_draft()))),
        provider_registry=ProviderExecutionRegistry({VideoProvider.SEEDANCE: adapter}),
    )
    package = agent.prepare(make_brief())

    blocked = agent.submit_video(package, VideoProvider.SEEDANCE, None)
    submitted = agent.submit_video(
        package,
        VideoProvider.SEEDANCE,
        HumanApproval(
            plan_id=package.content_plan.plan_id,
            approved=True,
            reviewer="operator@example.com",
            evidence_id="approval-creative-1",
            artifact_hash=package.artifact_hash,
        ),
    )

    assert blocked.status is VideoJobStatus.BLOCKED
    assert submitted.status is VideoJobStatus.SUBMITTED
    assert len(adapter.requests) == 1
