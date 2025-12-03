import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should display API status monitor', async ({ page }) => {
    // Wait for API status section to load
    await expect(page.locator('text=/API.*Status|상태/i').first()).toBeVisible({ timeout: 10000 });
  });

  test('should display quick actions cards', async ({ page }) => {
    // Check for quick action cards
    const cards = page.locator('[class*="card"], [class*="Card"]');
    await expect(cards.first()).toBeVisible({ timeout: 5000 });
  });

  test('should have auto-discover button', async ({ page }) => {
    const autoDiscoverBtn = page.locator('button', { hasText: /자동.*검색|Auto.*Discover/i });
    await expect(autoDiscoverBtn).toBeVisible();
  });

  test('should have add API button', async ({ page }) => {
    const addApiBtn = page.locator('button', { hasText: /API.*추가|Add.*API/i });
    await expect(addApiBtn).toBeVisible();
  });
});
