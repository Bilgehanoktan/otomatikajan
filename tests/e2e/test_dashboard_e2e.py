import pytest
from playwright.sync_api import Page, expect
from .pages.dashboard_page import DashboardPage

@pytest.fixture
def dashboard(page: Page, base_url: str):
    db_page = DashboardPage(page, base_url)
    db_page.navigate()
    return db_page

def test_dashboard_stats_display(dashboard: DashboardPage):
    """Dashboard istatistiklerinin mock verilerle doğru göründüğünü doğrula."""
    dashboard.verify_loaded()
    
    # mock_api'deki değerleri kontrol et
    assert dashboard.get_stat_value("s-total") == "50"
    assert dashboard.get_stat_value("s-cost") == "$15.75"
    assert dashboard.get_stat_value("health-score-label") == "95%"

def test_navigation_to_tasks(dashboard: DashboardPage, page: Page):
    """Görevler sayfasına geçişi doğrula."""
    dashboard.tasks_nav.click()
    
    # Sayfa başlığının değiştiğini kontrol et
    # core_app_v2.js -> labels['tasks'] = 'Görevler'
    page_title = page.locator("#page-title")
    from playwright.sync_api import expect
    expect(page_title).to_have_text("Görevler")

def test_create_task_modal_flow(dashboard: DashboardPage):
    """Yeni görev modalının açılıp kapandığını doğrula."""
    dashboard.open_new_task_modal()
    
    # Form alanlarını doldur (opsiyonel)
    dashboard.task_title_input.fill("E2E Test Görevi")
    
    # Kapat butonuna bas (modal içindeki X)
    dashboard.page.locator("#modal-create .modal-close").click()
    from playwright.sync_api import expect
    expect(dashboard.create_task_modal).not_to_be_visible()

def test_task_error_rendering(dashboard: DashboardPage, page: Page):
    """Hatalı görevlerin (zaman aşımı vb.) UI'da doğru 'HATA DETAYI' ile göründüğünü doğrula."""
    # Hatalı göreve tıkla
    page.locator("#recent-tasks").get_by_text("Physical E2E Test Task").first.click()
    
    # Detay modalının açıldığını bekle
    page.wait_for_selector("#modal-detail.open", timeout=5000)
    
    # Hata detayının yüklenmesini ve DOM'a girmesini bekle
    content_area = page.locator("#modal-detail-content")
    from playwright.sync_api import expect
    expect(content_area).to_contain_text("HATA DETAYI", timeout=5000)
    expect(content_area).to_contain_text("Reaper tarafından temizlendi", timeout=5000)

def test_navigation_to_logs(dashboard: DashboardPage, page: Page):
    """Sistem Kayıtları (Logs) sayfasının yüklendiğini doğrula."""
    # Yan menüden Kayıtlar'a tıkla
    page.get_by_text("Sistem Kayıtları").click()
    
    # Sayfa başlığını kontrol et
    from playwright.sync_api import expect
    expect(page.locator("#page-title")).to_have_text("Sistem Kayıtları")
    
    # Log akış alanının (log-feed) göründüğünü kontrol et
    expect(page.locator("#log-feed")).to_be_visible()

def test_agi_mission_control_rendering(dashboard: DashboardPage, page: Page):
    """Bilişsel Çekirdek (AGI Mission Control) verilerinin doğru yüklendiğini doğrula."""
    # AGI görevine tıkla
    page.locator("#recent-tasks").get_by_text("AGI Cognitive Core Mission").click()
    
    # Detay modalının açıldığını bekle
    page.wait_for_selector("#modal-detail.open", timeout=5000)
    
    # AGI container'ın görünürlüğünü kontrol et
    from playwright.sync_api import expect
    expect(dashboard.agi_container).to_be_visible()
    
    # Reality Score ve Episode ID verilerini kontrol et
    expect(dashboard.agi_reality_score).to_have_text("92%")
    expect(dashboard.agi_episode_info).to_contain_text("EP-77X-BETA")

def test_turkish_status_labels(dashboard: DashboardPage, page: Page):
    """Teknik durum kodlarının Türkçe etiketlere doğru dönüştüğünü doğrula."""
    dashboard.verify_loaded()
    # Tablodaki durumları kontrol et
    # queued -> Kuyrukta
    # pending_approval -> Onay Bekliyor
    expect(page.get_by_text("Kuyrukta").first).to_be_visible()
    expect(page.get_by_text("Onay Bekliyor").first).to_be_visible()
    expect(page.get_by_text("Tamamlandı").first).to_be_visible()
