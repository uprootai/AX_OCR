// API Types - 모든 인터페이스 및 타입 정의

import type { HealthCheckResponse, GenericAPIResponse } from '../types/api';

// Re-export for convenience
export type { HealthCheckResponse, GenericAPIResponse };

// 진행률 콜백 타입
export type ProgressCallback = (progress: number) => void;

// ==================== BlueprintFlow Workflow Types ====================

export interface WorkflowNode {
  id: string;
  type: string;
  label?: string;
  parameters: Record<string, unknown>;
  position?: { x: number; y: number };
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  condition?: Record<string, unknown>;
}

export interface WorkflowDefinition {
  name: string;
  description?: string;
  version?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  metadata?: Record<string, unknown>;
}

export interface StoredWorkflow extends WorkflowDefinition {
  id: string;
  created_at: string;
  updated_at: string;
}

export interface WorkflowExecutionRequest {
  workflow: WorkflowDefinition;
  inputs: Record<string, unknown>;
  config?: Record<string, unknown>;
}

export interface NodeExecutionStatus {
  node_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  progress: number;
  start_time?: string;
  end_time?: string;
  error?: string;
  output?: Record<string, unknown>;
}

export interface WorkflowExecutionResponse {
  execution_id: string;
  status: 'running' | 'completed' | 'failed';
  workflow_name: string;
  node_statuses: NodeExecutionStatus[];
  final_output?: Record<string, unknown>;
  error?: string;
  execution_time_ms?: number;
}

// ==================== API Key Management Types ====================

export interface APIKeyModel {
  id: string;
  name: string;
  cost: string;
  recommended: boolean;
}

export interface ProviderSettings {
  has_key: boolean;
  masked_key: string | null;
  source: 'dashboard' | 'environment' | null;
  model: string | null;
  models: APIKeyModel[];
  enabled: boolean;
}

export interface AllAPIKeySettings {
  openai: ProviderSettings;
  anthropic: ProviderSettings;
  google: ProviderSettings;
  local: ProviderSettings;
}

export interface SetAPIKeyRequest {
  provider: string;
  api_key: string;
  model?: string;
}

export interface TestConnectionResult {
  success: boolean;
  message?: string;
  error?: string;
  provider: string;
}

// ==================== Dynamic API Client Types ====================

export interface DynamicAPIClient {
  healthCheck: () => Promise<HealthCheckResponse>;
  process: (file: File, options?: Record<string, unknown>) => Promise<GenericAPIResponse>;
  getRaw: () => unknown;
}

// ==================== DSE Bearing Types ====================

export interface DSEQuoteData {
  success: boolean;
  quote_number: string;
  date: string;
  items: {
    no: string;
    description: string;
    material: string;
    material_cost: number;
    labor_cost: number;
    quantity: number;
    unit_price: number;
    total_price: number;
  }[];
  subtotal: number;
  discount: number;
  tax: number;
  total: number;
  currency: string;
}

// ==================== Template Types (Phase 2B) ====================

export interface TemplateNode {
  id: string;
  type: string;
  label?: string;
  position: { x: number; y: number };
  parameters: Record<string, unknown>;
}

export interface TemplateEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export interface TemplateCreate {
  name: string;
  description?: string;
  model_type: string;
  features: string[];
  drawing_type?: string;
  detection_params?: Record<string, unknown>;
  nodes: TemplateNode[];
  edges: TemplateEdge[];
}

export interface TemplateResponse {
  template_id: string;
  name: string;
  description?: string;
  model_type: string;
  features: string[];
  drawing_type: string;
  node_count: number;
  edge_count: number;
  node_types: string[];
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface TemplateDetail extends TemplateResponse {
  nodes: TemplateNode[];
  edges: TemplateEdge[];
  detection_params: Record<string, unknown>;
}

export interface TemplateListResponse {
  templates: TemplateResponse[];
  total: number;
}

// ==================== Workflow Session Types (Phase 2G) ====================

export interface WorkflowSessionCreate {
  name: string;
  description?: string;
  nodes: Array<{
    id: string;
    type: string;
    label?: string;
    parameters: Record<string, unknown>;
    position?: { x: number; y: number };
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    sourceHandle?: string;
    targetHandle?: string;
  }>;
  lock_level: 'full' | 'parameters' | 'none';
  allowed_parameters?: string[];
  customer_name?: string;
  expires_in_days?: number;
}

export interface WorkflowSessionResponse {
  session_id: string;
  share_url: string;
  access_token: string;
  expires_at: string;
  workflow_name: string;
}

export interface WorkflowSessionDetail {
  session_id: string;
  workflow_definition?: {
    name: string;
    description?: string;
    nodes: Array<Record<string, unknown>>;
    edges: Array<Record<string, unknown>>;
  };
  workflow_locked: boolean;
  lock_level: 'full' | 'parameters' | 'none';
  allowed_parameters: string[];
  customer_name?: string;
  access_token?: string;
  expires_at?: string;
}
