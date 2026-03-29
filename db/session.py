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

from db.models import Base
from observability.logging import get_logger
logger = get_logger("db.session")

# Repair modelleri Base.metadata'ya kayıt için import edilmeli
try:
    import db.repair_models  # noqa: F401 — tablo tanımlarını Base'e ekler
except Exception as e:
    logger.warning(f"Repair modelleri yuklenemedi: {e}")

from config import DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT

# ── Lazy Engine — import-time crash önlenir (asyncpg yoksa) ───
_engine = None
_async_session_factory = None
_last_loop = None
_lock = threading.Lock()


def _get_engine():
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
                _engine = create_async_engine(
                    DATABASE_URL,
                    pool_size=DB_POOL_SIZE,
                    max_overflow=DB_MAX_OVERFLOW,
                    pool_timeout=DB_POOL_TIMEOUT,
                    pool_pre_ping=True,
                    echo=False,
                    connect_args={
                        "command_timeout": 60,
                        "server_settings": {"search_path": "public"}
                    }
                )
                _last_loop = curr_active_loop
                if curr_active_loop:
                    logger.info("SQLAlchemy: Yeni event loop algılandı, engine yenilendi.")
    return _engine


def _get_session_factory():
    global _async_session_factory
    engine = _get_engine()
    
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






# ── DB Durumu — degraded mode takibi ─────────────────────
_DB_AVAILABLE: bool = False
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
        engine = _get_engine()
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

    global _DB_AVAILABLE, _DB_ERROR
    _DB_AVAILABLE = False
    try:
        engine = _get_engine()
        async with engine.begin() as conn:
            # pgvector uzantısı — hata olursa devam et (opsiyonel)
            try:
                await conn.execute(__import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS vector"))
            except Exception as e:
                logger.warning(f"pgvector uzantısı oluşturulamadı (vektör hafıza kısıtlı olabilir): {e}")

            if APP_ENV == "production":
                # Production'da create_all kullanma — Alembic migration'a güven
                await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
                print("OK: DB bağlantısı doğrulandı (production).")
                _DB_AVAILABLE = True
                _DB_ERROR = ""
            else:
                # Development/test: create_all
                await conn.run_sync(Base.metadata.create_all)
                print(f"OK: Veritabanı tabloları hazır ({APP_ENV} modu).")
                _DB_AVAILABLE = True
                _DB_ERROR = ""
    except Exception as e:
        _DB_ERROR = str(e)
        logger.error(f"[ERR] Kritik DB Bashlatma Hatasi: {e}")
        # Uygulama çökmesin ama degraded mode'da kalsın


async def close_db():
    await _get_engine().dispose()
    print("👋 Veritabanı bağlantısı kapatıldı.")


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Depends ile kullanım için context manager."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_dep() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Depends enjeksiyonu — async generator olmalı."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
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
        
        url = REDIS_URL or "redis://localhost:6379/0"
        
        # SRE: getaddrinfo hatasını önlemek için Windows/Host tarafındaysak 127.0.0.1'e zorla
        if "redis:6379" in url:
            import socket
            try:
                # Docker içinde değilsek (redis ismi çözülemiyorsa) localhost kullan
                socket.gethostbyname("redis")
            except socket.gaierror:
                url = url.replace("redis:6379", "127.0.0.1:6380") # docker-compose-mapped port
                logger.debug(f"Redis: 'redis' hostu bulunamadı, localhost:6380'e (host mode) yönlendiriliyor.")
        
        _redis_instance = redis.from_url(url, decode_responses=True)
        return _redis_instance
    except Exception as e:
        logger.warning(f"Redis baglantisi kurulamadi: {e}")
        return None
