"""
Merkezi Konfigürasyon
─────────────────────
Tüm modüller buradan APP_ENV ve diğer sabitleri okur.
Local run'da .env otomatik yüklenir (main.py de yükler, iki kez zararı yok).

Kullanım:
    from config import APP_ENV, is_dev, is_prod, is_test
"""

import os


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _default_runtime_profile(app_env: str) -> str:
    return "production" if app_env == "production" else "local-dev"


def _normalize_runtime_profile(raw: str | None, app_env: str) -> str:
    if not raw or not raw.strip():
        return _default_runtime_profile(app_env)

    value = raw.strip().lower()
    if value in {"local", "local-dev", "dev", "minimal"}:
        return "local-dev"
    if value in {"full", "full-stack", "full-stack-local", "local-full"}:
        return "full-stack-local"
    if value in {"prod", "production"}:
        return "production"
    return _default_runtime_profile(app_env)

def validate_production_config():
    """
    Üretim ortamı için kritik yapılandırma denetimi.
    Eksik veya zayıf bir ayar varsa RuntimeError fırlatır.
    """
    if not is_prod:
        return

    # SRE Hardening: Üretim ortamında kesinlikle olması gereken değişkenler
    mandatory_vars = {
        "ADMIN_SECRET": ADMIN_SECRET,
        "JWT_SECRET": JWT_SECRET,
        "DATABASE_URL": DATABASE_URL,
        "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
        "WEBHOOK_SECRET": WEBHOOK_SECRET,
    }
    
    # Opsiyonel ama önerilenler (Uyarı basar)
    recommended_vars = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "DEEPSEEK_API_KEY": DEEPSEEK_API_KEY,
    }

    missing = [k for k, v in mandatory_vars.items() if not v]
    if missing:
        raise RuntimeError(f"Üretim ortamı için kritik değişkenler eksik: {missing}")

    # Şablon/Zayıf şifre kontrolü
    for name, secret in [
        ("ADMIN_SECRET", ADMIN_SECRET),
        ("JWT_SECRET", JWT_SECRET),
        ("WEBHOOK_SECRET", WEBHOOK_SECRET),
    ]:
        is_weak = any(tpl in secret for tpl in WEAK_TEMPLATES)
        if is_weak:
            raise RuntimeError(f"{name} üretim ortamı için kabul edilemez!")
    
    if len(JWT_SECRET) < 64:
        raise RuntimeError("JWT_SECRET üretim ortamı için en az 64 karakter olmalı!")

    for r_name, r_val in recommended_vars.items():
        if not r_val:
            print(f"UYARI: {r_name} üretim ortamında eksik. Bazı özellikler devre dışı kalabilir.")


# ── .env local yükleme (ek güvence) ──────────────────────
try:
    from dotenv import load_dotenv
    _base_dir = os.path.dirname(os.path.abspath(__file__))
    # Öncelik: .env -> .env.local (Host mode)
    if os.path.exists(".env"):
        load_dotenv(".env", override=True)
    if os.path.exists(".env.local"):
        load_dotenv(".env.local", override=True) # local SHOULD override environment
        
    # Sadece development/test modunda örnek dosyayı yükle (güvenlik için)
    _temp_env = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower()
    if "prod" not in _temp_env and not os.path.exists(".env"):
        if os.path.exists(os.path.join(_base_dir, ".env.example")):
            load_dotenv(os.path.join(_base_dir, ".env.example"), override=True) # SRE Hardening: override=True
except ImportError:
    pass

# SRE Hardening: psutil kütüphanesinin varlığını startup aşamasında kontrol et
try:
    import psutil
except ImportError:
    print("HATA: 'psutil' kütüphanesi eksik. Sistem sağlığı izlenemez!")
    # Production modundaysak kritik bir eksiklik (opsiyonel: sys.exit(1))

# ── Tek standart env değişkeni: APP_ENV ──────────────────
# Kabul edilen değerler: development | test | production
_raw = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower().strip()

# ENVIRONMENT alias -> APP_ENV'e map'le
if _raw in ("dev", "develop", "development"):
    APP_ENV = "development"
elif _raw in ("test", "testing", "ci"):
    APP_ENV = "test"
elif _raw in ("prod", "production", "staging"):
    APP_ENV = "production"
else:
    APP_ENV = "development"

# ENVIRONMENT env değişkenini de APP_ENV ile senkronize et (geriye dönük uyumluluk)
os.environ["APP_ENV"]     = APP_ENV
os.environ["ENVIRONMENT"] = APP_ENV

# ── Kısa helper'lar ───────────────────────────────────────
is_dev  = APP_ENV == "development"
is_test = APP_ENV == "test"
is_prod = APP_ENV == "production"

RUNTIME_PROFILE = _normalize_runtime_profile(os.getenv("RUNTIME_PROFILE"), APP_ENV)
PROFILE_DEFAULTS = {
    "local-dev": {
        "QUEUE_BACKEND": "inprocess",
        "APP_UI_MODE": "api-only",
        "LOCAL_DEV_DB_STRATEGY": "sqlite-fallback",
        "REDIS_ENABLED": False,
        "CELERY_ENABLED": False,
        "DEERFLOW_ENABLED": False,
        "TELEGRAM_ENABLED": False,
        "SCHEDULER_ENABLED": False,
    },
    "full-stack-local": {
        "QUEUE_BACKEND": "celery",
        "APP_UI_MODE": "api-only",
        "LOCAL_DEV_DB_STRATEGY": "primary",
        "REDIS_ENABLED": True,
        "CELERY_ENABLED": True,
        "DEERFLOW_ENABLED": True,
        "TELEGRAM_ENABLED": False,
        "SCHEDULER_ENABLED": False,
    },
    "production": {
        "QUEUE_BACKEND": "celery",
        "APP_UI_MODE": "static",
        "LOCAL_DEV_DB_STRATEGY": "primary",
        "REDIS_ENABLED": True,
        "CELERY_ENABLED": True,
        "DEERFLOW_ENABLED": True,
        "TELEGRAM_ENABLED": False,
        "SCHEDULER_ENABLED": True,
    },
}
PROFILE_DEFAULT = PROFILE_DEFAULTS[RUNTIME_PROFILE]

QUEUE_BACKEND = os.getenv("QUEUE_BACKEND", PROFILE_DEFAULT["QUEUE_BACKEND"]).lower().strip()
if QUEUE_BACKEND not in {"auto", "celery", "inprocess"}:
    QUEUE_BACKEND = PROFILE_DEFAULT["QUEUE_BACKEND"]

APP_UI_MODE = os.getenv("APP_UI_MODE", PROFILE_DEFAULT["APP_UI_MODE"]).lower().strip()
if APP_UI_MODE not in {"static", "api-only"}:
    APP_UI_MODE = PROFILE_DEFAULT["APP_UI_MODE"]

LOCAL_DEV_DB_STRATEGY = os.getenv(
    "LOCAL_DEV_DB_STRATEGY",
    PROFILE_DEFAULT["LOCAL_DEV_DB_STRATEGY"],
).lower().strip()
if LOCAL_DEV_DB_STRATEGY not in {"primary", "sqlite-fallback"}:
    LOCAL_DEV_DB_STRATEGY = PROFILE_DEFAULT["LOCAL_DEV_DB_STRATEGY"]

REDIS_ENABLED = _env_bool("REDIS_ENABLED", PROFILE_DEFAULT["REDIS_ENABLED"])
CELERY_ENABLED = _env_bool("CELERY_ENABLED", PROFILE_DEFAULT["CELERY_ENABLED"])
DEERFLOW_ENABLED = _env_bool("DEERFLOW_ENABLED", PROFILE_DEFAULT["DEERFLOW_ENABLED"])
TELEGRAM_ENABLED = _env_bool("TELEGRAM_ENABLED", PROFILE_DEFAULT["TELEGRAM_ENABLED"])
SCHEDULER_ENABLED = _env_bool("SCHEDULER_ENABLED", PROFILE_DEFAULT["SCHEDULER_ENABLED"])

# Safety rail: local-dev should stay resilient even if .env carries full-stack knobs.
LOCAL_DEV_STRICT_MODE = _env_bool("LOCAL_DEV_STRICT_MODE", True)
LOCAL_DEV_STRICT_MODE_APPLIED = False
if APP_ENV == "development" and RUNTIME_PROFILE == "local-dev" and LOCAL_DEV_STRICT_MODE:
    QUEUE_BACKEND = "inprocess"
    LOCAL_DEV_DB_STRATEGY = "sqlite-fallback"
    REDIS_ENABLED = False
    CELERY_ENABLED = False
    DEERFLOW_ENABLED = False
    SCHEDULER_ENABLED = False
    LOCAL_DEV_STRICT_MODE_APPLIED = True

JOB_QUEUE_HYDRATE_ON_STARTUP = _env_bool(
    "JOB_QUEUE_HYDRATE_ON_STARTUP",
    False if (APP_ENV == "development" and RUNTIME_PROFILE == "local-dev") else True
)

os.environ["RUNTIME_PROFILE"] = RUNTIME_PROFILE
os.environ["QUEUE_BACKEND"] = QUEUE_BACKEND
os.environ["APP_UI_MODE"] = APP_UI_MODE
os.environ["LOCAL_DEV_DB_STRATEGY"] = LOCAL_DEV_DB_STRATEGY
os.environ["REDIS_ENABLED"] = str(REDIS_ENABLED).lower()
os.environ["CELERY_ENABLED"] = str(CELERY_ENABLED).lower()
os.environ["DEERFLOW_ENABLED"] = str(DEERFLOW_ENABLED).lower()
os.environ["TELEGRAM_ENABLED"] = str(TELEGRAM_ENABLED).lower()
os.environ["SCHEDULER_ENABLED"] = str(SCHEDULER_ENABLED).lower()
os.environ["LOCAL_DEV_STRICT_MODE"] = str(LOCAL_DEV_STRICT_MODE).lower()
os.environ["JOB_QUEUE_HYDRATE_ON_STARTUP"] = str(JOB_QUEUE_HYDRATE_ON_STARTUP).lower()

# ── Temel ayarlar ─────────────────────────────────────────
DEBUG     = os.getenv("DEBUG", "true" if is_dev else "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if is_dev else "INFO")

# ── Veritabanı URL Tespiti ────────────────────────────────
_raw_db_url = os.getenv("DATABASE_URL", "")
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sqlite_path = os.path.join(_root, "runtime", "data", "cortex_local_v2.db")

# Docker ortamında mıyız? (Konteyner içi tespiti)
_is_in_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER", "false").lower() == "true"

if _is_in_docker:
    wants_local_sqlite = (
        APP_ENV != "production"
        and RUNTIME_PROFILE == "local-dev"
        and LOCAL_DEV_DB_STRATEGY == "sqlite-fallback"
    )
    if wants_local_sqlite:
        DATABASE_URL = f"sqlite+aiosqlite:///{sqlite_path.replace('\\', '/')}"
    # Docker içinde '127.0.0.1' veya 'localhost' kullanımı genellikle hatadır (host portuna gitmeye çalışır)
    # Eğer URL'de localhost/127.0.0.1 varsa bunu 'db' olarak değiştir.
    elif not _raw_db_url or "127.0.0.1" in _raw_db_url or "localhost" in _raw_db_url:
        # Default veya hatalı localhost URL'sini Docker hiyerarşisine çek
        DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/ai_company"
    else:
        DATABASE_URL = _raw_db_url
else:
    # Force SQLite for stable operational state (Phase 31 Stabilization)
    if is_dev and LOCAL_DEV_DB_STRATEGY == "sqlite-fallback" and not _raw_db_url:
        DATABASE_URL = f"sqlite+aiosqlite:///{sqlite_path.replace('\\', '/')}"
    else:
        DATABASE_URL = _raw_db_url or f"sqlite+aiosqlite:///{sqlite_path.replace('\\', '/')}"



DB_POOL_SIZE   = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
REDIS_URL      = os.getenv("REDIS_URL", "") if REDIS_ENABLED else ""
JWT_SECRET     = os.getenv("JWT_SECRET", "sovereign-agi-control-plane-local-secret-stable-v1")
ADMIN_SECRET   = os.getenv("ADMIN_SECRET", "agi-admin-fallback-secret-2026")
MONTHLY_BUDGET = float(os.getenv("MONTHLY_BUDGET_USD", "50.0"))
os.environ["REDIS_URL"] = REDIS_URL

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3100,http://127.0.0.1:3100,http://192.168.1.61:3100,http://localhost:8000").split(",") if o.strip()]
ALLOWED_METHODS = os.getenv("ALLOWED_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS").split(",")
ALLOWED_HEADERS = os.getenv("ALLOWED_HEADERS", "Authorization,Content-Type,X-Trace-ID,X-Requested-With").split(",")

TELEGRAM_BOT_TOKEN      = os.getenv("TELEGRAM_BOT_TOKEN", "") if TELEGRAM_ENABLED else ""
TELEGRAM_ALLOWED_IDS    = os.getenv("TELEGRAM_ALLOWED_IDS", "") if TELEGRAM_ENABLED else ""
TELEGRAM_ADMIN_IDS      = os.getenv("TELEGRAM_ADMIN_IDS", "") if TELEGRAM_ENABLED else ""
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "") if TELEGRAM_ENABLED else ""

# ── New Providers & Services ──────────────────────────────
MOONSHOT_API_KEY    = os.getenv("MOONSHOT_API_KEY", "")
DEEPSEEK_API_KEY    = os.getenv("DEEPSEEK_API_KEY", "")
ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
FALLBACK_API_KEY    = os.getenv("FALLBACK_API_KEY", "")
CLAUDE_PROXY_URL    = os.getenv("CLAUDE_PROXY_URL", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# ── Memory Config ─────────────────────────────────────────
MEMORY_DATABASE_URL = os.getenv("MEMORY_DATABASE_URL", "sqlite:///./data/memory.db")
MEMORY_MODE         = os.getenv("MEMORY_MODE", "inject")

# ── Orkestrasyon & Ajanlar ──────────────────────────────────
AGENT_COUNT              = int(os.getenv("AGENT_COUNT", "12"))
ENABLE_HEALING           = os.getenv("ENABLE_HEALING", "true").lower() == "true"
ENABLE_MODEL_ROTATION    = os.getenv("ENABLE_MODEL_ROTATION", "true").lower() == "true"
ENABLE_WORKLOAD_REDIRECT = os.getenv("ENABLE_WORKLOAD_REDIRECT", "true").lower() == "true"

# ── Finansal Ayarlar ────────────────────────────────────────
BUDGET_USD               = float(os.getenv("BUDGET_USD", "10.0"))
ENABLE_COOLDOWN          = os.getenv("ENABLE_COOLDOWN", "true").lower() == "true"
ENABLE_QUARANTINE        = os.getenv("ENABLE_QUARANTINE", "true").lower() == "true"

# ── Queue / Worker ──────────────────────────────────────────
WORKER_CONCURRENCY       = int(os.getenv("WORKER_CONCURRENCY", "2"))
QUEUE_DEFAULT            = os.getenv("QUEUE_DEFAULT", "default")
QUEUE_CRITICAL           = os.getenv("QUEUE_CRITICAL", "critical")
QUEUE_BACKGROUND         = os.getenv("QUEUE_BACKGROUND", "background")
QUEUE_DEERFLOW           = os.getenv("QUEUE_DEERFLOW", "deerflow")

# ── DeerFlow Agent Family ────────────────────────────────────
WEAK_TEMPLATES = ["REPLACE_WITH", "your-secret", "123456"]
DEERFLOW_ROLES = ["deerflow_planner", "deerflow_researcher", "deerflow_reviewer", "deerflow_recovery"]
DEERFLOW_WORKER_CONCURRENCY = int(os.getenv("DEERFLOW_WORKER_CONCURRENCY", "2"))
DEERFLOW_BRIDGE_URL = (
    os.getenv("DEERFLOW_BRIDGE_URL", "http://deerflow-bridge:8010")
    if DEERFLOW_ENABLED
    else ""
)
os.environ["DEERFLOW_BRIDGE_URL"] = DEERFLOW_BRIDGE_URL

# ── Health & Monitoring ─────────────────────────────────────
HEALTHCHECK_ENABLED      = os.getenv("HEALTHCHECK_ENABLED", "true").lower() == "true"
METRICS_ENABLED          = os.getenv("METRICS_ENABLED", "true").lower() == "true"
TRACE_ENABLED            = os.getenv("TRACE_ENABLED", "true").lower() == "true"

# ── Webhook & Entegrasyon ───────────────────────────────────
WEBHOOK_SECRET           = os.getenv("WEBHOOK_SECRET", "your-webhook-secret")
WEBHOOK_TIMEOUT_S        = int(os.getenv("WEBHOOK_TIMEOUT_S", "15"))
FRONTEND_URL             = os.getenv("FRONTEND_URL", "http://localhost:3000")

N8N_BASE_URL             = os.getenv("N8N_BASE_URL", "http://n8n:5678")
N8N_API_KEY              = os.getenv("N8N_API_KEY", "")
N8N_WEBHOOK_URL          = os.getenv("N8N_WEBHOOK_URL", "")

# ── Dosya Sistemleri ────────────────────────────────────────
UPLOAD_DIR               = os.getenv("UPLOAD_DIR", "/app/uploads")
DATA_DIR                 = os.getenv("DATA_DIR", "/app/data")
LOG_DIR                  = os.getenv("LOG_DIR", "/app/logs")

LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "60"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "10"))

# ── CEO Engine Ayarları ──────────────────────────────────────
CEO_SUPERVISOR_INTERVAL_S = int(os.getenv("CEO_SUPERVISOR_INTERVAL_S", "300"))
CEO_ALERT_COOLDOWN_S      = int(os.getenv("CEO_ALERT_COOLDOWN_S", "3600"))
CEO_QUERY_BATCH_SIZE      = int(os.getenv("CEO_QUERY_BATCH_SIZE", "20"))
TELEGRAM_BATCH_SLEEP_MS   = int(os.getenv("TELEGRAM_BATCH_SLEEP_MS", "50"))
TELEGRAM_BURST_LIMIT      = int(os.getenv("TELEGRAM_BURST_LIMIT", "30"))

# ── Quality Gates & Self-Improvement (Faz 12.1) ──────────────
QUALITY_PASS_THRESHOLD            = float(os.getenv("QUALITY_PASS_THRESHOLD", "0.85"))
ENABLE_AUTONOMOUS_IMPROVEMENT     = os.getenv("ENABLE_AUTONOMOUS_IMPROVEMENT", "true").lower() == "true"
IMPROVEMENT_AUTO_APPLY_THRESHOLD  = float(os.getenv("IMPROVEMENT_AUTO_APPLY_THRESHOLD", "0.8"))
