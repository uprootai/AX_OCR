/**
 * Tests for useAPIRegistry hook
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useAPIRegistry, useAPIParameters, useRequiresContainer, CONTROL_NODES } from './useAPIRegistry';

// Mock the apiRegistryService
vi.mock('../services/apiRegistryService', () => ({
  fetchAPIRegistry: vi.fn(),
  getAPIParameters: vi.fn(),
  getDefaultParameters: vi.fn(),
  clearCache: vi.fn(),
  CONTROL_NODES: ['imageinput', 'textinput', 'if', 'loop', 'merge'],
}));

import {
  fetchAPIRegistry,
  getAPIParameters,
  getDefaultParameters,
  clearCache,
} from '../services/apiRegistryService';

const mockAPIs = [
  {
    id: 'yolo',
    nodeType: 'yolo',
    displayName: 'YOLO Detection',
    containerName: 'yolo-api',
    specId: 'yolo',
    port: 5005,
    category: 'detection' as const,
    description: 'Object detection',
    icon: 'Target',
    color: '#10b981',
    gpuEnabled: true,
  },
  {
    id: 'edocr2',
    nodeType: 'edocr2',
    displayName: 'eDOCr2 OCR',
    containerName: 'edocr2-api',
    specId: 'edocr2',
    port: 5002,
    category: 'ocr' as const,
    description: 'OCR extraction',
    icon: 'FileText',
    color: '#8b5cf6',
    gpuEnabled: true,
  },
  {
    id: 'gateway',
    nodeType: 'gateway',
    displayName: 'Gateway',
    containerName: 'gateway-api',
    specId: 'gateway',
    port: 8000,
    category: 'control' as const,
    description: 'API Gateway',
    icon: 'Server',
    color: '#6366f1',
    gpuEnabled: false,
  },
];

const mockParameters = [
  { name: 'confidence', type: 'number', default: 0.25, min: 0, max: 1, step: 0.05, description: 'Confidence threshold' },
  { name: 'visualize', type: 'boolean', default: true, description: 'Generate visualization' },
];

describe('useAPIRegistry', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (fetchAPIRegistry as ReturnType<typeof vi.fn>).mockResolvedValue(mockAPIs);
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should load APIs on mount', async () => {
    const { result } = renderHook(() => useAPIRegistry());

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.apis).toEqual(mockAPIs);
    expect(result.current.error).toBeNull();
  });

  it('should handle fetch errors gracefully', async () => {
    const error = new Error('Network error');
    (fetchAPIRegistry as ReturnType<typeof vi.fn>).mockRejectedValue(error);

    const { result } = renderHook(() => useAPIRegistry());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toEqual(error);
    expect(result.current.apis).toEqual([]);
  });

  it('should compute nodeToContainer mapping correctly', async () => {
    const { result } = renderHook(() => useAPIRegistry());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Gateway should be excluded from nodeToContainer
    expect(result.current.nodeToContainer).toEqual({
      yolo: 'yolo-api',
      edocr2: 'edocr2-api',
    });
  });

  it('should compute apiToContainer and apiToSpecId mappings', async () => {
    const { result } = renderHook(() => useAPIRegistry());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.apiToContainer).toEqual({
      yolo: 'yolo-api',
      edocr2: 'edocr2-api',
      gateway: 'gateway-api',
    });

    expect(result.current.apiToSpecId).toEqual({
      yolo: 'yolo',
      edocr2: 'edocr2',
      gateway: 'gateway',
    });
  });

  it('should provide getById method', async () => {
    const { result } = renderHook(() => useAPIRegistry());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const yolo = result.current.getById('yolo');
    expect(yolo?.displayName).toBe('YOLO Detection');

    const unknown = result.current.getById('unknown');
    expect(unknown).toBeUndefined();
  });

  it('should provide getByNodeType method', async () => {
    const { result } = renderHook(() => useAPIRegistry());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const edocr2 = result.current.getByNodeType('edocr2');
    expect(edocr2?.displayName).toBe('eDOCr2 OCR');
  });

  it('should provide getByCategory method', async () => {
    const { result } = renderHook(() => useAPIRegistry());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const ocrApis = result.current.getByCategory('ocr');
    expect(ocrApis).toHaveLength(1);
    expect(ocrApis[0].id).toBe('edocr2');
  });

  it('should refresh and clear cache', async () => {
    const { result } = renderHook(() => useAPIRegistry());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.refresh();
    });

    expect(clearCache).toHaveBeenCalled();
    expect(fetchAPIRegistry).toHaveBeenCalledTimes(2);
  });
});

describe('useAPIParameters', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (getAPIParameters as ReturnType<typeof vi.fn>).mockResolvedValue(mockParameters);
    (getDefaultParameters as ReturnType<typeof vi.fn>).mockResolvedValue({ confidence: 0.25, visualize: true });
  });

  it('should load parameters for an API', async () => {
    const { result } = renderHook(() => useAPIParameters('yolo'));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.parameters).toEqual(mockParameters);
    expect(result.current.defaults).toEqual({ confidence: 0.25, visualize: true });
    expect(result.current.error).toBeNull();
  });

  it('should return empty values for empty apiId', async () => {
    const { result } = renderHook(() => useAPIParameters(''));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.parameters).toEqual([]);
    expect(result.current.defaults).toEqual({});
  });

  it('should handle errors', async () => {
    const error = new Error('Failed to load parameters');
    (getAPIParameters as ReturnType<typeof vi.fn>).mockRejectedValue(error);

    const { result } = renderHook(() => useAPIParameters('yolo'));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toEqual(error);
  });
});

describe('useRequiresContainer', () => {
  it('should return true for API nodes', () => {
    const { result } = renderHook(() => useRequiresContainer('yolo'));
    expect(result.current).toBe(true);
  });

  it('should return false for control nodes', () => {
    const controlNodes = ['imageinput', 'textinput', 'if', 'loop', 'merge'];
    controlNodes.forEach(nodeType => {
      const { result } = renderHook(() => useRequiresContainer(nodeType));
      expect(result.current).toBe(false);
    });
  });
});

describe('CONTROL_NODES', () => {
  it('should export CONTROL_NODES constant', () => {
    expect(CONTROL_NODES).toEqual(['imageinput', 'textinput', 'if', 'loop', 'merge']);
  });
});
