---
name: e2e-testing
description: Playwright E2E testing patterns, Page Object Model, configuration, CI/CD integration, artifact management, and flaky test strategies.
origin: ECC
---

# E2E Testing Patterns

Use this skill when adding or reviewing end-to-end tests for user-facing flows, especially React/Next.js screens and API-backed workflows.

## When to Activate

- Adding Playwright tests for critical user journeys.
- Stabilizing flaky browser tests.
- Designing Page Object Model helpers.
- Capturing screenshots, traces, and videos for debugging.
- Wiring E2E tests into CI or local verification.

## Test Organization

```text
tests/
  e2e/
    auth/
      login.spec.ts
      logout.spec.ts
    features/
      search.spec.ts
      create.spec.ts
    api/
      endpoints.spec.ts
  fixtures/
    auth.ts
    data.ts
  playwright.config.ts
```

## Page Object Model

Prefer stable `data-testid` selectors and encapsulate repeated flows in page objects.

```typescript
import { Locator, Page } from '@playwright/test'

export class ItemsPage {
  readonly page: Page
  readonly searchInput: Locator
  readonly itemCards: Locator
  readonly createButton: Locator

  constructor(page: Page) {
    this.page = page
    this.searchInput = page.locator('[data-testid="search-input"]')
    this.itemCards = page.locator('[data-testid="item-card"]')
    this.createButton = page.locator('[data-testid="create-btn"]')
  }

  async goto() {
    await this.page.goto('/items')
    await this.page.waitForLoadState('networkidle')
  }

  async search(query: string) {
    const response = this.page.waitForResponse((resp) =>
      resp.url().includes('/api/search')
    )
    await this.searchInput.fill(query)
    await response
  }
}
```

## Test Structure

```typescript
import { expect, test } from '@playwright/test'
import { ItemsPage } from '../pages/ItemsPage'

test.describe('item search', () => {
  test('searches by keyword', async ({ page }) => {
    const itemsPage = new ItemsPage(page)
    await itemsPage.goto()
    await itemsPage.search('test')

    await expect(itemsPage.itemCards.first()).toContainText(/test/i)
  })
})
```

## Playwright Configuration

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'playwright-results.xml' }],
    ['json', { outputFile: 'playwright-results.json' }],
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
  ],
})
```

## Flake Reduction

- Prefer Playwright locators over raw selectors and manual waits.
- Wait for specific UI, route, or response conditions instead of fixed timeouts.
- Keep tests independent; seed test data per suite or per test.
- Use `test.fixme` only with a linked reason and a path to unquarantine.
- Run suspected flaky tests with `--repeat-each` before accepting a fix.

```bash
npx playwright test tests/e2e/search.spec.ts --repeat-each=10
npx playwright test tests/e2e/search.spec.ts --retries=3
```

## Artifact Management

- Use screenshots for visual state debugging.
- Use traces for timing, network, and action debugging.
- Retain videos only on failure to keep CI artifacts manageable.

```typescript
await page.screenshot({ path: 'artifacts/search-results.png', fullPage: true })
await page.locator('[data-testid="chart"]').screenshot({
  path: 'artifacts/chart.png',
})
```

## Review Checklist

- Tests cover the actual user journey, not only implementation details.
- Selectors are stable and accessible.
- Authentication and seeded data are deterministic.
- Tests avoid arbitrary sleeps.
- Artifacts are useful but not excessive.
