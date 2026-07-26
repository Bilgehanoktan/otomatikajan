"""
BilgeAPI Smoke Test
====================
Quick validation that BilgeAPI is running and core endpoints are accessible.

Usage:
    python scripts/smoke_bilgeapi.py
    python scripts/smoke_bilgeapi.py --base-url http://localhost:8100
    python scripts/smoke_bilgeapi.py --api-key dev-test-key-001
"""

import argparse
import sys
import urllib.error
import urllib.request


def smoke_test(base_url: str, api_key: str | None = None) -> bool:
    """Run smoke tests against BilgeAPI endpoints."""
    results: list[tuple[str, str, bool, str]] = []

    def check(
        name: str,
        method: str,
        path: str,
        expected_status: int = 200,
        headers: dict | None = None,
        body: bytes | None = None,
    ) -> bool:
        url = f"{base_url.rstrip('/')}{path}"
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.scheme not in ("http", "https"):
            raise ValueError(f"Forbidden URL scheme: {parsed_url.scheme}")
        req = urllib.request.Request(url, method=method, headers=headers or {})
        if body:
            req.data = body
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
                status = resp.status
                resp.read()
                passed = status == expected_status
                results.append((name, f"{method} {path}", passed, f"HTTP {status}"))
                return passed
        except urllib.error.HTTPError as e:
            status = e.code
            passed = status == expected_status
            results.append((name, f"{method} {path}", passed, f"HTTP {status}"))
            return passed
        except Exception as e:
            results.append((name, f"{method} {path}", False, str(e)[:60]))
            return False

    check("Health", "GET", "/health", 200)
    check("Docs (Swagger UI)", "GET", "/docs", 200)
    check("OpenAPI JSON", "GET", "/openapi.json", 200)

    if api_key:
        check(
            "Catalog (with key)",
            "GET",
            "/v1/catalog",
            200,
            headers={"X-API-Key": api_key},
        )
        check(
            "Incidents list (with key)",
            "GET",
            "/v1/incidents",
            200,
            headers={"X-API-Key": api_key},
        )
        check("Auth enforcement (no key -> 401/403)", "GET", "/v1/incidents", 401)
    else:
        check("Catalog (no key)", "GET", "/v1/catalog")

    print()
    print("=" * 70)
    print(f"  BilgeAPI Smoke Test - {base_url}")
    print("=" * 70)

    total = len(results)
    passed = sum(1 for r in results if r[2])
    failed = total - passed

    for name, endpoint, ok, detail in results:
        status_icon = "[OK]" if ok else "[FAIL]"
        print(f"  {status_icon:<6} {name:<35} {endpoint:<25} {detail}")

    print("-" * 70)
    print(f"  Result: {passed}/{total} passed", end="")
    if failed:
        print(f" ({failed} FAILED)")
    else:
        print(" - ALL PASSED")
    print("=" * 70)
    print()

    return failed == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="BilgeAPI Smoke Test")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8100",
        help="Base URL of BilgeAPI (default: http://localhost:8100)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key for authenticated endpoints",
    )
    args = parser.parse_args()

    success = smoke_test(args.base_url, args.api_key)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
