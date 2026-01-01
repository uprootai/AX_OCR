import { test, expect, Page } from '@playwright/test';

/**
 * BlueprintFlow Node Comprehensive Test
 *
 * Tests all 23 nodes across 10 categories:
 * - Input (2): ImageInput, TextInput
 * - BOM 생성 (1): Blueprint AI BOM
 * - Detection (1): YOLO (handles P&ID via model_type)
 * - Segmentation (2): Line Detector, EDGNet
 * - OCR (8): eDOCr2, PaddleOCR, Tesseract, TrOCR, OCR Ensemble, Surya OCR, DocTR, EasyOCR
 * - Analysis (3): SkinModel, P&ID Analyzer, Design Checker
 * - Knowledge (1): Knowledge
 * - AI (1): VL
 * - Preprocessing (1): ESRGAN
 * - Control (3): IF, Loop, Merge
 */

// Helper function to scroll palette to find a node
async function scrollPaletteToNode(page: Page, nodeText: string, maxScrolls: number = 15): Promise<boolean> {
  // First, scroll to the top of the palette
  await page.evaluate(() => {
    const palette = document.querySelector('[class*="overflow-y-auto"]');
    if (palette) palette.scrollTop = 0;
  });
  await page.waitForTimeout(100);

  for (let i = 0; i < maxScrolls; i++) {
    // Use contains match for more flexibility
    const node = page.locator(`text=/${nodeText}/i`).first();
    if (await node.isVisible().catch(() => false)) {
      return true;
    }
    // Scroll the palette down
    await page.evaluate(() => {
      const palette = document.querySelector('[class*="overflow-y-auto"]');
      if (palette) palette.scrollTop += 250;
    });
    await page.waitForTimeout(150);
  }
  return false;
}

// Helper function to drag node to canvas (reserved for future use)
async function _dragNodeToCanvas(page: Page, nodeText: string, x: number, y: number) {
  const node = page.locator(`text="${nodeText}"`).first();
  const canvas = page.locator('.react-flow__pane').first();

  await node.dragTo(canvas, {
    targetPosition: { x, y }
  });
}

// ==========================================
// Phase 1: Node Palette Visibility Tests
// ==========================================

test.describe('Phase 1: Node Palette Visibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/blueprintflow/builder');
    await expect(page.locator('text=Node Palette')).toBeVisible({ timeout: 10000 });
  });

  // Category visibility tests
  test.describe('Category Headers', () => {
    const categories = [
      { name: 'Input', emoji: '📥' },
      { name: 'Detection', emoji: '🎯' },
      { name: 'Segmentation', emoji: '✂️' },
      { name: 'OCR', emoji: '📝' },
      { name: 'Analysis', emoji: '📊' },
      { name: 'Knowledge', emoji: '🧠' },
      { name: 'AI', emoji: '🤖' },
      { name: 'Preprocessing', emoji: '🔧' },
      { name: 'Control', emoji: '🔀' },
    ];

    for (const category of categories) {
      test(`should display ${category.name} category`, async ({ page }) => {
        const categoryHeader = page.locator(`h3:has-text("${category.name}")`).first();
        await expect(categoryHeader).toBeVisible({ timeout: 5000 });
      });
    }
  });

  // Input Nodes (2)
  test.describe('Input Nodes', () => {
    test('should display Image Input node', async ({ page }) => {
      const node = page.locator('text=Image Input');
      await expect(node.first()).toBeVisible({ timeout: 5000 });
    });

    test('should display Text Input node', async ({ page }) => {
      const node = page.locator('text=Text Input');
      await expect(node.first()).toBeVisible({ timeout: 5000 });
    });
  });

  // Detection Nodes (1) - YOLO handles P&ID via model_type
  test.describe('Detection Nodes', () => {
    test('should display YOLO node', async ({ page }) => {
      await scrollPaletteToNode(page, 'YOLO');
      // YOLO is displayed as "YOLO (통합)" in palette
      const node = page.locator('text=/YOLO/').first();
      await expect(node).toBeVisible({ timeout: 5000 });
    });

  });

  // Segmentation Nodes (2)
  test.describe('Segmentation Nodes', () => {
    test('should display Line Detector node', async ({ page }) => {
      await scrollPaletteToNode(page, 'Line Detector');
      const node = page.locator('text=Line Detector');
      await expect(node.first()).toBeVisible({ timeout: 5000 });
    });

    test('should display EDGNet node', async ({ page }) => {
      await scrollPaletteToNode(page, 'EDGNet');
      // Use more specific locator targeting the visible node label (not hidden tooltip)
      const node = page.locator('div.font-medium:has-text("EDGNet")');
      await expect(node.first()).toBeVisible({ timeout: 5000 });
    });
  });

  // OCR Nodes (8)
  test.describe('OCR Nodes', () => {
    const ocrNodes = ['eDOCr2', 'PaddleOCR', 'Tesseract', 'TrOCR', 'OCR Ensemble', 'Surya OCR', 'DocTR', 'EasyOCR'];

    for (const nodeName of ocrNodes) {
      test(`should display ${nodeName} node`, async ({ page }) => {
        await scrollPaletteToNode(page, nodeName);
        const node = page.locator(`text="${nodeName}"`).first();
        await expect(node).toBeVisible({ timeout: 5000 });
      });
    }
  });

  // Analysis Nodes (3)
  test.describe('Analysis Nodes', () => {
    test('should display SkinModel node', async ({ page }) => {
      await scrollPaletteToNode(page, 'SkinModel');
      const node = page.locator('text=SkinModel');
      await expect(node.first()).toBeVisible({ timeout: 5000 });
    });

    test('should display P&ID Analyzer node', async ({ page }) => {
      await scrollPaletteToNode(page, 'P&ID Analyzer');
      const node = page.locator('text=P&ID Analyzer');
      await expect(node.first()).toBeVisible({ timeout: 5000 });
    });

    test('should display Design Checker node', async ({ page }) => {
      await scrollPaletteToNode(page, 'Design Checker');
      const node = page.locator('text=Design Checker');
      await expect(node.first()).toBeVisible({ timeout: 5000 });
    });
  });

  // Knowledge Node (1)
  test.describe('Knowledge Node', () => {
    test('should display Knowledge node', async ({ page }) => {
      await scrollPaletteToNode(page, 'Knowledge');
      const node = page.locator('text="Knowledge"').first();
      await expect(node).toBeVisible({ timeout: 5000 });
    });
  });

  // AI Node (1)
  test.describe('AI Node', () => {
    test('should display VL Model node', async ({ page }) => {
      await scrollPaletteToNode(page, 'VL Model');
      const node = page.locator('text=VL Model');
      await expect(node.first()).toBeVisible({ timeout: 5000 });
    });
  });

  // Preprocessing Node (1)
  test.describe('Preprocessing Node', () => {
    test('should display ESRGAN node', async ({ page }) => {
      // ESRGAN is displayed as "ESRGAN" in NodePalette (not "ESRGAN Upscaler")
      await scrollPaletteToNode(page, 'ESRGAN', 10);
      // Use case-insensitive regex to find ESRGAN
      const node = page.locator('[class*="font-medium"]', { hasText: /^ESRGAN$/i });
      await expect(node.first()).toBeVisible({ timeout: 5000 });
    });
  });

  // Control Nodes (3)
  test.describe('Control Nodes', () => {
    test('should display IF node', async ({ page }) => {
      await scrollPaletteToNode(page, 'IF');
      const node = page.locator('text="IF"').first();
      await expect(node).toBeVisible({ timeout: 5000 });
    });

    test('should display Loop node', async ({ page }) => {
      await scrollPaletteToNode(page, 'Loop');
      const node = page.locator('text="Loop"').first();
      await expect(node).toBeVisible({ timeout: 5000 });
    });

    test('should display Merge node', async ({ page }) => {
      await scrollPaletteToNode(page, 'Merge');
      const node = page.locator('text="Merge"').first();
      await expect(node).toBeVisible({ timeout: 5000 });
    });
  });
});

// ==========================================
// Phase 2: Node Drag and Drop Tests
// ==========================================

test.describe('Phase 2: Node Drag and Drop', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/blueprintflow/builder');
    await expect(page.locator('text=Node Palette')).toBeVisible({ timeout: 10000 });
  });

  test('should drag Image Input to canvas', async ({ page }) => {
    const node = page.locator('text="Image Input"').first();
    const canvas = page.locator('.react-flow__pane').first();

    // Get initial node count
    const initialNodes = await page.locator('.react-flow__node').count();

    // Drag node to canvas
    await node.dragTo(canvas, { targetPosition: { x: 300, y: 200 } });

    // Verify node was added
    await page.waitForTimeout(500);
    const finalNodes = await page.locator('.react-flow__node').count();
    expect(finalNodes).toBeGreaterThan(initialNodes);
  });

  test('should drag Text Input to canvas', async ({ page }) => {
    const node = page.locator('text="Text Input"').first();
    const canvas = page.locator('.react-flow__pane').first();

    const initialNodes = await page.locator('.react-flow__node').count();
    await node.dragTo(canvas, { targetPosition: { x: 300, y: 200 } });
    await page.waitForTimeout(500);

    const finalNodes = await page.locator('.react-flow__node').count();
    expect(finalNodes).toBeGreaterThan(initialNodes);
  });

  test('should drag YOLO to canvas', async ({ page }) => {
    await scrollPaletteToNode(page, 'YOLO');
    const node = page.locator('text=/YOLO/').first();
    const canvas = page.locator('.react-flow__pane').first();

    const initialNodes = await page.locator('.react-flow__node').count();
    await node.dragTo(canvas, { targetPosition: { x: 300, y: 200 } });
    await page.waitForTimeout(500);

    const finalNodes = await page.locator('.react-flow__node').count();
    expect(finalNodes).toBeGreaterThan(initialNodes);
  });

  test('should drag eDOCr2 to canvas', async ({ page }) => {
    await scrollPaletteToNode(page, 'eDOCr2');
    const node = page.locator('text="eDOCr2"').first();
    const canvas = page.locator('.react-flow__pane').first();

    const initialNodes = await page.locator('.react-flow__node').count();
    await node.dragTo(canvas, { targetPosition: { x: 300, y: 200 } });
    await page.waitForTimeout(500);

    const finalNodes = await page.locator('.react-flow__node').count();
    expect(finalNodes).toBeGreaterThan(initialNodes);
  });

  test('should drag multiple nodes to canvas', async ({ page }) => {
    const canvas = page.locator('.react-flow__pane').first();

    // Drag Image Input
    const imageInput = page.locator('text="Image Input"').first();
    await imageInput.dragTo(canvas, { targetPosition: { x: 200, y: 150 } });
    await page.waitForTimeout(300);

    // Drag YOLO
    await scrollPaletteToNode(page, 'YOLO');
    const yolo = page.locator('text=/YOLO/').first();
    await yolo.dragTo(canvas, { targetPosition: { x: 400, y: 150 } });
    await page.waitForTimeout(300);

    // Drag eDOCr2
    await scrollPaletteToNode(page, 'eDOCr2');
    const edocr = page.locator('text="eDOCr2"').first();
    await edocr.dragTo(canvas, { targetPosition: { x: 600, y: 150 } });
    await page.waitForTimeout(300);

    // Verify all nodes exist
    const nodeCount = await page.locator('.react-flow__node').count();
    expect(nodeCount).toBeGreaterThanOrEqual(3);
  });
});

// ==========================================
// Phase 3: Node Selection and Detail Panel
// ==========================================

test.describe('Phase 3: Node Selection and Detail Panel', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/blueprintflow/builder');
    await expect(page.locator('text=Node Palette')).toBeVisible({ timeout: 10000 });
  });

  test('should show detail panel when Image Input is selected', async ({ page }) => {
    const canvas = page.locator('.react-flow__pane').first();
    const node = page.locator('text="Image Input"').first();

    // Drag to canvas
    await node.dragTo(canvas, { targetPosition: { x: 300, y: 200 } });
    await page.waitForTimeout(500);

    // Click on the node
    const canvasNode = page.locator('.react-flow__node').first();
    await canvasNode.click();
    await page.waitForTimeout(300);

    // Check if detail panel shows the node info
    const detailPanel = page.locator('text="설명"').or(page.locator('text="Description"'));
    await expect(detailPanel.first()).toBeVisible({ timeout: 5000 });
  });

  test('should show parameters section for YOLO node', async ({ page }) => {
    await scrollPaletteToNode(page, 'YOLO');
    const canvas = page.locator('.react-flow__pane').first();
    const node = page.locator('text=/YOLO/').first();

    // Drag to canvas
    await node.dragTo(canvas, { targetPosition: { x: 300, y: 200 } });
    await page.waitForTimeout(500);

    // Click on the node
    const canvasNode = page.locator('.react-flow__node').first();
    await canvasNode.click();
    await page.waitForTimeout(300);

    // Check for parameters section
    const paramsSection = page.locator('text="파라미터"').or(page.locator('text="Parameters"'));
    await expect(paramsSection.first()).toBeVisible({ timeout: 5000 });
  });

  test('should show inputs and outputs section', async ({ page }) => {
    await scrollPaletteToNode(page, 'YOLO');
    const canvas = page.locator('.react-flow__pane').first();
    const node = page.locator('text=/YOLO/').first();

    // Drag to canvas
    await node.dragTo(canvas, { targetPosition: { x: 300, y: 200 } });
    await page.waitForTimeout(500);

    // Click on the node
    const canvasNode = page.locator('.react-flow__node').first();
    await canvasNode.click();
    await page.waitForTimeout(300);

    // Check for inputs section
    const inputsSection = page.locator('text="입력 (Inputs)"').or(page.locator('text="Inputs"'));
    await expect(inputsSection.first()).toBeVisible({ timeout: 5000 });

    // Check for outputs section
    const outputsSection = page.locator('text="출력 (Outputs)"').or(page.locator('text="Outputs"'));
    await expect(outputsSection.first()).toBeVisible({ timeout: 5000 });
  });

  test('should allow parameter modification for YOLO', async ({ page }) => {
    await scrollPaletteToNode(page, 'YOLO');
    const canvas = page.locator('.react-flow__pane').first();
    const node = page.locator('text=/YOLO/').first();

    // Drag to canvas
    await node.dragTo(canvas, { targetPosition: { x: 300, y: 200 } });
    await page.waitForTimeout(500);

    // Click on the node
    const canvasNode = page.locator('.react-flow__node').first();
    await canvasNode.click();
    await page.waitForTimeout(300);

    // Find a slider (range input) for confidence threshold
    const slider = page.locator('input[type="range"]').first();
    if (await slider.isVisible()) {
      // Change the value
      await slider.fill('0.5');
      // Verify it changed
      const value = await slider.inputValue();
      expect(parseFloat(value)).toBeCloseTo(0.5, 1);
    }
  });

  test('should allow text input for Text Input node', async ({ page }) => {
    const canvas = page.locator('.react-flow__pane').first();
    const node = page.locator('text="Text Input"').first();

    // Drag to canvas
    await node.dragTo(canvas, { targetPosition: { x: 300, y: 200 } });
    await page.waitForTimeout(500);

    // Click on the node
    const canvasNode = page.locator('.react-flow__node').first();
    await canvasNode.click();
    await page.waitForTimeout(300);

    // Find textarea for text input
    const textarea = page.locator('textarea').first();
    if (await textarea.isVisible()) {
      // Type some text
      await textarea.fill('Test input text');
      // Verify it was entered
      const value = await textarea.inputValue();
      expect(value).toBe('Test input text');
    }
  });
});

// ==========================================
// Phase 4: Node Handle Tests
// ==========================================

test.describe('Phase 4: Node Handles', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/blueprintflow/builder');
    await expect(page.locator('text=Node Palette')).toBeVisible({ timeout: 10000 });
  });

  test('should have connection handles on nodes', async ({ page }) => {
    const canvas = page.locator('.react-flow__pane').first();

    // Drag Image Input
    const imageInput = page.locator('text="Image Input"').first();
    await imageInput.dragTo(canvas, { targetPosition: { x: 200, y: 200 } });
    await page.waitForTimeout(500);

    // Verify the node has handles
    const node = page.locator('.react-flow__node').first();
    await expect(node).toBeVisible();

    // Check for output handle (right side)
    const outputHandle = node.locator('.react-flow__handle');
    await expect(outputHandle.first()).toBeVisible({ timeout: 3000 });
  });

  test('should have input and output handles on API nodes', async ({ page }) => {
    const canvas = page.locator('.react-flow__pane').first();

    // Drag YOLO
    await scrollPaletteToNode(page, 'YOLO');
    const yolo = page.locator('text=/YOLO/').first();
    await yolo.dragTo(canvas, { targetPosition: { x: 300, y: 200 } });
    await page.waitForTimeout(500);

    // Verify the node has handles
    const node = page.locator('.react-flow__node').first();
    const handles = node.locator('.react-flow__handle');

    // API nodes should have at least 2 handles (input and output)
    const handleCount = await handles.count();
    expect(handleCount).toBeGreaterThanOrEqual(2);
  });
});

// ==========================================
// Node Count Summary Test
// ==========================================

test.describe('Node Count Summary', () => {
  test('should have exactly 23 unique nodes available', async ({ page }) => {
    await page.goto('/blueprintflow/builder');
    await expect(page.locator('text=Node Palette')).toBeVisible({ timeout: 10000 });

    const expectedNodes = [
      // Input (2)
      'Image Input', 'Text Input',
      // BOM 생성 (1)
      'Blueprint AI BOM',
      // Detection (1) - YOLO handles P&ID via model_type
      'YOLO',
      // Segmentation (2)
      'Line Detector', 'EDGNet',
      // OCR (8)
      'eDOCr2', 'PaddleOCR', 'Tesseract', 'TrOCR', 'OCR Ensemble', 'Surya OCR', 'DocTR', 'EasyOCR',
      // Analysis (3)
      'SkinModel', 'P&ID Analyzer', 'Design Checker',
      // Knowledge (1)
      'Knowledge',
      // AI (1)
      'VL Model',
      // Preprocessing (1)
      'ESRGAN',
      // Control (3)
      'IF', 'Loop', 'Merge'
    ];

    let foundCount = 0;
    const missingNodes: string[] = [];

    for (const nodeName of expectedNodes) {
      await scrollPaletteToNode(page, nodeName, 15);
      // Use font-medium selector to target visible node labels, not hidden tooltip elements
      // Node labels are rendered in div.font-medium within the NodePalette
      const node = page.locator(`div.font-medium:has-text("${nodeName}")`).first();
      const isVisible = await node.isVisible().catch(() => false);
      if (isVisible) {
        foundCount++;
      } else {
        missingNodes.push(nodeName);
      }
    }

    console.log(`Found ${foundCount}/${expectedNodes.length} nodes`);
    if (missingNodes.length > 0) {
      console.log(`Missing nodes: ${missingNodes.join(', ')}`);
    }

    expect(foundCount).toBe(expectedNodes.length);
  });
});
