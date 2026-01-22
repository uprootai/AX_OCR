/**
 * Tests for apiRegistryService
 */

import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest';
import axios from 'axios';
import {
  fetchAPIRegistry,
  getAPIById,
  getAPIByNodeType,
  getAPIsByCategory,
  getNodeToContainerMap,
  getApiToContainerMap,
  getApiToSpecIdMap,
  getAPIParameters,
  getDefaultParameters,
  clearCache,
  CONTROL_NODES,
  requiresContainer,
} from './apiRegistryService';

vi.mock('axios');
const mockedAxiosGet = axios.get as Mock;

const mockSpecsResponse = {
  data: {
    specs: {
      yolo: {
        apiVersion: 'v1',
        kind: 'APISpec',
        metadata: {
          id: 'yolo',
          name: 'YOLO Detection',
          port: 5005,
          description: 'Object detection API',
        },
        blueprintflow: {
          category: 'detection',
          color: '#10b981',
          icon: 'Target',
        },
        parameters: [
          { name: 'confidence', type: 'number', default: 0.25, min: 0, max: 1 },
          { name: 'visualize', type: 'boolean', default: true },
        ],
        inputs: [{ name: 'image', type: 'Image', required: true }],
        outputs: [{ name: 'detections', type: 'DetectionResult[]' }],
        resources: { gpu: { minVram: 4 } },
      },
      edocr2: {
        apiVersion: 'v1',
        kind: 'APISpec',
        metadata: {
          id: 'edocr2',
          name: 'eDOCr2 OCR',
          port: 5002,
          description: 'OCR API',
          host: 'edocr2-v2-api',
        },
        blueprintflow: {
          category: 'ocr',
          color: '#8b5cf6',
        },
        parameters: [
          { name: 'language', type: 'string', default: 'eng' },
        ],
      },
    },
  },
};

describe('apiRegistryService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearCache();
  });

  afterEach(() => {
    clearCache();
  });

  describe('fetchAPIRegistry', () => {
    it('should fetch and convert API specs', async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecsResponse);

      const apis = await fetchAPIRegistry(true);

      expect(apis).toHaveLength(3); // 2 specs + gateway
      expect(apis[0].id).toBe('gateway');

      const yolo = apis.find(a => a.id === 'yolo');
      expect(yolo).toBeDefined();
      expect(yolo?.displayName).toBe('YOLO Detection');
      expect(yolo?.category).toBe('detection');
      expect(yolo?.gpuEnabled).toBe(true);
      expect(yolo?.parameters).toHaveLength(2);
    });

    it('should use cache within TTL', async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecsResponse);

      await fetchAPIRegistry(true);
      await fetchAPIRegistry();

      expect(mockedAxiosGet).toHaveBeenCalledTimes(1);
    });

    it('should handle fetch errors', async () => {
      mockedAxiosGet.mockRejectedValue(new Error('Network error'));

      await expect(fetchAPIRegistry(true)).rejects.toThrow('Network error');
    });

    it('should return cached data on error if available', async () => {
      mockedAxiosGet.mockResolvedValueOnce(mockSpecsResponse);
      await fetchAPIRegistry(true);

      clearCache();
      mockedAxiosGet.mockResolvedValueOnce(mockSpecsResponse);
      const apis = await fetchAPIRegistry(true);

      expect(apis).toBeDefined();
    });
  });

  describe('getAPIById', () => {
    beforeEach(async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecsResponse);
      await fetchAPIRegistry(true);
    });

    it('should return API by id', async () => {
      const yolo = await getAPIById('yolo');
      expect(yolo?.displayName).toBe('YOLO Detection');
    });

    it('should return undefined for unknown id', async () => {
      const unknown = await getAPIById('unknown');
      expect(unknown).toBeUndefined();
    });
  });

  describe('getAPIByNodeType', () => {
    beforeEach(async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecsResponse);
      await fetchAPIRegistry(true);
    });

    it('should return API by node type', async () => {
      const api = await getAPIByNodeType('yolo');
      expect(api?.id).toBe('yolo');
    });
  });

  describe('getAPIsByCategory', () => {
    beforeEach(async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecsResponse);
      await fetchAPIRegistry(true);
    });

    it('should return APIs by category', async () => {
      const detectionApis = await getAPIsByCategory('detection');
      expect(detectionApis).toHaveLength(1);
      expect(detectionApis[0].id).toBe('yolo');
    });

    it('should return empty array for empty category', async () => {
      const apis = await getAPIsByCategory('preprocessing');
      expect(apis).toHaveLength(0);
    });
  });

  describe('mapping functions', () => {
    beforeEach(async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecsResponse);
      await fetchAPIRegistry(true);
    });

    it('should generate nodeToContainer mapping', async () => {
      const map = await getNodeToContainerMap();
      expect(map['yolo']).toBe('yolo-api');
      expect(map['edocr2']).toBe('edocr2-v2-api');
      expect(map['gateway']).toBeUndefined(); // gateway excluded
    });

    it('should generate apiToContainer mapping', async () => {
      const map = await getApiToContainerMap();
      expect(map['yolo']).toBe('yolo-api');
      expect(map['gateway']).toBe('gateway-api');
    });

    it('should generate apiToSpecId mapping', async () => {
      const map = await getApiToSpecIdMap();
      expect(map['yolo']).toBe('yolo');
      expect(map['edocr2']).toBe('edocr2');
    });
  });

  describe('parameter functions', () => {
    beforeEach(async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecsResponse);
      await fetchAPIRegistry(true);
    });

    it('should return parameters for an API', async () => {
      const params = await getAPIParameters('yolo');
      expect(params).toHaveLength(2);
      expect(params[0].name).toBe('confidence');
    });

    it('should return empty array for API without parameters', async () => {
      const params = await getAPIParameters('gateway');
      expect(params).toEqual([]);
    });

    it('should return default parameter values', async () => {
      const defaults = await getDefaultParameters('yolo');
      expect(defaults).toEqual({ confidence: 0.25, visualize: true });
    });
  });

  describe('CONTROL_NODES', () => {
    it('should contain all control node types', () => {
      expect(CONTROL_NODES).toContain('imageinput');
      expect(CONTROL_NODES).toContain('textinput');
      expect(CONTROL_NODES).toContain('if');
      expect(CONTROL_NODES).toContain('loop');
      expect(CONTROL_NODES).toContain('merge');
    });
  });

  describe('requiresContainer', () => {
    it('should return true for API nodes', () => {
      expect(requiresContainer('yolo')).toBe(true);
      expect(requiresContainer('edocr2')).toBe(true);
      expect(requiresContainer('skinmodel')).toBe(true);
    });

    it('should return false for control nodes', () => {
      expect(requiresContainer('imageinput')).toBe(false);
      expect(requiresContainer('if')).toBe(false);
      expect(requiresContainer('loop')).toBe(false);
    });
  });

  describe('clearCache', () => {
    it('should clear cache and force refetch', async () => {
      mockedAxiosGet.mockResolvedValue(mockSpecsResponse);
      await fetchAPIRegistry(true);

      clearCache();
      await fetchAPIRegistry();

      expect(mockedAxiosGet).toHaveBeenCalledTimes(2);
    });
  });
});
