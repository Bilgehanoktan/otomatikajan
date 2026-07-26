import json
import os
from pathlib import Path
from urllib import request

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "apps" / "refine_control_plane" / "src" / "app"
FRONTEND = os.environ.get("FRONTEND_URL", "http://127.0.0.1:3100")
API = os.environ.get("API_URL", "http://127.0.0.1:8000/api/v1")
OUTPUT = ROOT / "runtime" / "live-test" / "page-audit-results.json"


SAMPLE_IDS = {
    "approvals/[id]": "index",
    "axiology/[id]": "index",
    "governance/approvals/[id]": "index",
    "governance/incidents/[id]": "4ca8eb88-fcb0-40d7-ab2a-12d450a2afa7",
    "governor/alerts/[id]": "index",
    "governor/drifts/[id]": "5643d9a6-9930-43d0-8812-080641b7c19a",
    "governor/proof/snapshots/[id]": "derived-local-proof-snapshot",
    "governor/[id]": "index",
    "incidents/[id]": "4ca8eb88-fcb0-40d7-ab2a-12d450a2afa7",
    "learning/fingerprints/[id]": "f3882485-1f1a-4f97-83ef-9db4d3f6f85e",
    "workflows/[id]": "26d6eacf-d116-4a3e-baad-9c0c4516d13f",
}

EMPTY_DATA_DYNAMIC = {
    "approvals/[id]",
    "axiology/[id]",
    "governance/approvals/[id]",
    "governor/alerts/[id]",
    "governor/[id]",
}


def login_token() -> str:
    payload = json.dumps({"email": "admin@sovereign.agi", "password": "admin1234"}).encode("utf-8")
    req = request.Request(
        f"{API}/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["access_token"]


def page_routes() -> list[dict]:
    routes = []
    for page in APP_DIR.rglob("page.*"):
        if page.name not in {"page.tsx", "page.ts", "page.jsx", "page.js"}:
            continue
        relative = page.parent.relative_to(APP_DIR).as_posix()
        route_key = "" if relative == "." else relative
        if route_key == "":
            url_path = "/"
            data_note = "static"
        elif "[id]" in route_key:
            sample = SAMPLE_IDS.get(route_key, "index")
            url_path = "/" + route_key.replace("[id]", sample)
            data_note = "empty-data-sample" if route_key in EMPTY_DATA_DYNAMIC else "live-sample"
        else:
            url_path = "/" + route_key
            data_note = "static"
        routes.append(
            {
                "route_key": route_key or "/",
                "url_path": url_path,
                "source": str(page.relative_to(ROOT)),
                "data_note": data_note,
            }
        )
    return sorted(routes, key=lambda item: item["url_path"])


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


def main() -> None:
    token = login_token()
    routes = page_routes()
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
        page = context.new_page()
        for index, item in enumerate(routes, start=1):
            url = FRONTEND + item["url_path"]
            page_errors: list[str] = []
            console_errors: list[str] = []

            def on_page_error(error):
                page_errors.append(str(error)[:500])

            def on_console(msg):
                if msg.type in {"error", "warning"}:
                    console_errors.append(msg.text[:500])

            page.on("pageerror", on_page_error)
            page.on("console", on_console)
            status = None
            title = ""
            text_sample = ""
            final_url = ""
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=20000)
                status = response.status if response else None
                try:
                    page.wait_for_load_state("networkidle", timeout=6000)
                except PlaywrightTimeoutError:
                    pass
                title = page.title()
                final_url = page.url
                body = page.locator("body")
                try:
                    text_sample = (body.inner_text(timeout=3000) or "")[:1200]
                except Exception as exc:
                    text_sample = f"BODY_READ_ERROR: {exc}"
            except Exception as exc:
                page_errors.append(str(exc)[:500])
            finally:
                page.remove_listener("pageerror", on_page_error)
                page.remove_listener("console", on_console)

            results.append(
                {
                    "index": index,
                    **item,
                    "url": url,
                    "final_url": final_url,
                    "http_status": status,
                    "title": title,
                    "classification": classify(text_sample, status, page_errors, console_errors),
                    "page_errors": page_errors,
                    "console_errors": console_errors[:5],
                    "text_sample": text_sample,
                }
            )
            print(
                f"{index:02d}/{len(routes)} {item['url_path']} status={status} "
                f"class={results[-1]['classification']} note={item['data_note']}"
            )
        browser.close()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = {}
    for result in results:
        summary[result["classification"]] = summary.get(result["classification"], 0) + 1
    print("SUMMARY=" + json.dumps(summary, sort_keys=True))
    print("OUTPUT=" + str(OUTPUT))


if __name__ == "__main__":
    main()
