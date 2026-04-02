from __future__ import annotations
import os
import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e_live

@pytest.mark.skipif(not os.getenv("E2E_BASE_URL"), reason="Canlı API tabanı verilmedi (E2E_BASE_URL)")
def test_dashboard_uses_live_api_without_route_mocks(page) -> None:
    base_url = os.environ["E2E_BASE_URL"].rstrip("/")
    page.goto(base_url)
    page.wait_for_load_state("networkidle")

    # Burada route interception yok: test gerçekten canlı backend'e gider.
    # expect(page.locator("#page-title")).to_be_visible()
    # Dashboard ana başlık kontrolü (index.html'e göre)
    expect(page.locator("h1")).to_contain_text("AI Yazılım Şirketi")
