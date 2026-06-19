import hmac
import hashlib
import socket
import ipaddress
import logging
from urllib.parse import urlparse
import httpx
from apps.bilgeapi.config import settings

logger = logging.getLogger("bilgeapi.webhook")

def is_ssrf_safe(url: str, allow_private: bool = False) -> bool:
    """
    Checks if a URL is safe against SSRF attacks.
    Resolves hostname to IP addresses and verifies that they do not belong to:
    - loopback / localhost (127.0.0.0/8, ::1)
    - private subnets (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, fc00::/7)
    - link-local (169.254.0.0/16, fe80::/10)
    - unspecified (0.0.0.0, ::)
    - multicast subnets
    - Cloud Metadata Service IP (169.254.169.254)
    """
    # Enforce production constraint: allow_private must be False in production
    if settings.APP_ENV == "production":
        allow_private = False

    if allow_private:
        return True

    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False

        host = parsed.hostname
        if not host:
            return False

        # Resolve hostname to all associated IPs
        addr_info = socket.getaddrinfo(host, None)
    except Exception as e:
        logger.warning(f"SSRF Check: Hostname resolution failed for {url}: {e}")
        return False

    for family, socktype, proto, canonname, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
            # Explicitly block cloud metadata IP
            if str(ip) == "169.254.169.254":
                return False

            # Block loopback, private, link-local, multicast, unspecified
            if (ip.is_loopback or 
                ip.is_private or 
                ip.is_link_local or 
                ip.is_multicast or 
                ip.is_unspecified):
                return False
        except ValueError:
            return False

    return True

def generate_signature(payload_str: str, secret: str) -> str:
    """
    Computes HMAC-SHA256 signature of the payload using the secret key.
    """
    return hmac.new(
        secret.encode("utf-8"),
        payload_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

class WebhookDispatcher:
    """
    Handles sending signed HTTP POST webhooks with SSRF guard, timeout, and redirect checks.
    """
    def __init__(self):
        # Enforce max_redirects = 0 using httpx config
        self.client = httpx.AsyncClient(
            timeout=settings.BILGEAPI_WEBHOOK_TIMEOUT,
            follow_redirects=False,
            max_redirects=0
        )

    async def dispatch(self, url: str, payload: dict, signature_secret: str, idempotency_key: str, timestamp: str) -> httpx.Response:
        """
        Dispatches a signed webhook payload.
        """
        allow_private = settings.BILGEAPI_ALLOW_PRIVATE_WEBHOOKS
        if not is_ssrf_safe(url, allow_private=allow_private):
            raise ValueError(f"SSRF Guard: Target URL {url} is forbidden.")

        import json
        payload_str = json.dumps(payload) if isinstance(payload, dict) else str(payload)
        signature = generate_signature(payload_str, signature_secret)

        headers = {
            "Content-Type": "application/json",
            "X-BilgeAPI-Signature": signature,
            "X-BilgeAPI-Timestamp": timestamp,
            "X-BilgeAPI-Idempotency-Key": idempotency_key
        }

        # follow_redirects=False explicitly passed to be safe
        response = await self.client.post(url, content=payload_str, headers=headers, follow_redirects=False)
        return response

    async def close(self):
        await self.client.aclose()
