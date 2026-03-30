from playwright.sync_api import Page, expect
import re

class DashboardPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        
        # Locators
        self.title_regex = re.compile(r"Otonom AI Şirketi", re.IGNORECASE)
        self.dashboard_nav = page.locator(".nav-item", has_text="Pano")
        self.tasks_nav = page.locator(".nav-item", has_text="Görevler")
        self.new_task_btn = page.get_by_role("button", name=re.compile(r"Yeni Görev", re.IGNORECASE)).first
        
        # Stats
        self.total_tasks_stat = page.locator("#s-total")
        self.cost_stat = page.locator("#s-cost")
        self.health_score = page.locator("#health-score-label")
        
        # Modals
        self.create_task_modal = page.locator("#modal-create")
        self.task_title_input = page.locator("#f-title")
        self.task_desc_input = page.locator("#f-desc")
        self.submit_task_btn = page.locator("#btn-submit-task")
        
        # AGI Mission Control
        self.agi_container = page.locator(".agi-mission-control")
        self.agi_reality_score = page.locator("text=Reality Score").locator("..").locator("div").last
        self.agi_episode_info = page.locator("text=Episode ID")

    def navigate(self):
        """Dashboard sayfasına gider."""
        self.page.goto(self.base_url)
        # JS yüklenmesini ve API isteklerinin tamamlanmasını bekle
        self.page.wait_for_load_state("networkidle")
        self.force_login()

    def force_login(self):
        """Oturumun açık olduğundan emin olur (Mocking'e ek olarak tarayıcı tarafında zorlar)."""
        self.page.evaluate("() => { if (typeof AUTH !== 'undefined') { AUTH.save('test@antigravity.ai', true); checkAuth(); } }")
        # Login modalının kapalı olduğundan emin ol
        from playwright.sync_api import expect
        expect(self.page.locator("#modal-login")).not_to_have_class("open", timeout=5000)

    def verify_loaded(self):
        """Sayfanın doğru yüklendiğini doğrular."""
        expect(self.page).to_have_title(self.title_regex)
        expect(self.dashboard_nav).to_have_class(re.compile(r"active"))

    def open_new_task_modal(self):
        """'Yeni Görev' modalını açar."""
        self.new_task_btn.click()
        expect(self.create_task_modal).to_be_visible()

    def get_stat_value(self, stat_id: str) -> str:
        """Belirli bir istatistik kartının değerini döner."""
        return self.page.locator(f"#{stat_id}").inner_text()
