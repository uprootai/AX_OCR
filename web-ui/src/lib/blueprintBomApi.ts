/**
 * Blueprint AI BOM - Project API Client
 * web-ui에서 Blueprint AI BOM API를 호출하기 위한 클라이언트
 * 기존 BLUEPRINT_AI_BOM_API 인스턴스 재사용
 */

import axios from 'axios';
import { BLUEPRINT_AI_BOM_BASE } from './api';

const api = axios.create({
  baseURL: BLUEPRINT_AI_BOM_BASE,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

// =====================
// Types
// =====================

export interface Project {
  project_id: string;
  name: string;
  customer: string;
  project_type: 'bom_quotation' | 'pid_detection' | 'general';
  description?: string;
  default_template_id?: string;
  default_template_name?: string;
  default_model_type?: string;
  default_features: string[];
  gt_folder?: string;
  reference_folder?: string;
  bom_source?: string;
  drawing_folder?: string;
  session_count: number;
  completed_count: number;
  pending_count: number;
  bom_item_count: number;
  quotation_item_count: number;
  quoted_count: number;
  total_quotation: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  sessions: Array<{
    session_id: string;
    filename: string;
    status: string;
    detection_count: number;
    verified_count: number;
  }>;
  template?: {
    template_id: string;
    name: string;
    nodes: unknown[];
    edges: unknown[];
  };
}

export interface ProjectCreate {
  name: string;
  customer: string;
  project_type?: 'bom_quotation' | 'pid_detection' | 'general';
  description?: string;
  default_template_id?: string;
  default_model_type?: string;
  default_features?: string[];
  bom_source?: string;
  drawing_folder?: string;
}

export interface ProjectUpdate {
  name?: string;
  customer?: string;
  project_type?: 'bom_quotation' | 'pid_detection';
  description?: string;
  default_template_id?: string;
  default_model_type?: string;
  default_features?: string[];
  gt_folder?: string;
  reference_folder?: string;
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
}

export interface BOMItem {
  item_no: string;
  level: 'assembly' | 'subassembly' | 'part';
  drawing_number: string;
  description: string;
  material: string;
  quantity: number;
  parent_item_no?: string;
  needs_quotation: boolean;
  matched_file?: string;
  session_id?: string;
}

export interface BOMHierarchyResponse {
  project_id: string;
  bom_source: string;
  total_items: number;
  assembly_count: number;
  subassembly_count: number;
  part_count: number;
  items: BOMItem[];
  hierarchy: Record<string, unknown>[];
}

export interface DrawingMatchResult {
  project_id: string;
  total_items: number;
  matched_count: number;
  unmatched_count: number;
  items: BOMItem[];
}

export interface SessionBatchCreateResponse {
  project_id: string;
  created_count: number;
  skipped_count: number;
  failed_count: number;
  sessions: Array<{
    session_id: string;
    drawing_number: string;
    description: string;
    material: string;
    filename: string;
  }>;
  message: string;
}

export interface SessionQuotationItem {
  session_id: string;
  drawing_number: string;
  bom_item_no: string;
  description: string;
  material: string;
  bom_quantity: number;
  quote_status: string;
  bom_item_count: number;
  subtotal: number;
  vat: number;
  total: number;
  session_status: string;
  bom_generated: boolean;
  material_cost: number;
  machining_cost: number;
  weight_kg: number;
  raw_dimensions?: Record<string, number>;
  original_dimensions?: Record<string, number>;
  allowance_applied?: boolean;
  cost_source: string;
  assembly_drawing_number?: string;
  doc_revision?: string;
  bom_revision?: number;
  part_no?: string;
  size?: string;
  remark?: string;
}

export interface MaterialGroup {
  material: string;
  item_count: number;
  total_quantity: number;
  subtotal: number;
  total_weight: number;
  material_cost_sum: number;
  items: SessionQuotationItem[];
}

export interface QuotationSummary {
  total_sessions: number;
  completed_sessions: number;
  pending_sessions: number;
  quoted_sessions: number;
  total_items: number;
  subtotal: number;
  vat: number;
  total: number;
  progress_percent: number;
}

export interface AssemblyQuotationGroup {
  assembly_drawing_number: string;
  assembly_description: string;
  bom_weight_kg: number;
  total_parts: number;
  quoted_parts: number;
  progress_percent: number;
  subtotal: number;
  vat: number;
  total: number;
  items: SessionQuotationItem[];
}

export interface ProjectQuotationResponse {
  project_id: string;
  project_name: string;
  customer: string;
  created_at: string;
  summary: QuotationSummary;
  items: SessionQuotationItem[];
  material_groups: MaterialGroup[];
  assembly_groups: AssemblyQuotationGroup[];
}

export interface SessionListItem {
  session_id: string;
  filename: string;
  status: string;
  detection_count: number;
  verified_count: number;
  project_id?: string | null;
  created_at?: string;
}

// =====================
// API Methods
// =====================

export const projectApi = {
  create: async (data: ProjectCreate): Promise<Project> => {
    const { data: result } = await api.post<Project>('/projects', data);
    return result;
  },

  list: async (customer?: string, limit = 50): Promise<ProjectListResponse> => {
    const { data } = await api.get<ProjectListResponse>('/projects', {
      params: { customer, limit },
    });
    return data;
  },

  get: async (projectId: string): Promise<ProjectDetail> => {
    const { data } = await api.get<ProjectDetail>(`/projects/${projectId}`);
    return data;
  },

  update: async (projectId: string, updates: ProjectUpdate): Promise<Project> => {
    const { data } = await api.put<Project>(`/projects/${projectId}`, updates);
    return data;
  },

  delete: async (projectId: string, deleteSessions = false): Promise<void> => {
    await api.delete(`/projects/${projectId}`, {
      params: { delete_sessions: deleteSessions },
    });
  },

  uploadGT: async (
    projectId: string,
    files: File[]
  ): Promise<{ uploaded: string[]; failed: string[] }> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    const { data } = await api.post(
      `/projects/${projectId}/gt`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  },

  listGT: async (
    projectId: string
  ): Promise<{ gt_files: string[]; total: number }> => {
    const { data } = await api.get(`/projects/${projectId}/gt`);
    return data;
  },

  batchUpload: async (
    projectId: string,
    files: File[],
    templateId?: string,
    autoDetect = true
  ): Promise<{ project_id: string; uploaded_count: number; session_ids: string[]; failed_files: string[]; message: string }> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    if (templateId) formData.append('template_id', templateId);
    formData.append('auto_detect', String(autoDetect));

    const { data } = await api.post(
      `/projects/${projectId}/upload-batch`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  },

  importBOM: async (projectId: string, file: File): Promise<BOMHierarchyResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const { data } = await api.post<BOMHierarchyResponse>(
      `/projects/${projectId}/import-bom`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  },

  getBOMHierarchy: async (projectId: string): Promise<BOMHierarchyResponse> => {
    const { data } = await api.get<BOMHierarchyResponse>(
      `/projects/${projectId}/bom-hierarchy`
    );
    return data;
  },

  matchDrawings: async (projectId: string, drawingFolder: string): Promise<DrawingMatchResult> => {
    const { data } = await api.post<DrawingMatchResult>(
      `/projects/${projectId}/match-drawings`,
      { drawing_folder: drawingFolder }
    );
    return data;
  },

  createSessions: async (
    projectId: string,
    templateName?: string,
    onlyMatched = true
  ): Promise<SessionBatchCreateResponse> => {
    const { data } = await api.post<SessionBatchCreateResponse>(
      `/projects/${projectId}/create-sessions`,
      { template_name: templateName, only_matched: onlyMatched }
    );
    return data;
  },

  getQuotation: async (projectId: string, refresh = false): Promise<ProjectQuotationResponse> => {
    const { data } = await api.get<ProjectQuotationResponse>(
      `/projects/${projectId}/quotation`,
      { params: { refresh } }
    );
    return data;
  },

  getQuotationDownloadUrl: (projectId: string, format: 'pdf' | 'excel' = 'pdf'): string => {
    const baseUrl = api.defaults.baseURL || '';
    return `${baseUrl}/projects/${projectId}/quotation/download?format=${format}`;
  },

  startBatchAnalysis: async (
    projectId: string,
    rootDrawingNumber?: string,
    forceRerun = false
  ): Promise<{ project_id: string; status: string; total: number; message: string }> => {
    const { data } = await api.post(`/analysis/batch/${projectId}`, {
      root_drawing_number: rootDrawingNumber || null,
      force_rerun: forceRerun,
    });
    return data;
  },

  getBatchStatus: async (
    projectId: string
  ): Promise<{
    project_id: string;
    status: string;
    total: number;
    completed: number;
    failed: number;
    skipped: number;
    current_drawing: string | null;
    errors: string[];
  }> => {
    const { data } = await api.get(`/analysis/batch/${projectId}/status`);
    return data;
  },

  cancelBatchAnalysis: async (projectId: string): Promise<void> => {
    await api.delete(`/analysis/batch/${projectId}`);
  },

  // ========================================
  // Project Export/Import
  // ========================================

  exportProject: async (projectId: string, includeImages = false): Promise<void> => {
    const { data } = await api.get(`/projects/${projectId}/export`, {
      params: { include_images: includeImages },
      responseType: 'blob',
    });
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `project_${projectId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  importProject: async (file: File): Promise<ProjectDetail> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post<ProjectDetail>('/projects/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    });
    return data;
  },

  // ========================================
  // Session API (세션 상세 - 치수, 이미지 등)
  // ========================================

  getSession: async (sessionId: string): Promise<SessionDetail> => {
    const { data } = await api.get<SessionDetail>(`/sessions/${sessionId}`);
    return data;
  },

  getSessionImageUrl: (sessionId: string): string => {
    const baseUrl = api.defaults.baseURL || '';
    return `${baseUrl}/sessions/${sessionId}/image`;
  },

  getSessionDimensions: async (sessionId: string): Promise<SessionDimension[]> => {
    const { data } = await api.get<{ dimensions: SessionDimension[] }>(
      `/analysis/dimensions/${sessionId}`
    );
    return data.dimensions || [];
  },

  updateDimensionStatus: async (
    sessionId: string,
    dimensionId: string,
    status: VerificationStatus,
    modifiedValue?: string
  ): Promise<void> => {
    await api.patch(`/analysis/dimensions/${sessionId}/${dimensionId}`, {
      verification_status: status,
      modified_value: modifiedValue,
    });
  },
};

export const sessionApi = {
  list: async (projectId?: string, limit = 50): Promise<SessionListItem[]> => {
    const { data } = await api.get<SessionListItem[]>('/sessions', {
      params: { project_id: projectId, limit },
    });
    return data;
  },

  updateProjectId: async (sessionId: string, projectId: string): Promise<void> => {
    await api.patch(`/sessions/${sessionId}`, { project_id: projectId });
  },

  unlinkProjectId: async (sessionId: string): Promise<void> => {
    await api.patch(`/sessions/${sessionId}`, { project_id: null });
  },
};

// ========================================
// Session Types
// ========================================

export interface SessionDetail {
  session_id: string;
  drawing_number: string;
  status: string;
  file_path: string;
  image_width: number;
  image_height: number;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, unknown>;
}

export type VerificationStatus = 'pending' | 'approved' | 'rejected' | 'modified' | 'manual';

export interface SessionDimension {
  id: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  value: string;
  raw_text: string;
  modified_value: string | null;
  modified_bbox: { x1: number; y1: number; x2: number; y2: number } | null;
  unit: string;
  tolerance: string | null;
  dimension_type: string;
  confidence: number;
  model_id: string;
  verification_status: VerificationStatus;
  linked_to: string | null;
}
