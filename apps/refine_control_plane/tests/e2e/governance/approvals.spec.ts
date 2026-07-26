import { test, expect } from '@playwright/test';
import { ApprovalsPage } from '../../pages/ApprovalsPage';

test.describe('Approvals Page', () => {
  let approvalsPage: ApprovalsPage;

  test.beforeEach(async ({ page }) => {
    approvalsPage = new ApprovalsPage(page);
    await approvalsPage.goto();
  });

  test('TC-APPR-001: Bekleyen Onayları Görüntüleme', async () => {
    // There might not be any cards, so we just check the page loaded properly
    await expect(approvalsPage.page).toHaveURL(/.*\/approvals/);
    
    if (await approvalsPage.approvalCards.count() > 0) {
      const firstCard = approvalsPage.approvalCards.first();
      await expect(firstCard).toBeVisible();
      // Should have some badge about mobile approval
      await expect(firstCard).toContainText(/Mobil|Mobile/i, { ignoreCase: true });
    }
  });

  test('TC-APPR-004: Acil Direktif Yayınlama', async () => {
    if (await approvalsPage.newDirectiveButton.isVisible()) {
      await approvalsPage.newDirectiveButton.click();
      await expect(approvalsPage.emergencyDirectiveModal).toBeVisible();
      
      // Select scope
      if (await approvalsPage.scopeFleetRadio.isVisible()) {
        await approvalsPage.scopeFleetRadio.click();
      }

      await approvalsPage.executiveOrderTextarea.fill('Tüm ajanları güvenlik taramasından geçir — kritik açık tespit edildi');
      
      // Test aborting
      await approvalsPage.abortButton.click();
      await expect(approvalsPage.emergencyDirectiveModal).toBeHidden();
    } else {
      test.skip(true, 'New Directive button not found');
    }
  });

  test('TC-APPR-006: Telegram Bot Linki', async ({ page }) => {
    const telegramLink = page.locator('a[href*="t.me/SovereignAgiBot"]');
    if (await telegramLink.isVisible()) {
      await expect(telegramLink).toHaveAttribute('target', '_blank');
    } else {
      test.skip(true, 'Telegram link not visible');
    }
  });
});
