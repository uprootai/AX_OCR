import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';

/**
 * BlueprintFlow Template Execution Tests
 *
 * Tests each template by:
 * 1. Loading the template
 * 2. Uploading a sample image
 * 3. Running the pipeline
 * 4. Verifying execution completes (or fails with expected error)
 */

// Template information for testing
// Order matches page render order: Featured → Basic → Advanced → AI
// (verified from BlueprintFlowTemplates.tsx renderCategorySection calls)
const TEMPLATES = [
  // Featured (2)
  { index: 0, name: 'Complete Drawing Analysis', nodes: 9, category: 'featured', requiresImage: true },
  { index: 1, name: 'P&ID Analysis Pipeline', nodes: 5, category: 'featured', requiresImage: true },
  // Basic (2)
  { index: 2, name: 'Speed Pipeline', nodes: 3, category: 'basic', requiresImage: true },
  { index: 3, name: 'Basic OCR Pipeline', nodes: 4, category: 'basic', requiresImage: true },
  // Advanced (5) - all non-featured advanced templates
  { index: 4, name: 'Accuracy Pipeline', nodes: 6, category: 'advanced', requiresImage: true },
  { index: 5, name: 'OCR Ensemble Pipeline', nodes: 6, category: 'advanced', requiresImage: true },
  { index: 6, name: 'Multi-OCR Comparison', nodes: 7, category: 'advanced', requiresImage: true },
  { index: 7, name: 'Conditional OCR Pipeline', nodes: 6, category: 'advanced', requiresImage: true },
  { index: 8, name: 'Loop Detection Pipeline', nodes: 5, category: 'advanced', requiresImage: true },
  // AI (2)
  { index: 9, name: 'VL-Assisted Analysis', nodes: 4, category: 'ai', requiresImage: true, requiresText: true },
  { index: 10, name: 'Knowledge-Enhanced Analysis', nodes: 6, category: 'ai', requiresImage: true, requiresText: true },
];

// Sample image path
const SAMPLE_IMAGE = '/home/uproot/ax/poc/samples/S60ME-C INTERM-SHAFT_대 주조전.jpg';

// Helper function to load template and navigate to builder
async function loadTemplateAndNavigate(page: Page, templateIndex: number): Promise<void> {
  await page.goto('/blueprintflow/templates');
  await expect(page.locator('text=Workflow Templates')).toBeVisible({ timeout: 15000 });

  // Click the Use Template button for the specified template
  const useButtons = page.locator('button:has-text("Use Template")');
  await useButtons.nth(templateIndex).click();

  // Wait for navigation to builder
  await expect(page).toHaveURL(/\/blueprintflow\/builder/, { timeout: 15000 });

  // Wait for React Flow to render nodes
  await page.waitForTimeout(2000);

  // Wait for nodes to appear
  await page.waitForSelector('.react-flow__node', { timeout: 10000 }).catch(() => {
    console.log('  Warning: No nodes found after timeout');
  });
}

// Helper function to upload image
async function uploadImage(page: Page, imagePath: string): Promise<void> {
  // Check if file exists
  if (!fs.existsSync(imagePath)) {
    throw new Error(`Sample image not found: ${imagePath}`);
  }

  // Find the file input and upload
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles(imagePath);

  // Wait for image to be loaded
  await page.waitForTimeout(1000);
}

// Helper function to run pipeline and wait for completion
async function runPipelineAndWait(page: Page, timeoutMs: number = 120000): Promise<{
  status: 'completed' | 'failed';
  successCount: number;
  failCount: number;
  error?: string;
}> {
  // Click Run button
  const runButton = page.locator('button:has-text("Run"), button:has-text("실행")').first();
  await runButton.click();

  // Wait for execution to start
  await page.waitForTimeout(500);

  // Wait for completion (either success or failure)
  const startTime = Date.now();

  while (Date.now() - startTime < timeoutMs) {
    // Check for completion status
    const statusText = await page.locator('text=/Status:|상태:/').first().textContent().catch(() => null);

    if (statusText) {
      if (statusText.includes('completed') || statusText.includes('완료')) {
        // Get success/fail counts
        const successText = await page.locator('text=/\\d+ success/').first().textContent().catch(() => '0 success');
        const failText = await page.locator('text=/\\d+ failed/').first().textContent().catch(() => '0 failed');

        const successCount = parseInt(successText?.match(/(\d+)/)?.[1] || '0');
        const failCount = parseInt(failText?.match(/(\d+)/)?.[1] || '0');

        return {
          status: failCount > 0 ? 'failed' : 'completed',
          successCount,
          failCount,
        };
      }

      if (statusText.includes('failed') || statusText.includes('실패')) {
        // Get error message
        const errorText = await page.locator('text=/Error:|에러:/').first().textContent().catch(() => 'Unknown error');

        return {
          status: 'failed',
          successCount: 0,
          failCount: 1,
          error: errorText || undefined,
        };
      }
    }

    // Check for Pipeline Summary card
    const summaryCard = page.locator('text="Pipeline Summary"');
    if (await summaryCard.isVisible().catch(() => false)) {
      // Parse summary
      const successText = await page.locator('text=/\\d+ success/').first().textContent().catch(() => '0 success');
      const failText = await page.locator('text=/\\d+ failed/').first().textContent().catch(() => null);

      const successCount = parseInt(successText?.match(/(\d+)/)?.[1] || '0');
      const failCount = failText ? parseInt(failText.match(/(\d+)/)?.[1] || '0') : 0;

      if (successCount > 0 || failCount > 0) {
        return {
          status: failCount > 0 ? 'failed' : 'completed',
          successCount,
          failCount,
        };
      }
    }

    await page.waitForTimeout(1000);
  }

  throw new Error('Pipeline execution timeout');
}

test.describe('Template Execution Tests', () => {
  test.setTimeout(180000); // 3 minutes per test

  // Skip execution tests - they depend on external services and are prone to GPU crashes
  // Use `npx playwright test template-execution.spec.ts --grep "Execution"` to run manually
  test.describe.skip('Execution Tests (requires running services)', () => {
    // Test each template
    for (const template of TEMPLATES) {
      test(`${template.index + 1}. ${template.name} (${template.nodes} nodes)`, async ({ page }) => {
      console.log(`\n========== Testing: ${template.name} ==========`);

      // 1. Load template
      console.log('1. Loading template...');
      await loadTemplateAndNavigate(page, template.index);

      // Verify nodes are loaded
      const nodes = page.locator('.react-flow__node');
      const nodeCount = await nodes.count();
      console.log(`   Nodes loaded: ${nodeCount} (expected: ${template.nodes})`);
      expect(nodeCount).toBe(template.nodes);

      // 2. Upload image if required
      if (template.requiresImage) {
        console.log('2. Uploading image...');
        try {
          await uploadImage(page, SAMPLE_IMAGE);
          console.log('   Image uploaded successfully');
        } catch (e) {
          console.log(`   Image upload failed: ${e}`);
          // Take screenshot for debugging
          await page.screenshot({ path: `test-results/${template.name.replace(/\s+/g, '-')}-upload-error.png` });
          throw e;
        }
      }

      // 3. Run pipeline
      console.log('3. Running pipeline...');
      try {
        const result = await runPipelineAndWait(page, 120000);

        console.log(`   Result: ${result.status}`);
        console.log(`   Success: ${result.successCount}, Failed: ${result.failCount}`);

        if (result.error) {
          console.log(`   Error: ${result.error}`);
        }

        // Take screenshot of results
        await page.screenshot({
          path: `test-results/${template.name.replace(/\s+/g, '-')}-result.png`,
          fullPage: true
        });

        // Assert based on category
        if (template.category === 'ai') {
          // AI templates may fail if VL/Knowledge services are not available
          console.log('   (AI template - checking for expected failures)');
          // Just check that pipeline ran (some nodes may fail)
          expect(result.successCount + result.failCount).toBeGreaterThan(0);
        } else {
          // Other templates should complete successfully
          // Some failures are acceptable if services are not running
          expect(result.successCount).toBeGreaterThan(0);
        }

      } catch (e) {
        console.log(`   Execution error: ${e}`);
        await page.screenshot({
          path: `test-results/${template.name.replace(/\s+/g, '-')}-error.png`,
          fullPage: true
        });
        throw e;
      }

      console.log(`========== Completed: ${template.name} ==========\n`);
    });
  }
  });  // Close skip block
});

// Quick smoke tests - verify each template loads with correct node count
test.describe('Template Load Smoke Test', () => {
  // Test each template individually for isolation
  for (const template of TEMPLATES) {
    test(`${template.index + 1}. ${template.name} should load with ${template.nodes} nodes`, async ({ page }) => {
      await loadTemplateAndNavigate(page, template.index);

      const nodes = page.locator('.react-flow__node');
      const nodeCount = await nodes.count();

      console.log(`Template ${template.index + 1}: ${template.name} - Nodes: ${nodeCount}/${template.nodes}`);
      expect(nodeCount).toBe(template.nodes);
    });
  }
});
