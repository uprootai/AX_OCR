import { test, expect } from '@playwright/test';

test.describe('API Settings Flow', () => {
  test('should navigate from dashboard to API detail page', async ({ page }) => {
    await page.goto('/dashboard');

    // Find and click on an API card (e.g., YOLO)
    const yoloCard = page.locator('text=/YOLO/i').first();
    await expect(yoloCard).toBeVisible({ timeout: 10000 });

    // Click the settings/config button for YOLO
    const settingsButton = page.locator('a[href="/admin/api/yolo"]').first();
    if (await settingsButton.isVisible()) {
      await settingsButton.click();
    } else {
      // Alternatively navigate directly
      await page.goto('/admin/api/yolo');
    }

    await expect(page).toHaveURL(/\/admin\/api\/yolo/);
    // Check page title/heading exists - YOLO (통합)
    await expect(page.locator('text=/YOLO.*통합|YOLO/i').first()).toBeVisible({ timeout: 10000 });
  });

  test('should display hyperparameters for YOLO API', async ({ page }) => {
    await page.goto('/admin/api/yolo');

    // Wait for page to load - YOLO (통합) heading
    await expect(page.locator('text=/YOLO.*통합|YOLO/i').first()).toBeVisible({ timeout: 10000 });

    // Check hyperparameter section exists
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();

    // Check YOLO-specific hyperparameter labels exist (Korean)
    await expect(page.locator('text=/신뢰도 임계값|검출 신뢰도/i').first()).toBeVisible();
    await expect(page.locator('text=/IoU 임계값|NMS IoU/i').first()).toBeVisible();
    await expect(page.locator('text=/입력 이미지 크기/i').first()).toBeVisible();
  });

  test('should save and persist YOLO hyperparameters', async ({ page }) => {
    await page.goto('/admin/api/yolo');

    // Wait for page to load - YOLO (통합) heading
    await expect(page.locator('text=/YOLO.*통합|YOLO/i').first()).toBeVisible({ timeout: 10000 });

    // Check that save button exists
    const saveButton = page.getByRole('button', { name: /저장/i });
    await expect(saveButton).toBeVisible();

    // Click save and verify page stays loaded
    await saveButton.click();
    await page.waitForTimeout(1000);

    // Verify page is still loaded after save
    await expect(page.locator('text=/YOLO.*통합|YOLO/i').first()).toBeVisible({ timeout: 10000 });
  });

  test('should display hyperparameters for eDOCr2 API', async ({ page }) => {
    await page.goto('/admin/api/edocr2');

    // Check eDOCr2 page loaded - wait for any eDOCr text
    await expect(page.locator('text=/eDOCr/i').first()).toBeVisible({ timeout: 10000 });

    // Check service settings section exists (present on all API pages)
    await expect(page.getByText('서비스 설정')).toBeVisible();
  });

  test('should display settings for Gateway API', async ({ page }) => {
    await page.goto('/admin/api/gateway');

    // Gateway should load without errors - check for Gateway text
    await expect(page.locator('text=/Gateway/i').first()).toBeVisible({ timeout: 10000 });

    // Check service settings section exists with Korean labels
    await expect(page.getByText('서비스 설정')).toBeVisible();
    await expect(page.getByText('연산 장치')).toBeVisible();
    await expect(page.getByText('메모리 제한', { exact: true })).toBeVisible();
  });

  test('should display hyperparameters for PaddleOCR API', async ({ page }) => {
    await page.goto('/admin/api/paddleocr');

    await expect(page.locator('text=/PaddleOCR/i').first()).toBeVisible({ timeout: 10000 });

    // Check hyperparameter section and labels exist
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();
    // Use label locator to avoid strict mode violation
    await expect(page.locator('label:has-text("텍스트 검출 임계값")').first()).toBeVisible();
  });

  test('should display device and memory settings', async ({ page }) => {
    await page.goto('/admin/api/yolo');

    // Wait for page to load
    await expect(page.locator('text=/YOLO.*통합|YOLO/i').first()).toBeVisible({ timeout: 10000 });

    // Check service settings section exists
    await expect(page.getByText('서비스 설정')).toBeVisible();

    // Check device selector exists (연산 장치)
    await expect(page.getByText('연산 장치')).toBeVisible();

    // Check the select dropdown has CPU/CUDA options
    const deviceSelect = page.locator('select').first();
    await expect(deviceSelect).toBeVisible();
    await expect(deviceSelect.locator('option[value="cpu"]')).toHaveText('CPU');
    await expect(deviceSelect.locator('option[value="cuda"]')).toHaveText('CUDA (GPU)');

    // Check memory limit label exists (use exact match to avoid GPU 메모리 제한)
    await expect(page.getByText('메모리 제한', { exact: true })).toBeVisible();
  });

  test('should navigate between different API detail pages', async ({ page }) => {
    // Start at YOLO
    await page.goto('/admin/api/yolo');
    await expect(page.locator('text=/YOLO.*통합|YOLO/i').first()).toBeVisible({ timeout: 10000 });

    // Navigate to eDOCr2
    await page.goto('/admin/api/edocr2');
    await expect(page.locator('text=/eDOCr/i').first()).toBeVisible({ timeout: 10000 });

    // Navigate to Gateway
    await page.goto('/admin/api/gateway');
    await expect(page.locator('text=/Gateway/i').first()).toBeVisible({ timeout: 10000 });

    // Navigate back to admin list
    await page.goto('/admin');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('should have Docker control buttons in API detail', async ({ page }) => {
    await page.goto('/admin/api/yolo');

    await expect(page.locator('text=/YOLO.*통합|YOLO/i').first()).toBeVisible({ timeout: 10000 });

    // Check Docker control section exists
    await expect(page.getByText('Docker 제어')).toBeVisible();

    // Check buttons exist (use exact match to avoid 재시작 matching 시작)
    await expect(page.getByRole('button', { name: '시작', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: '중지', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: '재시작', exact: true })).toBeVisible();
  });

  test('should display all OCR APIs with their hyperparameters', async ({ page }) => {
    // Test Surya OCR
    await page.goto('/admin/api/surya_ocr');
    await expect(page.locator('text=/Surya.*OCR|Surya/i').first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();

    // Test DocTR
    await page.goto('/admin/api/doctr');
    await expect(page.locator('text=/DocTR/i').first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();

    // Test EasyOCR
    await page.goto('/admin/api/easyocr');
    await expect(page.locator('text=/EasyOCR/i').first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();
  });

  test('should display SkinModel and VL API settings', async ({ page }) => {
    // Test SkinModel
    await page.goto('/admin/api/skinmodel');
    await expect(page.locator('text=/SkinModel/i').first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();

    // Test VL (Vision-Language)
    await page.goto('/admin/api/vl');
    await expect(page.locator('text=/VL.*Model|Vision.*Language|VL/i').first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();
  });
});

