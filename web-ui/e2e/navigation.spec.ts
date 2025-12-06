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

  test('should navigate to blueprintflow builder', async ({ page }) => {
    await page.goto('/blueprintflow/builder');
    await expect(page.locator('text=Node Palette')).toBeVisible({ timeout: 10000 });
  });

  test('should navigate to admin page', async ({ page }) => {
    await page.goto('/admin');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('should navigate to API detail page', async ({ page }) => {
    await page.goto('/admin/api/gateway');
    await expect(page.getByText('Gateway API')).toBeVisible({ timeout: 10000 });
  });

  test('should not have settings in sidebar', async ({ page }) => {
    await page.goto('/dashboard');
    // Sidebar should not contain Settings link
    const sidebar = page.locator('aside');
    await expect(sidebar.locator('a[href="/settings"]')).toHaveCount(0);
  });

  test('admin page should not have docker tab', async ({ page }) => {
    await page.goto('/admin');
    // Docker tab should not exist
    await expect(page.locator('button:has-text("Docker")')).toHaveCount(0);
    // But backup tab should exist
    await expect(page.getByRole('button', { name: /backup|백업/i })).toBeVisible();
  });
});
