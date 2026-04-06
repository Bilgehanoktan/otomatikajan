"""
Merkezi test izolasyon yöneticisi.

Amaç:
- Gerçek paket kuruluysa asla stub enjekte etme
- Gerçek paket yoksa minimal ama yeterli stub sağlama
- Özellikle Celery/Telegram gibi opsiyonel bağımlılıklar için import-time çöküşü önleme
"""
from __future__ import annotations

import importlib.util
import os
import sys
import types
from typing import Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_installed_stubs: list[str] = []


def _module_exists(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def _register_module(name: str, module: types.ModuleType) -> None:
    sys.modules[name] = module
    if name not in _installed_stubs:
        _installed_stubs.append(name)


def _install_stub_if_missing(name: str, factory: Callable[[], types.ModuleType] | None = None) -> bool:
    if name in sys.modules or _module_exists(name):
        return False
    mod = factory() if factory else types.ModuleType(name)
    _register_module(name, mod)
    return True


def _cleanup_test_stubs() -> None:
    for name in list(_installed_stubs):
        sys.modules.pop(name, None)
    _installed_stubs.clear()


# ---- Celery stub ---------------------------------------------------------

def _make_celery_stub() -> types.ModuleType:
    mod = types.ModuleType("celery")

    class _DummyTask:
        def __init__(self, func=None, name: str = ""):
            self.func = func
            self.name = name or getattr(func, "__name__", "task")
            self.request = types.SimpleNamespace(retries=0)

        def __call__(self, *args, **kwargs):
            if self.func is None:
                return None
            return self.func(*args, **kwargs)

        def apply_async(self, *args, **kwargs):
            return types.SimpleNamespace(id="stub-task-id", state="PENDING")

        def delay(self, *args, **kwargs):
            return self.apply_async(args=args, kwargs=kwargs)

        def retry(self, exc=None, countdown=None):
            raise exc if exc else RuntimeError("retry requested")

    class _Conf(dict):
        def __getattr__(self, item):
            try:
                return self[item]
            except KeyError as exc:
                raise AttributeError(item) from exc

        def __setattr__(self, key, value):
            self[key] = value

    class _Signal:
        """Celery sinyal stub'ı — connect() dekoratörünü destekler."""
        def __init__(self):
            self._handlers = []

        def connect(self, fn=None, **kwargs):
            if fn is None:
                def decorator(func):
                    self._handlers.append(func)
                    return func
                return decorator
            self._handlers.append(fn)
            return fn

    class Celery:
        def __init__(self, *args, **kwargs):
            self.conf = _Conf(beat_schedule={})
            self.on_after_finalize = _Signal()
            self.on_after_configure = _Signal()

        def task(self, *dargs, **dkwargs):
            bind = dkwargs.get("bind", False)
            name = dkwargs.get("name", "")

            def decorator(func):
                if bind:
                    def bound(*args, **kwargs):
                        task_self = _DummyTask(func, name=name)
                        return func(task_self, *args, **kwargs)
                    wrapped = _DummyTask(bound, name=name)
                else:
                    wrapped = _DummyTask(func, name=name)
                wrapped.apply_async = lambda *a, **kw: types.SimpleNamespace(id="stub-task-id", state="PENDING")
                wrapped.delay = lambda *a, **kw: wrapped.apply_async(args=a, kwargs=kw)
                return wrapped

            return decorator

        def send_task(self, *args, **kwargs):
            return types.SimpleNamespace(id="stub-task-id", state="PENDING")

    mod.Celery = Celery
    mod.Task = _DummyTask

    utils_mod = types.ModuleType("celery.utils")
    log_mod = types.ModuleType("celery.utils.log")

    class _Logger:
        def info(self, *a, **kw):
            pass

        def warning(self, *a, **kw):
            pass

        def error(self, *a, **kw):
            pass

        def debug(self, *a, **kw):
            pass

    log_mod.get_task_logger = lambda name=None: _Logger()

    schedules_mod = types.ModuleType("celery.schedules")
    schedules_mod.crontab = lambda *a, **kw: {"args": a, "kwargs": kw}

    signals_mod = types.ModuleType("celery.signals")
    signals_mod.setup_logging = _Signal()
    signals_mod.after_setup_logger = _Signal()

    result_mod = types.ModuleType("celery.result")

    class AsyncResult:
        def __init__(self, task_id="stub-task-id"):
            self.id = task_id
            self.state = "PENDING"
            self.status = "PENDING"
            self.result = None

    result_mod.AsyncResult = AsyncResult

    _register_module("celery.utils", utils_mod)
    _register_module("celery.utils.log", log_mod)
    _register_module("celery.schedules", schedules_mod)
    _register_module("celery.signals", signals_mod)
    _register_module("celery.result", result_mod)
    return mod


# ---- Telegram stub -------------------------------------------------------

def _make_telegram_stub() -> types.ModuleType:
    mod = types.ModuleType("telegram")
    mod.Update = type("Update", (), {})
    mod.Bot = type("Bot", (), {"__init__": lambda self, *a, **kw: None})

    ext_mod = types.ModuleType("telegram.ext")
    ext_mod.Application = type("Application", (), {})
    ext_mod.ApplicationBuilder = type(
        "ApplicationBuilder",
        (),
        {
            "token": lambda self, *a, **kw: self,
            "build": lambda self: types.SimpleNamespace(add_handler=lambda *a, **kw: None),
        },
    )
    ext_mod.CommandHandler = type("CommandHandler", (), {"__init__": lambda self, *a, **kw: None})
    ext_mod.ContextTypes = types.SimpleNamespace(DEFAULT_TYPE=object)
    ext_mod.MessageHandler = type("MessageHandler", (), {"__init__": lambda self, *a, **kw: None})
    ext_mod.filters = types.SimpleNamespace(TEXT=object(), COMMAND=object())

    _register_module("telegram.ext", ext_mod)
    return mod


_STUB_FACTORIES: dict[str, Callable[[], types.ModuleType] | None] = {
    "asyncpg": None,
    "celery": _make_celery_stub,
    "redis": None,
    "telegram": _make_telegram_stub,
}

# STUB_LEVEL: "none" | "warn" | "aggressive"
STUB_LEVEL = os.getenv("TEST_STUB_LEVEL", "warn").lower()

from config import is_dev

if STUB_LEVEL != "none":
    for _mod_name, _factory in _STUB_FACTORIES.items():
        if _install_stub_if_missing(_mod_name, _factory):
            # FAZ 12 HARDENING: Sadece development modunda stub'a izin ver.
            # Test veya Production modunda gerçek paketlerin eksikliği KRİTİK hatadır.
            if not is_dev and _mod_name in ("celery", "telegram", "asyncpg"):
                raise ImportError(
                    f"\n[CRITICAL TEST FAILURE] '{_mod_name}' paketi eksik! "
                    f"APP_ENV={os.getenv('APP_ENV')} modunda stub kullanılamaz. "
                    f"Lütfen 'pip install -r requirements.txt' komutunu çalıştırın."
                )
            
            if STUB_LEVEL == "warn":
                print(f"\n[STUB WARNING] '{_mod_name}' paketi bulunamadı, stub kullanılıyor. Bu gerçek hataları maskeleyebilir!")


def fresh_import(module_name: str):
    """
    Modülü cache'den düşürüp temiz import eder.
    Özellikle config / auth gibi env'e duyarlı modüller için gerekli.
    """
    import importlib
    import sys
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def fresh_import_many(*module_names: str):
    """
    Birden fazla modülü cache'den düşürür.
    """
    import sys
    for name in module_names:
        sys.modules.pop(name, None)

def pytest_sessionfinish(session, exitstatus):
    """Tüm testler bittiğinde DB bağlantılarını temizle (Hardening)."""
    try:
        import asyncio
        from packages.persistence.session import close_db
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                pass
            else:
                asyncio.run(close_db())
        except Exception:
            asyncio.run(close_db())
    except Exception:
        pass
