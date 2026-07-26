import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class DashboardPage extends BasePage {
  readonly overviewTab: Locator;
  readonly workflowsTab: Locator;
  readonly eventsTab: Locator;
  readonly healthTab: Locator;
  readonly economyTab: Locator;
  readonly metricCards: Locator;
  readonly liveEventStream: Locator;
  readonly triggerAuditButton: Locator;
  readonly ceoSuggestionsPanel: Locator;

  constructor(page: Page) {
    super(page);
    this.overviewTab = page.locator('button:has-text("Overview"), button:has-text("Genel Bakış")');
    this.workflowsTab = page.locator('button:has-text("Workflows"), button:has-text("İş Akışları")');
    this.eventsTab = page.locator('button:has-text("Events"), button:has-text("Olaylar")');
    this.healthTab = page.locator('button:has-text("Health"), button:has-text("Sağlık")');
    this.economyTab = page.locator('button:has-text("Economy"), button:has-text("Ekonomi")');
    
    // Ant Design cards usually have .ant-card class
    this.metricCards = page.locator('.glass-panel');
    
    this.liveEventStream = page.locator('.scrollbar-premium').first();
    this.triggerAuditButton = page.locator('button:has-text("Trigger Audit"), button:has-text("Tam Denetim")');
    this.ceoSuggestionsPanel = page.locator('[data-testid="ceo-suggestions"], .ceo-suggestions-panel');
  }

  async goto() {
    await this.page.goto('/', { waitUntil: 'domcontentloaded' });
    await this.waitForLoad();
  }
}
