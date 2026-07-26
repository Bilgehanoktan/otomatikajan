"""Human-approved adapters for external video generation providers."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol
from urllib.parse import urlparse

import httpx

from services.social_growth.content_orchestrator import VideoProvider
from services.social_growth.contracts import OperationEvidence, OperationStatus

VEO_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
VEO_MODEL = "veo-3.1-generate-preview"
HAILUO_BASE_URL = "https://api.minimax.io/v1"
HAILUO_MODEL = "MiniMax-Hailuo-2.3"
_OPERATION_NAME_PATTERN = re.compile(r"^[A-Za-z0-9._/-]{1,500}$")
_ARTIFACT_HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class VideoJobStatus(str, Enum):
    BLOCKED = "BLOCKED"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class HumanApproval:
    """Trusted governance decision bound to one deterministic content plan."""

    plan_id: str
    approved: bool
    reviewer: str
    evidence_id: str
    artifact_hash: str

    def __post_init__(self) -> None:
        if not self.plan_id.strip() or not self.reviewer.strip() or not self.evidence_id.strip():
            raise ValueError("HumanApproval alanları boş olamaz")
        if not _ARTIFACT_HASH_PATTERN.fullmatch(self.artifact_hash):
            raise ValueError("HumanApproval artifact_hash geçersiz")


@dataclass(frozen=True)
class VideoGenerationRequest:
    plan_id: str
    provider: VideoProvider
    artifact_hash: str
    prompt: str
    aspect_ratio: str = "9:16"
    duration_seconds: int = 6

    def __post_init__(self) -> None:
        if not self.plan_id.startswith("content-"):
            raise ValueError("plan_id content planına ait olmalı")
        if not _ARTIFACT_HASH_PATTERN.fullmatch(self.artifact_hash):
            raise ValueError("artifact_hash geçersiz")
        if not 1 <= len(self.prompt.strip()) <= 4_000:
            raise ValueError("prompt 1-4000 karakter arasında olmalı")
        if self.aspect_ratio not in {"9:16", "16:9"}:
            raise ValueError("aspect_ratio 9:16 veya 16:9 olmalı")
        if not 1 <= self.duration_seconds <= 10:
            raise ValueError("duration_seconds 1-10 arasında olmalı")
        if self.provider is VideoProvider.VEO and self.duration_seconds != 8:
            raise ValueError("Veo 3.1 duration_seconds değeri 8 olmalı")
        if self.provider is VideoProvider.HAILUO and self.duration_seconds not in {6, 10}:
            raise ValueError("Hailuo duration_seconds değeri 6 veya 10 olmalı")


@dataclass(frozen=True)
class VideoJob:
    provider: VideoProvider
    plan_id: str
    status: VideoJobStatus
    artifact_hash: str | None = None
    task_id: str | None = None
    file_id: str | None = None
    output_url: str | None = None
    blocker_code: str | None = None
    reason: str | None = None
    external_actions_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider.value,
            "plan_id": self.plan_id,
            "status": self.status.value,
            "artifact_hash": self.artifact_hash,
            "task_id": self.task_id,
            "file_id": self.file_id,
            "output_url": self.output_url,
            "blocker_code": self.blocker_code,
            "reason": self.reason,
            "external_actions_performed": self.external_actions_performed,
        }


class ProviderTransport(Protocol):
    def post(self, url: str, **kwargs: Any) -> Any:
        """Issue a provider POST request."""

    def get(self, url: str, **kwargs: Any) -> Any:
        """Issue a provider GET request."""


class VideoProviderAdapter(Protocol):
    def submit(self, request: VideoGenerationRequest) -> VideoJob:
        """Submit one approved provider task."""

    def poll(self, job: VideoJob) -> VideoJob:
        """Poll one previously submitted task."""


class VideoEvidenceSink(Protocol):
    def record(self, evidence: OperationEvidence) -> None:
        """Persist a redacted provider action record."""


class ProviderExecutionRegistry:
    """Fail-closed provider dispatch protected by a plan-bound human approval."""

    def __init__(
        self,
        adapters: dict[VideoProvider, VideoProviderAdapter],
        *,
        evidence_sink: VideoEvidenceSink | None = None,
    ) -> None:
        self._adapters = dict(adapters)
        self._evidence_sink = evidence_sink

    def submit(
        self,
        request: VideoGenerationRequest,
        approval: HumanApproval | None,
    ) -> VideoJob:
        if approval is None or not approval.approved:
            result = _blocked_job(request, "BLOCKED_HUMAN_APPROVAL_REQUIRED")
            self._record_submit(result)
            return result
        if approval.plan_id != request.plan_id:
            result = _blocked_job(request, "BLOCKED_APPROVAL_PLAN_MISMATCH")
            self._record_submit(result)
            return result
        if approval.artifact_hash != request.artifact_hash:
            result = _blocked_job(request, "BLOCKED_APPROVAL_ARTIFACT_MISMATCH")
            self._record_submit(result)
            return result
        adapter = self._adapters.get(request.provider)
        if adapter is None:
            result = _blocked_job(request, "BLOCKED_PROVIDER_NOT_CONFIGURED")
            self._record_submit(result)
            return result
        try:
            result = adapter.submit(request)
        except Exception:
            result = VideoJob(
                provider=request.provider,
                plan_id=request.plan_id,
                status=VideoJobStatus.FAILED,
                artifact_hash=request.artifact_hash,
                reason="Provider request güvenli biçimde tamamlanamadı",
                external_actions_performed=True,
            )
        self._record_submit(result)
        return result

    def _record_submit(self, job: VideoJob) -> None:
        if self._evidence_sink is None:
            return
        if job.status is VideoJobStatus.SUBMITTED:
            evidence_status = OperationStatus.SUCCEEDED
            provider_id = job.task_id
        elif job.status is VideoJobStatus.BLOCKED:
            evidence_status = OperationStatus.BLOCKED
            provider_id = None
        else:
            evidence_status = OperationStatus.FAILED
            provider_id = None
        self._evidence_sink.record(
            OperationEvidence(
                operation="video_generation_submit",
                status=evidence_status,
                provider_id=provider_id,
                reason=job.blocker_code or job.reason,
                metadata={
                    "plan_id": job.plan_id,
                    "provider": job.provider.value,
                    "artifact_hash": job.artifact_hash,
                    "job_status": job.status.value,
                    "external_actions_performed": job.external_actions_performed,
                    "tool_used": f"{job.provider.value}_video_adapter",
                },
            )
        )


class VeoVideoAdapter:
    """Veo 3.1 long-running REST adapter based on the official Gemini contract."""

    def __init__(
        self,
        api_key: str,
        transport: ProviderTransport | None = None,
        *,
        timeout_seconds: float = 30.0,
    ) -> None:
        if len(api_key) < 8:
            raise ValueError("Veo API key geçerli görünmüyor")
        self._api_key = api_key
        self._transport = transport or httpx.Client(timeout=timeout_seconds)

    def submit(self, request: VideoGenerationRequest) -> VideoJob:
        response = self._transport.post(
            f"{VEO_BASE_URL}/models/{VEO_MODEL}:predictLongRunning",
            headers={"x-goog-api-key": self._api_key, "Content-Type": "application/json"},
            json={
                "instances": [{"prompt": request.prompt}],
                "parameters": {"aspectRatio": request.aspect_ratio},
            },
        )
        response.raise_for_status()
        operation_name = response.json().get("name")
        _validate_operation_name(operation_name)
        return VideoJob(
            provider=request.provider,
            plan_id=request.plan_id,
            status=VideoJobStatus.SUBMITTED,
            artifact_hash=request.artifact_hash,
            task_id=operation_name,
            external_actions_performed=True,
        )

    def poll(self, job: VideoJob) -> VideoJob:
        task_id = job.task_id
        _validate_job(job, VideoProvider.VEO)
        _validate_operation_name(task_id)
        try:
            response = self._transport.get(
                f"{VEO_BASE_URL}/{task_id}",
                headers={"x-goog-api-key": self._api_key},
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return _failed_polled_job(job)
        if not payload.get("done", False):
            return _replace_job_status(job, VideoJobStatus.PROCESSING)
        try:
            output_url = payload["response"]["generateVideoResponse"]["generatedSamples"][0][
                "video"
            ]["uri"]
            _validate_public_https_url(output_url)
        except (KeyError, IndexError, TypeError, ValueError):
            return _failed_polled_job(job)
        return VideoJob(
            provider=job.provider,
            plan_id=job.plan_id,
            status=VideoJobStatus.SUCCEEDED,
            artifact_hash=job.artifact_hash,
            task_id=job.task_id,
            output_url=output_url,
            external_actions_performed=True,
        )


class HailuoVideoAdapter:
    """MiniMax Hailuo async task adapter; returned media is never auto-downloaded."""

    def __init__(
        self,
        api_key: str,
        transport: ProviderTransport | None = None,
        *,
        timeout_seconds: float = 30.0,
    ) -> None:
        if len(api_key) < 8:
            raise ValueError("Hailuo API key geçerli görünmüyor")
        self._api_key = api_key
        self._transport = transport or httpx.Client(timeout=timeout_seconds)

    def submit(self, request: VideoGenerationRequest) -> VideoJob:
        response = self._transport.post(
            f"{HAILUO_BASE_URL}/video_generation",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "prompt": request.prompt,
                "model": HAILUO_MODEL,
                "duration": request.duration_seconds,
                "resolution": "1080P",
            },
        )
        response.raise_for_status()
        task_id = response.json().get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("Hailuo task_id döndürmedi")
        return VideoJob(
            provider=request.provider,
            plan_id=request.plan_id,
            status=VideoJobStatus.SUBMITTED,
            artifact_hash=request.artifact_hash,
            task_id=task_id,
            external_actions_performed=True,
        )

    def poll(self, job: VideoJob) -> VideoJob:
        _validate_job(job, VideoProvider.HAILUO)
        if not job.task_id:
            raise ValueError("task_id zorunludur")
        headers = {"Authorization": f"Bearer {self._api_key}"}
        try:
            response = self._transport.get(
                f"{HAILUO_BASE_URL}/query/video_generation",
                headers=headers,
                params={"task_id": job.task_id},
            )
            response.raise_for_status()
            payload = response.json()
            provider_status = payload.get("status")
            if provider_status == "Fail":
                return _failed_polled_job(job)
            if provider_status != "Success":
                return _replace_job_status(job, VideoJobStatus.PROCESSING)
            file_id = payload.get("file_id")
            if not isinstance(file_id, str) or not file_id:
                return _failed_polled_job(job)
            file_response = self._transport.get(
                f"{HAILUO_BASE_URL}/files/retrieve",
                headers=headers,
                params={"file_id": file_id},
            )
            file_response.raise_for_status()
            output_url = file_response.json()["file"]["download_url"]
            _validate_public_https_url(output_url)
        except Exception:
            return _failed_polled_job(job)
        return VideoJob(
            provider=job.provider,
            plan_id=job.plan_id,
            status=VideoJobStatus.SUCCEEDED,
            artifact_hash=job.artifact_hash,
            task_id=job.task_id,
            file_id=file_id,
            output_url=output_url,
            external_actions_performed=True,
        )


def _blocked_job(request: VideoGenerationRequest, blocker_code: str) -> VideoJob:
    return VideoJob(
        provider=request.provider,
        plan_id=request.plan_id,
        status=VideoJobStatus.BLOCKED,
        artifact_hash=request.artifact_hash,
        blocker_code=blocker_code,
    )


def _validate_operation_name(value: object) -> None:
    if (
        not isinstance(value, str)
        or not _OPERATION_NAME_PATTERN.fullmatch(value)
        or value.startswith("/")
        or ".." in value
    ):
        raise ValueError("Veo operation name geçersiz")


def _validate_job(job: VideoJob, provider: VideoProvider) -> None:
    if job.provider is not provider:
        raise ValueError("VideoJob provider eşleşmiyor")
    if job.status not in {VideoJobStatus.SUBMITTED, VideoJobStatus.PROCESSING}:
        raise ValueError("VideoJob poll edilebilir durumda değil")


def _replace_job_status(job: VideoJob, status: VideoJobStatus) -> VideoJob:
    return VideoJob(
        provider=job.provider,
        plan_id=job.plan_id,
        status=status,
        artifact_hash=job.artifact_hash,
        task_id=job.task_id,
        file_id=job.file_id,
        external_actions_performed=True,
    )


def _failed_polled_job(job: VideoJob) -> VideoJob:
    return VideoJob(
        provider=job.provider,
        plan_id=job.plan_id,
        status=VideoJobStatus.FAILED,
        artifact_hash=job.artifact_hash,
        task_id=job.task_id,
        reason="Provider task güvenli biçimde tamamlanamadı",
        external_actions_performed=True,
    )


def _validate_public_https_url(url: object) -> None:
    if not isinstance(url, str):
        raise ValueError("output_url public HTTPS URL olmalı")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("output_url public HTTPS URL olmalı")
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith(".localhost"):
        raise ValueError("output_url public HTTPS URL olmalı")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return
    if not address.is_global:
        raise ValueError("output_url public HTTPS URL olmalı")
