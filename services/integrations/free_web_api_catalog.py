from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


QuotaClass = Literal[
    "no_published_quota",
    "no_daily_monthly_quota_with_abuse_guard",
    "limited_free_tier",
]


class FreeWebApiProvider(BaseModel):
    id: str
    name: str
    category: str
    use_case_tr: str
    docs_url: str
    base_url: str
    sample_endpoint: str
    auth_required: bool = False
    strict_kotasiz: bool
    quota_class: QuotaClass
    quota_notes_tr: str
    cors: Literal["yes", "no", "unknown"]
    browser_safe: bool
    recommended_use_tr: str
    caveats_tr: list[str] = Field(default_factory=list)
    self_hostable: bool = False
    evidence_urls: list[str] = Field(default_factory=list)


_CATALOG: tuple[FreeWebApiProvider, ...] = (
    FreeWebApiProvider(
        id="ipify",
        name="ipify",
        category="network",
        use_case_tr="Public IP adresini JSON veya düz metin olarak almak.",
        docs_url="https://www.ipify.org/",
        base_url="https://api.ipify.org",
        sample_endpoint="https://api.ipify.org?format=json",
        strict_kotasiz=True,
        quota_class="no_published_quota",
        quota_notes_tr="Resmi sayfa limitsiz kullanım iddia eder.",
        cors="yes",
        browser_safe=True,
        recommended_use_tr="Hafif IP görünürlük kontrolleri ve lokal teşhis ekranları.",
        self_hostable=False,
        evidence_urls=["https://www.ipify.org/"],
    ),
    FreeWebApiProvider(
        id="frankfurter",
        name="Frankfurter",
        category="currency",
        use_case_tr="Döviz kuru, tarihsel kur ve provider kaynaklı para birimi verisi.",
        docs_url="https://frankfurter.dev/",
        base_url="https://api.frankfurter.dev",
        sample_endpoint="https://api.frankfurter.dev/v2/rate/USD/TRY",
        strict_kotasiz=True,
        quota_class="no_daily_monthly_quota_with_abuse_guard",
        quota_notes_tr="API key yok; günlük/aylık kota yok, kötüye kullanımı önlemek için rate-limit uygulanabilir.",
        cors="yes",
        browser_safe=True,
        recommended_use_tr="Kontrol panelinde döviz göstergesi veya maliyet dönüşümü için cache ile kullan.",
        caveats_tr=["Yüksek hacimde backend cache veya self-host tercih edilmeli."],
        self_hostable=True,
        evidence_urls=["https://frankfurter.dev/"],
    ),
    FreeWebApiProvider(
        id="exchange_api",
        name="fawazahmed0/exchange-api",
        category="currency",
        use_case_tr="Döviz, kripto ve metal kurları için CDN üzerinden statik JSON.",
        docs_url="https://github.com/fawazahmed0/exchange-api",
        base_url="https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1",
        sample_endpoint="https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json",
        strict_kotasiz=True,
        quota_class="no_published_quota",
        quota_notes_tr="README no rate limit belirtir; veri günlük güncellenir.",
        cors="yes",
        browser_safe=True,
        recommended_use_tr="Günlük kur yeterliyse en düşük operasyon maliyetli aday.",
        caveats_tr=["CDN hatası için `currency-api.pages.dev` fallback mekanizması eklenmeli."],
        self_hostable=False,
        evidence_urls=["https://github.com/fawazahmed0/exchange-api"],
    ),
    FreeWebApiProvider(
        id="hexarate",
        name="HexaRate",
        category="currency",
        use_case_tr="Döviz kuru ve miktar dönüşümü.",
        docs_url="https://hexarate.paikama.co/",
        base_url="https://hexarate.paikama.co",
        sample_endpoint="https://hexarate.paikama.co/api/rates/USD/TRY/latest",
        strict_kotasiz=True,
        quota_class="no_published_quota",
        quota_notes_tr="Resmi sayfa API key, signup ve rate limit olmadığını belirtir.",
        cors="yes",
        browser_safe=True,
        recommended_use_tr="Hazır conversion endpoint gerektiğinde Frankfurter alternatifi.",
        caveats_tr=["Kritik finansal kararlar için provider doğrulaması ve cache zorunlu tutulmalı."],
        self_hostable=False,
        evidence_urls=["https://hexarate.paikama.co/"],
    ),
    FreeWebApiProvider(
        id="jsonplaceholder_dev",
        name="JSONPlaceholder.dev",
        category="mock",
        use_case_tr="Frontend/backend geliştirme için fake REST veri seti.",
        docs_url="https://jsonplaceholder.dev/api/reference",
        base_url="https://api.jsonplaceholder.dev",
        sample_endpoint="https://api.jsonplaceholder.dev/users",
        strict_kotasiz=True,
        quota_class="no_published_quota",
        quota_notes_tr="Dokümantasyon mevcut durumda rate limit uygulanmadığını belirtir.",
        cors="yes",
        browser_safe=True,
        recommended_use_tr="Demo, fixture ve entegrasyon prototipi için kullan.",
        caveats_tr=["Production verisi yerine sadece test/mock amaçlı kullanılmalı."],
        self_hostable=True,
        evidence_urls=["https://jsonplaceholder.dev/api/reference"],
    ),
    FreeWebApiProvider(
        id="freeapi_app",
        name="FreeAPI.app",
        category="mock",
        use_case_tr="Random user, quote, product ve eğitim amaçlı production-style endpointler.",
        docs_url="https://freeapi.app/",
        base_url="https://freeapi.app/api/v1",
        sample_endpoint="https://freeapi.app/api/v1/public/randomusers",
        strict_kotasiz=True,
        quota_class="no_published_quota",
        quota_notes_tr="Ana sayfa no key ve no quota belirtir.",
        cors="yes",
        browser_safe=True,
        recommended_use_tr="UI prototipleri ve entegrasyon öğrenme akışları için kullan.",
        caveats_tr=["Gerçek müşteri verisi gibi ele alınmamalı."],
        self_hostable=True,
        evidence_urls=["https://freeapi.app/"],
    ),
    FreeWebApiProvider(
        id="countapi",
        name="CountAPI",
        category="utility",
        use_case_tr="Public sayaç, hit counter ve basit metrik prototipi.",
        docs_url="https://countapi.mileshilliard.com/",
        base_url="https://countapi.mileshilliard.com/api/v1",
        sample_endpoint="https://countapi.mileshilliard.com/api/v1/hit/sovereign_demo_counter",
        strict_kotasiz=True,
        quota_class="no_published_quota",
        quota_notes_tr="No registration ve no API key; servis free-to-use olarak sunulur.",
        cors="unknown",
        browser_safe=False,
        recommended_use_tr="Sadece public ve düşük riskli sayaç prototipleri için kullan.",
        caveats_tr=["Tüm counter key ve değerleri public; gizli veri yazılmamalı."],
        self_hostable=True,
        evidence_urls=["https://countapi.mileshilliard.com/"],
    ),
    FreeWebApiProvider(
        id="open_meteo",
        name="Open-Meteo",
        category="weather",
        use_case_tr="Hava durumu ve tarihsel weather verisi.",
        docs_url="https://open-meteo.com/",
        base_url="https://api.open-meteo.com",
        sample_endpoint="https://api.open-meteo.com/v1/forecast?latitude=41.0082&longitude=28.9784&current=temperature_2m",
        strict_kotasiz=False,
        quota_class="limited_free_tier",
        quota_notes_tr="Free/open-access kullanımda günlük ve saatlik limitler vardır.",
        cors="yes",
        browser_safe=True,
        recommended_use_tr="Strict kotasız gerekmeyen prototip weather verisi için kullan.",
        caveats_tr=["Strict kotasız listede varsayılan olarak dışarıda bırakılır."],
        self_hostable=True,
        evidence_urls=["https://open-meteo.com/"],
    ),
    FreeWebApiProvider(
        id="github_rest",
        name="GitHub REST API",
        category="developer",
        use_case_tr="Public repo, issue ve metadata okuma.",
        docs_url="https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api",
        base_url="https://api.github.com",
        sample_endpoint="https://api.github.com/repos/openai/openai-python",
        strict_kotasiz=False,
        quota_class="limited_free_tier",
        quota_notes_tr="Unauthenticated public data için IP bazlı saatlik limit vardır.",
        cors="yes",
        browser_safe=True,
        recommended_use_tr="Token yönetimi ve cache olan backend akışlarında kullan.",
        caveats_tr=["Strict kotasız gereksinimi için uygun değil."],
        self_hostable=False,
        evidence_urls=["https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api"],
    ),
)


def list_free_web_api_providers(
    *,
    strict_kotasiz: bool = True,
    category: str | None = None,
    include_limited: bool = False,
) -> list[FreeWebApiProvider]:
    providers = list(_CATALOG)
    if strict_kotasiz:
        providers = [provider for provider in providers if provider.strict_kotasiz]
    elif not include_limited:
        providers = [
            provider
            for provider in providers
            if provider.quota_class != "limited_free_tier"
        ]

    if category:
        normalized = category.strip().lower()
        providers = [provider for provider in providers if provider.category == normalized]

    return providers


def get_free_web_api_provider(provider_id: str) -> FreeWebApiProvider:
    normalized = provider_id.strip().lower()
    for provider in _CATALOG:
        if provider.id == normalized:
            return provider
    raise KeyError(provider_id)


def count_limited_free_providers() -> int:
    return sum(1 for provider in _CATALOG if provider.quota_class == "limited_free_tier")


def available_categories() -> list[str]:
    return sorted({provider.category for provider in _CATALOG})
