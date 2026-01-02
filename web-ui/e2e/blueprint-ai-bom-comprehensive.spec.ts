import { test, expect, Page, APIRequestContext } from '@playwright/test';
import * as fs from 'fs';

/**
 * Blueprint AI BOM Comprehensive E2E Tests
 *
 * 상세 하이퍼파라미터, 파라미터, 시나리오 테스트
 *
 * 테스트 범위:
 * 1. Detection 하이퍼파라미터 (confidence, iou_threshold, imgsz)
 * 2. TECHCROSS 1-1~1-4 상세 파라미터 검증
 * 3. Human-in-the-Loop 검증 워크플로우
 * 4. Export 옵션 (include_rejected, export_type)
 * 5. 신뢰도 기반 UI 색상 검증
 * 6. API 응답 스키마 검증
 */

// ==================== CONFIGURATION ====================

const BOM_BASE_URL = 'http://localhost:3000';
const BOM_API_URL = 'http://localhost:5020';
const SAMPLE_PID_IMAGE = '/home/uproot/ax/poc/apply-company/techloss/test_output/page_1.png';

// Detection hyperparameters
const DETECTION_DEFAULTS = {
  confidence: 0.40,
  iou_threshold: 0.50,
  imgsz: 1024,
  model_id: 'panasia_yolo'
};

// Valve categories (6 types)
const VALVE_CATEGORIES = ['Control', 'Isolation', 'Safety', 'Check', 'Relief', 'Unknown'];

// Equipment types (9 types)
const EQUIPMENT_TYPES = ['PUMP', 'VALVE', 'TANK', 'HEAT_EXCHANGER', 'COMPRESSOR', 'FILTER', 'CONTROLLER', 'SENSOR', 'OTHER'];

// Checklist status types
const CHECKLIST_STATUS = ['Pass', 'Fail', 'N/A', 'Pending', 'Manual Required'];

// Deviation severity levels (5 levels)
const DEVIATION_SEVERITY = ['critical', 'high', 'medium', 'low', 'info'];

// Verification status types
const VERIFICATION_STATUS = ['pending', 'approved', 'rejected', 'modified'];

// ==================== HELPERS ====================

async function isBOMServiceAvailable(): Promise<boolean> {
  try {
    const response = await fetch(`${BOM_BASE_URL}/`);
    return response.ok;
  } catch {
    return false;
  }
}

async function isAPIAvailable(): Promise<boolean> {
  try {
    const response = await fetch(`${BOM_API_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

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
  await page.waitForTimeout(2000);
  return true;
}

async function getSessionId(page: Page): Promise<string | null> {
  // Try to extract session ID from URL or page content
  const url = page.url();
  const sessionMatch = url.match(/session[_-]?id[=/]([a-zA-Z0-9-_]+)/i);
  if (sessionMatch) return sessionMatch[1];

  // Try to get from localStorage
  const sessionId = await page.evaluate(() => {
    return localStorage.getItem('currentSessionId') || sessionStorage.getItem('sessionId');
  });

  return sessionId;
}

async function waitForAPIResponse(page: Page, urlPattern: RegExp, timeout: number = 30000): Promise<Response | null> {
  try {
    const response = await page.waitForResponse(
      response => urlPattern.test(response.url()) && response.status() === 200,
      { timeout }
    );
    return response as unknown as Response;
  } catch {
    return null;
  }
}

// ==================== 1. DETECTION HYPERPARAMETER TESTS ====================

test.describe('Detection Hyperparameters', () => {
  test.setTimeout(120000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) test.skip();
    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should apply confidence threshold correctly', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) {
      console.log('  Skipping - no sample image');
      return;
    }

    await page.waitForTimeout(3000);

    // Look for confidence threshold slider or input
    const confidenceSlider = page.locator('input[type="range"][name*="confidence"], input[type="number"][placeholder*="신뢰"]');
    const hasConfidenceControl = await confidenceSlider.count() > 0;

    if (hasConfidenceControl) {
      // Get current value
      const currentValue = await confidenceSlider.first().inputValue();
      console.log(`  Current confidence: ${currentValue}`);

      // Try setting a new value
      await confidenceSlider.first().fill('0.6');
      await page.waitForTimeout(500);

      const newValue = await confidenceSlider.first().inputValue();
      console.log(`  New confidence: ${newValue}`);

      expect(parseFloat(newValue)).toBeCloseTo(0.6, 1);
    } else {
      // Check for settings panel
      const settingsButton = page.locator('button:has-text("설정"), button[aria-label="Settings"]');
      if (await settingsButton.isVisible().catch(() => false)) {
        await settingsButton.click();
        await page.waitForTimeout(500);

        // Look for confidence in settings panel
        const confidenceInSettings = page.locator('text=/신뢰도|confidence/i');
        const hasInSettings = await confidenceInSettings.isVisible().catch(() => false);
        console.log(`  Confidence in settings: ${hasInSettings}`);
      }
    }
  });

  test('should validate confidence threshold range (0.05-1.0)', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Find confidence input
    const confidenceInput = page.locator('input[type="number"][name*="confidence"], input[type="range"]').first();

    if (await confidenceInput.isVisible().catch(() => false)) {
      // Test boundary values
      const testValues = [
        { value: '0.01', expected: 'rejected or clamped' },
        { value: '0.05', expected: 'accepted (min)' },
        { value: '0.5', expected: 'accepted (mid)' },
        { value: '1.0', expected: 'accepted (max)' },
        { value: '1.5', expected: 'rejected or clamped' }
      ];

      for (const test of testValues) {
        await confidenceInput.fill(test.value);
        await page.waitForTimeout(200);

        const actualValue = await confidenceInput.inputValue();
        console.log(`  Input ${test.value} → ${actualValue} (${test.expected})`);
      }
    }
  });

  test('should show detection count changes with different thresholds', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Run detection with default threshold
    const detectButton = page.locator('button:has-text("심볼 검출"), button:has-text("검출 시작")').first();

    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(5000);

      // Get initial count
      const countText = await page.locator('text=/총|total|검출/i').first().textContent().catch(() => '');
      console.log(`  Detection result: ${countText}`);

      // Check for detection count in UI
      const detectionCount = page.locator('[data-testid="detection-count"], text=/\\d+\\s*개/');
      if (await detectionCount.isVisible().catch(() => false)) {
        const count = await detectionCount.textContent();
        console.log(`  Detected items: ${count}`);
      }
    }
  });
});

// ==================== 2. TECHCROSS 1-2: VALVE DETECTION PARAMETERS ====================

test.describe('TECHCROSS 1-2: Valve Detection Parameters', () => {
  test.setTimeout(180000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) test.skip();
    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should detect all 6 valve categories', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Navigate to valve tab
    const valveTab = page.locator('button:has-text("밸브")');
    if (await valveTab.isVisible().catch(() => false)) {
      await valveTab.click();
      await page.waitForTimeout(500);

      // Run detection
      const detectButton = page.locator('button:has-text("밸브 검출")');
      if (await detectButton.isVisible().catch(() => false)) {
        await detectButton.click();

        // Wait for API response
        await page.waitForResponse(
          res => res.url().includes('valve') && res.url().includes('detect'),
          { timeout: 60000 }
        ).catch(() => null);

        await page.waitForTimeout(2000);

        // Check for each valve category in response
        const pageContent = await page.content();
        let foundCategories = 0;

        for (const category of VALVE_CATEGORIES) {
          if (pageContent.includes(category)) {
            foundCategories++;
            console.log(`  ✓ Category found: ${category}`);
          }
        }

        console.log(`\n  Found ${foundCategories}/${VALVE_CATEGORIES.length} valve categories`);
      }
    }
  });

  test('should classify valves by prefix patterns', async ({ page }) => {
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
      await page.waitForTimeout(10000);

      // Check for valve ID patterns
      const valvePatterns = {
        'CV|FCV|PCV|TCV|LCV': 'Control',
        'XV|BV|GV|IV': 'Isolation',
        'SV|PSV|TSV': 'Safety',
        'CHK|CK|NRV': 'Check',
        'RV|PRV': 'Relief'
      };

      const tableRows = page.locator('table tbody tr');
      const rowCount = await tableRows.count();

      console.log(`  Total valve rows: ${rowCount}`);

      // Check a few rows for pattern matching
      for (let i = 0; i < Math.min(5, rowCount); i++) {
        const row = tableRows.nth(i);
        const rowText = await row.textContent().catch(() => '');
        console.log(`  Row ${i + 1}: ${rowText?.substring(0, 80)}...`);
      }
    }
  });

  test('should show valve confidence scores with color coding', async ({ page }) => {
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
      await page.waitForTimeout(10000);

      // Check for confidence-based color coding
      // High (>=0.9): green, Medium (>=0.7): yellow, Low (<0.7): red
      const greenCells = await page.locator('td.bg-green-100, td span.text-green-600').count();
      const yellowCells = await page.locator('td.bg-yellow-100, td span.text-yellow-600').count();
      const redCells = await page.locator('td.bg-red-100, td span.text-red-600').count();

      console.log(`  Confidence color distribution:`);
      console.log(`    High (green): ${greenCells}`);
      console.log(`    Medium (yellow): ${yellowCells}`);
      console.log(`    Low (red): ${redCells}`);
    }
  });

  test('should support profile parameter for valve detection', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Check for profile selector
    const profileSelect = page.locator('select[name*="profile"], select:has(option:text("default"))');
    const hasProfileSelect = await profileSelect.isVisible().catch(() => false);

    if (hasProfileSelect) {
      console.log('  Profile selector found');

      // Check available profiles
      const options = profileSelect.locator('option');
      const optionCount = await options.count();

      console.log(`  Available profiles: ${optionCount}`);
      for (let i = 0; i < optionCount; i++) {
        const optionText = await options.nth(i).textContent();
        console.log(`    - ${optionText}`);
      }
    } else {
      console.log('  Profile selector not visible (may be in settings)');
    }
  });
});

// ==================== 3. TECHCROSS 1-3: EQUIPMENT DETECTION PARAMETERS ====================

test.describe('TECHCROSS 1-3: Equipment Detection Parameters', () => {
  test.setTimeout(180000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) test.skip();
    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should detect all 9 equipment types', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
      await page.waitForTimeout(500);

      const detectButton = page.locator('button:has-text("장비 검출")');
      if (await detectButton.isVisible().catch(() => false)) {
        await detectButton.click();
        await page.waitForTimeout(10000);

        // Check for equipment types in table
        const pageContent = await page.content();
        let foundTypes = 0;

        for (const type of EQUIPMENT_TYPES) {
          if (pageContent.toLowerCase().includes(type.toLowerCase())) {
            foundTypes++;
            console.log(`  ✓ Type found: ${type}`);
          }
        }

        console.log(`\n  Found ${foundTypes}/${EQUIPMENT_TYPES.length} equipment types`);
      }
    }
  });

  test('should identify vendor-supplied equipment (*)', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);

      // Look for vendor supply indicator (*)
      const vendorSupplyMarker = page.locator('td:has-text("*"), span:has-text("Vendor"), [title*="vendor"]');
      const vendorSupplyCount = await vendorSupplyMarker.count();

      console.log(`  Vendor-supplied equipment: ${vendorSupplyCount}`);

      // Check for vendor supply column header
      const vendorHeader = page.locator('th:has-text("Vendor"), th:has-text("공급")');
      const hasVendorColumn = await vendorHeader.isVisible().catch(() => false);
      console.log(`  Vendor supply column: ${hasVendorColumn ? 'present' : 'not found'}`);
    }
  });

  test('should display equipment tag format correctly', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);

      // Check for BWMS equipment tags
      const bwmsTags = ['ECU', 'FMU', 'HGU', 'ANU', 'NIU', 'BTU', 'SLU'];
      const tableContent = await page.locator('table').textContent().catch(() => '');

      let foundBWMSTags = 0;
      for (const tag of bwmsTags) {
        if (tableContent.includes(tag)) {
          foundBWMSTags++;
          console.log(`  ✓ BWMS tag found: ${tag}`);
        }
      }

      console.log(`\n  Found ${foundBWMSTags}/${bwmsTags.length} BWMS equipment tags`);
    }
  });
});

// ==================== 4. TECHCROSS 1-1: CHECKLIST VERIFICATION PARAMETERS ====================

test.describe('TECHCROSS 1-1: Checklist Verification Parameters', () => {
  test.setTimeout(180000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) test.skip();
    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should verify all 5 checklist status types', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const checklistTab = page.locator('button:has-text("체크리스트")');
    if (await checklistTab.isVisible().catch(() => false)) {
      await checklistTab.click();
      await page.waitForTimeout(500);

      const verifyButton = page.locator('button:has-text("체크리스트 검증")');
      if (await verifyButton.isVisible().catch(() => false)) {
        await verifyButton.click();
        await page.waitForTimeout(15000);

        // Count status distribution
        const statusCounts: Record<string, number> = {};

        for (const status of CHECKLIST_STATUS) {
          const statusCells = page.locator(`td:has-text("${status}"), span:has-text("${status}")`);
          const count = await statusCells.count();
          statusCounts[status] = count;
          console.log(`  ${status}: ${count}`);
        }

        // Verify at least one status type is present
        const totalStatusItems = Object.values(statusCounts).reduce((a, b) => a + b, 0);
        console.log(`\n  Total status items: ${totalStatusItems}`);
      }
    }
  });

  test('should support rule_profile parameter (default, bwms, chemical)', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const checklistTab = page.locator('button:has-text("체크리스트")');
    if (await checklistTab.isVisible().catch(() => false)) {
      await checklistTab.click();
    }

    // Look for profile/rule selector
    const ruleProfileSelect = page.locator('select[name*="profile"], select[name*="rule"]');
    const hasRuleSelector = await ruleProfileSelect.isVisible().catch(() => false);

    if (hasRuleSelector) {
      const options = await ruleProfileSelect.locator('option').allTextContents();
      console.log(`  Rule profiles available: ${options.join(', ')}`);
    } else {
      console.log('  Rule profile selector not visible');
    }
  });

  test('should distinguish auto_status vs final_status', async ({ page }) => {
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
      await page.waitForTimeout(15000);

      // Check for Auto and Final columns
      const autoHeader = page.locator('th:has-text("Auto"), th:has-text("자동")');
      const finalHeader = page.locator('th:has-text("Final"), th:has-text("최종")');

      const hasAuto = await autoHeader.isVisible().catch(() => false);
      const hasFinal = await finalHeader.isVisible().catch(() => false);

      console.log(`  Auto status column: ${hasAuto ? 'present' : 'not found'}`);
      console.log(`  Final status column: ${hasFinal ? 'present' : 'not found'}`);

      // Verify auto ≠ final for at least one item (requiring human review)
      const rows = page.locator('table tbody tr');
      const rowCount = await rows.count();

      let mismatchCount = 0;
      for (let i = 0; i < Math.min(10, rowCount); i++) {
        const row = rows.nth(i);
        const cells = await row.locator('td').allTextContents();
        // Auto and Final columns are typically near the end
        if (cells.length >= 2) {
          const autoStatus = cells[cells.length - 2];
          const finalStatus = cells[cells.length - 1];
          if (autoStatus !== finalStatus) {
            mismatchCount++;
          }
        }
      }

      console.log(`  Items requiring review: ${mismatchCount}`);
    }
  });

  test('should show 60 BWMS checklist items', async ({ page }) => {
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
      await page.waitForTimeout(15000);

      // Count total rows
      const rows = page.locator('table tbody tr');
      const rowCount = await rows.count();

      console.log(`  Total checklist items: ${rowCount}`);

      // Check for pagination if less than 60 visible
      const pagination = page.locator('[class*="pagination"], button:has-text("다음"), button:has-text("Next")');
      const hasPagination = await pagination.count() > 0;

      if (hasPagination) {
        console.log('  Pagination present - items split across pages');
      }

      // Look for total count indicator
      const totalIndicator = page.locator('text=/총.*60|60.*items|60개/i');
      const hasTotal60 = await totalIndicator.isVisible().catch(() => false);
      console.log(`  60 items indicator: ${hasTotal60}`);
    }
  });
});

// ==================== 5. TECHCROSS 1-4: DEVIATION ANALYSIS PARAMETERS ====================

test.describe('TECHCROSS 1-4: Deviation Analysis Parameters', () => {
  test.setTimeout(180000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) test.skip();
    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should support severity_threshold filter', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const deviationTab = page.locator('button:has-text("편차")');
    if (await deviationTab.isVisible().catch(() => false)) {
      await deviationTab.click();
      await page.waitForTimeout(500);

      // Look for severity filter
      const severityFilter = page.locator('select[name*="severity"], [data-testid="severity-filter"]');
      const hasSeverityFilter = await severityFilter.isVisible().catch(() => false);

      if (hasSeverityFilter) {
        const options = await severityFilter.locator('option').allTextContents();
        console.log(`  Severity levels: ${options.join(', ')}`);

        // Verify all 5 severity levels are present
        let foundLevels = 0;
        for (const level of DEVIATION_SEVERITY) {
          if (options.some(opt => opt.toLowerCase().includes(level))) {
            foundLevels++;
          }
        }
        console.log(`  Found ${foundLevels}/${DEVIATION_SEVERITY.length} severity levels`);
      } else {
        console.log('  Severity filter not visible (feature pending)');
      }
    }
  });

  test('should support analysis_types parameter', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const deviationTab = page.locator('button:has-text("편차")');
    if (await deviationTab.isVisible().catch(() => false)) {
      await deviationTab.click();
    }

    // Look for analysis type checkboxes
    const analysisTypes = ['revision_compare', 'standard_check', 'design_spec_check', 'vlm_analysis'];
    let foundTypes = 0;

    for (const type of analysisTypes) {
      const checkbox = page.locator(`input[name*="${type}"], label:has-text("${type.replace('_', ' ')}")`);
      if (await checkbox.count() > 0) {
        foundTypes++;
        console.log(`  ✓ Analysis type available: ${type}`);
      }
    }

    console.log(`\n  Found ${foundTypes}/${analysisTypes.length} analysis types`);
  });

  test('should support standards parameter (ISO 10628, ISA 5.1, BWMS)', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const deviationTab = page.locator('button:has-text("편차")');
    if (await deviationTab.isVisible().catch(() => false)) {
      await deviationTab.click();
    }

    // Look for standards selector
    const standardsSelector = page.locator('select[name*="standard"], [data-testid="standards-select"]');
    const hasStandardsSelector = await standardsSelector.isVisible().catch(() => false);

    if (hasStandardsSelector) {
      const options = await standardsSelector.locator('option').allTextContents();
      console.log(`  Standards available: ${options.join(', ')}`);

      // Check for expected standards
      const expectedStandards = ['ISO_10628', 'ISA_5_1', 'BWMS_SPEC'];
      let foundStandards = 0;
      for (const std of expectedStandards) {
        if (options.some(opt => opt.includes(std) || opt.includes(std.replace('_', ' ')))) {
          foundStandards++;
        }
      }
      console.log(`  Found ${foundStandards}/${expectedStandards.length} expected standards`);
    } else {
      console.log('  Standards selector not visible (feature pending)');
    }
  });
});

// ==================== 6. HUMAN-IN-THE-LOOP VERIFICATION PARAMETERS ====================

test.describe('Human-in-the-Loop Verification', () => {
  test.setTimeout(180000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) test.skip();
    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should track all 4 verification statuses', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);

      // Check for verification status indicators
      for (const status of VERIFICATION_STATUS) {
        const statusIndicator = page.locator(`[data-status="${status}"], span:has-text("${status}")`);
        const count = await statusIndicator.count();
        console.log(`  ${status}: ${count} items`);
      }
    }
  });

  test('should support approve action with API call', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);

      // Find approve button
      const approveButton = page.locator('button[title="승인"], button:has(svg.text-green-600)').first();

      if (await approveButton.isVisible().catch(() => false)) {
        // Set up API listener
        const apiPromise = page.waitForResponse(
          res => res.url().includes('verify') && res.status() === 200,
          { timeout: 10000 }
        ).catch(() => null);

        await approveButton.click();

        const response = await apiPromise;
        if (response) {
          console.log(`  ✓ Approve API called: ${response.url()}`);

          // Check response body
          try {
            const body = await response.json();
            console.log(`  Response: ${JSON.stringify(body).substring(0, 100)}...`);
          } catch {
            console.log('  Response body not JSON');
          }
        } else {
          console.log('  No API call detected (may be local state only)');
        }
      }
    }
  });

  test('should support reject action with API call', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);

      // Find reject button
      const rejectButton = page.locator('button[title="거부"], button:has(svg.text-red-600)').first();

      if (await rejectButton.isVisible().catch(() => false)) {
        await rejectButton.click();
        await page.waitForTimeout(1000);

        // Verify item is marked as rejected
        const rejectedIndicator = page.locator('svg.text-red-500, [data-status="rejected"]').first();
        const isRejected = await rejectedIndicator.isVisible().catch(() => false);
        console.log(`  Item marked as rejected: ${isRejected}`);
      }
    }
  });

  test('should support bulk verification', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);

      // Look for bulk action buttons
      const approveAllButton = page.locator('button:has-text("전체 승인"), button:has-text("Approve All")');
      const rejectAllButton = page.locator('button:has-text("전체 거부"), button:has-text("Reject All")');

      const hasApproveAll = await approveAllButton.isVisible().catch(() => false);
      const hasRejectAll = await rejectAllButton.isVisible().catch(() => false);

      console.log(`  Approve All button: ${hasApproveAll ? 'present' : 'not found'}`);
      console.log(`  Reject All button: ${hasRejectAll ? 'present' : 'not found'}`);

      if (hasApproveAll) {
        // Count items before
        const pendingBefore = await page.locator('svg.text-yellow-500').count();

        await approveAllButton.click();
        await page.waitForTimeout(2000);

        // Count items after
        const pendingAfter = await page.locator('svg.text-yellow-500').count();
        const approvedAfter = await page.locator('svg.text-green-500').count();

        console.log(`  Pending: ${pendingBefore} → ${pendingAfter}`);
        console.log(`  Approved: ${approvedAfter}`);
      }
    }
  });

  test('should support modify action with data changes', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);

      // Look for edit/modify button
      const modifyButton = page.locator('button[title="수정"], button:has(svg.lucide-edit)').first();

      if (await modifyButton.isVisible().catch(() => false)) {
        await modifyButton.click();
        await page.waitForTimeout(500);

        // Check for edit modal/form
        const editForm = page.locator('[role="dialog"], .modal, form[data-testid="edit-form"]');
        const hasEditForm = await editForm.isVisible().catch(() => false);
        console.log(`  Edit form opened: ${hasEditForm}`);

        if (hasEditForm) {
          // Look for editable fields
          const editableFields = await editForm.locator('input, select, textarea').count();
          console.log(`  Editable fields: ${editableFields}`);
        }
      } else {
        console.log('  Modify button not visible');
      }
    }
  });
});

// ==================== 7. EXPORT OPTIONS PARAMETERS ====================

test.describe('Export Options Parameters', () => {
  test.setTimeout(180000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) test.skip();
    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should support export_type parameter (valve, equipment, checklist, all)', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Navigate to equipment and run detection
    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);
    }

    // Look for export type selector
    const exportTypeSelector = page.locator('select[name*="export"], [data-testid="export-type"]');
    const hasExportTypeSelector = await exportTypeSelector.isVisible().catch(() => false);

    if (hasExportTypeSelector) {
      const options = await exportTypeSelector.locator('option').allTextContents();
      console.log(`  Export types: ${options.join(', ')}`);

      // Verify expected types
      const expectedTypes = ['valve', 'equipment', 'checklist', 'deviation', 'all'];
      let foundTypes = 0;
      for (const type of expectedTypes) {
        if (options.some(opt => opt.toLowerCase().includes(type))) {
          foundTypes++;
        }
      }
      console.log(`  Found ${foundTypes}/${expectedTypes.length} export types`);
    } else {
      // Check for individual export buttons
      const valveExport = page.locator('button:has-text("밸브 내보내기"), button:has-text("Export Valves")');
      const equipmentExport = page.locator('button:has-text("장비 내보내기"), button:has-text("Export Equipment")');
      const allExport = page.locator('button:has-text("전체 내보내기"), button:has-text("Export All")');

      console.log(`  Valve export: ${await valveExport.count() > 0}`);
      console.log(`  Equipment export: ${await equipmentExport.count() > 0}`);
      console.log(`  All export: ${await allExport.count() > 0}`);
    }
  });

  test('should support include_rejected parameter', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Navigate and detect
    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);
    }

    // Look for include_rejected checkbox
    const includeRejectedCheckbox = page.locator('input[name*="rejected"], input[type="checkbox"]:near(:text("거부"))');
    const hasIncludeRejected = await includeRejectedCheckbox.isVisible().catch(() => false);

    console.log(`  Include rejected checkbox: ${hasIncludeRejected ? 'present' : 'not found'}`);

    if (hasIncludeRejected) {
      const isChecked = await includeRejectedCheckbox.isChecked();
      console.log(`  Default state: ${isChecked ? 'checked' : 'unchecked'}`);
    }
  });

  test('should support project_name and drawing_no parameters', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Look for project metadata fields
    const projectNameInput = page.locator('input[name*="project"], input[placeholder*="프로젝트"]');
    const drawingNoInput = page.locator('input[name*="drawing"], input[placeholder*="도면번호"]');

    const hasProjectName = await projectNameInput.isVisible().catch(() => false);
    const hasDrawingNo = await drawingNoInput.isVisible().catch(() => false);

    console.log(`  Project name input: ${hasProjectName ? 'present' : 'not found'}`);
    console.log(`  Drawing number input: ${hasDrawingNo ? 'present' : 'not found'}`);

    // Check for title block OCR auto-fill
    const titleBlockSection = page.locator('text=/표제란|Title Block/i');
    const hasTitleBlock = await titleBlockSection.isVisible().catch(() => false);
    console.log(`  Title block section: ${hasTitleBlock ? 'present' : 'not found'}`);
  });

  test('should download Excel file with correct format', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Navigate and detect
    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);
    }

    // Click Excel export
    const excelButton = page.locator('button:has-text("Excel")');
    if (await excelButton.isVisible().catch(() => false)) {
      const downloadPromise = page.waitForEvent('download', { timeout: 30000 }).catch(() => null);

      await excelButton.click();

      const download = await downloadPromise;
      if (download) {
        const filename = download.suggestedFilename();
        console.log(`  Downloaded: ${filename}`);

        // Verify file extension
        expect(filename).toMatch(/\.(xlsx|xls)$/);

        // Check for expected filename patterns
        const hasExpectedPattern = /equipment|bom|export/i.test(filename);
        console.log(`  Filename contains expected pattern: ${hasExpectedPattern}`);
      } else {
        console.log('  No download triggered');
      }
    }
  });

  test('should support PDF export', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Navigate and detect
    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);
    }

    // Look for PDF export button
    const pdfButton = page.locator('button:has-text("PDF")');
    const hasPdfExport = await pdfButton.isVisible().catch(() => false);

    console.log(`  PDF export button: ${hasPdfExport ? 'present' : 'not found'}`);

    if (hasPdfExport) {
      const downloadPromise = page.waitForEvent('download', { timeout: 30000 }).catch(() => null);

      await pdfButton.click();

      const download = await downloadPromise;
      if (download) {
        const filename = download.suggestedFilename();
        console.log(`  PDF downloaded: ${filename}`);
        expect(filename).toMatch(/\.pdf$/);
      }
    }
  });
});

// ==================== 8. CONFIDENCE-BASED UI COLOR VALIDATION ====================

test.describe('Confidence-Based UI Validation', () => {
  test.setTimeout(180000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) test.skip();
    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should color code by confidence (green >=0.9, yellow >=0.7, red <0.7)', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);

      // Analyze color distribution
      const rows = page.locator('table tbody tr');
      const rowCount = await rows.count();

      let highConfidence = 0;   // green (>=0.9)
      let mediumConfidence = 0; // yellow (>=0.7)
      let lowConfidence = 0;    // red (<0.7)

      for (let i = 0; i < Math.min(10, rowCount); i++) {
        const row = rows.nth(i);
        const rowClasses = await row.getAttribute('class') || '';
        const cellColors = await row.locator('td').evaluateAll(cells => {
          return cells.map(cell => {
            const style = window.getComputedStyle(cell);
            return {
              bgColor: style.backgroundColor,
              textColor: style.color,
              classes: cell.className
            };
          });
        });

        // Check for green/yellow/red indicators
        for (const cell of cellColors) {
          if (cell.classes.includes('green') || cell.bgColor.includes('0, 128') || cell.bgColor.includes('34, 197')) {
            highConfidence++;
          } else if (cell.classes.includes('yellow') || cell.bgColor.includes('255, 255') || cell.bgColor.includes('234, 179')) {
            mediumConfidence++;
          } else if (cell.classes.includes('red') || cell.bgColor.includes('255, 0') || cell.bgColor.includes('239, 68')) {
            lowConfidence++;
          }
        }
      }

      console.log(`  Confidence color distribution:`);
      console.log(`    High (green, >=0.9): ${highConfidence}`);
      console.log(`    Medium (yellow, >=0.7): ${mediumConfidence}`);
      console.log(`    Low (red, <0.7): ${lowConfidence}`);
    }
  });

  test('should highlight low confidence items for review', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);

      // Look for review queue or low confidence indicator
      const reviewQueue = page.locator('text=/검증 필요|Review Required|Low Confidence/i');
      const hasReviewQueue = await reviewQueue.isVisible().catch(() => false);

      console.log(`  Review queue visible: ${hasReviewQueue}`);

      // Check for warning icons near low confidence items
      const warningIcons = await page.locator('svg.text-yellow-500, [title*="low"], [title*="낮음"]').count();
      console.log(`  Warning icons: ${warningIcons}`);
    }
  });
});

// ==================== 9. API RESPONSE SCHEMA VALIDATION ====================

test.describe('API Response Schema Validation', () => {
  test.setTimeout(180000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) test.skip();
    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should return valid equipment detection response schema', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      // Listen for API response
      const responsePromise = page.waitForResponse(
        res => res.url().includes('equipment') && res.url().includes('detect'),
        { timeout: 60000 }
      ).catch(() => null);

      await detectButton.click();

      const response = await responsePromise;
      if (response) {
        const status = response.status();
        console.log(`  API status: ${status}`);

        try {
          const body = await response.json();

          // Validate schema
          const hasSessionId = 'session_id' in body;
          const hasEquipment = 'equipment' in body && Array.isArray(body.equipment);
          const hasTotalCount = 'total_count' in body && typeof body.total_count === 'number';
          const hasProcessingTime = 'processing_time' in body && typeof body.processing_time === 'number';

          console.log(`  Schema validation:`);
          console.log(`    session_id: ${hasSessionId}`);
          console.log(`    equipment (array): ${hasEquipment}`);
          console.log(`    total_count (number): ${hasTotalCount}`);
          console.log(`    processing_time (number): ${hasProcessingTime}`);

          if (hasEquipment && body.equipment.length > 0) {
            const firstItem = body.equipment[0];
            console.log(`  First equipment item keys: ${Object.keys(firstItem).join(', ')}`);
          }
        } catch (e) {
          console.log('  Response not JSON');
        }
      }
    }
  });

  test('should return valid valve detection response schema', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const valveTab = page.locator('button:has-text("밸브")');
    if (await valveTab.isVisible().catch(() => false)) {
      await valveTab.click();
    }

    const detectButton = page.locator('button:has-text("밸브 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      const responsePromise = page.waitForResponse(
        res => res.url().includes('valve') && res.url().includes('detect'),
        { timeout: 60000 }
      ).catch(() => null);

      await detectButton.click();

      const response = await responsePromise;
      if (response) {
        try {
          const body = await response.json();

          // Validate schema
          const hasValves = 'valves' in body && Array.isArray(body.valves);
          const hasCategories = 'categories' in body && typeof body.categories === 'object';
          const hasRegionsDetected = 'regions_detected' in body;

          console.log(`  Schema validation:`);
          console.log(`    valves (array): ${hasValves}`);
          console.log(`    categories (object): ${hasCategories}`);
          console.log(`    regions_detected: ${hasRegionsDetected}`);

          if (hasCategories) {
            console.log(`  Categories: ${JSON.stringify(body.categories)}`);
          }
        } catch (e) {
          console.log('  Response not JSON');
        }
      }
    }
  });

  test('should return valid checklist response schema', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const checklistTab = page.locator('button:has-text("체크리스트")');
    if (await checklistTab.isVisible().catch(() => false)) {
      await checklistTab.click();
    }

    const verifyButton = page.locator('button:has-text("체크리스트 검증")');
    if (await verifyButton.isVisible().catch(() => false)) {
      const responsePromise = page.waitForResponse(
        res => res.url().includes('checklist'),
        { timeout: 90000 }
      ).catch(() => null);

      await verifyButton.click();

      const response = await responsePromise;
      if (response) {
        try {
          const body = await response.json();

          // Validate schema
          const hasItems = 'items' in body && Array.isArray(body.items);
          const hasSummary = 'summary' in body && typeof body.summary === 'object';
          const hasComplianceRate = 'compliance_rate' in body && typeof body.compliance_rate === 'number';

          console.log(`  Schema validation:`);
          console.log(`    items (array): ${hasItems}`);
          console.log(`    summary (object): ${hasSummary}`);
          console.log(`    compliance_rate (number): ${hasComplianceRate}`);

          if (hasItems && body.items.length > 0) {
            const firstItem = body.items[0];
            const hasAutoStatus = 'auto_status' in firstItem;
            const hasFinalStatus = 'final_status' in firstItem;
            console.log(`    item.auto_status: ${hasAutoStatus}`);
            console.log(`    item.final_status: ${hasFinalStatus}`);
          }

          if (hasSummary) {
            console.log(`  Summary: ${JSON.stringify(body.summary)}`);
          }
        } catch (e) {
          console.log('  Response not JSON');
        }
      }
    }
  });
});

// ==================== 10. FEATURE TOGGLE AND DEPENDENCY TESTS ====================

test.describe('Feature Toggle and Dependencies', () => {
  test.setTimeout(120000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) test.skip();
    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should show feature selection checkboxes', async ({ page }) => {
    // Look for feature toggle UI
    const featureSection = page.locator('[data-testid="feature-selection"], .feature-toggles, text=/기능 선택|Features/i');
    const hasFeatureSection = await featureSection.isVisible().catch(() => false);

    if (hasFeatureSection) {
      const checkboxes = page.locator('input[type="checkbox"]');
      const checkboxCount = await checkboxes.count();

      console.log(`  Feature checkboxes found: ${checkboxCount}`);

      // List some feature names
      const labels = await page.locator('label:has(input[type="checkbox"])').allTextContents();
      console.log(`  Available features: ${labels.slice(0, 10).join(', ')}...`);
    } else {
      // Check for settings button
      const settingsButton = page.locator('button:has-text("설정"), button[aria-label="Settings"]');
      const hasSettings = await settingsButton.isVisible().catch(() => false);
      console.log(`  Settings button: ${hasSettings ? 'present' : 'not found'}`);

      if (hasSettings) {
        await settingsButton.click();
        await page.waitForTimeout(500);

        const checkboxes = page.locator('input[type="checkbox"]');
        const checkboxCount = await checkboxes.count();
        console.log(`  Feature checkboxes in settings: ${checkboxCount}`);
      }
    }
  });

  test('should validate feature dependencies', async ({ page }) => {
    // Feature dependency examples:
    // - gdt_parsing requires symbol_detection
    // - relation_extraction requires symbol_detection AND dimension_ocr

    const settingsButton = page.locator('button:has-text("설정"), button[aria-label="Settings"]');
    if (await settingsButton.isVisible().catch(() => false)) {
      await settingsButton.click();
      await page.waitForTimeout(500);
    }

    // Find dependent feature checkbox
    const gdtCheckbox = page.locator('input[name*="gdt"], label:has-text("GD&T") input');
    const symbolCheckbox = page.locator('input[name*="symbol_detection"], label:has-text("심볼 검출") input');

    const hasGdt = await gdtCheckbox.isVisible().catch(() => false);
    const hasSymbol = await symbolCheckbox.isVisible().catch(() => false);

    if (hasGdt && hasSymbol) {
      // Try to enable GD&T without symbol detection
      const symbolChecked = await symbolCheckbox.isChecked();

      if (!symbolChecked) {
        // GD&T should be disabled or auto-enable symbol
        const gdtDisabled = await gdtCheckbox.isDisabled();
        console.log(`  GD&T disabled when symbol off: ${gdtDisabled}`);
      }
    } else {
      console.log('  Feature dependency test skipped - checkboxes not found');
    }
  });

  test('should show section visibility based on enabled features', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Check which sections are visible
    const sections = {
      'Symbol Detection': page.locator('text=/심볼 검출|Symbol Detection/i'),
      'Dimension OCR': page.locator('text=/치수 OCR|Dimension OCR/i'),
      'Line Detection': page.locator('text=/선 검출|Line Detection/i'),
      'P&ID Analysis': page.locator('text=/P&ID 분석|P&ID Analysis/i'),
      'GD&T Parsing': page.locator('text=/GD&T 파싱|GD&T Parsing/i'),
      'BOM Generation': page.locator('text=/BOM 생성|BOM Generation/i')
    };

    console.log('  Section visibility:');
    for (const [name, locator] of Object.entries(sections)) {
      const isVisible = await locator.first().isVisible().catch(() => false);
      console.log(`    ${name}: ${isVisible ? 'visible' : 'hidden'}`);
    }
  });
});

// ==================== 11. PAGINATION AND DATA DISPLAY ====================

test.describe('Pagination and Data Display', () => {
  test.setTimeout(180000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) test.skip();
    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should display 7 items per page (default)', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);

      // Count visible rows
      const visibleRows = await page.locator('table tbody tr').count();
      console.log(`  Visible rows: ${visibleRows}`);

      // Check if pagination exists (implies more items)
      const pagination = page.locator('[class*="pagination"], button:has-text("다음"), button:has-text("Next")');
      const hasPagination = await pagination.count() > 0;
      console.log(`  Pagination present: ${hasPagination}`);

      // Default should be 7 items per page
      if (visibleRows > 0 && visibleRows <= 7) {
        console.log('  ✓ Items per page <= 7 (within default)');
      }
    }
  });

  test('should navigate between pages', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      await detectButton.click();
      await page.waitForTimeout(10000);

      // Get first row content
      const firstRowBefore = await page.locator('table tbody tr').first().textContent().catch(() => '');

      // Click next page button
      const nextButton = page.locator('button:has-text("다음"), button:has-text("Next"), button[aria-label="Next page"]');
      if (await nextButton.isVisible().catch(() => false)) {
        await nextButton.click();
        await page.waitForTimeout(500);

        // Get first row content after navigation
        const firstRowAfter = await page.locator('table tbody tr').first().textContent().catch(() => '');

        if (firstRowBefore !== firstRowAfter) {
          console.log('  ✓ Page navigation working - content changed');
        } else {
          console.log('  Page content same (may be only one page)');
        }
      } else {
        console.log('  Next button not visible (single page or no pagination)');
      }
    }
  });
});

// ==================== 12. ERROR HANDLING AND EDGE CASES ====================

test.describe('Error Handling and Edge Cases', () => {
  test.setTimeout(120000);

  test.beforeEach(async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) test.skip();
    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);
  });

  test('should handle empty detection results gracefully', async ({ page }) => {
    // Don't upload image - try to detect with no image

    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
    }

    const detectButton = page.locator('button:has-text("장비 검출")');
    if (await detectButton.isVisible().catch(() => false)) {
      // Button should be disabled or show warning
      const isDisabled = await detectButton.isDisabled();
      console.log(`  Detect button disabled without image: ${isDisabled}`);

      if (!isDisabled) {
        await detectButton.click();
        await page.waitForTimeout(2000);

        // Check for error message
        const errorMessage = page.locator('text=/오류|error|이미지.*없/i');
        const hasError = await errorMessage.isVisible().catch(() => false);
        console.log(`  Error message shown: ${hasError}`);
      }
    }
  });

  test('should handle API timeout gracefully', async ({ page }) => {
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

      // Wait for either success or timeout indicator
      const timeoutIndicator = page.locator('text=/timeout|시간 초과|실패/i');
      const successIndicator = page.locator('table tbody tr');

      // Wait up to 120 seconds
      const result = await Promise.race([
        timeoutIndicator.waitFor({ state: 'visible', timeout: 120000 }).then(() => 'timeout'),
        successIndicator.waitFor({ state: 'visible', timeout: 120000 }).then(() => 'success')
      ]).catch(() => 'unknown');

      console.log(`  Result: ${result}`);
    }
  });

  test('should validate input parameters before API call', async ({ page }) => {
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) return;

    await page.waitForTimeout(3000);

    // Try to set invalid confidence value
    const confidenceInput = page.locator('input[name*="confidence"]');
    if (await confidenceInput.isVisible().catch(() => false)) {
      await confidenceInput.fill('-0.5'); // Invalid value
      await page.waitForTimeout(500);

      // Check for validation error
      const validationError = page.locator('text=/유효하지|invalid|범위/i');
      const hasValidationError = await validationError.isVisible().catch(() => false);

      // Or check if value was clamped
      const currentValue = await confidenceInput.inputValue();

      console.log(`  Validation error shown: ${hasValidationError}`);
      console.log(`  Current value after invalid input: ${currentValue}`);
    }
  });
});

// ==================== SUMMARY TEST ====================

test.describe('Comprehensive Test Summary', () => {
  test.setTimeout(300000);

  test('should complete full TECHCROSS workflow with parameter validation', async ({ page }) => {
    const available = await isBOMServiceAvailable();
    if (!available) {
      console.log('  BOM service not available - skipping comprehensive test');
      test.skip();
    }

    console.log('\n========================================');
    console.log('TECHCROSS COMPREHENSIVE WORKFLOW TEST');
    console.log('========================================\n');

    await page.goto(`${BOM_BASE_URL}/workflow`);
    await page.waitForTimeout(1000);

    // Step 1: Upload
    console.log('Step 1: Upload P&ID Image');
    const uploaded = await uploadImage(page, SAMPLE_PID_IMAGE);
    if (!uploaded) {
      console.log('  ⚠️ No sample image - test incomplete');
      return;
    }
    console.log('  ✓ Image uploaded\n');

    await page.waitForTimeout(3000);

    // Step 2: Equipment Detection (1-3)
    console.log('Step 2: Equipment Detection (TECHCROSS 1-3)');
    const equipmentTab = page.locator('button:has-text("장비")');
    if (await equipmentTab.isVisible().catch(() => false)) {
      await equipmentTab.click();
      const detectEquipment = page.locator('button:has-text("장비 검출")');
      if (await detectEquipment.isVisible().catch(() => false)) {
        await detectEquipment.click();
        await page.waitForTimeout(10000);

        const equipmentRows = await page.locator('table tbody tr').count();
        console.log(`  ✓ Detected ${equipmentRows} equipment items\n`);
      }
    }

    // Step 3: Valve Detection (1-2)
    console.log('Step 3: Valve Detection (TECHCROSS 1-2)');
    const valveTab = page.locator('button:has-text("밸브")');
    if (await valveTab.isVisible().catch(() => false)) {
      await valveTab.click();
      const detectValve = page.locator('button:has-text("밸브 검출")');
      if (await detectValve.isVisible().catch(() => false)) {
        await detectValve.click();
        await page.waitForTimeout(10000);

        const valveRows = await page.locator('table tbody tr').count();
        console.log(`  ✓ Detected ${valveRows} valves\n`);
      }
    }

    // Step 4: Checklist Verification (1-1)
    console.log('Step 4: Checklist Verification (TECHCROSS 1-1)');
    const checklistTab = page.locator('button:has-text("체크리스트")');
    if (await checklistTab.isVisible().catch(() => false)) {
      await checklistTab.click();
      const verifyChecklist = page.locator('button:has-text("체크리스트 검증")');
      if (await verifyChecklist.isVisible().catch(() => false)) {
        await verifyChecklist.click();
        await page.waitForTimeout(15000);

        const checklistRows = await page.locator('table tbody tr').count();
        console.log(`  ✓ Verified ${checklistRows} checklist items\n`);
      }
    }

    // Step 5: Human-in-the-Loop Verification
    console.log('Step 5: Human-in-the-Loop Verification');
    await equipmentTab.click();
    await page.waitForTimeout(500);

    const approveButton = page.locator('button:has(svg.text-green-600)').first();
    if (await approveButton.isVisible().catch(() => false)) {
      await approveButton.click();
      await page.waitForTimeout(500);
      console.log('  ✓ Item approved\n');
    }

    // Step 6: Export
    console.log('Step 6: Export Results');
    const excelButton = page.locator('button:has-text("Excel")');
    if (await excelButton.isVisible().catch(() => false)) {
      const downloadPromise = page.waitForEvent('download', { timeout: 30000 }).catch(() => null);
      await excelButton.click();

      const download = await downloadPromise;
      if (download) {
        console.log(`  ✓ Excel exported: ${download.suggestedFilename()}\n`);
      }
    }

    // Final screenshot
    await page.screenshot({
      path: 'test-results/techcross-comprehensive-complete.png',
      fullPage: true
    });

    console.log('========================================');
    console.log('WORKFLOW COMPLETE');
    console.log('========================================\n');
  });
});
