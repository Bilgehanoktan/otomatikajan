import json
import os
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("AUDIT_BASE_URL", "http://localhost:3100").rstrip("/")
EMAIL = os.environ["AUDIT_LOGIN_EMAIL"]
PASSWORD = os.environ["AUDIT_LOGIN_PASSWORD"]
ARTIFACT_DIR = Path(os.getenv("AUDIT_ARTIFACT_DIR", "runtime/validation-artifacts")).resolve()


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    screenshot_path = ARTIFACT_DIR / "bilgeapi-ops-auth-fixed.png"
    trace_path = ARTIFACT_DIR / "bilgeapi-ops-auth-fixed-trace.zip"

    with sync_playwright() as playwright:
        request = playwright.request.new_context(base_url=BASE_URL)
        login_response = request.post(
            "/api/v1/auth/login",
            data={"email": EMAIL, "password": PASSWORD},
        )
        if not login_response.ok:
            raise RuntimeError(f"Login failed with HTTP {login_response.status}")
        token = login_response.json().get("access_token")
        if not token:
            raise RuntimeError("Login response did not contain access_token")
        request.dispose()

        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()

        console_errors: list[str] = []
        page_errors: list[str] = []
        bilgeapi_auth_responses: list[dict[str, object]] = []

        page.on(
            "console",
            lambda message: console_errors.append(message.text)
            if message.type == "error"
            else None,
        )
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.on(
            "response",
            lambda response: bilgeapi_auth_responses.append(
                {"status": response.status, "url": response.url}
            )
            if "/bilgeapi/" in response.url and response.status in {401, 403}
            else None,
        )

        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.evaluate(
            """token => {
                sessionStorage.setItem('sqv_access_token', token);
                sessionStorage.setItem('bilgeapi_ops_api_key', 'stale-invalid-key');
                sessionStorage.removeItem('bilgeapi_ops_auth_recovery_attempted');
            }""",
            token,
        )

        page.goto(f"{BASE_URL}/bilgeapi-ops", wait_until="domcontentloaded")
        audit_passed = False
        timeout_error = None
        try:
            page.wait_for_function(
                """() => {
                    const text = document.body.innerText;
                    return sessionStorage.getItem('bilgeapi_ops_api_key') === 'dev-test-key-001'
                        && (text.includes('TOPLAM API ANAHTARI') || text.includes('TOTAL API KEYS'))
                        && !text.includes('Unauthorized: Invalid API key');
                }""",
                timeout=45_000,
            )
            audit_passed = True
        except PlaywrightTimeoutError as error:
            timeout_error = str(error)

        expected_initial_auth_responses = list(bilgeapi_auth_responses)
        if audit_passed:
            console_errors.clear()
            page_errors.clear()
            bilgeapi_auth_responses.clear()
            page.reload(wait_until="domcontentloaded")
            page.wait_for_function(
                """() => {
                    const text = document.body.innerText;
                    return (text.includes('TOPLAM API ANAHTARI') || text.includes('TOTAL API KEYS'))
                        && !text.includes('Unauthorized: Invalid API key');
                }""",
                timeout=30_000,
            )
        page.wait_for_timeout(1_500)
        body_text = page.locator("body").inner_text()
        key_state = page.evaluate(
            """() => {
                const key = sessionStorage.getItem('bilgeapi_ops_api_key');
                if (key === 'stale-invalid-key') return 'stale';
                if (key === 'dev-test-key-001') return 'dev-fallback';
                return key ? 'other' : 'missing';
            }"""
        )
        final_url = page.url
        page.screenshot(path=str(screenshot_path), full_page=True)
        context.tracing.stop(path=str(trace_path))
        browser.close()

    result = {
        "url": final_url,
        "audit_passed": audit_passed,
        "timeout_error": timeout_error,
        "key_state": key_state,
        "stale_key_recovered": key_state != "stale",
        "invalid_api_key_visible": "Unauthorized: Invalid API key" in body_text,
        "partial_data_visible": any(
            label in body_text for label in ("KISMI VERI", "KISMİ VERİ", "PARTIAL DATA")
        ),
        "management_gate_locked": any(
            label in body_text for label in ("KILITLI", "KİLİTLİ", "LOCKED")
        ),
        "expected_initial_auth_responses": expected_initial_auth_responses,
        "final_auth_responses": bilgeapi_auth_responses,
        "console_errors": console_errors,
        "page_errors": page_errors,
        "screenshot": str(screenshot_path),
        "trace": str(trace_path),
    }
    print(json.dumps(result, ensure_ascii=False))
    if not audit_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
