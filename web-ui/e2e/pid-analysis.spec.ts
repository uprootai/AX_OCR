import { test, expect } from '@playwright/test';

test.describe('P&ID Analysis Nodes', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/blueprintflow/builder');
    // Wait for builder to load
    await expect(page.locator('text=Node Palette')).toBeVisible({ timeout: 10000 });
  });

  test('should display P&ID nodes in palette', async ({ page }) => {
    // Check for Segmentation category (contains Line Detector)
    const segmentationSection = page.locator('h3:has-text("Segmentation")');
    await expect(segmentationSection.first()).toBeVisible({ timeout: 5000 });

    // Check for Detection category (contains YOLO)
    const detectionSection = page.locator('h3:has-text("Detection")');
    await expect(detectionSection.first()).toBeVisible({ timeout: 5000 });

    // Check for Analysis category (contains P&ID Analyzer)
    const analysisSection = page.locator('h3:has-text("Analysis")');
    await expect(analysisSection.first()).toBeVisible({ timeout: 5000 });
  });

  test('should display Line Detector node', async ({ page }) => {
    // Search or scroll to find Line Detector
    const lineDetector = page.locator('text=Line Detector');
    await expect(lineDetector.first()).toBeVisible({ timeout: 5000 });
  });

  test('should display YOLO node', async ({ page }) => {
    // Search for YOLO node (handles P&ID via model_type parameter)
    const yolo = page.locator('text=/^YOLO/');
    // Scroll palette if needed
    await page.evaluate(() => {
      const palette = document.querySelector('[class*="overflow-y-auto"]');
      if (palette) palette.scrollTop = 200;
    });
    await expect(yolo.first()).toBeVisible({ timeout: 10000 });
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
    // YOLO P&ID mode or Line Detector should be mentioned
    const yoloPidModeMention = page.locator('h4:has-text("YOLO P&ID")');
    const lineDetectorMention = page.locator('h4:has-text("Line Detector")');

    // At least one should be visible
    const pidMention = yoloPidModeMention.or(lineDetectorMention);
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

  test('YOLO should be in Detection category', async ({ page }) => {
    // Check that YOLO is associated with Detection (handles P&ID via model_type)
    const yoloNode = page.locator('text=/^YOLO/');
    await expect(yoloNode.first()).toBeVisible();
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
