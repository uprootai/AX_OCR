import { test, expect } from '@playwright/test';

test.describe('API Settings Flow', () => {
  test('should navigate from dashboard to API detail page', async ({ page }) => {
    await page.goto('/dashboard');

    // Find and click on an API card (e.g., YOLO)
    const yoloCard = page.locator('text=YOLOv11').first();
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
    // Check heading exists
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });
  });

  test('should display hyperparameters for YOLO API', async ({ page }) => {
    await page.goto('/admin/api/yolo');

    // Wait for page to load
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    // Check hyperparameter section exists
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();

    // Check YOLO-specific hyperparameter labels exist (Korean)
    await expect(page.getByText('신뢰도 임계값')).toBeVisible();
    await expect(page.getByText('IoU 임계값')).toBeVisible();
    await expect(page.getByText('입력 이미지 크기')).toBeVisible();
  });

  test('should save and persist YOLO hyperparameters', async ({ page }) => {
    await page.goto('/admin/api/yolo');

    // Wait for page to load
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    // Find confidence threshold input by its label sibling
    const confLabel = page.getByText('신뢰도 임계값').first();
    await expect(confLabel).toBeVisible();

    // Get the parent container and find the input within it
    const confInput = page.locator('div:has(> label:text("신뢰도 임계값")) input[type="number"]').first();

    // Clear and set new value
    await confInput.fill('0.5');

    // Save settings
    const saveButton = page.getByRole('button', { name: /저장/i });
    await saveButton.click();

    // Wait for save confirmation (alert)
    page.on('dialog', dialog => dialog.accept());

    // Refresh page
    await page.reload();

    // Verify value persisted
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });
    const confInputAfterReload = page.locator('div:has(> label:text("신뢰도 임계값")) input[type="number"]').first();
    await expect(confInputAfterReload).toHaveValue('0.5');
  });

  test('should display hyperparameters for eDOCr2 API', async ({ page }) => {
    await page.goto('/admin/api/edocr2_v2');

    // Check eDOCr2 specific hyperparameters
    await expect(page.getByRole('heading', { name: /eDOCr/i })).toBeVisible({ timeout: 10000 });

    // Check hyperparameter section and labels exist
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();
    await expect(page.getByText('치수 추출')).toBeVisible();
    await expect(page.getByText('언어 코드', { exact: true })).toBeVisible();
  });

  test('should display settings for Gateway API', async ({ page }) => {
    await page.goto('/admin/api/gateway');

    // Gateway should load without errors
    await expect(page.getByRole('heading', { name: /Gateway API/i })).toBeVisible({ timeout: 10000 });

    // Check service settings section exists with Korean labels
    await expect(page.getByText('서비스 설정')).toBeVisible();
    await expect(page.getByText('연산 장치')).toBeVisible();
    await expect(page.getByText('메모리 제한')).toBeVisible();
  });

  test('should display hyperparameters for PaddleOCR API', async ({ page }) => {
    await page.goto('/admin/api/paddleocr');

    await expect(page.getByRole('heading', { name: /PaddleOCR/i })).toBeVisible({ timeout: 10000 });

    // Check hyperparameter section and labels exist
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();
    await expect(page.getByText('텍스트 검출 임계값')).toBeVisible();
    await expect(page.getByText('최소 신뢰도')).toBeVisible();
  });

  test('should display device and memory settings', async ({ page }) => {
    await page.goto('/admin/api/yolo');

    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    // Check service settings section exists
    await expect(page.getByText('서비스 설정')).toBeVisible();

    // Check device selector exists (연산 장치)
    await expect(page.getByText('연산 장치')).toBeVisible();

    // Check the select dropdown has CPU/CUDA options
    const deviceSelect = page.locator('select').first();
    await expect(deviceSelect).toBeVisible();
    await expect(deviceSelect.locator('option[value="cpu"]')).toHaveText('CPU');
    await expect(deviceSelect.locator('option[value="cuda"]')).toHaveText('CUDA (GPU)');

    // Check memory limit input exists
    await expect(page.getByText('메모리 제한')).toBeVisible();
  });

  test('should navigate between different API detail pages', async ({ page }) => {
    // Start at YOLO
    await page.goto('/admin/api/yolo');
    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

    // Navigate to eDOCr2
    await page.goto('/admin/api/edocr2_v2');
    await expect(page.getByRole('heading', { name: /eDOCr/i })).toBeVisible({ timeout: 10000 });

    // Navigate to Gateway
    await page.goto('/admin/api/gateway');
    await expect(page.getByRole('heading', { name: /Gateway API/i })).toBeVisible({ timeout: 10000 });

    // Navigate back to admin list
    await page.goto('/admin');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('should have Docker control buttons in API detail', async ({ page }) => {
    await page.goto('/admin/api/yolo');

    await expect(page.getByRole('heading', { name: /YOLOv11/i })).toBeVisible({ timeout: 10000 });

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
    await expect(page.getByRole('heading', { name: /Surya OCR/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();
    await expect(page.getByText('언어', { exact: true })).toBeVisible();

    // Test DocTR
    await page.goto('/admin/api/doctr');
    await expect(page.getByRole('heading', { name: /DocTR/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();
    await expect(page.getByText('텍스트 검출 모델', { exact: true })).toBeVisible();

    // Test EasyOCR
    await page.goto('/admin/api/easyocr');
    await expect(page.getByRole('heading', { name: /EasyOCR/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();
    await expect(page.getByText('단락 분리', { exact: true })).toBeVisible();
  });

  test('should display SkinModel and VL API settings', async ({ page }) => {
    // Test SkinModel
    await page.goto('/admin/api/skinmodel');
    await expect(page.getByRole('heading', { name: /SkinModel/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();
    await expect(page.getByText('재질', { exact: true })).toBeVisible();
    await expect(page.getByText('제조 공정', { exact: true })).toBeVisible();

    // Test VL (Vision-Language)
    await page.goto('/admin/api/vl');
    await expect(page.getByRole('heading', { name: /VL/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('하이퍼파라미터')).toBeVisible();
    await expect(page.getByText('모델', { exact: true })).toBeVisible();
    await expect(page.getByText('최대 토큰', { exact: true })).toBeVisible();
  });
});

