import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

export class LoginPage extends BasePage {
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly usernameInput: Locator;
  readonly submitButton: Locator;
  readonly registerButton: Locator;
  readonly toggleRegisterLink: Locator;
  readonly rememberMeCheckbox: Locator;
  readonly errorAlert: Locator;

  constructor(page: Page) {
    super(page);
    this.emailInput = page.locator('input#login_email');
    this.passwordInput = page.locator('input#login_password');
    this.usernameInput = page.locator('input#register_username');
    this.submitButton = page.locator('form#login button[type="submit"], button[type="submit"]');
    this.registerButton = page.locator('form#register button[type="submit"]');
    this.toggleRegisterLink = page.locator('a:has-text("Kayıt Ol"), a:has-text("Sign up"), span:has-text("Kayıt Ol")');
    this.rememberMeCheckbox = page.locator('input[type="checkbox"]');
    this.errorAlert = page.locator('.ant-alert, .ant-message, [role="alert"]:not(#__next-route-announcer__)');
  }

  async goto() {
    await this.page.goto('/login', { waitUntil: 'domcontentloaded' });
    await this.waitForLoad();
  }

  async login(email: string, password: string) {
    await this.emailInput.waitFor({ state: 'visible' });
    await this.emailInput.click();
    await this.emailInput.fill(email);
    await this.emailInput.press('Tab');
    await this.passwordInput.click();
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async toggleRegister() {
    await this.toggleRegisterLink.click();
  }
}
