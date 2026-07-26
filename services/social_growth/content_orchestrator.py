"""Governed, side-effect-free planning for multi-provider social content."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol
from urllib.parse import urlparse

from services.social_growth.contracts import OperationEvidence, OperationStatus

MAX_TOPIC_LENGTH = 240
MAX_AUDIENCE_LENGTH = 240
KEYWORD_PATTERN = re.compile(r"^[A-ZÇĞİÖŞÜ0-9_]{3,24}$")


class ContentMode(str, Enum):
    """Primary business outcome for one content plan."""

    REACH = "reach"
    LEAD = "lead"
    SAVE = "save"
    AUTHORITY = "authority"


class ContentFormat(str, Enum):
    """Supported Instagram deliverable formats."""

    REEL = "reel"
    CAROUSEL = "carousel"
    HYBRID = "hybrid"


class ContentTemplate(str, Enum):
    """Evidence-backed MVP content structures."""

    TOOL_CAROUSEL = "tool_carousel"
    ONE_PROMPT_DEMO = "one_prompt_demo"
    EMOTIONAL_MINI_STORY = "emotional_mini_story"


class CTAMode(str, Enum):
    """Supported conversion mechanics."""

    SAVE_SHARE = "save_share"
    KEYWORD_DM = "keyword_dm"


class ProviderRoutingMode(str, Enum):
    """How candidate video providers participate in a plan."""

    AUTO = "auto"
    COMPARE = "compare"
    PIPELINE = "pipeline"


class VideoProvider(str, Enum):
    """Configurable video-provider identifiers; no API call is implied."""

    VEO = "veo"
    SEEDANCE = "seedance"
    KLING = "kling"
    HAILUO = "hailuo"


class UngroundedClaimError(ValueError):
    """Raised when a verifiable claim has no evidence source."""


class DuplicateKeywordError(ValueError):
    """Raised when two active plans attempt to own the same DM keyword."""


class ProviderRoutingError(ValueError):
    """Raised when enabled provider profiles cannot satisfy a routing mode."""


@dataclass(frozen=True)
class Claim:
    """One claim and the HTTPS sources that ground it."""

    text: str
    source_urls: tuple[str, ...] = ()
    verifiable: bool = True

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("claim text boş olamaz")
        for source_url in self.source_urls:
            _validate_public_https_url(source_url, field_name="claim source")

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "source_urls": list(self.source_urls),
            "verifiable": self.verifiable,
        }


@dataclass(frozen=True)
class ContentBrief:
    """Validated operator request for a side-effect-free campaign plan."""

    topic: str
    audience: str
    mode: ContentMode
    format: ContentFormat
    template: ContentTemplate
    cta_mode: CTAMode
    keyword: str | None = None
    routing_mode: ProviderRoutingMode = ProviderRoutingMode.AUTO
    preferred_providers: tuple[VideoProvider, ...] = ()
    claims: tuple[Claim, ...] = ()

    def __post_init__(self) -> None:
        topic = self.topic.strip()
        audience = self.audience.strip()
        if not topic or len(topic) > MAX_TOPIC_LENGTH:
            raise ValueError(f"topic 1-{MAX_TOPIC_LENGTH} karakter arasında olmalı")
        if not audience or len(audience) > MAX_AUDIENCE_LENGTH:
            raise ValueError(f"audience 1-{MAX_AUDIENCE_LENGTH} karakter arasında olmalı")
        object.__setattr__(self, "topic", topic)
        object.__setattr__(self, "audience", audience)

        keyword = self.keyword.strip().upper() if self.keyword else None
        if self.cta_mode is CTAMode.KEYWORD_DM:
            if keyword is None or not KEYWORD_PATTERN.fullmatch(keyword):
                raise ValueError(
                    "keyword_dm için keyword 3-24 karakterlik tek ve güvenli bir token olmalı"
                )
        elif keyword is not None:
            raise ValueError("keyword yalnız keyword_dm CTA modunda kullanılabilir")
        object.__setattr__(self, "keyword", keyword)

        if len(set(self.preferred_providers)) != len(self.preferred_providers):
            raise ValueError("preferred_providers tekrarlanan sağlayıcı içeremez")
        if self.template is ContentTemplate.TOOL_CAROUSEL:
            if self.format not in {ContentFormat.CAROUSEL, ContentFormat.HYBRID}:
                raise ValueError("tool_carousel yalnız carousel veya hybrid formatında kullanılabilir")
        elif self.format not in {ContentFormat.REEL, ContentFormat.HYBRID}:
            raise ValueError("video şablonları yalnız reel veya hybrid formatında kullanılabilir")

    def to_fingerprint_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "audience": self.audience,
            "mode": self.mode.value,
            "format": self.format.value,
            "template": self.template.value,
            "cta_mode": self.cta_mode.value,
            "keyword": self.keyword,
            "routing_mode": self.routing_mode.value,
            "preferred_providers": [item.value for item in self.preferred_providers],
            "claims": [claim.to_dict() for claim in self.claims],
        }


@dataclass(frozen=True)
class ProviderProfile:
    """Operator-configurable routing labels, not vendor capability claims."""

    provider: VideoProvider
    capabilities: frozenset[str]
    enabled: bool = True


@dataclass(frozen=True)
class ProviderStage:
    provider: VideoProvider
    role: str
    matched_capabilities: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider.value,
            "role": self.role,
            "matched_capabilities": list(self.matched_capabilities),
        }


@dataclass(frozen=True)
class ProviderRoute:
    mode: ProviderRoutingMode
    stages: tuple[ProviderStage, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "stages": [stage.to_dict() for stage in self.stages],
        }


@dataclass(frozen=True)
class HookVariant:
    category: str
    text: str

    def to_dict(self) -> dict[str, str]:
        return {"category": self.category, "text": self.text}


@dataclass(frozen=True)
class ContentUnit:
    kind: str
    instruction: str

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "instruction": self.instruction}


@dataclass(frozen=True)
class CTAPlan:
    mode: CTAMode
    text: str
    keyword: str | None = None
    fulfilment: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "text": self.text,
            "keyword": self.keyword,
            "fulfilment": self.fulfilment,
        }


@dataclass(frozen=True)
class ContentPlan:
    """Complete planning artifact; it never represents a published post."""

    plan_id: str
    template: ContentTemplate
    hooks: tuple[HookVariant, ...]
    content_units: tuple[ContentUnit, ...]
    cta: CTAPlan
    provider_route: ProviderRoute
    claims: tuple[Claim, ...]
    quality_gates: tuple[str, ...]
    metrics: tuple[str, ...]
    status: str = "DRY_RUN"
    external_actions_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "status": self.status,
            "external_actions_performed": self.external_actions_performed,
            "template": self.template.value,
            "hooks": [hook.to_dict() for hook in self.hooks],
            "content_units": [unit.to_dict() for unit in self.content_units],
            "cta": self.cta.to_dict(),
            "provider_route": self.provider_route.to_dict(),
            "claims": [claim.to_dict() for claim in self.claims],
            "quality_gates": list(self.quality_gates),
            "metrics": list(self.metrics),
        }


class KeywordRegistry(Protocol):
    """Reserves one fulfilment keyword for one active campaign plan."""

    def claim(self, keyword: str, plan_id: str) -> bool:
        """Return false when the keyword is already reserved."""

    def release(self, keyword: str, plan_id: str) -> None:
        """Release a reservation after a failed plan persistence."""


class PlanEvidenceSink(Protocol):
    """Persists a governed operation evidence record."""

    def record(self, evidence: OperationEvidence) -> None:
        """Persist one plan operation."""


class RedisKeywordClient(Protocol):
    """Subset of redis-py required for durable keyword ownership."""

    def set(
        self,
        name: str,
        value: str,
        *,
        nx: bool,
        ex: int,
    ) -> object:
        """Reserve a key only when it is absent."""

    def eval(self, script: str, numkeys: int, *keys_and_args: str) -> object:
        """Execute owner-checked release atomically."""


class InMemoryKeywordRegistry:
    """Process-local keyword registry suitable for planning and unit tests."""

    def __init__(self) -> None:
        self._owners: dict[str, str] = {}

    def claim(self, keyword: str, plan_id: str) -> bool:
        if keyword in self._owners:
            return False
        self._owners = {**self._owners, keyword: plan_id}
        return True

    def release(self, keyword: str, plan_id: str) -> None:
        if self._owners.get(keyword) != plan_id:
            return
        self._owners = {key: owner for key, owner in self._owners.items() if key != keyword}


_RELEASE_KEYWORD_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
  return redis.call('del', KEYS[1])
end
return 0
""".strip()


class RedisKeywordRegistry:
    """Cross-process CTA keyword ownership backed by Redis SET NX."""

    def __init__(
        self,
        client: RedisKeywordClient,
        *,
        key_prefix: str = "social-growth:cta-keyword:",
        ttl_seconds: int = 30 * 24 * 60 * 60,
    ) -> None:
        if ttl_seconds < 60:
            raise ValueError("Keyword TTL en az 60 saniye olmalı")
        self._client = client
        self._key_prefix = key_prefix
        self._ttl_seconds = ttl_seconds

    def claim(self, keyword: str, plan_id: str) -> bool:
        return bool(
            self._client.set(
                f"{self._key_prefix}{keyword}",
                plan_id,
                nx=True,
                ex=self._ttl_seconds,
            )
        )

    def release(self, keyword: str, plan_id: str) -> None:
        self._client.eval(
            _RELEASE_KEYWORD_SCRIPT,
            1,
            f"{self._key_prefix}{keyword}",
            plan_id,
        )


class ProviderRouter:
    """Select video providers from explicit, replaceable capability profiles."""

    def __init__(self, profiles: tuple[ProviderProfile, ...] | None = None) -> None:
        self._profiles = profiles or default_provider_profiles()
        providers = [profile.provider for profile in self._profiles]
        if len(providers) != len(set(providers)):
            raise ValueError("provider profiles tekrarlanan sağlayıcı içeremez")

    def route(self, brief: ContentBrief) -> ProviderRoute:
        if brief.format is ContentFormat.CAROUSEL:
            return ProviderRoute(mode=brief.routing_mode, stages=())

        desired = _desired_capabilities(brief.template)
        preferred = set(brief.preferred_providers)
        candidates = [
            profile
            for profile in self._profiles
            if profile.enabled and (not preferred or profile.provider in preferred)
        ]
        ranked = sorted(
            enumerate(candidates),
            key=lambda item: (
                -len(item[1].capabilities.intersection(desired)),
                item[0],
            ),
        )
        ordered = [profile for _, profile in ranked]
        required = 1 if brief.routing_mode is ProviderRoutingMode.AUTO else 2
        if len(ordered) < required:
            raise ProviderRoutingError(
                f"{brief.routing_mode.value} için en az {required} etkin sağlayıcı gerekli"
            )

        selected = ordered[:required]
        roles: tuple[str, ...]
        if brief.routing_mode is ProviderRoutingMode.AUTO:
            roles = ("generate",)
        elif brief.routing_mode is ProviderRoutingMode.COMPARE:
            roles = ("candidate", "candidate")
        else:
            roles = ("generate", "refine")
        stages = tuple(
            ProviderStage(
                provider=profile.provider,
                role=role,
                matched_capabilities=tuple(sorted(profile.capabilities.intersection(desired))),
            )
            for profile, role in zip(selected, roles, strict=True)
        )
        return ProviderRoute(mode=brief.routing_mode, stages=stages)


def default_provider_profiles() -> tuple[ProviderProfile, ...]:
    """Return editable routing defaults; labels must be verified before live use."""

    return (
        ProviderProfile(
            VideoProvider.VEO,
            frozenset({"cinematic", "emotional", "story"}),
        ),
        ProviderProfile(
            VideoProvider.SEEDANCE,
            frozenset({"demo", "motion", "multi_scene"}),
        ),
        ProviderProfile(
            VideoProvider.KLING,
            frozenset({"demo", "motion", "realism"}),
        ),
        ProviderProfile(
            VideoProvider.HAILUO,
            frozenset({"emotional", "rapid_iteration", "stylized"}),
        ),
    )


QUALITY_GATES = (
    "claim_sources",
    "reference_rights",
    "brand_identity",
    "ocr_and_subtitles",
    "format_safe_area",
    "human_approval",
)

CORE_METRICS = (
    "three_second_hold_rate",
    "completion_rate",
    "saves",
    "shares",
    "comments",
    "keyword_dm_conversion_rate",
    "sales_conversion_rate",
)


class ContentOrchestrator:
    """Create governed content plans without invoking or publishing providers."""

    def __init__(
        self,
        *,
        provider_router: ProviderRouter | None = None,
        keyword_registry: KeywordRegistry | None = None,
        evidence_sink: PlanEvidenceSink | None = None,
    ) -> None:
        self._provider_router = provider_router or ProviderRouter()
        self._keyword_registry = keyword_registry or InMemoryKeywordRegistry()
        self._evidence_sink = evidence_sink

    def plan(self, brief: ContentBrief) -> ContentPlan:
        """Build and audit a reusable content campaign plan."""

        _validate_claims(brief.claims)
        route = self._provider_router.route(brief)
        plan_id = _build_plan_id(brief)
        plan = ContentPlan(
            plan_id=plan_id,
            template=brief.template,
            hooks=_build_hooks(brief),
            content_units=_build_content_units(brief),
            cta=_build_cta(brief),
            provider_route=route,
            claims=brief.claims,
            quality_gates=QUALITY_GATES,
            metrics=CORE_METRICS,
        )

        keyword = brief.keyword
        if keyword and not self._keyword_registry.claim(keyword, plan_id):
            raise DuplicateKeywordError(f"{keyword} keyword başka bir kampanya tarafından kullanılıyor")
        try:
            self._record_plan(plan, brief)
        except Exception:
            if keyword:
                self._keyword_registry.release(keyword, plan_id)
            raise
        return plan

    def _record_plan(self, plan: ContentPlan, brief: ContentBrief) -> None:
        if self._evidence_sink is None:
            return
        self._evidence_sink.record(
            OperationEvidence(
                operation="content_campaign_plan",
                status=OperationStatus.DRY_RUN,
                reason="Plan üretildi; insan onayı ve sağlayıcı çalıştırması bekleniyor",
                metadata={
                    "plan_id": plan.plan_id,
                    "mode": brief.mode.value,
                    "format": brief.format.value,
                    "template": brief.template.value,
                    "provider_route": plan.provider_route.to_dict(),
                    "external_actions_performed": False,
                    "tool_used": "ContentOrchestrator",
                },
            )
        )


def _validate_claims(claims: tuple[Claim, ...]) -> None:
    for claim in claims:
        if claim.verifiable and not claim.source_urls:
            raise UngroundedClaimError(
                f"Doğrulanabilir claim için kaynak zorunludur: {claim.text}"
            )


def _desired_capabilities(template: ContentTemplate) -> frozenset[str]:
    if template is ContentTemplate.EMOTIONAL_MINI_STORY:
        return frozenset({"cinematic", "emotional", "story"})
    return frozenset({"demo", "motion", "multi_scene"})


def _build_hooks(brief: ContentBrief) -> tuple[HookVariant, ...]:
    topic = brief.topic
    if brief.template is ContentTemplate.TOOL_CAROUSEL:
        return (
            HookVariant("list", f"{topic} için kaydetmen gereken 7 araç"),
            HookVariant("contrarian", f"{topic} için tek araca bağlı kalma"),
            HookVariant("comparison", f"{topic}: hangi araç hangi işte daha uygun?"),
        )
    if brief.template is ContentTemplate.ONE_PROMPT_DEMO:
        return (
            HookVariant("proof", f"Tek promptla {topic} ürettim"),
            HookVariant("contrarian", f"{topic} saatler sürmek zorunda değil"),
            HookVariant("comparison", f"Prompttan sonuca: {topic}"),
        )
    return (
        HookVariant("emotional", "Bazı anılar neden hiç eskimez?"),
        HookVariant("relatable", f"{brief.audience} bunu çok iyi anlayacak"),
        HookVariant("curiosity", f"{topic} için son sahneyi bekle"),
    )


def _build_content_units(brief: ContentBrief) -> tuple[ContentUnit, ...]:
    if brief.template is ContentTemplate.TOOL_CAROUSEL:
        return (
            ContentUnit("cover", "Tek vaat ve 3-7 kelimelik yüksek kontrastlı başlık kullan."),
            ContentUnit("tool_list", "Araçları kullanım amacına göre grupla; doğrulanmamış iddia ekleme."),
            ContentUnit("selection_guide", "Her araç için seçim ölçütü ve sınırlama belirt."),
            ContentUnit("cta", "Son slaytta yalnız seçilen CTA'yı göster."),
        )
    if brief.template is ContentTemplate.ONE_PROMPT_DEMO:
        return (
            ContentUnit("hook", "İlk üç saniyede insan yüzü veya nihai çıktıyı göster."),
            ContentUnit("demo", "Girdi, prompt ve üretim adımlarını kısa kesitlerle kanıtla."),
            ContentUnit("proof", "Gerçek çıktıyı göster; gelir veya sınırsızlık iddiası uydurma."),
            ContentUnit("cta", "Tek CTA kullan ve varsa DM fulfilment varlığını eşleştir."),
        )
    return (
        ContentUnit("hook", "İlk karede duygusu okunabilen bir karakter veya an kullan."),
        ContentUnit("setup", "Tek mekân, karakter ve anlaşılır bir gündelik bağlam kur."),
        ContentUnit("tension", "Kısa bir özlem, çatışma veya merak yükselişi oluştur."),
        ContentUnit("payoff", "Son sahnede duygusal karşılığı ver; gereksiz araç tanıtımı yapma."),
        ContentUnit("cta", "Duyguyu bozmayan kısa kaydetme veya paylaşma çağrısı kullan."),
    )


def _build_cta(brief: ContentBrief) -> CTAPlan:
    if brief.cta_mode is CTAMode.KEYWORD_DM:
        return CTAPlan(
            mode=brief.cta_mode,
            text=f"{brief.keyword} yaz, rehberi DM ile gönderelim.",
            keyword=brief.keyword,
            fulfilment="configured_dm_asset",
        )
    return CTAPlan(
        mode=brief.cta_mode,
        text="Kaydet ve ihtiyacı olan biriyle paylaş.",
    )


def _build_plan_id(brief: ContentBrief) -> str:
    canonical = json.dumps(
        brief.to_fingerprint_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"content-{digest}"


def _validate_public_https_url(url: str, *, field_name: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(f"{field_name} public HTTPS URL olmalı")
    if parsed.username or parsed.password:
        raise ValueError(f"{field_name} credential içeremez")
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith(".localhost"):
        raise ValueError(f"{field_name} public HTTPS URL olmalı")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return
    if not address.is_global:
        raise ValueError(f"{field_name} public HTTPS URL olmalı")
