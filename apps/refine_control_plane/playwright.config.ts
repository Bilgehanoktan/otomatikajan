import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'playwright-results.json' }],
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3100',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 15000,
    navigationTimeout: 45000,
    testIdAttribute: 'data-testid',
  },
  webServer: {
    command: 'npm run dev -- -p 3100',
    url: 'http://localhost:3100',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
  projects: [
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        storageState: 'tests/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],
});
