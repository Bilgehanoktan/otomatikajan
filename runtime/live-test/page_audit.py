import json
import os
import re
import time
from pathlib import Path
from urllib import request

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "apps" / "refine_control_plane" / "src" / "app"
FRONTEND = os.environ.get("FRONTEND_URL", "http://127.0.0.1:3100")
API = os.environ.get("API_URL", "http://127.0.0.1:8000/api/v1")
OUTPUT = ROOT / "runtime" / "live-test" / "page-audit-results.json"
DEFAULT_AUDIT_EMAIL = "admin@sovereign.agi"
DEFAULT_PASSWORD_FILE = ROOT / "runtime" / "live-test" / ".page-audit-password"
GOTO_TIMEOUT_MS = int(os.environ.get("PAGE_AUDIT_GOTO_TIMEOUT_MS", "12000"))
NETWORK_IDLE_TIMEOUT_MS = int(os.environ.get("PAGE_AUDIT_NETWORK_IDLE_TIMEOUT_MS", "2500"))
BODY_TIMEOUT_MS = int(os.environ.get("PAGE_AUDIT_BODY_TIMEOUT_MS", "1500"))
MAX_ATTEMPTS = int(os.environ.get("PAGE_AUDIT_MAX_ATTEMPTS", "2"))


FALLBACK_SAMPLE_IDS = {
    "axiology/[id]": "index",
    "governor/[id]": "index",
}

DYNAMIC_PARAM_PATTERN = re.compile(r"\[[^/\]]+\]")
TRANSIENT_NAVIGATION_ERRORS = (
    "net::ERR_NETWORK_IO_SUSPENDED",
    "net::ERR_EMPTY_RESPONSE",
    "net::ERR_CONNECTION_REFUSED",
    "net::ERR_CONNECTION_RESET",
)


def _read_dotenv_value(name: str) -> str | None:
    dotenv = ROOT / ".env"
    if not dotenv.exists():
        return None
    for raw_line in dotenv.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip().lstrip("\ufeff")
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == name:
            return value.strip().strip('"').strip("'") or None
    return None


def _config_value(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name) or _read_dotenv_value(name)
        if value:
            return value
    return None


def _read_password_file() -> str | None:
    configured_path = _config_value("AUDIT_LOGIN_PASSWORD_FILE")
    candidates = [Path(configured_path)] if configured_path else []
    candidates.append(DEFAULT_PASSWORD_FILE)
    for path in candidates:
        if path.exists():
            value = path.read_text(encoding="utf-8").strip().lstrip("\ufeff")
            if value:
                return value
    return None


def get_login_credentials() -> tuple[str, str]:
    email = _config_value("AUDIT_LOGIN_EMAIL", "NEXT_PUBLIC_DEV_OPERATOR_EMAIL", "DEV_OPERATOR_EMAIL")
    password = (
        _config_value("AUDIT_LOGIN_PASSWORD", "NEXT_PUBLIC_DEV_OPERATOR_PASSWORD", "DEV_OPERATOR_PASSWORD")
        or _read_password_file()
    )
    if not password:
        raise RuntimeError(
            "Set AUDIT_LOGIN_PASSWORD, NEXT_PUBLIC_DEV_OPERATOR_PASSWORD, DEV_OPERATOR_PASSWORD, "
            "AUDIT_LOGIN_PASSWORD_FILE, or runtime/live-test/.page-audit-password before running page_audit.py."
        )
    return email or DEFAULT_AUDIT_EMAIL, password


def login_token() -> str:
    email, password = get_login_credentials()
    payload = json.dumps({"email": email, "password": password}).encode("utf-8")
    req = request.Request(
        f"{API}/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["access_token"]


def api_get_json(path: str, token: str) -> object:
    req = request.Request(
        f"{API}{path}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _first_record(payload: object) -> dict | None:
    if isinstance(payload, list):
        return payload[0] if payload and isinstance(payload[0], dict) else None
    if not isinstance(payload, dict):
        return None

    for key in ("items", "data", "results"):
        value = payload.get(key)
        if isinstance(value, list) and value and isinstance(value[0], dict):
            return value[0]

    search_results = payload.get("search_results")
    if isinstance(search_results, dict):
        items = search_results.get("items")
        if isinstance(items, list) and items and isinstance(items[0], dict):
            return items[0]

    return None


def _extract_first_value(payload: object, fields: tuple[str, ...] = ("id",)) -> str | None:
    record = _first_record(payload)
    if not record:
        return None
    for field in fields:
        value = record.get(field)
        if value:
            return str(value)
    return None


def _add_live_sample(
    samples: dict[str, str],
    skipped_samples: dict[str, str],
    *,
    route_keys: tuple[str, ...],
    endpoint: str,
    token: str,
    fields: tuple[str, ...] = ("id",),
    empty_reason: str,
) -> None:
    try:
        payload = api_get_json(endpoint, token)
    except Exception as exc:
        reason = f"Sample discovery failed for {endpoint}: {exc}"
        for route_key in route_keys:
            skipped_samples[route_key] = reason[:500]
        return

    sample = _extract_first_value(payload, fields)
    if sample:
        for route_key in route_keys:
            samples[route_key] = sample
        return

    for route_key in route_keys:
        skipped_samples[route_key] = empty_reason


def discover_route_samples(token: str) -> tuple[dict[str, str], dict[str, str]]:
    samples: dict[str, str] = {}
    skipped_samples: dict[str, str] = {}
    _add_live_sample(
        samples,
        skipped_samples,
        route_keys=("approvals/[id]", "governance/approvals/[id]"),
        endpoint="/governance/approvals",
        token=token,
        empty_reason="No approval records available for detail route audit.",
    )
    _add_live_sample(
        samples,
        skipped_samples,
        route_keys=("incidents/[id]", "governance/incidents/[id]"),
        endpoint="/governance/incidents",
        token=token,
        empty_reason="No incident records available for detail route audit.",
    )
    _add_live_sample(
        samples,
        skipped_samples,
        route_keys=("workflows/[id]",),
        endpoint="/workflows",
        token=token,
        empty_reason="No workflow records available for detail route audit.",
    )
    _add_live_sample(
        samples,
        skipped_samples,
        route_keys=("proof/snapshots/[id]", "governor/proof/snapshots/[id]"),
        endpoint="/governance/governor/proof/snapshots",
        token=token,
        empty_reason="No proof snapshots available for detail route audit.",
    )
    _add_live_sample(
        samples,
        skipped_samples,
        route_keys=("governor/alerts/[id]",),
        endpoint="/governance/governor/alerts",
        token=token,
        empty_reason="No governor alerts available for detail route audit.",
    )
    _add_live_sample(
        samples,
        skipped_samples,
        route_keys=("governor/drifts/[id]",),
        endpoint="/governance/governor/drifts",
        token=token,
        empty_reason="No governor drifts available for detail route audit.",
    )
    _add_live_sample(
        samples,
        skipped_samples,
        route_keys=("learning/fingerprints/[id]",),
        endpoint="/learning/fingerprints",
        token=token,
        empty_reason="No learning fingerprints available for detail route audit.",
    )
    _add_live_sample(
        samples,
        skipped_samples,
        route_keys=("project-factory/[project_id]",),
        endpoint="/project-factory/portfolio/search?sort=updated_at_desc&limit=1&offset=0",
        token=token,
        fields=("project_id", "id"),
        empty_reason="No project-factory portfolio projects available for detail route audit.",
    )
    return samples, skipped_samples


def _replace_dynamic_segments(route_key: str, sample: str) -> str:
    return DYNAMIC_PARAM_PATTERN.sub(sample, route_key)


def page_routes(samples: dict[str, str] | None = None, skipped_samples: dict[str, str] | None = None) -> list[dict]:
    live_samples = samples or {}
    skipped = skipped_samples or {}
    routes = []
    for page in APP_DIR.rglob("page.*"):
        if page.name not in {"page.tsx", "page.ts", "page.jsx", "page.js"}:
            continue
        relative = page.parent.relative_to(APP_DIR).as_posix()
        route_key = "" if relative == "." else relative
        if route_key == "":
            url_path = "/"
            data_note = "static"
            route = {
                "route_key": route_key or "/",
                "url_path": url_path,
                "source": page.relative_to(ROOT).as_posix(),
                "data_note": data_note,
            }
        elif DYNAMIC_PARAM_PATTERN.search(route_key):
            if route_key in skipped:
                route = {
                    "route_key": route_key,
                    "url_path": None,
                    "source": page.relative_to(ROOT).as_posix(),
                    "data_note": "skipped_no_sample",
                    "skip_reason": skipped[route_key],
                }
            elif route_key in live_samples:
                url_path = "/" + _replace_dynamic_segments(route_key, live_samples[route_key])
                route = {
                    "route_key": route_key,
                    "url_path": url_path,
                    "source": page.relative_to(ROOT).as_posix(),
                    "data_note": "live-sample",
                }
            elif route_key in FALLBACK_SAMPLE_IDS:
                url_path = "/" + _replace_dynamic_segments(route_key, FALLBACK_SAMPLE_IDS[route_key])
                route = {
                    "route_key": route_key,
                    "url_path": url_path,
                    "source": page.relative_to(ROOT).as_posix(),
                    "data_note": "fallback-sample",
                }
            else:
                route = {
                    "route_key": route_key,
                    "url_path": None,
                    "source": page.relative_to(ROOT).as_posix(),
                    "data_note": "skipped_no_sample",
                    "skip_reason": "No live sample discovered for dynamic route.",
                }
        else:
            url_path = "/" + route_key
            route = {
                "route_key": route_key or "/",
                "url_path": url_path,
                "source": page.relative_to(ROOT).as_posix(),
                "data_note": "static",
            }
        routes.append(route)
    return sorted(routes, key=lambda item: (item["url_path"] is None, item["url_path"] or item["route_key"]))


def classify(text: str, status: int | None, page_errors: list[str], console_errors: list[str]) -> str:
    lowered = text.lower()
    if status and status >= 500:
        return "http_5xx"
    if status == 404:
        return "http_404"
    fatal_markers = [
        "application error",
        "unhandled runtime error",
        "runtime error",
        "internal server error",
        "failed to compile",
    ]
    if any(marker in lowered for marker in fatal_markers):
        return "fatal_ui"
    if page_errors:
        return "page_error"
    if console_errors:
        return "console_error"
    return "ok"


def _has_transient_navigation_error(errors: list[str]) -> bool:
    return any(marker in error for error in errors for marker in TRANSIENT_NAVIGATION_ERRORS)


def _write_results(results: list[dict]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    token = login_token()
    samples, skipped_samples = discover_route_samples(token)
    routes = page_routes(samples=samples, skipped_samples=skipped_samples)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1100})
        context.add_init_script(
            script=f"""
            window.localStorage.setItem('sqv_access_token', {json.dumps(token)});
            window.localStorage.setItem('sqv_operator_email', 'admin@sovereign.agi');
            window.localStorage.setItem('auth', JSON.stringify({{ role: 'OPERATOR' }}));
            """
        )
        for index, item in enumerate(routes, start=1):
            if item["url_path"] is None:
                results.append(
                    {
                        "index": index,
                        **item,
                        "url": None,
                        "final_url": "",
                        "http_status": None,
                        "title": "",
                        "classification": "skipped_no_sample",
                        "page_errors": [],
                        "console_errors": [],
                        "text_sample": "",
                    }
                )
                print(
                    f"{index:02d}/{len(routes)} {item['route_key']} status=None "
                    f"class=skipped_no_sample note={item['data_note']}",
                    flush=True,
                )
                _write_results(results)
                continue

            url = FRONTEND + item["url_path"]
            status = None
            title = ""
            text_sample = ""
            final_url = ""
            page_errors: list[str] = []
            console_errors: list[str] = []
            transient_errors: list[str] = []
            attempts = 0
            for attempt in range(1, MAX_ATTEMPTS + 1):
                attempts = attempt
                page_errors = []
                console_errors = []
                page = context.new_page()

                def on_page_error(error):
                    page_errors.append(str(error)[:500])

                def on_console(msg):
                    if msg.type in {"error", "warning"}:
                        console_errors.append(msg.text[:500])

                page.on("pageerror", on_page_error)
                page.on("console", on_console)
                try:
                    response = page.goto(url, wait_until="domcontentloaded", timeout=GOTO_TIMEOUT_MS)
                    status = response.status if response else None
                    try:
                        page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_TIMEOUT_MS)
                    except PlaywrightTimeoutError:
                        pass
                    title = page.title()
                    final_url = page.url
                    body = page.locator("body")
                    try:
                        text_sample = (body.inner_text(timeout=BODY_TIMEOUT_MS) or "")[:1200]
                    except Exception as exc:
                        text_sample = f"BODY_READ_ERROR: {exc}"
                except Exception as exc:
                    page_errors.append(str(exc)[:500])
                finally:
                    page.remove_listener("pageerror", on_page_error)
                    page.remove_listener("console", on_console)
                    page.close()

                if page_errors and _has_transient_navigation_error(page_errors) and attempt < MAX_ATTEMPTS:
                    transient_errors.extend(page_errors)
                    time.sleep(1.5 * attempt)
                    continue
                break

            results.append(
                {
                    "index": index,
                    **item,
                    "url": url,
                    "final_url": final_url,
                    "http_status": status,
                    "title": title,
                    "classification": classify(text_sample, status, page_errors, console_errors),
                    "attempts": attempts,
                    "transient_errors": transient_errors[:5],
                    "page_errors": page_errors,
                    "console_errors": console_errors[:5],
                    "text_sample": text_sample,
                }
            )
            print(
                f"{index:02d}/{len(routes)} {item['url_path']} status={status} "
                f"class={results[-1]['classification']} note={item['data_note']} attempts={attempts}",
                flush=True,
            )
            _write_results(results)
        browser.close()

    _write_results(results)
    summary = {}
    for result in results:
        summary[result["classification"]] = summary.get(result["classification"], 0) + 1
    print("SUMMARY=" + json.dumps(summary, sort_keys=True))
    print("OUTPUT=" + str(OUTPUT))


if __name__ == "__main__":
    main()
