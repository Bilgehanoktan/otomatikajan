"""Fail-closed configuration for Meta Graph API integrations."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlparse

REDACTED = "***REDACTED***"
DEFAULT_GRAPH_BASE_URL = "https://graph.instagram.com"
ALLOWED_GRAPH_HOSTS = frozenset({"graph.instagram.com", "graph.facebook.com"})
ACCOUNT_ID_PATTERN = re.compile(r"^[0-9]{5,40}$")
API_VERSION_PATTERN = re.compile(r"^v[0-9]{1,3}\.[0-9]{1,2}$")
MIN_ACCESS_TOKEN_LENGTH = 20
MIN_APP_SECRET_LENGTH = 32


class ConfigurationError(ValueError):
    """Raised when required Meta configuration is absent or unsafe."""


@dataclass(frozen=True, repr=False)
class MetaSettings:
    """Validated Meta credentials without plaintext repr output."""

    account_id: str
    access_token: str
    app_secret: str
    verify_token: str
    api_version: str
    graph_base_url: str = DEFAULT_GRAPH_BASE_URL

    def __post_init__(self) -> None:
        required = {
            "INSTAGRAM_ACCOUNT_ID": self.account_id,
            "INSTAGRAM_ACCESS_TOKEN": self.access_token,
            "META_APP_SECRET": self.app_secret,
            "META_WEBHOOK_VERIFY_TOKEN": self.verify_token,
            "META_API_VERSION": self.api_version,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise ConfigurationError(f"Eksik Meta ayarı: {', '.join(missing)}")
        if not ACCOUNT_ID_PATTERN.fullmatch(self.account_id):
            raise ConfigurationError("INSTAGRAM_ACCOUNT_ID yalnız sayısal bir Meta kimliği olmalı")
        if len(self.access_token) < MIN_ACCESS_TOKEN_LENGTH:
            raise ConfigurationError("INSTAGRAM_ACCESS_TOKEN güvenli minimum uzunluğun altında")
        if len(self.app_secret) < MIN_APP_SECRET_LENGTH:
            raise ConfigurationError("META_APP_SECRET en az 32 karakter olmalı")
        if not API_VERSION_PATTERN.fullmatch(self.api_version):
            raise ConfigurationError("META_API_VERSION 'vNN.N' biçiminde olmalı")

        parsed = urlparse(self.graph_base_url)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_GRAPH_HOSTS:
            raise ConfigurationError("META_GRAPH_BASE_URL resmi HTTPS Meta host'u olmalı")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ConfigurationError("META_GRAPH_BASE_URL credential veya query içermemeli")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> MetaSettings:
        """Load required values from an injected mapping or the process environment."""

        source = os.environ if env is None else env
        return cls(
            account_id=source.get("INSTAGRAM_ACCOUNT_ID", ""),
            access_token=source.get("INSTAGRAM_ACCESS_TOKEN", ""),
            app_secret=source.get("META_APP_SECRET", ""),
            verify_token=source.get("META_WEBHOOK_VERIFY_TOKEN", ""),
            api_version=source.get("META_API_VERSION", ""),
            graph_base_url=source.get("META_GRAPH_BASE_URL", DEFAULT_GRAPH_BASE_URL),
        )

    def __repr__(self) -> str:
        """Return an operator-safe representation."""

        return (
            "MetaSettings("
            f"account_id={self.account_id!r}, "
            f"access_token={REDACTED!r}, "
            f"app_secret={REDACTED!r}, "
            f"verify_token={REDACTED!r}, "
            f"api_version={self.api_version!r}, "
            f"graph_base_url={self.graph_base_url!r})"
        )
