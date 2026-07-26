import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

function dotenvValue(name: string): string | undefined {
  const dotenvPath = path.resolve(process.cwd(), "../..", ".env");
  if (!fs.existsSync(dotenvPath)) return undefined;
  const match = fs
    .readFileSync(dotenvPath, "utf8")
    .split(/\r?\n/)
    .find((line) => line.trim().startsWith(`${name}=`));
  return match?.split("=", 2)[1]?.trim().replace(/^['"]|['"]$/g, "") || undefined;
}

test.beforeEach(async ({ page }) => {
  const repoRoot = path.resolve(process.cwd(), "../..");
  const passwordFile = path.join(repoRoot, "runtime", "live-test", ".page-audit-password");
  const email = process.env.AUDIT_LOGIN_EMAIL || dotenvValue("AUDIT_LOGIN_EMAIL") || "admin@sovereign.agi";
  const password =
    process.env.AUDIT_LOGIN_PASSWORD ||
    dotenvValue("AUDIT_LOGIN_PASSWORD") ||
    fs.readFileSync(passwordFile, "utf8").trim();
  const response = await page.request.post("http://127.0.0.1:8000/api/v1/auth/login", {
    data: { email, password },
  });
  expect(response.ok()).toBeTruthy();
  const { access_token: token } = await response.json();
  await page.addInitScript((accessToken) => {
    window.localStorage.setItem("sqv_access_token", accessToken);
    window.localStorage.setItem("auth", JSON.stringify({ role: "OPERATOR" }));
  }, token);
});

test.describe("UI Repair responsive shell", () => {
  test("keeps the desktop content rectangular and inside the viewport", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1100 });
    await page.goto("/ui-repair");
    await expect(page.getByRole("heading", { name: "UI Repair Center" })).toBeVisible({ timeout: 30_000 });

    const content = page.getByTestId("ui-repair-content");
    await expect(content).toBeVisible();
    const box = await content.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(1440);
    expect(await content.evaluate((element) => parseFloat(getComputedStyle(element).borderRadius))).toBeLessThanOrEqual(16);
  });

  test("uses a mobile drawer without pushing content off screen", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/ui-repair");
    await expect(page.getByRole("heading", { name: "UI Repair Center" })).toBeVisible({ timeout: 30_000 });

    const content = page.getByTestId("ui-repair-content");
    const box = await content.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(390);

    const openNavigation = page.getByRole("button", { name: "Open navigation" });
    await expect(openNavigation).toBeVisible();
    await openNavigation.click();
    await expect(page.getByRole("dialog", { name: "Mobile navigation" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Close navigation" })).toBeVisible();
  });
});
