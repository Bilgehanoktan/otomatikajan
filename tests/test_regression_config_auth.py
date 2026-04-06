import importlib
import os
import sys
from pathlib import Path

import pytest


def _fresh_import(module_name: str):
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def _fresh_import_pair():
    sys.modules.pop("apps.api.routers.auth.jwt_auth", None)
    sys.modules.pop("config", None)
    return importlib.import_module("apps.api.routers.auth.jwt_auth")


def test_config_should_prefer_env_local_over_env(tmp_path, monkeypatch):
    """
    Yeni config davranışı:
    .env.local, .env'i override etmeli.
    """
    (tmp_path / ".env").write_text(
        "APP_ENV=development\nJWT_SECRET=base_secret_value\n",
        encoding="utf-8",
    )
    (tmp_path / ".env.local").write_text(
        "JWT_SECRET=override_secret_value\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    sys.modules.pop("config", None)
    config = importlib.import_module("config")

    assert config.JWT_SECRET == "override_secret_value"
    assert config.APP_ENV == "development"


def test_jwt_auth_should_fail_in_production_when_secret_missing(tmp_path, monkeypatch):
    """
    Production'da JWT_SECRET boşsa import aşamasında hard-fail vermeli.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        _fresh_import_pair()


def test_jwt_auth_should_fail_in_production_when_secret_too_short(tmp_path, monkeypatch):
    """
    Production'da kısa JWT secret reddedilmeli.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "short-secret")

    with pytest.raises(RuntimeError, match="64 karakter"):
        _fresh_import_pair()


@pytest.mark.asyncio
async def test_auth_service_should_fail_without_bcrypt_in_production(tmp_path, monkeypatch):
    """
    Production'da bcrypt yoksa register akışı sessiz fallback yapmamalı.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "a" * 64)

    jwt_auth = _fresh_import_pair()

    monkeypatch.setattr(jwt_auth, "_BCRYPT_OK", False, raising=False)
    monkeypatch.setattr(jwt_auth, "_bcrypt", None, raising=False)

    class DummyResult:
        def scalar_one_or_none(self):
            return None

    class DummyDB:
        async def execute(self, *args, **kwargs):
            return DummyResult()

    svc = jwt_auth.AuthService()

    with pytest.raises(RuntimeError, match="bcrypt"):
        await svc.register(
            DummyDB(),
            email="test@example.com",
            password="12345678",
        )
