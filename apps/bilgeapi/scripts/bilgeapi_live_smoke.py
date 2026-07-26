"""
Live BilgeAPI smoke test with markdown evidence output.

Examples:
    py -3.13 scripts/bilgeapi_live_smoke.py
    py -3.13 scripts/bilgeapi_live_smoke.py --api-key <key>
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def _request(base_url: str, method: str, path: str, api_key: str | None = None) -> tuple[int | None, str]:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    full_url = f"{base_url.rstrip('/')}{path}"
    parsed_url = urllib.parse.urlparse(full_url)
    if parsed_url.scheme not in ("http", "https"):
        raise ValueError(f"Forbidden URL scheme: {parsed_url.scheme}")
    request = urllib.request.Request(full_url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:  # nosec B310
            content = response.read().decode("utf-8", errors="replace")
            return response.status, content[:500]
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")[:500]
    except Exception as exc:
        return None, str(exc)


def _expected_label(expected: set[int]) -> str:
    return "/".join(str(item) for item in sorted(expected))


def run(base_url: str, api_key: str | None) -> tuple[bool, list[str]]:
    catalog_expected = {200} if api_key else {200, 401, 403}
    checks = [
        ("Health", "GET", "/health", {200}, None),
        ("Root", "GET", "/", {200, 404}, None),
        ("Metrics", "GET", "/metrics", {200, 401, 403}, None),
        ("Swagger docs", "GET", "/docs", {200}, None),
        ("OpenAPI JSON", "GET", "/openapi.json", {200}, None),
        ("Catalog", "GET", "/v1/catalog", catalog_expected, api_key),
    ]

    rows = []
    for name, method, path, expected, key in checks:
        status, body = _request(base_url, method, path, key)
        ok = status in expected
        rows.append((name, f"{method} {path}", _expected_label(expected), status, ok, body.replace("\n", " ")[:120]))

    passed = all(row[4] for row in rows)
    lines = [
        "# BilgeAPI Phase 15 Live Smoke Evidence",
        "",
        f"- Base URL: `{base_url}`",
        f"- Generated at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Authenticated catalog check: `{'enabled' if api_key else 'skipped/no key'}`",
        "",
        "| Check | Endpoint | Expected | Actual | Result | Sample |",
        "|---|---|---:|---:|---:|---|",
    ]
    for name, endpoint, expected, actual, ok, sample in rows:
        lines.append(f"| {name} | `{endpoint}` | {expected} | {actual} | {'PASS' if ok else 'FAIL'} | `{sample}` |")
    lines.extend(["", f"Overall: {'PASS' if passed else 'FAIL'}"])
    return passed, lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Run live BilgeAPI smoke checks and write evidence.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8100")
    parser.add_argument("--api-key")
    parser.add_argument("--evidence", default="docs/evidence/bilgeapi_phase15_live_smoke.md")
    args = parser.parse_args()

    ok, lines = run(args.base_url, args.api_key)
    output = "\n".join(lines) + "\n"
    print(output)
    evidence_path = Path(args.evidence)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(output, encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
