"""
BilgeAPI API key admin CLI.

Examples:
    py -3.13 scripts/bilgeapi_api_key_admin.py create --admin-api-key <key> --role OPERATOR --description "worker"
    py -3.13 scripts/bilgeapi_api_key_admin.py list --admin-api-key <key>
    py -3.13 scripts/bilgeapi_api_key_admin.py revoke --admin-api-key <key> --key-id key_123 --reason "rotation"
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def _request_json(base_url: str, method: str, path: str, admin_api_key: str, payload: dict | None = None) -> dict | list:
    body = None
    headers = {
        "Accept": "application/json",
        "X-API-Key": admin_api_key,
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            content = response.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {detail}") from exc


def _print_json(data: dict | list) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def create_key(args: argparse.Namespace) -> None:
    payload = {
        "role": args.role,
        "description": args.description,
        "tenant_id": args.tenant_id,
        "expires_in_days": args.expires_in_days,
        "quota_daily": args.quota_daily,
        "quota_monthly": args.quota_monthly,
    }
    payload = {key: value for key, value in payload.items() if value is not None}
    data = _request_json(args.base_url, "POST", "/v1/admin/api-keys", args.admin_api_key, payload)
    print("Plaintext key is shown once. Store it in a secrets manager now.", file=sys.stderr)
    _print_json(data)


def list_keys(args: argparse.Namespace) -> None:
    _print_json(_request_json(args.base_url, "GET", "/v1/admin/api-keys", args.admin_api_key))


def get_key(args: argparse.Namespace) -> None:
    _print_json(_request_json(args.base_url, "GET", f"/v1/admin/api-keys/{args.key_id}", args.admin_api_key))


def revoke_key(args: argparse.Namespace) -> None:
    payload = {"reason": args.reason}
    _print_json(_request_json(args.base_url, "POST", f"/v1/admin/api-keys/{args.key_id}/revoke", args.admin_api_key, payload))


def update_quota(args: argparse.Namespace) -> None:
    payload = {"quota_daily": args.quota_daily, "quota_monthly": args.quota_monthly}
    _print_json(_request_json(args.base_url, "PUT", f"/v1/admin/api-keys/{args.key_id}/quota", args.admin_api_key, payload))


def quota_usage(args: argparse.Namespace) -> None:
    _print_json(_request_json(args.base_url, "GET", f"/v1/admin/api-keys/{args.key_id}/quota-usage", args.admin_api_key))


def _base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage BilgeAPI database-backed API keys.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8100", help="BilgeAPI base URL")
    parser.add_argument("--admin-api-key", required=True, help="Admin or SOVEREIGN_PRIME API key")
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = _base_parser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a new API key")
    create.add_argument("--role", required=True, choices=["ADMIN", "OPERATOR", "AUDIT_OBSERVER", "SOVEREIGN_PRIME"])
    create.add_argument("--description")
    create.add_argument("--tenant-id")
    create.add_argument("--expires-in-days", type=int)
    create.add_argument("--quota-daily", type=int)
    create.add_argument("--quota-monthly", type=int)
    create.set_defaults(func=create_key)

    list_cmd = subparsers.add_parser("list", help="List API key metadata")
    list_cmd.set_defaults(func=list_keys)

    get_cmd = subparsers.add_parser("get", help="Get one API key metadata record")
    get_cmd.add_argument("--key-id", required=True)
    get_cmd.set_defaults(func=get_key)

    revoke = subparsers.add_parser("revoke", help="Revoke an API key")
    revoke.add_argument("--key-id", required=True)
    revoke.add_argument("--reason", required=True)
    revoke.set_defaults(func=revoke_key)

    quota = subparsers.add_parser("quota", help="Update API key quota")
    quota.add_argument("--key-id", required=True)
    quota.add_argument("--quota-daily", type=int)
    quota.add_argument("--quota-monthly", type=int)
    quota.set_defaults(func=update_quota)

    usage = subparsers.add_parser("quota-usage", help="Read API key quota usage")
    usage.add_argument("--key-id", required=True)
    usage.set_defaults(func=quota_usage)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
