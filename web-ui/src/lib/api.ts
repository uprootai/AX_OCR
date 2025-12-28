import axios, { type AxiosProgressEvent } from 'axios';
import type {
  HealthCheckResponse,
  AnalysisResult,
  QuoteResult,
  OCRResult,
  SegmentationResult,
  ToleranceResult,
  GenericAPIResponse,
} from '../types/api';

// API Base URLs (환경변수로 설정 가능)
const API_BASE = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000';
const EDOCR2_BASE = import.meta.env.VITE_EDOCR2_URL || 'http://localhost:5001';
const EDOCR2_V2_BASE = import.meta.env.VITE_EDOCR2_V2_URL || 'http://localhost:5002';
const EDGNET_BASE = import.meta.env.VITE_EDGNET_URL || 'http://localhost:5012';
const SKINMODEL_BASE = import.meta.env.VITE_SKINMODEL_URL || 'http://localhost:5003';
const YOLO_BASE = import.meta.env.VITE_YOLO_URL || 'http://localhost:5005';
const PADDLEOCR_BASE = import.meta.env.VITE_PADDLEOCR_URL || 'http://localhost:5006';
const VL_BASE = import.meta.env.VITE_VL_URL || 'http://localhost:5004';

// Additional OCR Services
const TESSERACT_BASE = import.meta.env.VITE_TESSERACT_URL || 'http://localhost:5008';
const TROCR_BASE = import.meta.env.VITE_TROCR_URL || 'http://localhost:5009';
const ESRGAN_BASE = import.meta.env.VITE_ESRGAN_URL || 'http://localhost:5010';
const OCR_ENSEMBLE_BASE = import.meta.env.VITE_OCR_ENSEMBLE_URL || 'http://localhost:5011';
const SURYA_OCR_BASE = import.meta.env.VITE_SURYA_OCR_URL || 'http://localhost:5013';
const DOCTR_BASE = import.meta.env.VITE_DOCTR_URL || 'http://localhost:5014';
const EASYOCR_BASE = import.meta.env.VITE_EASYOCR_URL || 'http://localhost:5015';

// Knowledge & P&ID Services
const KNOWLEDGE_BASE = import.meta.env.VITE_KNOWLEDGE_URL || 'http://localhost:5007';
const YOLO_PID_BASE = import.meta.env.VITE_YOLO_PID_URL || 'http://localhost:5017';
const LINE_DETECTOR_BASE = import.meta.env.VITE_LINE_DETECTOR_URL || 'http://localhost:5016';
const PID_ANALYZER_BASE = import.meta.env.VITE_PID_ANALYZER_URL || 'http://localhost:5018';
const DESIGN_CHECKER_BASE = import.meta.env.VITE_DESIGN_CHECKER_URL || 'http://localhost:5019';

// Axios 인스턴스 생성
const gatewayAPI = axios.create({ baseURL: API_BASE });
const edocr2API = axios.create({ baseURL: EDOCR2_BASE });
const edocr2V2API = axios.create({ baseURL: EDOCR2_V2_BASE });
const edgnetAPI = axios.create({ baseURL: EDGNET_BASE });
const skinmodelAPI = axios.create({ baseURL: SKINMODEL_BASE });
const yoloAPI = axios.create({ baseURL: YOLO_BASE });
const paddleocrAPI = axios.create({ baseURL: PADDLEOCR_BASE });
const vlAPI = axios.create({ baseURL: VL_BASE });

// Additional OCR Services
const tesseractAPI = axios.create({ baseURL: TESSERACT_BASE });
const trocrAPI = axios.create({ baseURL: TROCR_BASE });
const esrganAPI = axios.create({ baseURL: ESRGAN_BASE });
const ocrEnsembleAPI = axios.create({ baseURL: OCR_ENSEMBLE_BASE });
const suryaOcrAPI = axios.create({ baseURL: SURYA_OCR_BASE });
const doctrAPI = axios.create({ baseURL: DOCTR_BASE });
const easyocrAPI = axios.create({ baseURL: EASYOCR_BASE });

// Knowledge & P&ID Services
const knowledgeAPI = axios.create({ baseURL: KNOWLEDGE_BASE });
const yoloPidAPI = axios.create({ baseURL: YOLO_PID_BASE });
const lineDetectorAPI = axios.create({ baseURL: LINE_DETECTOR_BASE });
const pidAnalyzerAPI = axios.create({ baseURL: PID_ANALYZER_BASE });
const designCheckerAPI = axios.create({ baseURL: DESIGN_CHECKER_BASE });

// 진행률 콜백 타입
export type ProgressCallback = (progress: number) => void;

// ==================== Gateway API ====================

export const gatewayApi = {
  // Health Check
  healthCheck: async (): Promise<HealthCheckResponse> => {
    const response = await gatewayAPI.get('/api/v1/health');
    return response.data;
  },

  // Process (통합 분석)
  process: async (
    file: File,
    options: {
      pipeline_mode?: 'hybrid' | 'speed';
      use_ocr?: boolean;
      use_segmentation?: boolean;
      use_tolerance?: boolean;
      visualize?: boolean;
      use_yolo_crop_ocr?: boolean;
      use_ensemble?: boolean;
      // Hyperparameters
      yolo_conf_threshold?: number;
      yolo_iou_threshold?: number;
      yolo_imgsz?: number;
      edgnet_num_classes?: number;
      edocr_use_vl_model?: boolean;
    },
    onProgress?: ProgressCallback
  ): Promise<AnalysisResult> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('pipeline_mode', options.pipeline_mode ?? 'speed');
    formData.append('use_ocr', String(options.use_ocr ?? true));
    formData.append('use_segmentation', String(options.use_segmentation ?? true));
    formData.append('use_tolerance', String(options.use_tolerance ?? true));
    formData.append('visualize', String(options.visualize ?? true));
    formData.append('use_yolo_crop_ocr', String(options.use_yolo_crop_ocr ?? false));
    formData.append('use_ensemble', String(options.use_ensemble ?? false));

    // Add hyperparameters if provided
    if (options.yolo_conf_threshold !== undefined) {
      formData.append('yolo_conf_threshold', String(options.yolo_conf_threshold));
    }
    if (options.yolo_iou_threshold !== undefined) {
      formData.append('yolo_iou_threshold', String(options.yolo_iou_threshold));
    }
    if (options.yolo_imgsz !== undefined) {
      formData.append('yolo_imgsz', String(options.yolo_imgsz));
    }
    if (options.edgnet_num_classes !== undefined) {
      formData.append('edgnet_num_classes', String(options.edgnet_num_classes));
    }
    if (options.edocr_use_vl_model !== undefined) {
      formData.append('edocr_use_vl_model', String(options.edocr_use_vl_model));
    }

    const response = await gatewayAPI.post('/api/v1/process', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e: AxiosProgressEvent) => {
        if (e.total && onProgress) {
          const progress = Math.round((e.loaded * 100) / e.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  // Quote (견적)
  quote: async (
    file: File,
    params: {
      material_cost_per_kg?: number;
      machining_rate_per_hour?: number;
      tolerance_premium_factor?: number;
    },
    onProgress?: ProgressCallback
  ): Promise<QuoteResult> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('material_cost_per_kg', String(params.material_cost_per_kg ?? 5.0));
    formData.append('machining_rate_per_hour', String(params.machining_rate_per_hour ?? 50.0));
    formData.append('tolerance_premium_factor', String(params.tolerance_premium_factor ?? 1.2));

    const response = await gatewayAPI.post('/api/v1/quote', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e: AxiosProgressEvent) => {
        if (e.total && onProgress) {
          const progress = Math.round((e.loaded * 100) / e.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },
};

// ==================== eDOCr2 API ====================

export const edocr2Api = {
  // Health Check - v1
  healthCheck: async (): Promise<HealthCheckResponse> => {
    const response = await edocr2API.get('/api/v1/health');
    return response.data;
  },

  // Health Check - v2
  healthCheckV2: async (): Promise<HealthCheckResponse> => {
    const response = await edocr2V2API.get('/api/v2/health');
    return response.data;
  },

  // OCR - v1
  ocr: async (
    file: File,
    options: {
      extract_dimensions?: boolean;
      extract_gdt?: boolean;
      extract_text?: boolean;
      use_vl_model?: boolean;
      visualize?: boolean;
    },
    onProgress?: ProgressCallback
  ): Promise<{ status: string; data: OCRResult; processing_time: number; version: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('extract_dimensions', String(options.extract_dimensions ?? true));
    formData.append('extract_gdt', String(options.extract_gdt ?? true));
    formData.append('extract_text', String(options.extract_text ?? true));
    formData.append('use_vl_model', String(options.use_vl_model ?? false));
    formData.append('visualize', String(options.visualize ?? false));

    const response = await edocr2API.post('/api/v1/ocr', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e: AxiosProgressEvent) => {
        if (e.total && onProgress) {
          const progress = Math.round((e.loaded * 100) / e.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  // OCR - v2 (Advanced with table support)
  ocrV2: async (
    file: File,
    options: {
      extract_dimensions?: boolean;
      extract_gdt?: boolean;
      extract_text?: boolean;
      extract_tables?: boolean;
      visualize?: boolean;
      language?: string;
      cluster_threshold?: number;
    },
    onProgress?: ProgressCallback
  ): Promise<{ status: string; data: OCRResult; processing_time: number; version: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('extract_dimensions', String(options.extract_dimensions ?? true));
    formData.append('extract_gdt', String(options.extract_gdt ?? true));
    formData.append('extract_text', String(options.extract_text ?? true));
    formData.append('extract_tables', String(options.extract_tables ?? true));
    formData.append('visualize', String(options.visualize ?? false));
    formData.append('language', options.language ?? 'eng');
    formData.append('cluster_threshold', String(options.cluster_threshold ?? 20));

    const response = await edocr2V2API.post('/api/v2/ocr', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e: AxiosProgressEvent) => {
        if (e.total && onProgress) {
          const progress = Math.round((e.loaded * 100) / e.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  // Enhanced OCR with performance improvement strategies
  ocrEnhanced: async (
    file: File,
    options: {
      extract_dimensions?: boolean;
      extract_gdt?: boolean;
      extract_text?: boolean;
      visualize?: boolean;
      strategy?: 'basic' | 'edgnet' | 'vl' | 'hybrid';
      vl_provider?: 'openai' | 'anthropic';
    },
    onProgress?: ProgressCallback
  ): Promise<{ status: string; data: OCRResult; processing_time: number; enhancement: Record<string, unknown> }> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('extract_dimensions', String(options.extract_dimensions ?? true));
    formData.append('extract_gdt', String(options.extract_gdt ?? true));
    formData.append('extract_text', String(options.extract_text ?? false));
    formData.append('visualize', String(options.visualize ?? false));
    formData.append('strategy', options.strategy ?? 'edgnet');
    formData.append('vl_provider', options.vl_provider ?? 'openai');

    const response = await edocr2API.post('/api/v1/ocr/enhanced', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e: AxiosProgressEvent) => {
        if (e.total && onProgress) {
          const progress = Math.round((e.loaded * 100) / e.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },
};

// ==================== EDGNet API ====================

export const edgnetApi = {
  // Health Check
  healthCheck: async (): Promise<HealthCheckResponse> => {
    const response = await edgnetAPI.get('/api/v1/health');
    return response.data;
  },

  // Segment
  segment: async (
    file: File,
    options: {
      visualize?: boolean;
      num_classes?: number;
    },
    onProgress?: ProgressCallback
  ): Promise<{ status: string; data: SegmentationResult; processing_time: number }> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('visualize', String(options.visualize ?? true));
    formData.append('num_classes', String(options.num_classes ?? 3));

    const response = await edgnetAPI.post('/api/v1/segment', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e: AxiosProgressEvent) => {
        if (e.total && onProgress) {
          const progress = Math.round((e.loaded * 100) / e.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  // Vectorize
  vectorize: async (
    file: File,
    options: {
      save_bezier?: boolean;
    },
    onProgress?: ProgressCallback
  ): Promise<GenericAPIResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('save_bezier', String(options.save_bezier ?? true));

    const response = await edgnetAPI.post('/api/v1/vectorize', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e: AxiosProgressEvent) => {
        if (e.total && onProgress) {
          const progress = Math.round((e.loaded * 100) / e.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },
};

// ==================== Skin Model API ====================

export const skinmodelApi = {
  // Health Check
  healthCheck: async (): Promise<HealthCheckResponse> => {
    const response = await skinmodelAPI.get('/api/v1/health');
    return response.data;
  },

  // Tolerance Prediction
  tolerance: async (data: {
    dimensions: Array<{
      type: string;
      value: number;
      tolerance?: number;
      unit?: string;
    }>;
    material: {
      name: string;
      youngs_modulus?: number;
      poisson_ratio?: number;
      density?: number;
    };
    manufacturing_process?: string;
    correlation_length?: number;
  }): Promise<{ status: string; data: ToleranceResult; processing_time: number }> => {
    const response = await skinmodelAPI.post('/api/v1/tolerance', data);
    return response.data;
  },

  // Validate GD&T
  validate: async (data: {
    gdt_specs: Array<{
      type: string;
      value: number;
      datum?: string;
    }>;
    dimensions: Array<{
      type: string;
      value: number;
    }>;
  }): Promise<GenericAPIResponse> => {
    const response = await skinmodelAPI.post('/api/v1/validate', data);
    return response.data;
  },
};

// ==================== YOLOv11 API ====================

export const yoloApi = {
  // Health Check
  healthCheck: async (): Promise<HealthCheckResponse> => {
    const response = await yoloAPI.get('/api/v1/health');
    return response.data;
  },

  // Detect
  detect: async (
    file: File,
    options: {
      conf_threshold?: number;
      iou_threshold?: number;
      imgsz?: number;
      visualize?: boolean;
    },
    onProgress?: ProgressCallback
  ): Promise<{
    status: string;
    file_id: string;
    detections: Array<{
      class_id: number;
      class_name: string;
      confidence: number;
      bbox: { x: number; y: number; width: number; height: number };
      value: string | null;
    }>;
    detection_count: number;
    processing_time: number;
    model_info: {
      model_name: string;
      version: string;
      device: string;
    };
    visualized_image?: string;
  }> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('conf_threshold', String(options.conf_threshold ?? 0.25));
    formData.append('iou_threshold', String(options.iou_threshold ?? 0.7));
    formData.append('imgsz', String(options.imgsz ?? 1280));
    formData.append('visualize', String(options.visualize ?? false));

    const response = await yoloAPI.post('/api/v1/detect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e: AxiosProgressEvent) => {
        if (e.total && onProgress) {
          const progress = Math.round((e.loaded * 100) / e.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },
};

// ==================== PaddleOCR API ====================

export const paddleocrApi = {
  // Health Check
  healthCheck: async (): Promise<HealthCheckResponse> => {
    const response = await paddleocrAPI.get('/api/v1/health');
    return response.data;
  },
};

// ==================== VL API ====================

export const vlApi = {
  // Health Check
  healthCheck: async (): Promise<HealthCheckResponse> => {
    const response = await vlAPI.get('/api/v1/health');
    return response.data;
  },

  // Extract Information Block
  extractInfoBlock: async (
    file: File,
    options: {
      query_fields?: string[];
      model?: string;
    } = {}
  ): Promise<GenericAPIResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('query_fields', JSON.stringify(options.query_fields || ["name", "part number", "material", "scale", "weight"]));
    formData.append('model', options.model || 'claude-3-5-sonnet-20241022');

    const response = await vlAPI.post('/api/v1/extract_info_block', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Extract Dimensions
  extractDimensions: async (
    file: File,
    model: string = 'claude-3-5-sonnet-20241022'
  ): Promise<GenericAPIResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model', model);

    const response = await vlAPI.post('/api/v1/extract_dimensions', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Infer Manufacturing Process
  inferManufacturingProcess: async (
    file: File,
    model: string = 'claude-3-5-sonnet-20241022'
  ): Promise<GenericAPIResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model', model);

    const response = await vlAPI.post('/api/v1/infer_manufacturing_process', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Generate QC Checklist
  generateQCChecklist: async (
    file: File,
    model: string = 'claude-3-5-sonnet-20241022'
  ): Promise<GenericAPIResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model', model);

    const response = await vlAPI.post('/api/v1/generate_qc_checklist', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

// ==================== Surya OCR API (90+ languages, Layout Analysis) ====================

export const suryaOcrApi = {
  // Health Check
  healthCheck: async (): Promise<HealthCheckResponse> => {
    const response = await suryaOcrAPI.get('/health');
    return response.data;
  },
};

// ==================== DocTR API (2-Stage Pipeline OCR) ====================

export const doctrApi = {
  // Health Check
  healthCheck: async (): Promise<HealthCheckResponse> => {
    const response = await doctrAPI.get('/health');
    return response.data;
  },
};

// ==================== EasyOCR API (80+ languages, CPU Friendly) ====================

export const easyocrApi = {
  // Health Check
  healthCheck: async (): Promise<HealthCheckResponse> => {
    const response = await easyocrAPI.get('/health');
    return response.data;
  },
};

// ==================== 유틸리티 함수 ====================

// 모든 서비스 헬스체크 (19개 API - 실제 Docker 컨테이너 기준)
export const checkAllServices = async () => {
  // 각 서비스의 헬스체크를 개별적으로 수행 (일부 실패해도 나머지 확인 가능)
  const healthChecks: Record<string, Promise<boolean>> = {
    gateway: gatewayAPI.get('/api/v1/health', { timeout: 3000 }).then(() => true).catch(() => false),
    yolo: yoloAPI.get('/api/v1/health', { timeout: 3000 }).then(() => true).catch(() => false),
    yolo_pid: yoloPidAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    edocr2: edocr2V2API.get('/api/v1/health', { timeout: 3000 }).then(() => true).catch(() => false),
    paddleocr: paddleocrAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    tesseract: tesseractAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    trocr: trocrAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    ocr_ensemble: ocrEnsembleAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    surya_ocr: suryaOcrAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    doctr: doctrAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    easyocr: easyocrAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    edgnet: edgnetAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    line_detector: lineDetectorAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    esrgan: esrganAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    skinmodel: skinmodelAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    pid_analyzer: pidAnalyzerAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    design_checker: designCheckerAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    knowledge: knowledgeAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
    vl: vlAPI.get('/health', { timeout: 3000 }).then(() => true).catch(() => false),
  };

  const entries = Object.entries(healthChecks);
  const results = await Promise.all(entries.map(async ([key, promise]) => [key, await promise]));

  return Object.fromEntries(results) as Record<string, boolean>;
};

// ==================== BlueprintFlow Workflow API ====================

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

// ==================== Dynamic API Client Creation ====================

export interface DynamicAPIClient {
  healthCheck: () => Promise<HealthCheckResponse>;
  process: (file: File, options?: Record<string, unknown>) => Promise<GenericAPIResponse>;
  getRaw: () => unknown;
}

/**
 * 동적으로 API 클라이언트를 생성합니다.
 * 사용자가 Dashboard에서 추가한 커스텀 API를 위한 클라이언트를 생성합니다.
 */
export function createDynamicAPIClient(baseUrl: string): DynamicAPIClient {
  const axiosInstance = axios.create({
    baseURL: baseUrl,
    timeout: 30000,
  });

  return {
    healthCheck: async (): Promise<HealthCheckResponse> => {
      const response = await axiosInstance.get('/api/v1/health');
      return response.data;
    },

    // 일반적인 POST 요청 (파일 업로드 등)
    process: async (file: File, options?: Record<string, unknown>): Promise<GenericAPIResponse> => {
      const formData = new FormData();
      formData.append('file', file);

      if (options) {
        Object.entries(options).forEach(([key, value]) => {
          formData.append(key, String(value));
        });
      }

      const response = await axiosInstance.post('/api/v1/process', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },

    // 원시 axios 인스턴스 제공 (고급 사용자용)
    getRaw: () => axiosInstance,
  };
}

/**
 * localStorage에 저장된 모든 커스텀 API의 클라이언트를 반환합니다.
 */
export function getAllDynamicAPIClients(): Record<string, DynamicAPIClient> {
  const customAPIsJSON = localStorage.getItem('custom-apis-storage');
  if (!customAPIsJSON) {
    return {};
  }

  try {
    const storage = JSON.parse(customAPIsJSON);
    const customAPIs: Array<{ id: string; enabled: boolean; baseUrl: string }> = storage.state?.customAPIs || [];

    const clients: Record<string, DynamicAPIClient> = {};

    customAPIs.forEach((api) => {
      if (api.enabled) {
        clients[api.id] = createDynamicAPIClient(api.baseUrl);
      }
    });

    return clients;
  } catch (error) {
    console.error('Failed to load custom API clients:', error);
    return {};
  }
}

/**
 * 모든 서비스 (기본 + 커스텀) 헬스체크
 * Returns boolean for each service (true = healthy, false = unhealthy)
 */
export const checkAllServicesIncludingCustom = async (): Promise<Record<string, boolean>> => {
  // 기본 서비스 체크 (returns Record<string, boolean>)
  const baseResults = await checkAllServices();

  // 커스텀 API 클라이언트 가져오기
  const customClients = getAllDynamicAPIClients();

  // 커스텀 API 헬스체크
  const customHealthChecks = Object.entries(customClients).map(async ([id, client]) => {
    try {
      await client.healthCheck();
      return { id, healthy: true };
    } catch {
      return { id, healthy: false };
    }
  });

  const customResults = await Promise.all(customHealthChecks);

  // 커스텀 결과를 객체로 변환
  const customResultsObj: Record<string, boolean> = {};
  customResults.forEach(({ id, healthy }) => {
    customResultsObj[id] = healthy;
  });

  return {
    ...baseResults,
    ...customResultsObj,
  };
};
