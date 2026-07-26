import { test as setup, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

import { LoginPage } from '../pages/LoginPage';

const authFile = path.join(__dirname, '../.auth/user.json');

setup('authenticate', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();

  // Fill credentials and submit
  await loginPage.login('admin@sovereign.agi', 'admin1234');
  
  // Wait for the token to be set in sessionStorage
  await page.waitForFunction(() => {
    return window.sessionStorage.getItem('sqv_access_token') !== null;
  }, { timeout: 15000 });

  // Copy sessionStorage TOKEN to localStorage so Playwright can save it
  await page.evaluate(() => {
    const token = window.sessionStorage.getItem('sqv_access_token');
    if (token) {
      window.localStorage.setItem('sqv_access_token', token);
    }
  });

  // Ensure the directory exists
  fs.mkdirSync(path.dirname(authFile), { recursive: true });
  // Save storage state
  await page.context().storageState({ path: authFile });
});
