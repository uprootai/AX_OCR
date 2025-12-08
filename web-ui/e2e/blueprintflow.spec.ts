import { test, expect } from '@playwright/test';

test.describe('BlueprintFlow Builder', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/blueprintflow/builder');
    // Wait for builder to load
    await expect(page.locator('text=Node Palette')).toBeVisible({ timeout: 10000 });
  });

  test('should display node palette with categories', async ({ page }) => {
    // Check for different node categories (h3 headings with emoji)
    await expect(page.locator('h3:has-text("Input")').first()).toBeVisible();
    await expect(page.locator('h3:has-text("Detection")').first()).toBeVisible();
    await expect(page.locator('h3:has-text("OCR")').first()).toBeVisible();
  });

  test('should display canvas area', async ({ page }) => {
    // ReactFlow canvas should be present
    const canvas = page.locator('.react-flow');
    await expect(canvas).toBeVisible();
  });

  test('should have image upload section', async ({ page }) => {
    // Look for dropzone or file input area
    const uploadArea = page.locator('[class*="dropzone"], input[type="file"], [data-testid="file-upload"]').first();
    // If no explicit dropzone, look for Image Input node in palette
    const imageInputNode = page.locator('text=Image Input');
    await expect(imageInputNode.or(uploadArea).first()).toBeVisible();
  });

  test('should display workflow controls', async ({ page }) => {
    // Look for execute/run button
    const controlsArea = page.locator('button', { hasText: /Execute|실행|Run/i });
    await expect(controlsArea.first()).toBeVisible();
  });
});

test.describe('BlueprintFlow Templates', () => {
  test('should load templates page', async ({ page }) => {
    await page.goto('/blueprintflow/templates');
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe('BlueprintFlow List', () => {
  test('should load list page', async ({ page }) => {
    await page.goto('/blueprintflow/list');
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });
  });
});
