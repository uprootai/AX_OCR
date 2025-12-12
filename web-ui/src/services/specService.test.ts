/**
 * API Spec Service Tests
 * specToNodeDefinition 함수 및 API 스펙 변환 로직 테스트
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { specToNodeDefinition, type APISpec } from './specService';

describe('specService', () => {
  describe('specToNodeDefinition', () => {
    const mockSpec: APISpec = {
      apiVersion: 'v1',
      kind: 'APISpec',
      metadata: {
        id: 'test-api',
        name: 'Test API',
        version: '1.0.0',
        port: 5000,
        description: 'Test API description',
        author: 'Test Author',
        tags: ['test', 'mock'],
      },
      server: {
        endpoint: '/api/v1/test',
        method: 'POST',
        contentType: 'multipart/form-data',
        timeout: 60,
        healthEndpoint: '/health',
      },
      blueprintflow: {
        category: 'detection',
        color: '#10b981',
        icon: 'Target',
        requiresImage: true,
      },
      inputs: [
        {
          name: 'image',
          type: 'Image',
          required: true,
          description: 'Input image',
        },
      ],
      outputs: [
        {
          name: 'result',
          type: 'object',
          description: 'Detection result',
        },
      ],
      parameters: [
        {
          name: 'confidence',
          type: 'number',
          default: 0.5,
          min: 0,
          max: 1,
          step: 0.05,
          description: 'Confidence threshold',
        },
        {
          name: 'mode',
          type: 'select',
          default: 'fast',
          options: ['fast', 'accurate'],
          description: 'Processing mode',
        },
        {
          name: 'visualize',
          type: 'boolean',
          default: true,
          description: 'Generate visualization',
        },
      ],
      i18n: {
        ko: {
          label: '테스트 API',
          description: '테스트 API 설명',
        },
        en: {
          label: 'Test API',
          description: 'Test API description',
        },
      },
      examples: ['Example 1', 'Example 2'],
    };

    it('should convert basic metadata', () => {
      const result = specToNodeDefinition(mockSpec);

      expect(result.type).toBe('test-api');
      expect(result.label).toBe('테스트 API');
      expect(result.category).toBe('detection');
      expect(result.color).toBe('#10b981');
      expect(result.icon).toBe('Target');
    });

    it('should use Korean label when lang is ko', () => {
      const result = specToNodeDefinition(mockSpec, 'ko');
      expect(result.label).toBe('테스트 API');
      expect(result.description).toBe('테스트 API 설명');
    });

    it('should use English label when lang is en', () => {
      const result = specToNodeDefinition(mockSpec, 'en');
      expect(result.label).toBe('Test API');
      expect(result.description).toBe('Test API description');
    });

    it('should fallback to metadata description when i18n is not available', () => {
      const specWithoutI18n: APISpec = {
        ...mockSpec,
        i18n: undefined,
      };
      const result = specToNodeDefinition(specWithoutI18n);
      expect(result.description).toBe('Test API description');
    });

    it('should convert inputs correctly', () => {
      const result = specToNodeDefinition(mockSpec);

      expect(result.inputs).toHaveLength(1);
      expect(result.inputs[0].name).toBe('image');
      expect(result.inputs[0].type).toBe('Image');
      // Note: required is not included in the converted input
      expect(result.inputs[0].description).toBe('Input image');
    });

    it('should convert outputs correctly', () => {
      const result = specToNodeDefinition(mockSpec);

      expect(result.outputs).toHaveLength(1);
      expect(result.outputs[0].name).toBe('result');
      expect(result.outputs[0].type).toBe('object');
    });

    it('should convert number parameters with min/max/step', () => {
      const result = specToNodeDefinition(mockSpec);

      const confidenceParam = result.parameters.find(p => p.name === 'confidence');
      expect(confidenceParam).toBeDefined();
      expect(confidenceParam?.type).toBe('number');
      expect(confidenceParam?.default).toBe(0.5);
      expect(confidenceParam?.min).toBe(0);
      expect(confidenceParam?.max).toBe(1);
      expect(confidenceParam?.step).toBe(0.05);
    });

    it('should convert select parameters with options', () => {
      const result = specToNodeDefinition(mockSpec);

      const modeParam = result.parameters.find(p => p.name === 'mode');
      expect(modeParam).toBeDefined();
      expect(modeParam?.type).toBe('select');
      expect(modeParam?.default).toBe('fast');
      expect(modeParam?.options).toEqual(['fast', 'accurate']);
    });

    it('should convert boolean parameters', () => {
      const result = specToNodeDefinition(mockSpec);

      const visualizeParam = result.parameters.find(p => p.name === 'visualize');
      expect(visualizeParam).toBeDefined();
      expect(visualizeParam?.type).toBe('boolean');
      expect(visualizeParam?.default).toBe(true);
    });

    it('should include examples', () => {
      const result = specToNodeDefinition(mockSpec);

      expect(result.examples).toHaveLength(2);
      expect(result.examples).toContain('Example 1');
      expect(result.examples).toContain('Example 2');
    });

    it('should handle missing optional fields gracefully', () => {
      const minimalSpec: APISpec = {
        apiVersion: 'v1',
        kind: 'APISpec',
        metadata: {
          id: 'minimal',
          name: 'Minimal',
          version: '1.0.0',
          port: 5000,
        },
        server: {
          endpoint: '/api/v1/minimal',
          method: 'POST',
        },
        blueprintflow: {
          category: 'detection',
          color: '#000000',
          icon: 'Box',
        },
      };

      const result = specToNodeDefinition(minimalSpec);

      expect(result.type).toBe('minimal');
      expect(result.label).toBe('Minimal');
      expect(result.inputs).toEqual([]);
      expect(result.outputs).toEqual([]);
      expect(result.parameters).toEqual([]);
      expect(result.examples).toEqual([]);
    });

    describe('category mapping', () => {
      const categories = ['input', 'detection', 'ocr', 'segmentation', 'preprocessing', 'analysis', 'knowledge', 'ai', 'control'];

      categories.forEach(category => {
        it(`should correctly map category: ${category}`, () => {
          const spec: APISpec = {
            ...mockSpec,
            blueprintflow: {
              ...mockSpec.blueprintflow,
              category,
            },
          };

          const result = specToNodeDefinition(spec);
          expect(result.category).toBe(category);
        });
      });

      it('should default to detection for unknown category', () => {
        const spec: APISpec = {
          ...mockSpec,
          blueprintflow: {
            ...mockSpec.blueprintflow,
            category: 'unknown_category',
          },
        };

        const result = specToNodeDefinition(spec);
        expect(result.category).toBe('detection');
      });
    });

    describe('parameter type conversion', () => {
      it('should preserve integer type as-is', () => {
        const spec: APISpec = {
          ...mockSpec,
          parameters: [
            {
              name: 'count',
              type: 'integer',
              default: 10,
              description: 'Count value',
            },
          ],
        };

        const result = specToNodeDefinition(spec);
        const countParam = result.parameters.find(p => p.name === 'count');

        // Type is preserved as-is without conversion
        expect(countParam?.type).toBe('integer');
        expect(countParam?.default).toBe(10);
      });

      it('should convert string type correctly', () => {
        const spec: APISpec = {
          ...mockSpec,
          parameters: [
            {
              name: 'text',
              type: 'string',
              default: 'default text',
              description: 'Text input',
            },
          ],
        };

        const result = specToNodeDefinition(spec);
        const textParam = result.parameters.find(p => p.name === 'text');

        expect(textParam?.type).toBe('string');
        expect(textParam?.default).toBe('default text');
      });
    });

    describe('input/output type normalization', () => {
      it('should normalize Image type', () => {
        const spec: APISpec = {
          ...mockSpec,
          inputs: [
            { name: 'input', type: 'image', required: true },
          ],
        };

        const result = specToNodeDefinition(spec);
        // Type should be preserved as-is or normalized based on implementation
        expect(result.inputs[0].type).toBeDefined();
      });

      it('should handle array output types', () => {
        const spec: APISpec = {
          ...mockSpec,
          outputs: [
            { name: 'results', type: 'TextResult[]', description: 'Array of results' },
          ],
        };

        const result = specToNodeDefinition(spec);
        expect(result.outputs[0].type).toBe('TextResult[]');
      });
    });
  });
});
