import { describe, it, expect } from 'vitest';
import { nodeDefinitions, getNodeDefinition } from './nodeDefinitions';

describe('nodeDefinitions', () => {
  const requiredNodeTypes = [
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

  it('should have all required node types defined', () => {
    requiredNodeTypes.forEach(nodeType => {
      expect(nodeDefinitions[nodeType]).toBeDefined();
      expect(nodeDefinitions[nodeType].type).toBe(nodeType);
    });
  });

  it('should have valid categories for all nodes', () => {
    const validCategories = [
      'input', 'detection', 'ocr', 'segmentation',
      'preprocessing', 'analysis', 'knowledge', 'ai', 'control'
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
    expect(yoloNode?.label).toBe('YOLO Detection');
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
          expect(['number', 'string', 'boolean', 'select']).toContain(param.type);
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
});
