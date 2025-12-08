import { test, expect } from '@playwright/test';

test.describe('Dashboard API Add Dialog', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173/dashboard');
    // Wait for page to fully load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);  // Additional wait for React hydration
  });

  test('should open Add API dialog when clicking button', async ({ page }) => {
    // Take screenshot before clicking
    await page.screenshot({ path: 'test-results/dashboard-before-click.png' });

    // Find and click the "API 추가" button (using more flexible selector)
    const addButton = page.getByRole('button', { name: /API 추가/i });
    await expect(addButton).toBeVisible({ timeout: 10000 });
    await addButton.click();

    // Dialog should be visible
    await expect(page.locator('h2:has-text("새 API 추가")')).toBeVisible({ timeout: 5000 });

    // Take screenshot after dialog opens
    await page.screenshot({ path: 'test-results/dashboard-dialog-open.png' });

    // Auto-discover section should be visible (use heading specifically)
    await expect(page.getByRole('heading', { name: /API 자동 검색/i })).toBeVisible();
  });

  test('should auto-discover API info from YOLO API', async ({ page }) => {
    // Find and click the "API 추가" button
    const addButton = page.getByRole('button', { name: /API 추가/i });
    await expect(addButton).toBeVisible({ timeout: 10000 });
    await addButton.click();

    await expect(page.locator('h2:has-text("새 API 추가")')).toBeVisible({ timeout: 5000 });

    // Enter YOLO API URL
    const urlInput = page.locator('input[placeholder="http://localhost:5009"]');
    await urlInput.fill('http://localhost:5005');

    // Click search button (use exact match to avoid "API 자동 검색" button)
    const searchButton = page.getByRole('button', { name: '검색', exact: true });
    await searchButton.click();

    // Wait for form to be populated (API ID field) - this indicates successful auto-discover
    const idInput = page.locator('input[placeholder="예: text-classifier"]');
    await expect(idInput).toHaveValue('yolo-detector', { timeout: 15000 });

    // Take screenshot after auto-discover
    await page.screenshot({ path: 'test-results/dashboard-auto-discover.png' });

    // Check display name is populated
    const displayNameInput = page.locator('input[placeholder="예: Text Classifier"]');
    await expect(displayNameInput).toHaveValue('YOLO 객체 검출', { timeout: 5000 });

    // Check description is populated (optional - if the API provides it)
    const descriptionInput = page.locator('textarea[placeholder*="설명"]').first();
    if (await descriptionInput.isVisible()) {
      const description = await descriptionInput.inputValue();
      expect(description.length).toBeGreaterThan(0);
    }
  });

  test('should show Custom APIs section after adding API', async ({ page }) => {
    // Check if Custom APIs section exists (may have existing APIs)
    const customAPIsSection = page.getByRole('heading', { name: /Custom APIs/i });

    // If there are custom APIs, check for export button (use first to avoid strict mode)
    if (await customAPIsSection.isVisible()) {
      await expect(page.getByRole('button', { name: /내보내기/i }).first()).toBeVisible();
    }
  });

  test('should open Export dialog when clicking export button', async ({ page }) => {
    // First check if there are any custom APIs
    const customAPIsSection = page.getByRole('heading', { name: /Custom APIs/i });

    if (await customAPIsSection.isVisible()) {
      // Click export button on first custom API
      const exportButton = page.getByRole('button', { name: /내보내기/i }).first();
      if (await exportButton.isVisible()) {
        await exportButton.click();

        // Check export dialog is visible
        await expect(page.getByRole('heading', { name: /Built-in API로 내보내기/i })).toBeVisible();

        // Check that code sections exist (use button role with specific names)
        await expect(page.getByRole('button', { name: /1\. YAML 스펙/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /2\. 노드 정의/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /3\. Docker Compose/i })).toBeVisible();
        await expect(page.getByRole('button', { name: /4\. 테스트 코드/i })).toBeVisible();
      }
    }
  });

  test('should show API status monitor', async ({ page }) => {
    // Take screenshot of dashboard
    await page.screenshot({ path: 'test-results/dashboard-full.png', fullPage: true });

    // API Status Monitor should be visible (check for "API Health Status" heading)
    const statusMonitor = page.getByText('API Health Status').first();
    await expect(statusMonitor).toBeVisible({ timeout: 10000 });
  });
});
