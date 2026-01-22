/**
 * Tests for specToHyperparams utility
 */

import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest';
import axios from 'axios';
import {
  fetchSpecParameters,
  getHyperparamDefinitions,
  getDefaultHyperparams,
  getHyperparamDefinitionsWithFallback,
  getDefaultHyperparamsWithFallback,
  clearSpecCache,
  type HyperparamDefinition,
} from './specToHyperparams';

vi.mock('axios');
const mockedAxiosGet = axios.get as Mock;

const mockSpecResponse = {
  data: {
    spec: {
      parameters: [
        { name: 'confidence', type: 'number', default: 0.25, min: 0, max: 1, step: 0.05, description: 'Detection confidence' },
        { name: 'visualize', type: 'boolean', default: true, description: 'Generate visualization' },
        { name: 'model_type', type: 'select', default: 'engineering', options: ['engineering', 'pid_symbol'], description: 'Model type' },
        { name: 'language', type: 'string', default: 'eng', description: 'OCR language' },
        { name: 'engines', type: 'array', default: ['tesseract'], description: 'OCR engines' },
      ],
    },
  },
};

describe('specToHyperparams', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearSpecCache();
  });

  afterEach(() => {
    clearSpecCache();
  });

  describe('fetchSpecParameters', () => {
    it('should fetch parameters from API spec', async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecResponse);

      const params = await fetchSpecParameters('yolo');

      expect(params).toHaveLength(5);
      expect(params[0].name).toBe('confidence');
      expect(mockedAxiosGet).toHaveBeenCalledWith(expect.stringContaining('/api/v1/specs/yolo'));
    });

    it('should use cache within TTL', async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecResponse);

      await fetchSpecParameters('yolo');
      await fetchSpecParameters('yolo');

      expect(mockedAxiosGet).toHaveBeenCalledTimes(1);
    });

    it('should convert underscore to hyphen in spec ID', async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecResponse);

      await fetchSpecParameters('ocr_ensemble');

      expect(mockedAxiosGet).toHaveBeenCalledWith(expect.stringContaining('/api/v1/specs/ocr-ensemble'));
    });

    it('should return empty array on fetch error', async () => {
      mockedAxiosGet.mockRejectedValue(new Error('Network error'));
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const params = await fetchSpecParameters('yolo');

      expect(params).toEqual([]);
      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  describe('getHyperparamDefinitions', () => {
    it('should convert parameters to UI definitions', async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecResponse);

      const defs = await getHyperparamDefinitions('yolo');

      // Array type parameter should be filtered out
      expect(defs).toHaveLength(4);

      const confidenceDef = defs.find(d => d.key === 'confidence');
      expect(confidenceDef?.type).toBe('number');
      expect(confidenceDef?.min).toBe(0);
      expect(confidenceDef?.max).toBe(1);
      expect(confidenceDef?.step).toBe(0.05);

      const visualizeDef = defs.find(d => d.key === 'visualize');
      expect(visualizeDef?.type).toBe('boolean');

      const modelTypeDef = defs.find(d => d.key === 'model_type');
      expect(modelTypeDef?.type).toBe('select');
      expect(modelTypeDef?.options).toHaveLength(2);

      const languageDef = defs.find(d => d.key === 'language');
      expect(languageDef?.type).toBe('text');
    });

    it('should filter out array type parameters', async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecResponse);

      const defs = await getHyperparamDefinitions('yolo');

      const enginesDef = defs.find(d => d.key === 'engines');
      expect(enginesDef).toBeUndefined();
    });

    it('should infer step for number parameters without max <= 1', async () => {
      mockedAxiosGet.mockResolvedValue({
        data: {
          spec: {
            parameters: [
              { name: 'imgsz', type: 'number', default: 1280, min: 320, max: 3200 },
            ],
          },
        },
      });

      const defs = await getHyperparamDefinitions('yolo');
      expect(defs[0].step).toBe(1);
    });
  });

  describe('getDefaultHyperparams', () => {
    it('should return default values from spec', async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecResponse);

      const defaults = await getDefaultHyperparams('yolo');

      // Array type parameter should be filtered out
      expect(defaults).toEqual({
        confidence: 0.25,
        visualize: true,
        model_type: 'engineering',
        language: 'eng',
      });
    });

    it('should not include array type parameters', async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecResponse);

      const defaults = await getDefaultHyperparams('yolo');

      expect(defaults).not.toHaveProperty('engines');
    });
  });

  describe('getHyperparamDefinitionsWithFallback', () => {
    const hardcodedDefinitions: Record<string, HyperparamDefinition[]> = {
      yolo: [{ key: 'fallback_param', label: 'Fallback', type: 'number', description: 'Fallback parameter' }],
    };

    it('should return spec definitions when available', async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecResponse);

      const defs = await getHyperparamDefinitionsWithFallback('yolo', hardcodedDefinitions);

      expect(defs).toHaveLength(4);
      expect(defs[0].key).toBe('confidence');
    });

    it('should return fallback definitions when spec is empty', async () => {
      mockedAxiosGet.mockResolvedValue({ data: { spec: { parameters: [] } } });

      const defs = await getHyperparamDefinitionsWithFallback('yolo', hardcodedDefinitions);

      expect(defs).toEqual(hardcodedDefinitions['yolo']);
    });

    it('should return fallback definitions on error', async () => {
      mockedAxiosGet.mockRejectedValue(new Error('Network error'));
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      const defs = await getHyperparamDefinitionsWithFallback('yolo', hardcodedDefinitions);

      expect(defs).toEqual(hardcodedDefinitions['yolo']);
      consoleSpy.mockRestore();
    });

    it('should return empty array when no fallback exists', async () => {
      mockedAxiosGet.mockResolvedValue({ data: { spec: { parameters: [] } } });

      const defs = await getHyperparamDefinitionsWithFallback('unknown', {});

      expect(defs).toEqual([]);
    });
  });

  describe('getDefaultHyperparamsWithFallback', () => {
    const hardcodedDefaults: Record<string, Record<string, unknown>> = {
      yolo: { fallback_param: 100 },
    };

    it('should return spec defaults when available', async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecResponse);

      const defaults = await getDefaultHyperparamsWithFallback('yolo', hardcodedDefaults);

      expect(defaults).toHaveProperty('confidence', 0.25);
    });

    it('should return fallback defaults when spec is empty', async () => {
      mockedAxiosGet.mockResolvedValue({ data: { spec: { parameters: [] } } });

      const defaults = await getDefaultHyperparamsWithFallback('yolo', hardcodedDefaults);

      expect(defaults).toEqual(hardcodedDefaults['yolo']);
    });
  });

  describe('clearSpecCache', () => {
    it('should clear cache and force refetch', async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecResponse);

      await fetchSpecParameters('yolo');
      clearSpecCache();
      await fetchSpecParameters('yolo');

      expect(mockedAxiosGet).toHaveBeenCalledTimes(2);
    });
  });
});
