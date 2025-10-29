const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  console.log('🚀 Starting OCR Visualization test...\n');

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  try {
    // Step 1: Navigate to Analyze page
    console.log('📍 Step 1: Navigate to Analyze page...');
    await page.goto('http://localhost:5173/analyze', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await page.screenshot({ path: '/home/uproot/ax/poc/screenshot-01-analyze-page.png' });
    console.log('   ✓ Screenshot saved: screenshot-01-analyze-page.png\n');

    // Step 2: Select sample file
    console.log('📍 Step 2: Select sample image file...');
    const sampleSelect = await page.locator('select').first();
    await sampleSelect.selectOption({ label: /Intermediate Shaft \(Image\)/ });
    await page.waitForTimeout(2000); // Wait for file to load
    await page.screenshot({ path: '/home/uproot/ax/poc/screenshot-02-file-selected.png' });
    console.log('   ✓ Sample file selected\n');

    // Step 3: Check OCR option
    console.log('📍 Step 3: Enable OCR option...');
    const ocrCheckbox = await page.locator('input[type="checkbox"]').first();
    const isChecked = await ocrCheckbox.isChecked();
    if (!isChecked) {
      await ocrCheckbox.check();
    }
    await page.screenshot({ path: '/home/uproot/ax/poc/screenshot-03-ocr-enabled.png' });
    console.log('   ✓ OCR option enabled\n');

    // Step 4: Click analyze button
    console.log('📍 Step 4: Click analyze button...');
    const analyzeButton = await page.locator('button:has-text("분석 시작")');
    await analyzeButton.click();
    console.log('   ✓ Analysis started, waiting for completion...\n');

    // Wait for analysis to complete (up to 60 seconds)
    console.log('⏳ Waiting for analysis to complete...');
    await page.waitForSelector('text=분석 완료', { timeout: 60000 });
    await page.waitForTimeout(2000);
    await page.screenshot({ path: '/home/uproot/ax/poc/screenshot-04-analysis-complete.png' });
    console.log('   ✓ Analysis completed!\n');

    // Step 5: Click OCR tab
    console.log('📍 Step 5: Click OCR tab...');
    const ocrTab = await page.locator('button:has-text("OCR")');
    await ocrTab.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: '/home/uproot/ax/poc/screenshot-05-ocr-tab.png' });
    console.log('   ✓ OCR tab opened\n');

    // Step 6: Check for OCRVisualization component
    console.log('📍 Step 6: Check for OCR Visualization component...');

    // Look for visualization title
    const visualizationTitle = await page.locator('text=OCR 인식 위치 시각화').count();
    console.log(`   - Visualization title found: ${visualizationTitle > 0 ? '✓ YES' : '✗ NO'}`);

    // Look for canvas element
    const canvasCount = await page.locator('canvas').count();
    console.log(`   - Canvas elements found: ${canvasCount}`);

    // Look for legend items
    const legendDimensions = await page.locator('text=치수').count();
    const legendGDT = await page.locator('text=GD&T').count();
    console.log(`   - Legend "치수" found: ${legendDimensions > 0 ? '✓ YES' : '✗ NO'}`);
    console.log(`   - Legend "GD&T" found: ${legendGDT > 0 ? '✓ YES' : '✗ NO'}`);

    // Take final screenshot
    await page.screenshot({ path: '/home/uproot/ax/poc/screenshot-06-final.png', fullPage: true });
    console.log('   ✓ Full page screenshot saved: screenshot-06-final.png\n');

    // Scroll down to see if visualization is below
    console.log('📍 Step 7: Scroll down to find visualization...');
    await page.evaluate(() => window.scrollBy(0, 500));
    await page.waitForTimeout(500);
    await page.screenshot({ path: '/home/uproot/ax/poc/screenshot-07-scrolled.png', fullPage: true });
    console.log('   ✓ Scrolled screenshot saved\n');

    // Final check
    const visualizationExists = visualizationTitle > 0 && canvasCount > 0;

    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📊 TEST RESULTS:');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`OCR Visualization Component: ${visualizationExists ? '✅ FOUND' : '❌ NOT FOUND'}`);
    console.log(`- Visualization Title: ${visualizationTitle > 0 ? '✓' : '✗'}`);
    console.log(`- Canvas Element: ${canvasCount > 0 ? '✓' : '✗'}`);
    console.log(`- Legend Items: ${legendDimensions > 0 && legendGDT > 0 ? '✓' : '✗'}`);
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    if (!visualizationExists) {
      console.log('⚠️  WARNING: OCR Visualization component not found!');
      console.log('Please check the screenshots to debug the issue.\n');
    } else {
      console.log('🎉 SUCCESS: OCR Visualization component is working!\n');
    }

    // Get page HTML for debugging
    const htmlContent = await page.content();
    fs.writeFileSync('/home/uproot/ax/poc/page-content.html', htmlContent);
    console.log('💾 Page HTML saved to: page-content.html\n');

  } catch (error) {
    console.error('❌ Test failed with error:', error.message);
    await page.screenshot({ path: '/home/uproot/ax/poc/screenshot-error.png' });
    console.log('   Error screenshot saved: screenshot-error.png\n');
  } finally {
    await browser.close();
    console.log('✅ Test completed!\n');
  }
})();
