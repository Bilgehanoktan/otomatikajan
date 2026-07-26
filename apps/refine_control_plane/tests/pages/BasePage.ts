import { Page, Locator } from '@playwright/test';

export class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async waitForLoad() {
    await this.page.waitForLoadState('domcontentloaded');
  }

  // Common UI elements like sidebar, navbar can be added here
}
