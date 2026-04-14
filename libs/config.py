"""
Merkezi Konfigürasyon
─────────────────────
Tüm modüller buradan APP_ENV ve diğer sabitleri okur.
Local run'da .env otomatik yüklenir (main.py de yükler, iki kez zararı yok).

Kullanım:
    from config import APP_ENV, is_dev, is_prod, is_test
"""

import os

QUEUE_BACKEND = os.getenv("QUEUE_BACKEND", "auto").lower()

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
    for name, secret in [("ADMIN_SECRET", ADMIN_SECRET), ("JWT_SECRET", JWT_SECRET)]:
        is_weak = any(tpl in secret for tpl in WEAK_TEMPLATES)
        if is_weak:
            raise RuntimeError(f"{name} üretim ortamı için kabul edilemez (Template eşleşmesi)!")
    
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
        load_dotenv(".env", override=False)
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

# ── Temel ayarlar ─────────────────────────────────────────
DEBUG     = os.getenv("DEBUG", "true" if is_dev else "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if is_dev else "INFO")

# ── Veritabanı URL Tespiti ────────────────────────────────
_raw_db_url = os.getenv("DATABASE_URL", "")

# Docker ortamında mıyız? (Konteyner içi tespiti)
_is_in_docker = os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER", "false").lower() == "true"

if _is_in_docker:
    # Docker içinde '127.0.0.1' veya 'localhost' kullanımı genellikle hatadır (host portuna gitmeye çalışır)
    # Eğer URL'de localhost/127.0.0.1 varsa bunu 'db' olarak değiştir.
    if not _raw_db_url or "127.0.0.1" in _raw_db_url or "localhost" in _raw_db_url:
        # Default veya hatalı localhost URL'sini Docker hiyerarşisine çek
        DATABASE_URL = "postgresql+asyncpg://postgres:postgres@db:5432/ai_company"
    else:
        DATABASE_URL = _raw_db_url
else:
    # Host modunda çalışıyorken env yoksa localhost'a düş
    DATABASE_URL = _raw_db_url or "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/ai_company"

DB_POOL_SIZE   = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
REDIS_URL      = os.getenv("REDIS_URL", "")
JWT_SECRET     = os.getenv("JWT_SECRET", "")
ADMIN_SECRET   = os.getenv("ADMIN_SECRET", "")
MONTHLY_BUDGET = float(os.getenv("MONTHLY_BUDGET_USD", "50.0"))

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",") if o.strip()]
ALLOWED_METHODS = os.getenv("ALLOWED_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS").split(",")
ALLOWED_HEADERS = os.getenv("ALLOWED_HEADERS", "Authorization,Content-Type,X-Trace-ID,X-Requested-With").split(",")

TELEGRAM_BOT_TOKEN     = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ALLOWED_IDS   = os.getenv("TELEGRAM_ALLOWED_IDS", "")
TELEGRAM_ADMIN_IDS      = os.getenv("TELEGRAM_ADMIN_IDS", "")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")

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
QUEUE_BACKEND            = os.getenv("QUEUE_BACKEND", "auto").lower()  # auto|celery|inprocess
QUEUE_DEFAULT            = os.getenv("QUEUE_DEFAULT", "default")
QUEUE_CRITICAL           = os.getenv("QUEUE_CRITICAL", "critical")
QUEUE_BACKGROUND         = os.getenv("QUEUE_BACKGROUND", "background")
QUEUE_DEERFLOW           = os.getenv("QUEUE_DEERFLOW", "deerflow")

# ── DeerFlow Agent Family ────────────────────────────────────
WEAK_TEMPLATES = ["REPLACE_WITH", "your-secret", "123456"]
DEERFLOW_ROLES = ["deerflow_planner", "deerflow_researcher", "deerflow_reviewer", "deerflow_recovery"]
DEERFLOW_WORKER_CONCURRENCY = int(os.getenv("DEERFLOW_WORKER_CONCURRENCY", "2"))

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
