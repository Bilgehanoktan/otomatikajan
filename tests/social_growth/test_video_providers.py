from __future__ import annotations

from typing import Any

import pytest

from services.social_growth.content_orchestrator import VideoProvider
from services.social_growth.contracts import OperationEvidence, OperationStatus
from services.social_growth.video_providers import (
    HailuoVideoAdapter,
    HumanApproval,
    ProviderExecutionRegistry,
    VeoVideoAdapter,
    VideoGenerationRequest,
    VideoJobStatus,
)

TEST_ARTIFACT_HASH = "sha256:" + "a" * 64


class FakeResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"provider failed with api_key=secret: {self.status_code}")

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeTransport:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = responses
        self.requests: list[dict[str, Any]] = []

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.requests.append({"method": "POST", "url": url, **kwargs})
        return self.responses.pop(0)

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.requests.append({"method": "GET", "url": url, **kwargs})
        return self.responses.pop(0)


class FakeEvidenceSink:
    def __init__(self) -> None:
        self.records: list[OperationEvidence] = []

    def record(self, evidence: OperationEvidence) -> None:
        self.records.append(evidence)


def request(provider: VideoProvider) -> VideoGenerationRequest:
    return VideoGenerationRequest(
        plan_id="content-0123456789abcdef",
        provider=provider,
        artifact_hash=TEST_ARTIFACT_HASH,
        prompt="Portrait 9:16 cinematic demo with readable safe areas.",
        aspect_ratio="9:16",
        duration_seconds=8 if provider is VideoProvider.VEO else 6,
    )


def approval(*, plan_id: str = "content-0123456789abcdef") -> HumanApproval:
    return HumanApproval(
        plan_id=plan_id,
        approved=True,
        reviewer="operator@example.com",
        evidence_id="approval-123",
        artifact_hash=TEST_ARTIFACT_HASH,
    )


def test_registry_blocks_provider_transport_without_matching_human_approval() -> None:
    transport = FakeTransport([FakeResponse({"name": "operations/never"})])
    registry = ProviderExecutionRegistry(
        {VideoProvider.VEO: VeoVideoAdapter("gemini-secret", transport)}
    )

    unapproved = registry.submit(request(VideoProvider.VEO), None)
    mismatched = registry.submit(
        request(VideoProvider.VEO),
        approval(plan_id="content-other"),
    )

    assert unapproved.status is VideoJobStatus.BLOCKED
    assert unapproved.blocker_code == "BLOCKED_HUMAN_APPROVAL_REQUIRED"
    assert mismatched.blocker_code == "BLOCKED_APPROVAL_PLAN_MISMATCH"
    assert transport.requests == []


def test_registry_blocks_approval_bound_to_a_different_creative_artifact() -> None:
    transport = FakeTransport([FakeResponse({"name": "operations/never"})])
    registry = ProviderExecutionRegistry(
        {VideoProvider.VEO: VeoVideoAdapter("gemini-secret", transport)}
    )
    mismatched_approval = HumanApproval(
        plan_id="content-0123456789abcdef",
        approved=True,
        reviewer="operator@example.com",
        evidence_id="approval-other-artifact",
        artifact_hash="sha256:" + "b" * 64,
    )

    result = registry.submit(request(VideoProvider.VEO), mismatched_approval)

    assert result.blocker_code == "BLOCKED_APPROVAL_ARTIFACT_MISMATCH"
    assert transport.requests == []


def test_veo_adapter_submits_and_polls_official_long_running_contract() -> None:
    transport = FakeTransport(
        [
            FakeResponse({"name": "models/veo-3.1-generate-preview/operations/job-1"}),
            FakeResponse(
                {
                    "done": True,
                    "response": {
                        "generateVideoResponse": {
                            "generatedSamples": [
                                {"video": {"uri": "https://files.example.com/veo.mp4"}}
                            ]
                        }
                    },
                }
            ),
        ]
    )
    adapter = VeoVideoAdapter("gemini-secret", transport)
    registry = ProviderExecutionRegistry({VideoProvider.VEO: adapter})

    submitted = registry.submit(request(VideoProvider.VEO), approval())
    completed = adapter.poll(submitted)

    assert submitted.status is VideoJobStatus.SUBMITTED
    assert submitted.task_id.endswith("job-1")
    assert transport.requests[0]["url"].endswith(
        "/models/veo-3.1-generate-preview:predictLongRunning"
    )
    assert transport.requests[0]["json"]["parameters"]["aspectRatio"] == "9:16"
    assert completed.status is VideoJobStatus.SUCCEEDED
    assert completed.output_url == "https://files.example.com/veo.mp4"
    assert "gemini-secret" not in str(completed.to_dict())


def test_hailuo_adapter_submits_polls_and_resolves_file_without_downloading() -> None:
    transport = FakeTransport(
        [
            FakeResponse({"task_id": "hailuo-task-1"}),
            FakeResponse({"status": "Success", "file_id": "file-1"}),
            FakeResponse({"file": {"download_url": "https://files.example.com/hailuo.mp4"}}),
        ]
    )
    adapter = HailuoVideoAdapter("minimax-secret", transport)
    registry = ProviderExecutionRegistry({VideoProvider.HAILUO: adapter})

    submitted = registry.submit(request(VideoProvider.HAILUO), approval())
    completed = adapter.poll(submitted)

    assert transport.requests[0]["url"] == "https://api.minimax.io/v1/video_generation"
    assert transport.requests[0]["json"]["model"] == "MiniMax-Hailuo-2.3"
    assert transport.requests[1]["params"] == {"task_id": "hailuo-task-1"}
    assert completed.status is VideoJobStatus.SUCCEEDED
    assert completed.file_id == "file-1"
    assert completed.output_url == "https://files.example.com/hailuo.mp4"
    assert len(transport.requests) == 3


@pytest.mark.parametrize("provider", [VideoProvider.SEEDANCE, VideoProvider.KLING])
def test_unverified_seedance_and_kling_contracts_fail_closed(
    provider: VideoProvider,
) -> None:
    result = ProviderExecutionRegistry({}).submit(request(provider), approval())

    assert result.status is VideoJobStatus.BLOCKED
    assert result.blocker_code == "BLOCKED_PROVIDER_NOT_CONFIGURED"
    assert result.external_actions_performed is False


def test_provider_failure_is_sanitized() -> None:
    transport = FakeTransport([FakeResponse({}, status_code=500)])
    registry = ProviderExecutionRegistry(
        {VideoProvider.VEO: VeoVideoAdapter("gemini-secret", transport)}
    )

    result = registry.submit(request(VideoProvider.VEO), approval())

    assert result.status is VideoJobStatus.FAILED
    assert "secret" not in (result.reason or "")
    assert result.external_actions_performed is True


def test_provider_specific_duration_contracts_are_validated_before_transport() -> None:
    with pytest.raises(ValueError, match="Veo"):
        VideoGenerationRequest(
            plan_id="content-0123456789abcdef",
            provider=VideoProvider.VEO,
            artifact_hash=TEST_ARTIFACT_HASH,
            prompt="Portrait demo",
            duration_seconds=6,
        )

    with pytest.raises(ValueError, match="Hailuo"):
        VideoGenerationRequest(
            plan_id="content-0123456789abcdef",
            provider=VideoProvider.HAILUO,
            artifact_hash=TEST_ARTIFACT_HASH,
            prompt="Portrait demo",
            duration_seconds=7,
        )


def test_provider_registry_records_redacted_action_evidence() -> None:
    sink = FakeEvidenceSink()
    transport = FakeTransport([FakeResponse({"name": "operations/job-2"})])
    registry = ProviderExecutionRegistry(
        {VideoProvider.VEO: VeoVideoAdapter("gemini-secret", transport)},
        evidence_sink=sink,
    )

    registry.submit(request(VideoProvider.VEO), None)
    registry.submit(request(VideoProvider.VEO), approval())

    assert [item.status for item in sink.records] == [
        OperationStatus.BLOCKED,
        OperationStatus.SUCCEEDED,
    ]
    assert sink.records[1].provider_id == "operations/job-2"
    assert "prompt" not in sink.records[1].metadata
    assert "secret" not in str(sink.records[1])
