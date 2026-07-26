import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class ApprovalsPage extends BasePage {
  readonly approvalCards: Locator;
  readonly newDirectiveButton: Locator;
  readonly quorumStatePanel: Locator;
  readonly emergencyDirectiveModal: Locator;
  readonly scopeLocalRadio: Locator;
  readonly scopeFleetRadio: Locator;
  readonly executiveOrderTextarea: Locator;
  readonly broadcastButton: Locator;
  readonly abortButton: Locator;
  
  constructor(page: Page) {
    super(page);
    this.approvalCards = page.locator('.group\\/item');
    this.newDirectiveButton = page.locator('button:has-text("New Directive"), button:has-text("Yeni Direktif")');
    this.quorumStatePanel = page.locator('[data-testid="quorum-state-panel"], .quorum-panel');
    
    // Modal locators
    this.emergencyDirectiveModal = page.locator('.animate-in.fade-in.zoom-in');
    this.scopeLocalRadio = page.locator('form .grid button').nth(1);
    this.scopeFleetRadio = page.locator('form .grid button').nth(0);
    this.executiveOrderTextarea = page.locator('textarea');
    this.broadcastButton = page.locator('button:has-text("Broadcast"), button:has-text("Yayınla")');
    this.abortButton = page.locator('button:has-text("Abort"), button:has-text("İptal")');
  }

  async goto() {
    await this.page.goto('/approvals', { waitUntil: 'domcontentloaded' });
    await this.waitForLoad();
  }

  async approveFirstCard() {
    // Assuming there's an Approve button inside the first card
    const firstCard = this.approvalCards.first();
    const approveBtn = firstCard.locator('button:has-text("Approve"), button:has-text("Onayla")');
    await approveBtn.click();
  }

  async rejectFirstCard() {
    const firstCard = this.approvalCards.first();
    const rejectBtn = firstCard.locator('button:has-text("Reject"), button:has-text("Reddet")');
    await rejectBtn.click();
  }
}
