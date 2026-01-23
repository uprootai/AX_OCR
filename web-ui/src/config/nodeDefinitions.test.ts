import { describe, it, expect, beforeEach } from 'vitest';
import { nodeDefinitions, getNodeDefinition, getAllNodeDefinitions } from './nodeDefinitions';

describe('nodeDefinitions', () => {
  // Core node types (16개)
  const coreNodeTypes = [
    'imageinput',
    'textinput',
    'yolo',
    'edocr2',
    'edgnet',
    'skinmodel',
    'paddleocr',
    'vl',
    'if',
    'loop',
    'merge',
    'knowledge',
    'tesseract',
    'trocr',
    'esrgan',
    'ocr_ensemble',
  ];

  // Additional OCR node types (3개)
  const additionalOCRNodes = ['suryaocr', 'doctr', 'easyocr'];

  // P&ID Analysis node types (3개)
  const pidAnalysisNodes = ['linedetector', 'pidanalyzer', 'designchecker'];

  // All required node types (총 22개)
  const requiredNodeTypes = [
    ...coreNodeTypes,
    ...additionalOCRNodes,
    ...pidAnalysisNodes,
  ];

  it('should have all required node types defined', () => {
    requiredNodeTypes.forEach(nodeType => {
      expect(nodeDefinitions[nodeType]).toBeDefined();
      expect(nodeDefinitions[nodeType].type).toBe(nodeType);
    });
  });

  it('should have valid categories for all nodes', () => {
    const validCategories = [
      'input', 'detection', 'ocr', 'segmentation',
      'preprocessing', 'analysis', 'knowledge', 'ai', 'control', 'bom'
    ];

    Object.values(nodeDefinitions).forEach(node => {
      expect(validCategories).toContain(node.category);
    });
  });

  it('should have all required fields in each node definition', () => {
    Object.entries(nodeDefinitions).forEach(([type, node]) => {
      expect(node.type).toBe(type);
      expect(node.label).toBeTruthy();
      expect(node.color).toMatch(/^#[0-9a-f]{6}$/i);
      expect(node.description).toBeTruthy();
      expect(Array.isArray(node.inputs)).toBe(true);
      expect(Array.isArray(node.outputs)).toBe(true);
      expect(Array.isArray(node.parameters)).toBe(true);
      expect(Array.isArray(node.examples)).toBe(true);
    });
  });

  it('should return correct node definition using getNodeDefinition', () => {
    const yoloNode = getNodeDefinition('yolo');
    expect(yoloNode).toBeDefined();
    expect(yoloNode?.label).toBe('YOLO (통합)');
    expect(yoloNode?.category).toBe('detection');
  });

  it('should return undefined for unknown node type', () => {
    const unknownNode = getNodeDefinition('unknown_node_type');
    expect(unknownNode).toBeUndefined();
  });

  describe('API nodes should have parameters', () => {
    const apiNodeTypes = [
      'yolo', 'edocr2', 'edgnet', 'skinmodel',
      'paddleocr', 'vl', 'knowledge', 'tesseract',
      'trocr', 'esrgan', 'ocr_ensemble'
    ];

    apiNodeTypes.forEach(nodeType => {
      it(`${nodeType} should have at least one parameter`, () => {
        const node = nodeDefinitions[nodeType];
        expect(node.parameters.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Parameter validation', () => {
    it('all parameters should have required fields', () => {
      Object.values(nodeDefinitions).forEach(node => {
        node.parameters.forEach(param => {
          expect(param.name).toBeTruthy();
          expect(['number', 'string', 'boolean', 'select', 'textarea', 'checkboxGroup']).toContain(param.type);
          expect(param.description).toBeTruthy();
          expect(param.default).toBeDefined();
        });
      });
    });

    it('select parameters should have options', () => {
      Object.values(nodeDefinitions).forEach(node => {
        node.parameters
          .filter(p => p.type === 'select')
          .forEach(param => {
            expect(param.options).toBeDefined();
            expect(param.options?.length).toBeGreaterThan(0);
          });
      });
    });

    it('number parameters should have min/max/step', () => {
      Object.values(nodeDefinitions).forEach(node => {
        node.parameters
          .filter(p => p.type === 'number')
          .forEach(param => {
            expect(typeof param.min).toBe('number');
            expect(typeof param.max).toBe('number');
            expect(typeof param.step).toBe('number');
          });
      });
    });
  });

  describe('Input/Output validation', () => {
    it('input nodes should have no inputs', () => {
      ['imageinput', 'textinput'].forEach(nodeType => {
        const node = nodeDefinitions[nodeType];
        expect(node.inputs.length).toBe(0);
      });
    });

    it('input nodes should have outputs', () => {
      ['imageinput', 'textinput'].forEach(nodeType => {
        const node = nodeDefinitions[nodeType];
        expect(node.outputs.length).toBeGreaterThan(0);
      });
    });

    it('API nodes should have both inputs and outputs', () => {
      const apiNodes = ['yolo', 'edocr2', 'paddleocr', 'edgnet'];
      apiNodes.forEach(nodeType => {
        const node = nodeDefinitions[nodeType];
        expect(node.inputs.length).toBeGreaterThan(0);
        expect(node.outputs.length).toBeGreaterThan(0);
      });
    });
  });

  describe('getAllNodeDefinitions', () => {
    beforeEach(() => {
      // Clear localStorage before each test
      localStorage.clear();
    });

    it('should return all base node definitions when no custom APIs exist', () => {
      const allNodes = getAllNodeDefinitions();
      // Should return at least the base definitions
      expect(Object.keys(allNodes).length).toBeGreaterThanOrEqual(Object.keys(nodeDefinitions).length);
    });

    it('should return base definitions with proper structure', () => {
      const allNodes = getAllNodeDefinitions();
      // Verify base definitions are included
      expect(allNodes['yolo']).toBeDefined();
      expect(allNodes['yolo'].type).toBe('yolo');
      expect(allNodes['edocr2']).toBeDefined();
      expect(allNodes['edocr2'].type).toBe('edocr2');
    });

    it('should handle malformed localStorage data gracefully', () => {
      localStorage.setItem('custom-apis-storage', 'invalid-json');

      // Should not throw, should return base definitions
      const allNodes = getAllNodeDefinitions();
      expect(Object.keys(allNodes).length).toBeGreaterThanOrEqual(Object.keys(nodeDefinitions).length);
    });

    it('should handle empty localStorage gracefully', () => {
      localStorage.setItem('custom-apis-storage', JSON.stringify({ state: { customAPIs: [] } }));

      const allNodes = getAllNodeDefinitions();
      expect(Object.keys(allNodes).length).toBe(Object.keys(nodeDefinitions).length);
    });
  });

  describe('Additional OCR nodes', () => {
    const additionalOCRNodes = ['suryaocr', 'doctr', 'easyocr'];

    additionalOCRNodes.forEach(nodeType => {
      describe(nodeType, () => {
        it('should be defined', () => {
          expect(nodeDefinitions[nodeType]).toBeDefined();
        });

        it('should have category "ocr"', () => {
          expect(nodeDefinitions[nodeType].category).toBe('ocr');
        });

        it('should have image input', () => {
          const hasImageInput = nodeDefinitions[nodeType].inputs.some(
            input => input.type === 'image' || input.type === 'Image'
          );
          expect(hasImageInput).toBe(true);
        });

        it('should have at least one output', () => {
          expect(nodeDefinitions[nodeType].outputs.length).toBeGreaterThan(0);
        });
      });
    });
  });

  describe('P&ID Analysis nodes', () => {
    const pidNodes = {
      linedetector: { category: 'segmentation', label: 'Line Detector', hasImageInput: true },
      pidanalyzer: { category: 'analysis', label: 'P&ID Analyzer', hasImageInput: false },
      designchecker: { category: 'analysis', label: 'Design Checker', hasImageInput: false },
    };

    Object.entries(pidNodes).forEach(([nodeType, expected]) => {
      describe(nodeType, () => {
        it('should be defined', () => {
          expect(nodeDefinitions[nodeType]).toBeDefined();
        });

        it(`should have category "${expected.category}"`, () => {
          expect(nodeDefinitions[nodeType].category).toBe(expected.category);
        });

        it(`should have label "${expected.label}"`, () => {
          expect(nodeDefinitions[nodeType].label).toBe(expected.label);
        });

        if (expected.hasImageInput) {
          it('should have image input', () => {
            const hasImageInput = nodeDefinitions[nodeType].inputs.some(
              input => input.type === 'Image' || input.type === 'image'
            );
            expect(hasImageInput).toBe(true);
          });
        } else {
          it('should have data input (not image)', () => {
            expect(nodeDefinitions[nodeType].inputs.length).toBeGreaterThan(0);
          });
        }

        it('should have examples array', () => {
          expect(Array.isArray(nodeDefinitions[nodeType].examples)).toBe(true);
        });
      });
    });
  });

  describe('Control nodes', () => {
    const controlNodes = ['if', 'loop', 'merge'];

    controlNodes.forEach(nodeType => {
      describe(nodeType, () => {
        it('should be defined', () => {
          expect(nodeDefinitions[nodeType]).toBeDefined();
        });

        it('should have category "control"', () => {
          expect(nodeDefinitions[nodeType].category).toBe('control');
        });
      });
    });

    it('IF node should have "true" and "false" outputs', () => {
      const ifNode = nodeDefinitions['if'];
      const outputNames = ifNode.outputs.map(o => o.name);
      expect(outputNames).toContain('true');
      expect(outputNames).toContain('false');
    });

    it('Loop node should have iterator parameter', () => {
      const loopNode = nodeDefinitions['loop'];
      const paramNames = loopNode.parameters.map(p => p.name);
      expect(paramNames).toContain('iterator');
    });
  });

  describe('Node color format', () => {
    it('all nodes should have valid hex color codes', () => {
      Object.values(nodeDefinitions).forEach(node => {
        expect(node.color).toMatch(/^#[0-9a-fA-F]{6}$/);
      });
    });

    it('nodes within each category should have defined colors', () => {
      const categories = ['detection', 'ocr', 'segmentation', 'analysis', 'control'];
      categories.forEach(category => {
        const categoryNodes = Object.values(nodeDefinitions).filter(
          node => node.category === category
        );
        categoryNodes.forEach(node => {
          expect(node.color).toBeTruthy();
          expect(node.color).toMatch(/^#[0-9a-fA-F]{6}$/);
        });
      });
    });
  });

  describe('Node description quality', () => {
    it('all nodes should have descriptions with at least 10 characters', () => {
      Object.values(nodeDefinitions).forEach(node => {
        expect(node.description.length).toBeGreaterThanOrEqual(10);
      });
    });

    it('no description should be a placeholder', () => {
      const placeholders = ['TODO', 'TBD', 'placeholder', 'description here'];
      Object.values(nodeDefinitions).forEach(node => {
        placeholders.forEach(placeholder => {
          expect(node.description.toLowerCase()).not.toContain(placeholder.toLowerCase());
        });
      });
    });
  });

  describe('Node count verification', () => {
    it('should have exactly 35 node types', () => {
      // 23 기존 + 5 신규 + 1 pidcomposer + 1 table_detector + 1 titleblock + 1 partslist + 1 dimensionparser + 1 bommatcher + 1 quotegenerator
      expect(Object.keys(nodeDefinitions).length).toBe(35);
    });

    it('should have correct count per category', () => {
      const categoryCounts: Record<string, number> = {};
      Object.values(nodeDefinitions).forEach(node => {
        categoryCounts[node.category] = (categoryCounts[node.category] || 0) + 1;
      });

      expect(categoryCounts['input']).toBe(2);      // imageinput, textinput
      expect(categoryCounts['detection']).toBe(2);  // yolo (통합 API), table_detector
      expect(categoryCounts['ocr']).toBe(8);        // edocr2, paddleocr, tesseract, trocr, ocr_ensemble, suryaocr, doctr, easyocr
      expect(categoryCounts['segmentation']).toBe(2); // edgnet, linedetector
      expect(categoryCounts['preprocessing']).toBe(1); // esrgan
      expect(categoryCounts['analysis']).toBe(14);  // skinmodel, pidanalyzer, designchecker, pidcomposer, titleblock, partslist, dimensionparser, bommatcher, quotegenerator + gtcomparison, pdfexport, excelexport, pidfeatures, verificationqueue
      expect(categoryCounts['knowledge']).toBe(1);  // knowledge
      expect(categoryCounts['ai']).toBe(1);         // vl
      expect(categoryCounts['control']).toBe(3);    // if, loop, merge
      expect(categoryCounts['bom']).toBe(1);        // blueprint-ai-bom
    });
  });
});
