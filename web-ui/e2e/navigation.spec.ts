import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should load landing page', async ({ page }) => {
    await page.goto('/');
    // Title can be "web-ui" (dev) or custom title in production
    await expect(page).toHaveTitle(/web-ui|AX POC|Web UI/i);
  });

  test('should navigate to dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.locator('h1')).toContainText(/Dashboard|대시보드/i);
  });

  test('should navigate to guide page', async ({ page }) => {
    await page.goto('/guide');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('should navigate to test hub', async ({ page }) => {
    await page.goto('/test');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('should navigate to blueprintflow builder', async ({ page }) => {
    await page.goto('/blueprintflow/builder');
    await expect(page.locator('text=Node Palette')).toBeVisible({ timeout: 10000 });
  });

  test('should navigate to analyze page', async ({ page }) => {
    await page.goto('/analyze');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('should navigate to settings', async ({ page }) => {
    await page.goto('/settings');
    await expect(page.locator('h1')).toBeVisible();
  });
});
