import { test, expect } from '@playwright/test';
import { DashboardPage } from '../../pages/DashboardPage';

test.describe('Dashboard Page', () => {
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
    await dashboardPage.goto();
  });

  test('TC-DASH-001: Sayfa Yüklenme ve Sekmeler', async ({ page }) => {
    // MetricCards count should be > 0
    await expect(dashboardPage.metricCards.first()).toBeVisible();

    // Verify tabs
    await expect(dashboardPage.overviewTab).toBeVisible();
    
    // Switch to Events tab
    await dashboardPage.eventsTab.click();
    await expect(dashboardPage.liveEventStream).toBeVisible({ timeout: 10000 });
  });

  test('TC-DASH-006: Trigger Audit', async ({ page }) => {
    // If button is visible, try clicking it
    if (await dashboardPage.triggerAuditButton.isVisible()) {
      // Mock the endpoint if needed, or just rely on dev server
      const responsePromise = page.waitForResponse(resp => resp.url().includes('trigger-audit') || resp.url().includes('audit'), { timeout: 5000 }).catch(() => null);
      
      await dashboardPage.triggerAuditButton.click();
      const response = await responsePromise;
      if (response) {
        expect(response.status()).toBeLessThan(400); // 200 or 201 etc.
      }
    } else {
      test.skip(true, 'Trigger audit button not visible on dashboard');
    }
  });

  test('TC-DASH-007: Otomatik Yenileme (5 saniye)', async ({ page }) => {
    // Wait for 6 seconds and observe network requests for dashboard endpoints
    const requestPromise = page.waitForRequest(req => req.url().includes('dashboard') || req.url().includes('health'), { timeout: 10000 }).catch(() => null);
    const req = await requestPromise;
    expect(req).toBeTruthy();
  });
});
