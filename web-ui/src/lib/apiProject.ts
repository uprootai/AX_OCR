// API Project - 워크플로우, API Key, 세션, 템플릿, DSE Bearing API 클라이언트

import axios from 'axios';
import { API_BASE, BLUEPRINT_AI_BOM_BASE } from './apiServices';
import type {
  WorkflowDefinition,
  StoredWorkflow,
  WorkflowExecutionRequest,
  WorkflowExecutionResponse,
  AllAPIKeySettings,
  SetAPIKeyRequest,
  TestConnectionResult,
  TemplateCreate,
  TemplateResponse,
  TemplateDetail,
  TemplateListResponse,
  TemplateNode,
  TemplateEdge,
  WorkflowSessionCreate,
  WorkflowSessionResponse,
  WorkflowSessionDetail,
  DSEQuoteData,
} from './apiTypes';

// Axios 인스턴스
const gatewayAPI = axios.create({ baseURL: API_BASE });

// Blueprint AI BOM API Base
const BLUEPRINT_AI_BOM_API = axios.create({ baseURL: BLUEPRINT_AI_BOM_BASE });

// ==================== BlueprintFlow Workflow API ====================

export const workflowApi = {
  // Execute workflow
  execute: async (request: WorkflowExecutionRequest): Promise<WorkflowExecutionResponse> => {
    const response = await gatewayAPI.post('/api/v1/workflow/execute', request);
    return response.data;
  },

  // Get available node types
  getNodeTypes: async (): Promise<{ node_types: string[]; count: number; categories: Record<string, string[]> }> => {
    const response = await gatewayAPI.get('/api/v1/workflow/node-types');
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<{ status: string; engine: string; version: string; features: Record<string, boolean> }> => {
    const response = await gatewayAPI.get('/api/v1/workflow/health');
    return response.data;
  },

  // Save workflow (localStorage for now)
  saveWorkflow: async (workflow: WorkflowDefinition): Promise<{ id: string }> => {
    const workflows = JSON.parse(localStorage.getItem('workflows') || '[]');
    const id = `workflow_${Date.now()}`;
    const savedWorkflow = {
      id,
      ...workflow,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    workflows.push(savedWorkflow);
    localStorage.setItem('workflows', JSON.stringify(workflows));
    return { id };
  },

  // Load workflow by ID
  loadWorkflow: async (id: string): Promise<StoredWorkflow> => {
    const workflows: StoredWorkflow[] = JSON.parse(localStorage.getItem('workflows') || '[]');
    const workflow = workflows.find((w) => w.id === id);
    if (!workflow) {
      throw new Error('Workflow not found');
    }
    return workflow;
  },

  // List all workflows
  listWorkflows: async (): Promise<StoredWorkflow[]> => {
    const workflows: StoredWorkflow[] = JSON.parse(localStorage.getItem('workflows') || '[]');
    return workflows;
  },

  // Delete workflow
  deleteWorkflow: async (id: string): Promise<void> => {
    const workflows: StoredWorkflow[] = JSON.parse(localStorage.getItem('workflows') || '[]');
    const filteredWorkflows = workflows.filter((w) => w.id !== id);
    localStorage.setItem('workflows', JSON.stringify(filteredWorkflows));
  },

  // Update workflow
  updateWorkflow: async (id: string, workflow: WorkflowDefinition): Promise<void> => {
    const workflows: StoredWorkflow[] = JSON.parse(localStorage.getItem('workflows') || '[]');
    const index = workflows.findIndex((w) => w.id === id);
    if (index === -1) {
      throw new Error('Workflow not found');
    }
    workflows[index] = {
      ...workflows[index],
      ...workflow,
      updated_at: new Date().toISOString(),
    };
    localStorage.setItem('workflows', JSON.stringify(workflows));
  },
};

// ==================== API Key Management ====================

export const apiKeyApi = {
  // 모든 API Key 설정 조회
  getAllSettings: async (): Promise<AllAPIKeySettings> => {
    const response = await gatewayAPI.get('/admin/api-keys');
    return response.data.data;
  },

  // API Key 설정
  setAPIKey: async (request: SetAPIKeyRequest): Promise<{ status: string; message: string }> => {
    const response = await gatewayAPI.post('/admin/api-keys', request);
    return response.data;
  },

  // API Key 삭제
  deleteAPIKey: async (provider: string): Promise<{ status: string; message: string }> => {
    const response = await gatewayAPI.delete(`/admin/api-keys/${provider}`);
    return response.data;
  },

  // 연결 테스트
  testConnection: async (provider: string, apiKey?: string): Promise<TestConnectionResult> => {
    const response = await gatewayAPI.post('/admin/api-keys/test', {
      provider,
      api_key: apiKey,
    });
    return response.data;
  },

  // 모델 선택
  setModel: async (provider: string, model: string): Promise<{ status: string; message: string }> => {
    const response = await gatewayAPI.post(`/admin/api-keys/${provider}/model`, { model });
    return response.data;
  },

  // 특정 Provider의 API Key 조회 (내부 서비스용)
  getAPIKey: async (provider: string): Promise<{ status: string; api_key: string | null; model: string | null }> => {
    const response = await gatewayAPI.get(`/admin/api-keys/${provider}`);
    return response.data;
  },
};

// ==================== DSE Bearing APIs ====================

export const dseBearing = {
  /**
   * Title Block 파싱
   */
  parseTitleBlock: async (file: File, profile = 'bearing') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('profile', profile);
    const response = await gatewayAPI.post('/api/v1/dsebearing/titleblock', formData);
    return response.data;
  },

  /**
   * Parts List 파싱
   */
  parsePartsList: async (file: File, profile = 'bearing') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('profile', profile);
    const response = await gatewayAPI.post('/api/v1/dsebearing/partslist', formData);
    return response.data;
  },

  /**
   * Dimension 파싱
   */
  parseDimensions: async (file: File, profile = 'bearing') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('profile', profile);
    const response = await gatewayAPI.post('/api/v1/dsebearing/dimensionparser', formData);
    return response.data;
  },

  /**
   * 견적 생성
   */
  generateQuote: async (
    bomData: Record<string, unknown>,
    customerId?: string,
    options?: {
      materialMarkup?: number;
      laborMarkup?: number;
      taxRate?: number;
    }
  ): Promise<DSEQuoteData> => {
    const formData = new FormData();
    formData.append('bom_data', JSON.stringify(bomData));
    if (customerId) formData.append('customer_id', customerId);
    if (options?.materialMarkup) formData.append('material_markup', options.materialMarkup.toString());
    if (options?.laborMarkup) formData.append('labor_markup', options.laborMarkup.toString());
    if (options?.taxRate) formData.append('tax_rate', options.taxRate.toString());
    const response = await gatewayAPI.post('/api/v1/dsebearing/quotegenerator', formData);
    return response.data;
  },

  /**
   * 견적서 Excel 내보내기
   */
  exportToExcel: async (quoteData: DSEQuoteData, customerId?: string): Promise<Blob> => {
    const formData = new FormData();
    formData.append('quote_data', JSON.stringify(quoteData));
    if (customerId) formData.append('customer_id', customerId);
    const response = await gatewayAPI.post('/api/v1/dsebearing/quote/export/excel', formData, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * 견적서 PDF 내보내기
   */
  exportToPdf: async (quoteData: DSEQuoteData, customerId?: string): Promise<Blob> => {
    const formData = new FormData();
    formData.append('quote_data', JSON.stringify(quoteData));
    if (customerId) formData.append('customer_id', customerId);
    const response = await gatewayAPI.post('/api/v1/dsebearing/quote/export/pdf', formData, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * 재질 가격 목록 조회
   */
  getMaterialPrices: async () => {
    const response = await gatewayAPI.get('/api/v1/dsebearing/prices/materials');
    return response.data;
  },

  /**
   * 가공비 목록 조회
   */
  getLaborCosts: async () => {
    const response = await gatewayAPI.get('/api/v1/dsebearing/prices/labor');
    return response.data;
  },

  /**
   * 고객 목록 조회
   */
  getCustomers: async () => {
    const response = await gatewayAPI.get('/api/v1/dsebearing/customers');
    return response.data;
  },

  /**
   * 고객 상세 정보 조회
   */
  getCustomerDetails: async (customerId: string) => {
    const response = await gatewayAPI.get(`/api/v1/dsebearing/customers/${customerId}/full`);
    return response.data;
  },
};

// ==================== Workflow Session API (Phase 2G) ====================

export const workflowSessionApi = {
  /**
   * BlueprintFlow 워크플로우로부터 잠긴 세션 생성
   */
  createFromWorkflow: async (request: WorkflowSessionCreate): Promise<WorkflowSessionResponse> => {
    const response = await BLUEPRINT_AI_BOM_API.post('/sessions/from-workflow', request);
    return response.data;
  },

  /**
   * 세션의 워크플로우 정의 조회
   */
  getWorkflow: async (sessionId: string, accessToken?: string): Promise<WorkflowSessionDetail> => {
    const params: Record<string, string> = {};
    if (accessToken) params.access_token = accessToken;
    const response = await BLUEPRINT_AI_BOM_API.get(`/sessions/${sessionId}/workflow`, { params });
    return response.data;
  },

  /**
   * 워크플로우 실행
   */
  execute: async (
    sessionId: string,
    imageIds: string[],
    parameters?: Record<string, unknown>,
    accessToken?: string
  ): Promise<{ execution_id: string; status: string; message: string }> => {
    const params: Record<string, string> = {};
    if (accessToken) params.access_token = accessToken;
    const response = await BLUEPRINT_AI_BOM_API.post(
      `/sessions/${sessionId}/execute`,
      { image_ids: imageIds, parameters },
      { params }
    );
    return response.data;
  },
};

// ==================== Template API (Phase 2B) ====================

export const templateApi = {
  /**
   * 템플릿 생성
   */
  create: async (template: TemplateCreate): Promise<TemplateResponse> => {
    const response = await BLUEPRINT_AI_BOM_API.post('/templates', template);
    return response.data;
  },

  /**
   * 템플릿 목록 조회
   */
  list: async (modelType?: string, limit = 50): Promise<TemplateListResponse> => {
    const params: Record<string, string | number> = { limit };
    if (modelType) params.model_type = modelType;
    const response = await BLUEPRINT_AI_BOM_API.get('/templates', { params });
    return response.data;
  },

  /**
   * 템플릿 상세 조회
   */
  get: async (templateId: string): Promise<TemplateDetail> => {
    const response = await BLUEPRINT_AI_BOM_API.get(`/templates/${templateId}`);
    return response.data;
  },

  /**
   * 템플릿 요약 조회 (노드/엣지 제외)
   */
  getSummary: async (templateId: string): Promise<TemplateResponse> => {
    const response = await BLUEPRINT_AI_BOM_API.get(`/templates/${templateId}/summary`);
    return response.data;
  },

  /**
   * 템플릿 수정
   */
  update: async (templateId: string, updates: Partial<TemplateCreate>): Promise<TemplateResponse> => {
    const response = await BLUEPRINT_AI_BOM_API.put(`/templates/${templateId}`, updates);
    return response.data;
  },

  /**
   * 템플릿 삭제
   */
  delete: async (templateId: string): Promise<{ success: boolean; message: string }> => {
    const response = await BLUEPRINT_AI_BOM_API.delete(`/templates/${templateId}`);
    return response.data;
  },

  /**
   * 템플릿 복제
   */
  duplicate: async (templateId: string, newName: string): Promise<TemplateResponse> => {
    const response = await BLUEPRINT_AI_BOM_API.post(`/templates/${templateId}/duplicate`, null, {
      params: { new_name: newName },
    });
    return response.data;
  },

  /**
   * 템플릿 미리보기
   */
  preview: async (templateId: string): Promise<{
    template_id: string;
    name: string;
    nodes: TemplateNode[];
    edges: TemplateEdge[];
    node_count: number;
    edge_count: number;
    node_types: string[];
  }> => {
    const response = await BLUEPRINT_AI_BOM_API.get(`/templates/${templateId}/preview`);
    return response.data;
  },
};
