import { test, expect } from '@playwright/test';

test('detailed image persistence analysis', async ({ page }) => {
  // Enable console logging
  page.on('console', msg => {
    if (msg.type() === 'log' || msg.type() === 'info') {
      console.log('  [browser]', msg.text());
    }
  });

  // 1. Go to builder
  console.log('\n=== STEP 1: Go to builder ===');
  await page.goto('/blueprintflow/builder');
  await page.waitForLoadState('networkidle');
  
  // Check initial state
  let state = await page.evaluate(() => {
    const img = sessionStorage.getItem('blueprintflow-uploadedImage');
    return {
      sessionStorageKeys: Object.keys(sessionStorage),
      hasImageInStorage: !!img,
      imageLength: img ? img.length : 0,
    };
  });
  console.log('Initial state:', state);
  
  // Check if there's an image preview already visible
  const previewImgs = await page.locator('img').all();
  console.log('Preview images on page:', previewImgs.length);
  
  // 2. Upload file
  console.log('\n=== STEP 2: Upload image ===');
  const fileInput = page.locator('input[type="file"][accept="image/*"]');
  const buffer = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mNk+M9QzwAEjDAGNzYAAIoaB/lnseQAAAAASUVORK5CYII=', 'base64');
  await fileInput.setInputFiles({
    name: 'my-test-image.png',
    mimeType: 'image/png',
    buffer: buffer
  });
  await page.waitForTimeout(1500);
  
  // Check state after upload
  state = await page.evaluate(() => {
    const img = sessionStorage.getItem('blueprintflow-uploadedImage');
    const fileName = sessionStorage.getItem('blueprintflow-uploadedFileName');
    return {
      hasImageInStorage: !!img,
      imageLength: img ? img.length : 0,
      fileName: fileName,
    };
  });
  console.log('After upload:', state);
  
  // Take screenshot
  await page.screenshot({ path: 'test-results/step2-after-upload.png' });
  
  // 3. Navigate to templates
  console.log('\n=== STEP 3: Navigate to templates ===');
  await page.goto('/blueprintflow/templates');
  await page.waitForLoadState('networkidle');
  
  state = await page.evaluate(() => {
    const img = sessionStorage.getItem('blueprintflow-uploadedImage');
    return {
      hasImageInStorage: !!img,
      imageLength: img ? img.length : 0,
    };
  });
  console.log('On templates page:', state);
  
  // 4. Click Use Template
  console.log('\n=== STEP 4: Click Use Template ===');
  await page.locator('button:has-text("Use Template")').first().click();
  await page.waitForURL(/\/blueprintflow\/builder/);
  await page.waitForTimeout(1000);
  
  // Check state after template load
  state = await page.evaluate(() => {
    const img = sessionStorage.getItem('blueprintflow-uploadedImage');
    const fileName = sessionStorage.getItem('blueprintflow-uploadedFileName');
    return {
      hasImageInStorage: !!img,
      imageLength: img ? img.length : 0,
      fileName: fileName,
    };
  });
  console.log('After template load - sessionStorage:', state);
  
  // Check the actual store state via window
  const storeState = await page.evaluate(() => {
    // Try to get the zustand store state
    // The store should have uploadedImage
    const storeElement = document.querySelector('[data-store-state]');
    return storeElement ? storeElement.getAttribute('data-store-state') : 'not found';
  });
  console.log('Store element:', storeState);
  
  // Check if image preview is visible in UI
  const uploadSection = page.locator('text=/Uploaded|Preview|my-test-image/i');
  const uploadSectionCount = await uploadSection.count();
  console.log('Upload section elements:', uploadSectionCount);
  
  // Check all images on page
  const allImgs = await page.locator('img').all();
  console.log('Total images on page:', allImgs.length);
  for (let i = 0; i < Math.min(allImgs.length, 5); i++) {
    const src = await allImgs[i].getAttribute('src');
    const alt = await allImgs[i].getAttribute('alt');
    console.log(`  Image ${i}: alt="${alt}", src starts with: ${src?.substring(0, 50)}...`);
  }
  
  // Take screenshot
  await page.screenshot({ path: 'test-results/step4-after-template.png', fullPage: true });
  
  // The test: sessionStorage should have the image
  expect(state.hasImageInStorage).toBe(true);
});
