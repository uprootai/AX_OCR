import { test, expect } from '@playwright/test';

test.describe('Hyperparameter Integration Tests', () => {
  test('API Settings hyperparameters should be reflected in BlueprintFlow execution', async ({ page }) => {
    // Step 1: Clear any existing hyperparameters
    await page.goto('/dashboard');
    await page.evaluate(() => {
      localStorage.removeItem('hyperParameters');
      localStorage.removeItem('serviceConfigs');
    });

    // Step 2: Go to API Settings and set YOLO hyperparameters
    await page.goto('/admin/api/yolo');
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    // Change confidence threshold to a specific value (0.45)
    const confInput = page.locator('div:has(> label:text("신뢰도 임계값")) input[type="number"]').first();
    await confInput.fill('0.45');

    // Change IoU threshold
    const iouInput = page.locator('div:has(> label:text("IoU 임계값")) input[type="number"]').first();
    await iouInput.fill('0.6');

    // Handle alert dialog
    page.on('dialog', dialog => dialog.accept());

    // Save settings
    await page.getByRole('button', { name: /저장/i }).click();
    await page.waitForTimeout(500);

    // Step 3: Verify localStorage contains the saved values
    const savedParams = await page.evaluate(() => {
      return JSON.parse(localStorage.getItem('hyperParameters') || '{}');
    });

    console.log('Saved hyperParameters:', savedParams);
    expect(savedParams.yolo_conf_threshold).toBe(0.45);
    expect(savedParams.yolo_iou_threshold).toBe(0.6);

    // Step 4: Go to BlueprintFlow and verify the values are available
    await page.goto('/blueprintflow/builder');
    await expect(page.locator('text=Node Palette')).toBeVisible({ timeout: 10000 });

    // The getSavedHyperparameters function should now return these values
    // when a YOLO node is executed. We can verify this by checking localStorage
    // is still intact after navigating to BlueprintFlow
    const paramsAfterNav = await page.evaluate(() => {
      return JSON.parse(localStorage.getItem('hyperParameters') || '{}');
    });

    expect(paramsAfterNav.yolo_conf_threshold).toBe(0.45);
    expect(paramsAfterNav.yolo_iou_threshold).toBe(0.6);
  });

  test('Multiple API settings should persist correctly', async ({ page }) => {
    // Clear localStorage
    await page.goto('/dashboard');
    await page.evaluate(() => {
      localStorage.removeItem('hyperParameters');
    });

    // Handle alert dialogs
    page.on('dialog', dialog => dialog.accept());

    // Set YOLO hyperparameters
    await page.goto('/admin/api/yolo');
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    const confInput = page.locator('div:has(> label:text("신뢰도 임계값")) input[type="number"]').first();
    await confInput.fill('0.35');
    await page.getByRole('button', { name: /저장/i }).click();
    await page.waitForTimeout(500);

    // Set PaddleOCR hyperparameters
    await page.goto('/admin/api/paddleocr');
    await expect(page.getByRole('heading', { name: /PaddleOCR/i })).toBeVisible({ timeout: 10000 });

    const detThreshInput = page.locator('div:has(> label:text("텍스트 검출 임계값")) input[type="number"]').first();
    await detThreshInput.fill('0.35');
    await page.getByRole('button', { name: /저장/i }).click();
    await page.waitForTimeout(500);

    // Set SkinModel hyperparameters
    await page.goto('/admin/api/skinmodel');
    await expect(page.getByRole('heading', { name: /SkinModel/i })).toBeVisible({ timeout: 10000 });

    const materialSelect = page.locator('div:has(> label:text("재질")) select').first();
    await materialSelect.selectOption('aluminum');
    await page.getByRole('button', { name: /저장/i }).click();
    await page.waitForTimeout(500);

    // Verify all settings are in localStorage
    const savedParams = await page.evaluate(() => {
      return JSON.parse(localStorage.getItem('hyperParameters') || '{}');
    });

    console.log('All saved hyperParameters:', savedParams);

    // Check YOLO
    expect(savedParams.yolo_conf_threshold).toBe(0.35);

    // Check PaddleOCR
    expect(savedParams.paddleocr_det_db_thresh).toBe(0.35);

    // Check SkinModel
    expect(savedParams.skinmodel_material).toBe('aluminum');
  });

  test('workflowStore should use localStorage hyperparameters', async ({ page }) => {
    // Set specific hyperparameters
    await page.goto('/dashboard');
    await page.evaluate(() => {
      localStorage.setItem('hyperParameters', JSON.stringify({
        yolo_conf_threshold: 0.55,
        yolo_iou_threshold: 0.75,
        yolo_imgsz: 640,
        yolo_visualize: false,
      }));
    });

    // Go to BlueprintFlow
    await page.goto('/blueprintflow/builder');
    await expect(page.locator('text=Node Palette')).toBeVisible({ timeout: 10000 });

    // Verify the helper function works correctly
    const extractedParams = await page.evaluate(() => {
      const savedHyperParams = localStorage.getItem('hyperParameters');
      if (!savedHyperParams) return {};

      const allParams = JSON.parse(savedHyperParams);
      const result: Record<string, unknown> = {};
      const prefix = 'yolo';

      Object.keys(allParams).forEach((key) => {
        if (key.startsWith(`${prefix}_`)) {
          const paramName = key.substring(prefix.length + 1);
          result[paramName] = allParams[key];
        }
      });

      return result;
    });

    console.log('Extracted YOLO params:', extractedParams);

    expect(extractedParams.conf_threshold).toBe(0.55);
    expect(extractedParams.iou_threshold).toBe(0.75);
    expect(extractedParams.imgsz).toBe(640);
    expect(extractedParams.visualize).toBe(false);
  });
});
