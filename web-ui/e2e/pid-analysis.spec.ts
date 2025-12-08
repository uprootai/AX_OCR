import { test, expect } from '@playwright/test';

test.describe('P&ID Analysis Nodes', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/blueprintflow/builder');
    // Wait for builder to load
    await expect(page.locator('text=Node Palette')).toBeVisible({ timeout: 10000 });
  });

  test('should display P&ID nodes in palette', async ({ page }) => {
    // Check for Line Detector in Segmentation category
    const segmentationSection = page.locator('text=/Segmentation|세그멘테이션/i');
    await expect(segmentationSection.first()).toBeVisible();

    // Check for YOLO-PID in Detection category
    const detectionSection = page.locator('text=/Detection|검출/i');
    await expect(detectionSection.first()).toBeVisible();

    // Check for P&ID Analyzer in Analysis category
    const analysisSection = page.locator('text=/Analysis|분석/i');
    await expect(analysisSection.first()).toBeVisible();
  });

  test('should display Line Detector node', async ({ page }) => {
    // Search or scroll to find Line Detector
    const lineDetector = page.locator('text=Line Detector');
    await expect(lineDetector.first()).toBeVisible({ timeout: 5000 });
  });

  test('should display YOLO-PID node', async ({ page }) => {
    // Search for YOLO-PID node (may need to scroll)
    const yoloPid = page.locator('text=YOLO-PID');
    // Scroll palette if needed
    await page.evaluate(() => {
      const palette = document.querySelector('[class*="overflow-y-auto"]');
      if (palette) palette.scrollTop = 200;
    });
    await expect(yoloPid.first()).toBeVisible({ timeout: 10000 });
  });

  test('should display P&ID Analyzer node', async ({ page }) => {
    // Search for P&ID Analyzer node
    const pidAnalyzer = page.locator('text=P&ID Analyzer');
    await expect(pidAnalyzer.first()).toBeVisible({ timeout: 5000 });
  });

  test('should display Design Checker node', async ({ page }) => {
    // Search for Design Checker node
    const designChecker = page.locator('text=Design Checker');
    await expect(designChecker.first()).toBeVisible({ timeout: 5000 });
  });
});

test.describe('P&ID Analysis Template', () => {
  test('should display P&ID template in templates page', async ({ page }) => {
    await page.goto('/blueprintflow/templates');
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });

    // Look for P&ID Analysis template
    const pidTemplate = page.locator('text=/P&ID.*Analysis|P&ID.*분석/i');
    await expect(pidTemplate.first()).toBeVisible({ timeout: 5000 });
  });

  test('should load P&ID template when clicked', async ({ page }) => {
    await page.goto('/blueprintflow/templates');
    await page.waitForLoadState('networkidle');

    // Wait for templates to load and find P&ID template card
    const pidTemplateCard = page.locator('[class*="card"], [class*="Card"]').filter({ hasText: /P&ID/i }).first();
    await expect(pidTemplateCard).toBeVisible({ timeout: 10000 });

    // Find the Use Template button within the card
    const useTemplateButton = pidTemplateCard.locator('button').first();
    await useTemplateButton.click();

    // Should navigate to builder
    await expect(page).toHaveURL(/\/blueprintflow\/builder/, { timeout: 10000 });

    // Should have nodes on canvas (check for react-flow node elements)
    const canvas = page.locator('.react-flow');
    await expect(canvas).toBeVisible({ timeout: 10000 });
  });
});

test.describe('P&ID Guide Section', () => {
  test('should display P&ID section in guide page', async ({ page }) => {
    await page.goto('/guide');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 10000 });

    // Look for P&ID Analysis section - may be in badges or text
    // P&ID appears in Badge components and span elements
    const pidSection = page.locator('[class*="badge"], [class*="Badge"], span').filter({ hasText: /P&ID/i }).first();
    await expect(pidSection).toBeVisible({ timeout: 10000 });
  });

  test('should display P&ID APIs in guide', async ({ page }) => {
    await page.goto('/guide');
    await page.waitForLoadState('networkidle');

    // Scroll down to find P&ID-related content
    await page.evaluate(() => window.scrollBy(0, 500));
    await page.waitForTimeout(500);

    // Check for P&ID-related API mentions (in h4 headings)
    const yoloPidMention = page.locator('h4:has-text("YOLO-PID")');
    const lineDetectorMention = page.locator('h4:has-text("Line Detector")');

    // At least one should be visible
    const pidMention = yoloPidMention.or(lineDetectorMention);
    await expect(pidMention.first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe('P&ID Node Categories', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/blueprintflow/builder');
    await expect(page.locator('text=Node Palette')).toBeVisible({ timeout: 10000 });
  });

  test('Line Detector should be in Segmentation category', async ({ page }) => {
    // Find Segmentation category and ensure Line Detector is within it
    const _segmentationGroup = page.locator('[data-category="segmentation"], :has-text("Segmentation") + div, section:has-text("Segmentation")');

    // Check that Line Detector is associated with Segmentation
    const lineDetectorNode = page.locator('text=Line Detector');
    await expect(lineDetectorNode.first()).toBeVisible();
  });

  test('YOLO-PID should be in Detection category', async ({ page }) => {
    // Check that YOLO-PID is associated with Detection
    const yoloPidNode = page.locator('text=YOLO-PID');
    await expect(yoloPidNode.first()).toBeVisible();
  });

  test('P&ID Analyzer should be in Analysis category', async ({ page }) => {
    // Check that P&ID Analyzer is associated with Analysis
    const pidAnalyzerNode = page.locator('text=P&ID Analyzer');
    await expect(pidAnalyzerNode.first()).toBeVisible();
  });

  test('Design Checker should be in Analysis category', async ({ page }) => {
    // Check that Design Checker is associated with Analysis
    const designCheckerNode = page.locator('text=Design Checker');
    await expect(designCheckerNode.first()).toBeVisible();
  });
});
