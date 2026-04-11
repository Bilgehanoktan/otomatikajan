"""
Async PostgreSQL Bağlantı Yönetimi
SQLAlchemy 2.x async engine + session factory
"""
import asyncio
import os
import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from packages.persistence.models import Base
from packages.observability.logging import get_logger
logger = get_logger("db.session")

# Repair modelleri Base.metadata'ya kayıt için import edilmeli
try:
    import packages.persistence.models.repair_models  # noqa: F401 — tablo tanımlarını Base'e ekler
except Exception as e:
    logger.warning(f"Repair modelleri yuklenemedi: {e}")

from config import DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT

# ── Lazy Engine — import-time crash önlenir (asyncpg yoksa) ───
_engine = None
_async_session_factory = None
_last_loop = None
_lock = threading.Lock()


def get_engine():
    global _engine, _last_loop
    curr_active_loop = None
    try:
        curr_active_loop = asyncio.get_running_loop()
    except RuntimeError:
        pass

    # Eğer engine yoksa VEYA mevcut loop değişmişse (Celery/Asyncio mismatch) yenile
    if _engine is None or (curr_active_loop is not None and _last_loop is not curr_active_loop):
        with _lock:
            # Re-check under lock
            if _engine is None or (curr_active_loop is not None and _last_loop is not curr_active_loop):
                logger.debug(f"SQLAlchemy: Creating engine for loop {id(curr_active_loop)} (URL: {DATABASE_URL.split('@')[-1]})")
                try:
                    # SRE Hardening: Provider-aware connect_args (Faz 12.1)
                    connect_args = {}
                    if "postgresql" in DATABASE_URL:
                        connect_args = {
                            "command_timeout": 60,
                            "server_settings": {"search_path": "public"}
                        }
                    
                    _engine = create_async_engine(
                        DATABASE_URL,
                        pool_size=DB_POOL_SIZE,
                        max_overflow=DB_MAX_OVERFLOW,
                        pool_timeout=DB_POOL_TIMEOUT,
                        pool_pre_ping=True,
                        echo=False,
                        connect_args=connect_args
                    )
                    # Asyncio task başlatma yerine sessiz kal, init_db zaten yapılacak
                    pass
                except Exception as e:
                    # ── PRODUCTION GUARD: SQLite üretimde kabul edilemez ──
                    app_env = os.environ.get("APP_ENV", "development").lower()
                    if app_env == "production":
                        logger.critical(
                            f"FATAL: PostgreSQL bağlantısı başarısız ve APP_ENV=production. "
                            f"SQLite fallback üretimde devre dışı. Hata: {e}"
                        )
                        raise RuntimeError(
                            "PostgreSQL connection failed in production. "
                            "SQLite fallback is disabled for data safety. "
                            "Please fix DATABASE_URL."
                        ) from e
                    
                    logger.warning(f"SQLAlchemy: Ana DB (Postgres) bağlantısı kurulamadı: {e}. SQLite Fallback aktif ediliyor.")
                    # Fallback to Local SQLite
                    sqlite_url = "sqlite+aiosqlite:///./runtime/data/cortex_local.db"
                    _engine = create_async_engine(sqlite_url)
                    # Explicitly track degraded state
                    global _DB_DEGRADED
                    _DB_DEGRADED = True
                
                _last_loop = curr_active_loop
                if curr_active_loop:
                    logger.info("SQLAlchemy: Yeni event loop algılandı, engine yenilendi.")
    return _engine


def _get_session_factory():
    global _async_session_factory
    engine = get_engine()
    
    # Engine yenilenmiş olabilir, factory'i de kontrol et
    if _async_session_factory is None or _async_session_factory.kw["bind"] is not engine:
        with _lock:
            if _async_session_factory is None or _async_session_factory.kw["bind"] is not engine:
                _async_session_factory = async_sessionmaker(
                    engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                )
    return _async_session_factory


class _LazySessionLocal:
    """AsyncSessionLocal gibi davranır ama engine'i lazy oluşturur."""
    def __call__(self):
        return _get_session_factory()()

AsyncSessionLocal = _LazySessionLocal()
async_session = AsyncSessionLocal  # Faz 12.1/12.2 Geriye Dönük Uyumluluk


# Celery Fork Safety: Worker process baslatildiginda engine'i temizle
# Bu sayede her worker kendi pool'una sahip olur.
try:
    from celery.signals import worker_process_init
    @worker_process_init.connect
    def on_worker_process_init(**kwargs):
        global _engine, _async_session_factory
        _engine = None
        _async_session_factory = None
        logger.info("Celery Worker: Engine ve Session Factory sifirlandi (fork-safe).")
except ImportError:
    pass





# Public engine access
_DB_AVAILABLE: bool = False
_DB_DEGRADED:  bool = False
_DB_ERROR:     str  = ""

def db_error() -> str:
    """Son DB hata mesajını döndür."""
    return _DB_ERROR

async def is_db_available() -> bool:
    """DB bağlantısını aktif olarak test eder (SRE Hardening)."""
    return await verify_db_connection()

async def verify_db_connection() -> bool:
    """DB bağlantısını gerçekten test et (Async)."""
    global _DB_AVAILABLE, _DB_ERROR
    try:
        # P0: Timeout — veritabanı asılı kalırsa orkestrasyonun kilitlenmesini önler
        return await asyncio.wait_for(_verify_core(), timeout=2.0)
    except Exception as e:
        _DB_ERROR = str(e)
        _DB_AVAILABLE = False
        return False

async def _verify_core() -> bool:
    global _DB_AVAILABLE
    try:
        engine = get_engine()
        if engine is None:
            return False
        async with engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        _DB_AVAILABLE = True
        return True
    except Exception:
        return False


async def init_db():
    """DB başlatma stratejisi:
    - development/test: create_all ile otomatik tablo oluşturma
    - production: create_all ÇALIŞMAZ — alembic upgrade head gerekir
    """
    import os
    try:
        from config import APP_ENV
    except ImportError:
        APP_ENV = os.getenv("APP_ENV", "development")

    global _DB_AVAILABLE, _DB_ERROR, _engine
    _DB_AVAILABLE = False
    
    async def run_init(target_engine):
        is_sqlite = "sqlite" in str(target_engine.url)
        async with target_engine.begin() as conn:
            if not is_sqlite:
                try:
                    from sqlalchemy import text
                    await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                except Exception as e:
                    logger.warning(f"pgvector uzantısı oluşturulamadı: {e}")

            import packages.persistence.models
            import packages.persistence.models.repair_models
            await conn.run_sync(Base.metadata.create_all)
            _log_msg = "SQLite Fallback Hazır" if is_sqlite else "Postgres Hazır"
            logger.info(f"OK: Veritabanı tabloları hazır ({APP_ENV} - {_log_msg}).")
            return True

    try:
        engine = get_engine()
        await run_init(engine)
        _DB_AVAILABLE = True
        _DB_ERROR = ""
    except Exception as e:
        _DB_ERROR = str(e)
        if "sqlite" not in str(get_engine().url):
            logger.warning(f"Postgres bağlantısı başlatma sırasında başarısız oldu: {e}. SQLite'a zorlanıyor...")
            sqlite_url = "sqlite+aiosqlite:///./runtime/data/cortex_local.db"
            _engine = create_async_engine(sqlite_url)
            try:
                await run_init(_engine)
                _DB_AVAILABLE = True
                _DB_ERROR = ""
                return
            except Exception as e2:
                _DB_ERROR = f"SQLite Fallback da başarısız: {e2}"
        
        logger.error(f"[ERR] Kritik DB Başlatma Hatası: {_DB_ERROR}")
        # Uygulama çökmesin ama degraded mode'da kalsın

def is_db_degraded() -> bool:
    """Sistemin fallback (SQLite) modunda olup olmadığını döner."""
    return _DB_DEGRADED


async def close_db():
    await _get_engine().dispose()
    print("👋 Veritabanı bağlantısı kapatıldı.")


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Sistem genelinde güvenli veritabanı oturumu sağlar."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Sadece aktif bir işlem varsa commit yap
            if session.in_transaction():
                await session.commit()
        except Exception as e:
            # Kritik: Hata anında derhal geri al
            try:
                if session.is_active:
                    await session.rollback()
            except Exception as rb_err:
                logger.error(f"DB Rollback hatası (get_db): {rb_err}")
            
            from sqlalchemy.exc import IntegrityError, PendingRollbackError
            if isinstance(e, (IntegrityError, PendingRollbackError)):
                 logger.warning(f"DB Oturum Çakışması/Zehirlenmesi Yakalandı: {e}")
            else:
                 logger.error(f"DB Kritik Hata: {e}", exc_info=True)
            raise
        finally:
            # Oturumu kapatmadan önce temizlik
            await session.close()


async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Depends enjeksiyonu — async generator olmalı."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            if session.in_transaction():
                await session.commit()
        except Exception as e:
            # SRE Hardening: Hata anında oturumu temizle
            try:
                if session.is_active:
                    await session.rollback()
            except Exception as rb_err:
                logger.error(f"DB Rollback hatası (get_db_dep): {rb_err}")
            
            # Log & Re-raise
            from sqlalchemy.exc import IntegrityError, PendingRollbackError
            if isinstance(e, (IntegrityError, PendingRollbackError)):
                logger.warning(f"DB Bağımlılık Oturum Zehirlenmesi: {e}")
            else:
                logger.error(f"DB İşlem Hatası: {e}")
            raise
        finally:
            await session.close()


session_scope = get_db

# ── Redis (Faz 12.1) ──────────────────────────────────
_redis_instance = None

def get_redis_client():
    """Redis bağlantısını döner. (SRE Hardening: Host/Docker tespiti)"""
    global _redis_instance
    if _redis_instance is not None:
        return _redis_instance

    try:
        import redis.asyncio as redis
        from config import REDIS_URL
        
        # SRE: URL tespiti ve normalizasyon
        url = REDIS_URL
        if not url:
            # Fallback zinciri
            if os.getenv("DOCKER_CONTAINER", "false").lower() == "true":
                url = "redis://redis:6379/0"
            else:
                url = "redis://127.0.0.1:6380/0"

        # Docker dışında mıyız testi (Socket check)
        if "redis:6379" in url:
            import socket
            try:
                # Docker içinde değilsek (redis ismi çözülemiyorsa) localhost kullan
                socket.gethostbyname("redis")
            except socket.gaierror:
                url = url.replace("redis:6379", "127.0.0.1:6380")
                logger.debug(f"Redis: Host mode detected (DNS fail), using 127.0.0.1:6380")
        
        # SRE Robustness: URL icinde localhost gecerse ama 6379 ise ve baglanamazsa 6380 dene (opsiyonel ama guvenli)
        
        logger.info(f"Redis: Connecting to {url}")
        _redis_instance = redis.from_url(
            url, 
            decode_responses=True,
            socket_connect_timeout=2.0,
            retry_on_timeout=True
        )
        return _redis_instance
    except Exception as e:
        logger.warning(f"Redis baglantisi kurulamadi ({url}): {e}")
        return None

