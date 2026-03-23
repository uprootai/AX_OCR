import { test, expect } from '@playwright/test';
import { BOM_UI_BASE_URL } from './fixtures/runtime';

test.describe('AX dual UI smoke', () => {
  test('loads web-ui dashboard shell', async ({ page }) => {
    await page.goto('/dashboard');

    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.locator('body')).toBeVisible();
  });

  test('redirects /bom routes into Blueprint AI BOM frontend', async ({ page }) => {
    await page.goto('/bom/workflow');

    await page.waitForURL(
      (url) => url.href.startsWith(`${BOM_UI_BASE_URL}/workflow`),
      { timeout: 15000 }
    );
    await expect(page.locator('body')).toBeVisible();

    const hasFileInput = await page
      .locator('input[type="file"]')
      .first()
      .isVisible()
      .catch(() => false);
    const hasWorkflowText = await page
      .getByText(/워크플로우|Workflow|세션|session/i)
      .first()
      .isVisible()
      .catch(() => false);

    expect(hasFileInput || hasWorkflowText).toBeTruthy();
  });
});
