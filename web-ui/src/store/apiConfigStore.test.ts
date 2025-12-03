import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAPIConfigStore, type APIConfig } from './apiConfigStore';

// Mock fetch
globalThis.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
  } as Response)
);

describe('apiConfigStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useAPIConfigStore.setState({ customAPIs: [] });
    vi.clearAllMocks();
  });

  const mockAPI: APIConfig = {
    id: 'test-api',
    name: 'TestAPI',
    displayName: 'Test API',
    baseUrl: 'http://localhost:9999',
    port: 9999,
    icon: '🧪',
    color: '#ff0000',
    category: 'ocr',
    description: 'Test API for testing',
    enabled: true,
    inputs: [{ name: 'image', type: 'Image', description: 'Input image' }],
    outputs: [{ name: 'result', type: 'object', description: 'Output result' }],
    parameters: [],
  };

  describe('addAPI', () => {
    it('should add a new API to the store', async () => {
      const { addAPI } = useAPIConfigStore.getState();

      await addAPI(mockAPI);

      const updatedAPIs = useAPIConfigStore.getState().customAPIs;
      expect(updatedAPIs).toHaveLength(1);
      expect(updatedAPIs[0].id).toBe('test-api');
    });

    it('should not add duplicate API', async () => {
      const { addAPI } = useAPIConfigStore.getState();

      await addAPI(mockAPI);
      await addAPI(mockAPI); // Try to add again

      const updatedAPIs = useAPIConfigStore.getState().customAPIs;
      expect(updatedAPIs).toHaveLength(1);
    });
  });

  describe('removeAPI', () => {
    it('should remove an API from the store', async () => {
      const { addAPI, removeAPI } = useAPIConfigStore.getState();

      await addAPI(mockAPI);
      expect(useAPIConfigStore.getState().customAPIs).toHaveLength(1);

      await removeAPI('test-api');
      expect(useAPIConfigStore.getState().customAPIs).toHaveLength(0);
    });
  });

  describe('updateAPI', () => {
    it('should update an existing API', async () => {
      const { addAPI, updateAPI } = useAPIConfigStore.getState();

      await addAPI(mockAPI);
      await updateAPI('test-api', { displayName: 'Updated Test API' });

      const updatedAPIs = useAPIConfigStore.getState().customAPIs;
      expect(updatedAPIs[0].displayName).toBe('Updated Test API');
    });
  });

  describe('toggleAPI', () => {
    it('should toggle API enabled status', async () => {
      const { addAPI, toggleAPI } = useAPIConfigStore.getState();

      await addAPI(mockAPI);
      expect(useAPIConfigStore.getState().customAPIs[0].enabled).toBe(true);

      await toggleAPI('test-api');
      expect(useAPIConfigStore.getState().customAPIs[0].enabled).toBe(false);

      await toggleAPI('test-api');
      expect(useAPIConfigStore.getState().customAPIs[0].enabled).toBe(true);
    });
  });

  describe('getAPIById', () => {
    it('should return API by id', async () => {
      const { addAPI, getAPIById } = useAPIConfigStore.getState();

      await addAPI(mockAPI);

      const api = getAPIById('test-api');
      expect(api).toBeDefined();
      expect(api?.id).toBe('test-api');
    });

    it('should return undefined for non-existent id', () => {
      const { getAPIById } = useAPIConfigStore.getState();

      const api = getAPIById('non-existent');
      expect(api).toBeUndefined();
    });
  });

  describe('getAllAPIs', () => {
    it('should return all APIs', async () => {
      const { addAPI, getAllAPIs } = useAPIConfigStore.getState();

      await addAPI(mockAPI);
      await addAPI({ ...mockAPI, id: 'test-api-2', name: 'TestAPI2' });

      const allAPIs = getAllAPIs();
      expect(allAPIs).toHaveLength(2);
    });
  });

  describe('category validation', () => {
    it('should accept all valid categories', async () => {
      const { addAPI } = useAPIConfigStore.getState();
      const categories: APIConfig['category'][] = [
        'input', 'detection', 'ocr', 'segmentation',
        'preprocessing', 'analysis', 'knowledge', 'ai', 'control'
      ];

      for (let i = 0; i < categories.length; i++) {
        await addAPI({
          ...mockAPI,
          id: `api-${categories[i]}`,
          category: categories[i],
        });
      }

      const allAPIs = useAPIConfigStore.getState().customAPIs;
      expect(allAPIs).toHaveLength(categories.length);
    });
  });
});
