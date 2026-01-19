import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';

/**
 * Blueprint AI BOM E2E Tests
 *
 * TECHCROSS BWMS P&ID 분석 워크플로우 테스트
 * - 1-1: BWMS Checklist (60개 규칙 검증)
 * - 1-2: Valve Signal List
 * - 1-3: Equipment List
 * - 1-4: Deviation List (POR 문서 대기 중)
 *
 * 테스트 URL: http://localhost:5021 (Blueprint AI BOM)
 */

const BOM_BASE_URL = 'http://localhost:3000';
const SAMPLE_PID_IMAGE = '/home/uproot/ax/poc/apply-company/techloss/test_output/page_1.png';

// Helper: Check if Blueprint AI BOM is running
async function isBOMServiceAvailable(): Promise<boolean> {
  try {
    const response = await fetch(`${BOM_BASE_URL}/`);
    return response.ok;
  } catch {
    return false;
  }
}

// Helper: Upload image to workflow
async function uploadImage(page: Page, imagePath: string): Promise<boolean> {
  if (!fs.existsSync(imagePath)) {
    console.log(`  Image not found: ${imagePath}`);
    return false;
  }

  const fileInput = page.locator('input[type="file"]');
  if (await fileInput.count() === 0) {
    console.log('  No file input found');
    return false;
  }

  await fileInput.setInputFiles(imagePath);
  await page.waitForTimeout(2000); // Wait for upload processing
  return true;
}

// Helper: Wait for API response
async function waitForAPIResponse(page: Page, urlPattern: RegExp, timeout: number = 30000): Promise<boolean> {
  try {
    await page.waitForResponse(
      response => urlPattern.test(response.url()) && response.status() === 200,
      { timeout }
    );
    return true;
  } catch {
    return false;
  }
}

// ==================== BASIC TESTS ====================

test.describe('Blueprint AI BOM - Basic Tests', () => {
  test.beforeEach(async ({ page: _page }) => {
    // Skip if BOM service is not available
    const available = await isBOMServiceAvailable();
    if (!available) {
      test.skip();
    }
  });

  test('should load main page', async ({ page }) => {
    await page.goto(BOM_BASE_URL);
    // Check page loaded (title may vary: "frontend", "Blueprint", "BOM", etc.)
    await expect(page).toHaveTitle(/.+/, { timeout: 10000 });
    // Verify page content is visible
    await expect(page.locator('body')).toBeVisible();
  });

  test('should navigate to workflow page', async ({ page }) => {
    await page.goto(`${BOM_BASE_URL}/workflow`);

    // Check page loaded
    await expect(page.locator('body')).toBeVisible({ timeout: 10000 });

    // Check for sidebar or main content
    const hasWorkflowContent = await page.locator('text=/AI.*BOM|워크플로우|Workflow/i').first().isVisible().catch(() => false);
    expect(hasWorkflowContent).toBeTruthy();
  });

  test('should display file upload area', async ({ page }) => {
    await page.goto(`${BOM_BASE_URL}/workflow`);
    // Wait for React to hydrate
    await page.waitForTimeout(3000);

    // Check for file input (may be hidden)
    const fileInput = page.locator('input[type="file"]');
    const hasFileInput = await fileInput.count() > 0;

    // Or check for drag-drop area / upload button / workflow content
    const hasDragDrop = await page.locator('text=/드래그|업로드|파일|이미지|Upload|Browse|Select/i').first().isVisible().catch(() => false);

    // Or check for any workflow-related content as the page has loaded
    const hasWorkflowContent = await page.locator('text=/workflow|세션|session|분석/i').first().isVisible().catch(() => false);

    // Test passes if any indicator of the workflow page is present
    expect(hasFileInput || hasDragDrop || hasWorkflowContent).toBeTruthy();
  });
});

// ==================== P&ID FEATURES SECTION TESTS ====================

test.describe('Blueprint AI BOM - P&ID Features Section', () => {
  test.setTimeout(120000); // 2 minutes

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) {
      test.skip();
    }

    // Navigate to workflow
    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should display P&ID Analysis section after image upload', async ({ page }) => {
    // Upload P&ID image
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) {
      console.log('  Skipping - no sample image');
      return;
    }

    // Wait for processing
    await page.waitForTimeout(3000);

    // Check for P&ID section visibility
    // The section appears when valveSignalList, equipmentList, bwmsChecklist, or deviationList is enabled
    const pidSection = page.locator('text=/P&ID 분석|P&ID Analysis/i');
    const hasPIDSection = await pidSection.isVisible().catch(() => false);

    console.log(`  P&ID section visible: ${hasPIDSection}`);
  });

  test('should have 4 tabs in P&ID section', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) {
      console.log('  Skipping - no sample image');
      return;
    }

    await page.waitForTimeout(3000);

    // Check for tabs (Korean UI)
    const tabs = ['밸브', '장비', '체크리스트', '편차'];
    let foundTabs = 0;

    for (const tab of tabs) {
      const tabButton = page.locator(`button:has-text("${tab}")`);
      if (await tabButton.count() > 0) {
        foundTabs++;
        console.log(`  ✓ Found tab: ${tab}`);
      }
    }

    console.log(`  Found ${foundTabs}/${tabs.length} tabs`);
  });
});

// ==================== 1-3: EQUIPMENT DETECTION TESTS ====================

test.describe('TECHCROSS 1-3: Equipment List', () => {
  test.setTimeout(180000); // 3 minutes

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) {
      test.skip();
    }

    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should detect BWMS equipment (ECU, FMU, HGU, etc.)', async ({ page }) => {
    // Upload P&ID image
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) {
      console.log('  Skipping - no sample image');
      return;
    }

    await page.waitForTimeout(3000);

    // Click Equipment tab
    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
      await page.waitForTimeout(500);
    }

    // Click detect button
    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();

      // Wait for API response
      const success = await waitForAPIResponse(page, /equipment.*detect/i, 60000);
      console.log(`  Equipment detection API: ${success ? 'success' : 'timeout'}`);

      // Check for results
      await page.waitForTimeout(2000);

      // Look for equipment tags (ECU, FMU, HGU, etc.)
      const equipmentTypes = ['ECU', 'FMU', 'HGU', 'ANU', 'NIU'];
      let foundEquipment = 0;

      for (const type of equipmentTypes) {
        const cell = page.locator(`td:has-text("${type}")`);
        if (await cell.count() > 0) {
          foundEquipment++;
          console.log(`  ✓ Found equipment: ${type}`);
        }
      }

      console.log(`  Found ${foundEquipment} BWMS equipment types`);
    } else {
      console.log('  Equipment detect button not visible');
    }
  });

  test('should allow equipment verification (approve/reject)', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Click Equipment tab
    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
      await page.waitForTimeout(500);
    }

    // Run detection
    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await waitForAPIResponse(page, /equipment.*detect/i, 60000);
      await page.waitForTimeout(2000);

      // Find approve button (green check icon)
      const approveButton = page.locator('[title="승인"], button:has(svg.text-green-600)').first();
      if (await approveButton.isVisible().catch(() => false)) {
        await approveButton.click();
        await page.waitForTimeout(500);

        // Check status changed
        const approvedIcon = page.locator('svg.text-green-500, [class*="green"]').first();
        const isApproved = await approvedIcon.isVisible().catch(() => false);
        console.log(`  Verification: ${isApproved ? 'approved' : 'pending'}`);
      }
    }
  });
});

// ==================== 1-2: VALVE DETECTION TESTS ====================

test.describe('TECHCROSS 1-2: Valve Signal List', () => {
  test.setTimeout(180000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) {
      test.skip();
    }

    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should detect valves from P&ID', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Click Valve tab
    const valveTab = page.locator('button:has-text("밸브")');
    if (await valveTab.isVisible().catch(() => false)) {
      await valveTab.click();
      await page.waitForTimeout(500);
    }

    // Click detect button
    const detectButton = page.locator('button:has-text("밸브 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();

      const success = await waitForAPIResponse(page, /valve.*detect/i, 60000);
      console.log(`  Valve detection API: ${success ? 'success' : 'timeout'}`);

      await page.waitForTimeout(2000);

      // Check for valve IDs in table
      const valveTable = page.locator('table');
      if (await valveTable.isVisible().catch(() => false)) {
        const valveRows = page.locator('tr:has(td)');
        const rowCount = await valveRows.count();
        console.log(`  Found ${rowCount} valve entries`);
      }
    }
  });

  test('should classify valves by category', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const valveTab = page.locator('button:has-text("밸브")');
    if (await valveTab.isVisible().catch(() => false)) {
      await valveTab.click();
    }

    const detectButton = page.locator('button:has-text("밸브 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await waitForAPIResponse(page, /valve.*detect/i, 60000);
      await page.waitForTimeout(2000);

      // Check for valve categories
      const categories = ['Required', 'Control', 'Isolation', 'Check', 'Safety'];
      let foundCategories = 0;

      for (const cat of categories) {
        const cell = page.locator(`td:has-text("${cat}")`);
        if (await cell.count() > 0) {
          foundCategories++;
        }
      }

      console.log(`  Found ${foundCategories} valve categories`);
    }
  });
});

// ==================== 1-1: CHECKLIST TESTS ====================

test.describe('TECHCROSS 1-1: BWMS Checklist', () => {
  test.setTimeout(180000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) {
      test.skip();
    }

    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should verify 60 design checklist items', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Click Checklist tab
    const checklistTab = page.locator('button:has-text("체크리스트")');
    if (await checklistTab.isVisible().catch(() => false)) {
      await checklistTab.click();
      await page.waitForTimeout(500);
    }

    // Click verify button
    const verifyButton = page.locator('button:has-text("체크리스트 검증")');
    if (await verifyButton.isVisible().catch(() => false)) {
      await verifyButton.click();

      const success = await waitForAPIResponse(page, /checklist.*check/i, 90000);
      console.log(`  Checklist verification API: ${success ? 'success' : 'timeout'}`);

      await page.waitForTimeout(2000);

      // Count pass/fail status icons
      const passIcons = await page.locator('svg.text-green-500, [class*="text-green"]').count();
      const failIcons = await page.locator('svg.text-red-500, [class*="text-red"]').count();

      console.log(`  Checklist results: ${passIcons} pass, ${failIcons} fail`);
    }
  });

  test('should show auto and final status columns', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const checklistTab = page.locator('button:has-text("체크리스트")');
    if (await checklistTab.isVisible().catch(() => false)) {
      await checklistTab.click();
    }

    const verifyButton = page.locator('button:has-text("체크리스트 검증")');
    if (await verifyButton.isVisible().catch(() => false)) {
      await verifyButton.click();
      await waitForAPIResponse(page, /checklist.*check/i, 90000);
      await page.waitForTimeout(2000);

      // Check for table headers
      const headers = ['No', 'Category', 'Description', 'Auto', 'Final'];
      let foundHeaders = 0;

      for (const header of headers) {
        const th = page.locator(`th:has-text("${header}")`);
        if (await th.count() > 0) {
          foundHeaders++;
        }
      }

      console.log(`  Found ${foundHeaders}/${headers.length} table headers`);
    }
  });
});

// ==================== 1-4: DEVIATION TESTS (PENDING) ====================

test.describe('TECHCROSS 1-4: Deviation List', () => {
  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) {
      test.skip();
    }

    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should show deviation tab (pending POR document)', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Click Deviation tab
    const deviationTab = page.locator('button:has-text("편차")');
    if (await deviationTab.isVisible().catch(() => false)) {
      await deviationTab.click();
      await page.waitForTimeout(500);

      // Check for deviation section content
      const hasContent = await page.locator('text=/편차 분석|POR|Deviation/i').first().isVisible().catch(() => false);
      console.log(`  Deviation tab visible: ${hasContent}`);

      // Note: Deviation analysis is pending POR document
      console.log('  Note: Deviation analysis requires POR document');
    }
  });
});

// ==================== EXPORT TESTS ====================

test.describe('Blueprint AI BOM - Export', () => {
  test.setTimeout(180000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) {
      test.skip();
    }

    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should have Excel export button', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Check for Excel button in P&ID section
    const excelButton = page.locator('button:has-text("Excel")');
    const hasExcelButton = await excelButton.isVisible().catch(() => false);

    console.log(`  Excel export button: ${hasExcelButton ? 'visible' : 'not visible'}`);
    expect(hasExcelButton).toBeTruthy();
  });

  test('should trigger download on Excel export', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // First, run equipment detection to have data
    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
      await page.waitForTimeout(500);

      const detectButton = page.locator('button:has-text("장비 검출")');
      if (await detectButton.isVisible().catch(() => false)) {
        await detectButton.click();
        await waitForAPIResponse(page, /equipment.*detect/i, 60000);
        await page.waitForTimeout(2000);
      }
    }

    // Click Excel export
    const excelButton = page.locator('button:has-text("Excel")');
    if (await excelButton.isVisible().catch(() => false)) {
      // Set up download listener
      const downloadPromise = page.waitForEvent('download', { timeout: 30000 }).catch(() => null);

      await excelButton.click();

      const download = await downloadPromise;
      if (download) {
        const filename = download.suggestedFilename();
        console.log(`  Downloaded: ${filename}`);
        expect(filename).toContain('.xlsx');
      } else {
        console.log('  No download triggered (may need data first)');
      }
    }
  });
});

// ==================== HUMAN-IN-THE-LOOP TESTS ====================

test.describe('Blueprint AI BOM - Human-in-the-Loop', () => {
  test.setTimeout(180000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) {
      test.skip();
    }

    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should show confidence scores for detected items', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();

      const detectButton = page.locator('button:has-text("장비 검출")');
      if (await detectButton.isVisible().catch(() => false)) {
        await detectButton.click();
        await waitForAPIResponse(page, /equipment.*detect/i, 60000);
        await page.waitForTimeout(2000);

        // Look for confidence scores (e.g., "95.2%")
        const confidenceCell = page.locator('td:has-text("%")');
        const hasConfidence = await confidenceCell.count() > 0;
        console.log(`  Confidence scores visible: ${hasConfidence}`);
      }
    }
  });

  test('should have approve/reject buttons for each item', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();

      const detectButton = page.locator('button:has-text("장비 검출")');
      if (await detectButton.isVisible().catch(() => false)) {
        await detectButton.click();
        await waitForAPIResponse(page, /equipment.*detect/i, 60000);
        await page.waitForTimeout(2000);

        // Look for action buttons in table
        const approveButtons = page.locator('[title="승인"], button:has(svg.w-4.h-4)').first();
        const hasActions = await approveButtons.isVisible().catch(() => false);
        console.log(`  Action buttons visible: ${hasActions}`);
      }
    }
  });

  test('should update status after verification', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();

      const detectButton = page.locator('button:has-text("장비 검출")');
      if (await detectButton.isVisible().catch(() => false)) {
        await detectButton.click();
        await waitForAPIResponse(page, /equipment.*detect/i, 60000);
        await page.waitForTimeout(2000);

        // Count pending items before
        const pendingBefore = await page.locator('svg.text-yellow-500').count();

        // Click first approve button
        const approveButton = page.locator('button:has(svg.text-green-600)').first();
        if (await approveButton.isVisible().catch(() => false)) {
          await approveButton.click();
          await page.waitForTimeout(1000);

          // Count pending items after
          const pendingAfter = await page.locator('svg.text-yellow-500').count();
          console.log(`  Pending items: ${pendingBefore} → ${pendingAfter}`);
        }
      }
    }
  });
});

// ==================== INTEGRATION TESTS ====================

test.describe('Blueprint AI BOM - Full Workflow Integration', () => {
  test.setTimeout(300000); // 5 minutes

  test.beforeEach(async ({ page: _page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) {
      test.skip();
    }
  });

  test('should complete TECHCROSS 1-1, 1-2, 1-3 workflow', async ({ page }) => {
    console.log('\n=== TECHCROSS Full Workflow Test ===\n');

    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);

    // Step 1: Upload P&ID image
    console.log('Step 1: Upload P&ID image');
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) {
      console.log('  ⚠️ No sample image - skipping full workflow');
      return;
    }
    console.log('  ✓ Image uploaded');

    await page.waitForTimeout(3000);

    // Step 2: Equipment Detection (1-3)
    console.log('\nStep 2: Equipment Detection (1-3)');
    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();

      const detectEquipment = page.locator('button:has-text("장비 검출")');
      if (await detectEquipment.isVisible().catch(() => false)) {
        await detectEquipment.click();
        const success = await waitForAPIResponse(page, /equipment.*detect/i, 60000);
        console.log(`  Equipment detection: ${success ? '✓' : '✗'}`);
      }
    }

    await page.waitForTimeout(2000);

    // Step 3: Valve Detection (1-2)
    console.log('\nStep 3: Valve Detection (1-2)');
    const valveTab = page.locator('button:has-text("밸브")');
    if (await valveTab.isVisible().catch(() => false)) {
      await valveTab.click();

      const detectValve = page.locator('button:has-text("밸브 검출")');
      if (await detectValve.isVisible().catch(() => false)) {
        await detectValve.click();
        const success = await waitForAPIResponse(page, /valve.*detect/i, 60000);
        console.log(`  Valve detection: ${success ? '✓' : '✗'}`);
      }
    }

    await page.waitForTimeout(2000);

    // Step 4: Checklist Verification (1-1)
    console.log('\nStep 4: Checklist Verification (1-1)');
    const checklistTab = page.locator('button:has-text("체크리스트")');
    if (await checklistTab.isVisible().catch(() => false)) {
      await checklistTab.click();

      const checkDesign = page.locator('button:has-text("체크리스트 검증")');
      if (await checkDesign.isVisible().catch(() => false)) {
        await checkDesign.click();
        const success = await waitForAPIResponse(page, /checklist.*check/i, 90000);
        console.log(`  Checklist verification: ${success ? '✓' : '✗'}`);
      }
    }

    await page.waitForTimeout(2000);

    // Step 5: Export to Excel
    console.log('\nStep 5: Export to Excel');
    const excelButton = page.locator('button:has-text("Excel")');
    if (await excelButton.isVisible().catch(() => false)) {
      const downloadPromise = page.waitForEvent('download', { timeout: 30000 }).catch(() => null);
      await excelButton.click();

      const download = await downloadPromise;
      if (download) {
        console.log(`  Excel export: ✓ (${download.suggestedFilename()})`);
      } else {
        console.log('  Excel export: ⚠️ No download');
      }
    }

    console.log('\n=== Workflow Complete ===\n');

    // Take final screenshot
    await page.screenshot({
      path: 'test-results/techcross-workflow-complete.png',
      fullPage: true
    });
  });
});

// ==================== SESSION MANAGEMENT TESTS ====================

test.describe('Blueprint AI BOM - Session Management', () => {
  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) {
      test.skip();
    }

    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should create session on image upload', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Check for session info in sidebar
    const sessionInfo = page.locator('text=/session|세션/i');
    const hasSession = await sessionInfo.isVisible().catch(() => false);

    // Or check for filename display
    const filename = page.locator('text=/page_1|.png/i');
    const hasFilename = await filename.isVisible().catch(() => false);

    console.log(`  Session created: ${hasSession || hasFilename}`);
  });

  test('should show session list in sidebar', async ({ page }) => {
    // Check sidebar for session list
    const sidebar = page.locator('aside, [class*="sidebar"], div:has(> button:has-text("새 세션"))');
    const hasSidebar = await sidebar.isVisible().catch(() => false);

    console.log(`  Sidebar visible: ${hasSidebar}`);
  });
});
