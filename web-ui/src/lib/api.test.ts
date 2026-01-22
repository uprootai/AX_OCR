/**
 * Tests for lib/api - API client utilities
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  gatewayApi,
  edocr2Api,
  edgnetApi,
  skinmodelApi,
  yoloApi,
  vlApi,
  checkAllServices,
  workflowApi,
  apiKeyApi,
  createDynamicAPIClient,
  getAllDynamicAPIClients,
  checkAllServicesIncludingCustom,
} from './api';

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      delete: vi.fn(),
    })),
  },
}));

describe('API clients', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('gatewayApi', () => {
    it('should have healthCheck method', () => {
      expect(gatewayApi.healthCheck).toBeDefined();
      expect(typeof gatewayApi.healthCheck).toBe('function');
    });

    it('should have process method', () => {
      expect(gatewayApi.process).toBeDefined();
      expect(typeof gatewayApi.process).toBe('function');
    });

    it('should have quote method', () => {
      expect(gatewayApi.quote).toBeDefined();
      expect(typeof gatewayApi.quote).toBe('function');
    });
  });

  describe('edocr2Api', () => {
    it('should have healthCheck methods', () => {
      expect(edocr2Api.healthCheck).toBeDefined();
      expect(edocr2Api.healthCheckV2).toBeDefined();
    });

    it('should have ocr methods', () => {
      expect(edocr2Api.ocr).toBeDefined();
      expect(edocr2Api.ocrV2).toBeDefined();
      expect(edocr2Api.ocrEnhanced).toBeDefined();
    });
  });

  describe('edgnetApi', () => {
    it('should have healthCheck method', () => {
      expect(edgnetApi.healthCheck).toBeDefined();
    });

    it('should have segment method', () => {
      expect(edgnetApi.segment).toBeDefined();
    });

    it('should have vectorize method', () => {
      expect(edgnetApi.vectorize).toBeDefined();
    });
  });

  describe('skinmodelApi', () => {
    it('should have healthCheck method', () => {
      expect(skinmodelApi.healthCheck).toBeDefined();
    });

    it('should have tolerance method', () => {
      expect(skinmodelApi.tolerance).toBeDefined();
    });

    it('should have validate method', () => {
      expect(skinmodelApi.validate).toBeDefined();
    });
  });

  describe('yoloApi', () => {
    it('should have healthCheck method', () => {
      expect(yoloApi.healthCheck).toBeDefined();
    });

    it('should have detect method', () => {
      expect(yoloApi.detect).toBeDefined();
    });
  });

  describe('vlApi', () => {
    it('should have healthCheck method', () => {
      expect(vlApi.healthCheck).toBeDefined();
    });

    it('should have extractInfoBlock method', () => {
      expect(vlApi.extractInfoBlock).toBeDefined();
    });

    it('should have extractDimensions method', () => {
      expect(vlApi.extractDimensions).toBeDefined();
    });

    it('should have inferManufacturingProcess method', () => {
      expect(vlApi.inferManufacturingProcess).toBeDefined();
    });

    it('should have generateQCChecklist method', () => {
      expect(vlApi.generateQCChecklist).toBeDefined();
    });
  });
});

describe('workflowApi', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should have execute method', () => {
    expect(workflowApi.execute).toBeDefined();
  });

  it('should have getNodeTypes method', () => {
    expect(workflowApi.getNodeTypes).toBeDefined();
  });

  it('should have healthCheck method', () => {
    expect(workflowApi.healthCheck).toBeDefined();
  });

  describe('localStorage workflow management', () => {
    it('should save workflow to localStorage', async () => {
      const workflow = {
        name: 'Test Workflow',
        description: 'A test workflow',
        nodes: [],
        edges: [],
      };

      const result = await workflowApi.saveWorkflow(workflow);

      expect(result.id).toBeDefined();
      expect(result.id).toMatch(/^workflow_\d+$/);

      const saved = JSON.parse(localStorage.getItem('workflows') || '[]');
      expect(saved).toHaveLength(1);
      expect(saved[0].name).toBe('Test Workflow');
    });

    it('should load workflow by ID', async () => {
      const workflow = {
        name: 'Test Workflow',
        nodes: [],
        edges: [],
      };

      const { id } = await workflowApi.saveWorkflow(workflow);
      const loaded = await workflowApi.loadWorkflow(id);

      expect(loaded.name).toBe('Test Workflow');
      expect(loaded.id).toBe(id);
    });

    it('should throw error for unknown workflow ID', async () => {
      await expect(workflowApi.loadWorkflow('unknown_id')).rejects.toThrow('Workflow not found');
    });

    it('should list all workflows', async () => {
      await workflowApi.saveWorkflow({ name: 'Workflow 1', nodes: [], edges: [] });
      await workflowApi.saveWorkflow({ name: 'Workflow 2', nodes: [], edges: [] });

      const workflows = await workflowApi.listWorkflows();

      expect(workflows).toHaveLength(2);
    });

    it('should delete workflow by ID', async () => {
      const { id } = await workflowApi.saveWorkflow({ name: 'To Delete', nodes: [], edges: [] });

      await workflowApi.deleteWorkflow(id);

      const workflows = await workflowApi.listWorkflows();
      expect(workflows).toHaveLength(0);
    });

    it('should update existing workflow', async () => {
      const { id } = await workflowApi.saveWorkflow({ name: 'Original', nodes: [], edges: [] });

      await workflowApi.updateWorkflow(id, { name: 'Updated', nodes: [], edges: [] });

      const loaded = await workflowApi.loadWorkflow(id);
      expect(loaded.name).toBe('Updated');
    });

    it('should throw error when updating non-existent workflow', async () => {
      await expect(
        workflowApi.updateWorkflow('unknown_id', { name: 'Test', nodes: [], edges: [] })
      ).rejects.toThrow('Workflow not found');
    });
  });
});

describe('apiKeyApi', () => {
  it('should have getAllSettings method', () => {
    expect(apiKeyApi.getAllSettings).toBeDefined();
  });

  it('should have setAPIKey method', () => {
    expect(apiKeyApi.setAPIKey).toBeDefined();
  });

  it('should have deleteAPIKey method', () => {
    expect(apiKeyApi.deleteAPIKey).toBeDefined();
  });

  it('should have testConnection method', () => {
    expect(apiKeyApi.testConnection).toBeDefined();
  });

  it('should have setModel method', () => {
    expect(apiKeyApi.setModel).toBeDefined();
  });

  it('should have getAPIKey method', () => {
    expect(apiKeyApi.getAPIKey).toBeDefined();
  });
});

describe('createDynamicAPIClient', () => {
  it('should create a client with healthCheck method', () => {
    const client = createDynamicAPIClient('http://localhost:5025');

    expect(client.healthCheck).toBeDefined();
    expect(typeof client.healthCheck).toBe('function');
  });

  it('should create a client with process method', () => {
    const client = createDynamicAPIClient('http://localhost:5025');

    expect(client.process).toBeDefined();
    expect(typeof client.process).toBe('function');
  });

  it('should create a client with getRaw method', () => {
    const client = createDynamicAPIClient('http://localhost:5025');

    expect(client.getRaw).toBeDefined();
    expect(typeof client.getRaw).toBe('function');
  });
});

describe('getAllDynamicAPIClients', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should return empty object when no custom APIs', () => {
    const clients = getAllDynamicAPIClients();
    expect(clients).toEqual({});
  });

  it('should return clients for enabled custom APIs', () => {
    const customAPIs = {
      state: {
        customAPIs: [
          { id: 'custom1', enabled: true, baseUrl: 'http://localhost:5030' },
          { id: 'custom2', enabled: false, baseUrl: 'http://localhost:5031' },
          { id: 'custom3', enabled: true, baseUrl: 'http://localhost:5032' },
        ],
      },
    };
    localStorage.setItem('custom-apis-storage', JSON.stringify(customAPIs));

    const clients = getAllDynamicAPIClients();

    expect(Object.keys(clients)).toHaveLength(2);
    expect(clients['custom1']).toBeDefined();
    expect(clients['custom2']).toBeUndefined();
    expect(clients['custom3']).toBeDefined();
  });

  it('should handle malformed localStorage data', () => {
    localStorage.setItem('custom-apis-storage', 'invalid-json');
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const clients = getAllDynamicAPIClients();

    expect(clients).toEqual({});
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });

  it('should handle missing state in localStorage', () => {
    localStorage.setItem('custom-apis-storage', JSON.stringify({}));

    const clients = getAllDynamicAPIClients();

    expect(clients).toEqual({});
  });
});

describe('checkAllServices', () => {
  it('should be a function', () => {
    expect(checkAllServices).toBeDefined();
    expect(typeof checkAllServices).toBe('function');
  });
});

describe('checkAllServicesIncludingCustom', () => {
  it('should be a function', () => {
    expect(checkAllServicesIncludingCustom).toBeDefined();
    expect(typeof checkAllServicesIncludingCustom).toBe('function');
  });
});
