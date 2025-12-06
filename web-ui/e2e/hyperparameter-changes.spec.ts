import { test, expect } from '@playwright/test';

test.describe('Hyperparameter Change Tests', () => {
  // Clear localStorage before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.evaluate(() => {
      localStorage.removeItem('hyperParameters');
      localStorage.removeItem('serviceConfigs');
    });
  });

  test('should save and restore number type hyperparameter (YOLO conf_threshold)', async ({ page }) => {
    await page.goto('/admin/api/yolo');
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    // Find confidence threshold input
    const confInput = page.locator('div:has(> label:text("신뢰도 임계값")) input[type="number"]').first();

    // Get initial value
    const initialValue = await confInput.inputValue();
    console.log('Initial confidence value:', initialValue);

    // Change to new value
    await confInput.fill('0.75');

    // Handle alert dialog
    page.on('dialog', dialog => dialog.accept());

    // Save
    await page.getByRole('button', { name: /저장/i }).click();

    // Wait a bit for save to complete
    await page.waitForTimeout(500);

    // Reload and verify
    await page.reload();
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    const newConfInput = page.locator('div:has(> label:text("신뢰도 임계값")) input[type="number"]').first();
    await expect(newConfInput).toHaveValue('0.75');
  });

  test('should save and restore boolean type hyperparameter (YOLO visualize)', async ({ page }) => {
    await page.goto('/admin/api/yolo');
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    // Find visualize checkbox
    const visualizeCheckbox = page.locator('div:has(> label:text("시각화 생성")) input[type="checkbox"]').first();

    // Get initial state
    const initialChecked = await visualizeCheckbox.isChecked();
    console.log('Initial visualize state:', initialChecked);

    // Toggle the checkbox
    if (initialChecked) {
      await visualizeCheckbox.uncheck();
    } else {
      await visualizeCheckbox.check();
    }

    // Handle alert dialog
    page.on('dialog', dialog => dialog.accept());

    // Save
    await page.getByRole('button', { name: /저장/i }).click();
    await page.waitForTimeout(500);

    // Reload and verify
    await page.reload();
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    const newVisualizeCheckbox = page.locator('div:has(> label:text("시각화 생성")) input[type="checkbox"]').first();

    // Should be opposite of initial state
    if (initialChecked) {
      await expect(newVisualizeCheckbox).not.toBeChecked();
    } else {
      await expect(newVisualizeCheckbox).toBeChecked();
    }
  });

  test('should save and restore select type hyperparameter (YOLO imgsz)', async ({ page }) => {
    await page.goto('/admin/api/yolo');
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    // Find image size select
    const imgsizeSelect = page.locator('div:has(> label:text("입력 이미지 크기")) select').first();

    // Get initial value
    const initialValue = await imgsizeSelect.inputValue();
    console.log('Initial image size:', initialValue);

    // Change to different value
    const newValue = initialValue === '1280' ? '640' : '1280';
    await imgsizeSelect.selectOption(newValue);

    // Handle alert dialog
    page.on('dialog', dialog => dialog.accept());

    // Save
    await page.getByRole('button', { name: /저장/i }).click();
    await page.waitForTimeout(500);

    // Reload and verify
    await page.reload();
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    const newImgsizeSelect = page.locator('div:has(> label:text("입력 이미지 크기")) select').first();
    await expect(newImgsizeSelect).toHaveValue(newValue);
  });

  test('should save and restore eDOCr2 hyperparameters', async ({ page }) => {
    await page.goto('/admin/api/edocr2_v2');
    await expect(page.getByRole('heading', { name: /eDOCr/i })).toBeVisible({ timeout: 10000 });

    // Change language code (text type)
    const langInput = page.locator('div:has(> label:text("언어 코드")) input').first();
    await langInput.fill('kor');

    // Toggle 치수 추출 (boolean)
    const dimCheckbox = page.locator('div:has(> label:text("치수 추출")) input[type="checkbox"]').first();
    const initialDimState = await dimCheckbox.isChecked();
    if (initialDimState) {
      await dimCheckbox.uncheck();
    } else {
      await dimCheckbox.check();
    }

    // Handle alert dialog
    page.on('dialog', dialog => dialog.accept());

    // Save
    await page.getByRole('button', { name: /저장/i }).click();
    await page.waitForTimeout(500);

    // Reload and verify
    await page.reload();
    await expect(page.getByRole('heading', { name: /eDOCr/i })).toBeVisible({ timeout: 10000 });

    const newLangInput = page.locator('div:has(> label:text("언어 코드")) input').first();
    await expect(newLangInput).toHaveValue('kor');

    const newDimCheckbox = page.locator('div:has(> label:text("치수 추출")) input[type="checkbox"]').first();
    if (initialDimState) {
      await expect(newDimCheckbox).not.toBeChecked();
    } else {
      await expect(newDimCheckbox).toBeChecked();
    }
  });

  test('should save and restore PaddleOCR hyperparameters', async ({ page }) => {
    await page.goto('/admin/api/paddleocr');
    await expect(page.getByRole('heading', { name: /PaddleOCR/i })).toBeVisible({ timeout: 10000 });

    // Change text detection threshold (number)
    const detThreshInput = page.locator('div:has(> label:text("텍스트 검출 임계값")) input[type="number"]').first();
    await detThreshInput.fill('0.4');

    // Toggle rotation detection (boolean)
    const rotationCheckbox = page.locator('div:has(> label:text("회전 텍스트 감지")) input[type="checkbox"]').first();
    const initialRotState = await rotationCheckbox.isChecked();
    if (initialRotState) {
      await rotationCheckbox.uncheck();
    } else {
      await rotationCheckbox.check();
    }

    // Handle alert dialog
    page.on('dialog', dialog => dialog.accept());

    // Save
    await page.getByRole('button', { name: /저장/i }).click();
    await page.waitForTimeout(500);

    // Reload and verify
    await page.reload();
    await expect(page.getByRole('heading', { name: /PaddleOCR/i })).toBeVisible({ timeout: 10000 });

    const newDetThreshInput = page.locator('div:has(> label:text("텍스트 검출 임계값")) input[type="number"]').first();
    await expect(newDetThreshInput).toHaveValue('0.4');

    const newRotationCheckbox = page.locator('div:has(> label:text("회전 텍스트 감지")) input[type="checkbox"]').first();
    if (initialRotState) {
      await expect(newRotationCheckbox).not.toBeChecked();
    } else {
      await expect(newRotationCheckbox).toBeChecked();
    }
  });

  test('should save and restore SkinModel select hyperparameters', async ({ page }) => {
    await page.goto('/admin/api/skinmodel');
    await expect(page.getByRole('heading', { name: /SkinModel/i })).toBeVisible({ timeout: 10000 });

    // Change material (select)
    const materialSelect = page.locator('div:has(> label:text("재질")) select').first();
    const initialMaterial = await materialSelect.inputValue();
    const newMaterial = initialMaterial === 'steel' ? 'aluminum' : 'steel';
    await materialSelect.selectOption(newMaterial);

    // Change manufacturing process (select)
    const processSelect = page.locator('div:has(> label:text("제조 공정")) select').first();
    const initialProcess = await processSelect.inputValue();
    const newProcess = initialProcess === 'machining' ? 'casting' : 'machining';
    await processSelect.selectOption(newProcess);

    // Handle alert dialog
    page.on('dialog', dialog => dialog.accept());

    // Save
    await page.getByRole('button', { name: /저장/i }).click();
    await page.waitForTimeout(500);

    // Reload and verify
    await page.reload();
    await expect(page.getByRole('heading', { name: /SkinModel/i })).toBeVisible({ timeout: 10000 });

    const newMaterialSelect = page.locator('div:has(> label:text("재질")) select').first();
    await expect(newMaterialSelect).toHaveValue(newMaterial);

    const newProcessSelect = page.locator('div:has(> label:text("제조 공정")) select').first();
    await expect(newProcessSelect).toHaveValue(newProcess);
  });

  test('should save and restore device/memory settings', async ({ page }) => {
    await page.goto('/admin/api/yolo');
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    // Change memory limit
    const memoryInput = page.locator('div:has(> label:text("메모리 제한")) input').first();
    await memoryInput.fill('8g');

    // Handle alert dialog
    page.on('dialog', dialog => dialog.accept());

    // Save
    await page.getByRole('button', { name: /저장/i }).click();
    await page.waitForTimeout(500);

    // Reload and verify
    await page.reload();
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    const newMemoryInput = page.locator('div:has(> label:text("메모리 제한")) input').first();
    await expect(newMemoryInput).toHaveValue('8g');
  });

  test('should verify localStorage contains saved hyperparameters', async ({ page }) => {
    await page.goto('/admin/api/yolo');
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    // Change confidence threshold
    const confInput = page.locator('div:has(> label:text("신뢰도 임계값")) input[type="number"]').first();
    await confInput.fill('0.33');

    // Handle alert dialog
    page.on('dialog', dialog => dialog.accept());

    // Save
    await page.getByRole('button', { name: /저장/i }).click();
    await page.waitForTimeout(500);

    // Check localStorage directly
    const hyperParams = await page.evaluate(() => {
      return JSON.parse(localStorage.getItem('hyperParameters') || '{}');
    });

    console.log('Saved hyperParameters:', JSON.stringify(hyperParams, null, 2));

    // Verify the value was saved
    expect(hyperParams).toHaveProperty('yolo_conf_threshold', 0.33);
  });
});
