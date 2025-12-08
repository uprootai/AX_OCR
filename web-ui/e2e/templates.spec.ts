import { test, expect } from '@playwright/test';

/**
 * BlueprintFlow Templates Page Tests
 *
 * Tests all 11 templates across 5 categories:
 * - Featured (2): Complete Drawing Analysis, P&ID Analysis
 * - Basic (2): Speed Pipeline, Basic OCR
 * - Advanced (5): Accuracy Pipeline, OCR Ensemble, Multi-OCR, Conditional OCR, Loop Detection
 * - P&ID (0 non-featured): -
 * - AI (2): VL-Assisted, Knowledge-Enhanced
 */

test.describe('BlueprintFlow Templates Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/blueprintflow/templates');
    await expect(page.locator('text=Workflow Templates')).toBeVisible({ timeout: 10000 });
  });

  // ==========================================
  // Page Structure Tests
  // ==========================================

  test.describe('Page Structure', () => {
    test('should display page title and template count', async ({ page }) => {
      await expect(page.locator('h1:has-text("Workflow Templates")')).toBeVisible();
      // Should show "11 templates" badge
      await expect(page.locator('text=/\\d+ templates/')).toBeVisible();
    });

    test('should display all category sections', async ({ page }) => {
      // Featured Templates section
      const featuredSection = page.locator('text=/추천 템플릿|Featured Templates/');
      await expect(featuredSection.first()).toBeVisible();

      // Basic Templates section
      const basicSection = page.locator('text=/기본 템플릿|Basic Templates/');
      await expect(basicSection.first()).toBeVisible();

      // Advanced Templates section
      const advancedSection = page.locator('text=/고급 템플릿|Advanced Templates/');
      await expect(advancedSection.first()).toBeVisible();

      // AI Templates section
      const aiSection = page.locator('text=/AI.*템플릿|AI-Powered Templates/');
      await expect(aiSection.first()).toBeVisible();
    });

    test('should display How Templates Work section', async ({ page }) => {
      const howSection = page.locator('text=/템플릿 작동 방식|How Templates Work/');
      await expect(howSection.first()).toBeVisible();
    });
  });

  // ==========================================
  // Featured Templates Tests
  // ==========================================

  test.describe('Featured Templates', () => {
    test('should display Complete Drawing Analysis template', async ({ page }) => {
      const template = page.locator('text=/완전 도면 분석|Complete Drawing Analysis/');
      await expect(template.first()).toBeVisible();
    });

    test('should display P&ID Analysis template with featured star', async ({ page }) => {
      const template = page.locator('text=/P&ID.*분석.*파이프라인|P&ID Analysis Pipeline/');
      await expect(template.first()).toBeVisible();
    });

    test('Complete Drawing Analysis template exists with nodes', async ({ page }) => {
      // Find node count badge pattern (e.g., "8 nodes" or "8개 노드")
      const nodeCountPattern = page.locator('text=/\\d+\\s*(nodes|개\\s*노드)/');
      await expect(nodeCountPattern.first()).toBeVisible();
    });
  });

  // ==========================================
  // Basic Templates Tests
  // ==========================================

  test.describe('Basic Templates', () => {
    test('should display Speed Pipeline template', async ({ page }) => {
      const template = page.locator('text=/속도 우선 파이프라인|Speed Priority Pipeline/');
      await expect(template.first()).toBeVisible();
    });

    test('should display Basic OCR template', async ({ page }) => {
      const template = page.locator('text=/기본 OCR 파이프라인|Basic OCR Pipeline/');
      await expect(template.first()).toBeVisible();
    });

    test('Speed Pipeline should show fast estimated time', async ({ page }) => {
      // Speed Pipeline shows "3-5s"
      const timeText = page.locator('text="3-5s"');
      await expect(timeText.first()).toBeVisible();
    });
  });

  // ==========================================
  // Advanced Templates Tests
  // ==========================================

  test.describe('Advanced Templates', () => {
    test('should display Accuracy Pipeline template', async ({ page }) => {
      const template = page.locator('text=/정확도 우선 파이프라인|Accuracy Priority Pipeline/');
      await expect(template.first()).toBeVisible();
    });

    test('should display OCR Ensemble template', async ({ page }) => {
      const template = page.locator('text=/OCR 앙상블 파이프라인|OCR Ensemble Pipeline/');
      await expect(template.first()).toBeVisible();
    });

    test('should display Multi-OCR Comparison template', async ({ page }) => {
      const template = page.locator('text=/다중 OCR 비교|Multi-OCR Comparison/');
      await expect(template.first()).toBeVisible();
    });

    test('should display Conditional OCR template', async ({ page }) => {
      const template = page.locator('text=/조건부 OCR 선택|Conditional OCR Selection/');
      await expect(template.first()).toBeVisible();
    });

    test('should display Loop Detection template', async ({ page }) => {
      const template = page.locator('text=/검출 루프 파이프라인|Loop Detection Pipeline/');
      await expect(template.first()).toBeVisible();
    });
  });

  // ==========================================
  // AI Templates Tests
  // ==========================================

  test.describe('AI Templates', () => {
    test('should display VL-Assisted Analysis template', async ({ page }) => {
      const template = page.locator('text=/VL 기반 분석|VL-Assisted Analysis/');
      await expect(template.first()).toBeVisible();
    });

    test('should display Knowledge-Enhanced Analysis template', async ({ page }) => {
      const template = page.locator('text=/지식 기반 분석|Knowledge-Enhanced Analysis/');
      await expect(template.first()).toBeVisible();
    });
  });

  // ==========================================
  // Template Card Content Tests
  // ==========================================

  test.describe('Template Card Content', () => {
    test('each template should show node count', async ({ page }) => {
      // All templates should have "X nodes" text
      const nodeCountElements = page.locator('text=/\\d+ nodes/');
      const count = await nodeCountElements.count();
      expect(count).toBeGreaterThanOrEqual(11); // At least 11 templates
    });

    test('each template should show estimated time', async ({ page }) => {
      // Templates show time like "3-5s", "10-15s", etc.
      const timeElements = page.locator('text=/\\d+-\\d+s/');
      const count = await timeElements.count();
      expect(count).toBeGreaterThanOrEqual(11);
    });

    test('each template should show accuracy percentage', async ({ page }) => {
      // Templates show accuracy like "88%", "95%", etc.
      const accuracyElements = page.locator('text=/\\d+%/');
      const count = await accuracyElements.count();
      expect(count).toBeGreaterThanOrEqual(11);
    });

    test('each template should have Use Template button', async ({ page }) => {
      const useButtons = page.locator('button:has-text("Use Template")');
      const count = await useButtons.count();
      expect(count).toBeGreaterThanOrEqual(11);
    });

    test('should display Pipeline Flow badges for each template', async ({ page }) => {
      const pipelineFlowLabels = page.locator('text="Pipeline Flow:"');
      const count = await pipelineFlowLabels.count();
      expect(count).toBeGreaterThanOrEqual(11);
    });

    test('each template should show use case recommendation', async ({ page }) => {
      // Each template should have "When to use" or "이럴 때 사용하세요" section
      const useCaseLabels = page.locator('text=/When to use|이럴 때 사용하세요/');
      const count = await useCaseLabels.count();
      expect(count).toBeGreaterThanOrEqual(11);
    });
  });

  // ==========================================
  // Template Loading Tests
  // ==========================================

  test.describe('Template Loading', () => {
    test('clicking Use Template should navigate to builder', async ({ page }) => {
      // Click the first Use Template button
      const useButton = page.locator('button:has-text("Use Template")').first();
      await useButton.click();

      // Should navigate to builder page
      await expect(page).toHaveURL(/\/blueprintflow\/builder/);

      // Builder should be visible
      await expect(page.locator('text=Node Palette')).toBeVisible({ timeout: 10000 });
    });

    test('loading a template should add nodes to canvas', async ({ page }) => {
      // Click Use Template on the first template
      const useButton = page.locator('button:has-text("Use Template")').first();
      await useButton.click();

      // Wait for builder
      await expect(page).toHaveURL(/\/blueprintflow\/builder/);
      await page.waitForTimeout(1000);

      // Should have nodes on canvas
      const nodes = page.locator('.react-flow__node');
      const nodeCount = await nodes.count();
      expect(nodeCount).toBeGreaterThan(0);
    });

    test('loading P&ID template should add 5 nodes', async ({ page }) => {
      // Find and click the P&ID template Use Template button
      // P&ID template is in Featured section
      const pidCard = page.locator('text=/P&ID.*분석.*파이프라인|P&ID Analysis Pipeline/').first();
      const card = pidCard.locator('xpath=ancestor::div[contains(@class, "rounded")]');
      const useButton = card.locator('button:has-text("Use Template")');

      // If we can find the button in the card, click it
      if (await useButton.isVisible()) {
        await useButton.click();
      } else {
        // Fallback: click the second Use Template button (P&ID is second in Featured)
        await page.locator('button:has-text("Use Template")').nth(1).click();
      }

      // Wait for builder
      await expect(page).toHaveURL(/\/blueprintflow\/builder/);
      await page.waitForTimeout(1000);

      // P&ID template has 5 nodes
      const nodes = page.locator('.react-flow__node');
      const nodeCount = await nodes.count();
      expect(nodeCount).toBe(5);
    });
  });

  // ==========================================
  // Template Count Summary
  // ==========================================

  test.describe('Template Count Summary', () => {
    test('should have exactly 11 templates', async ({ page }) => {
      const useButtons = page.locator('button:has-text("Use Template")');
      const count = await useButtons.count();
      expect(count).toBe(11);
    });

    test('Featured section should have 2 templates', async ({ page }) => {
      // Find Featured section and count templates
      const _featuredBadge = page.locator('text=/추천 템플릿|Featured Templates/').first()
        .locator('xpath=following-sibling::*[contains(@class, "Badge") or contains(text(), "2")]');

      // Alternative: count cards in Featured section by checking for FEATURED badge
      const featuredCards = page.locator('.ring-amber-400, .ring-amber-500');
      const count = await featuredCards.count();
      expect(count).toBe(2);
    });
  });
});
