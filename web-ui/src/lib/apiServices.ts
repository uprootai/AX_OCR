// API Services - Base URLs, Axios 인스턴스, 개별 API 클라이언트

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
import type { ProgressCallback } from './apiTypes';

// Re-export ProgressCallback for convenience
export type { ProgressCallback } from './apiTypes';

// API Base URLs (환경변수로 설정 가능) - 다른 파일에서도 사용 가능하도록 export
export const API_BASE = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000';
export const GATEWAY_URL = API_BASE; // alias
export const EDOCR2_BASE = import.meta.env.VITE_EDOCR2_URL || 'http://localhost:5001';
export const EDOCR2_V2_BASE = import.meta.env.VITE_EDOCR2_V2_URL || 'http://localhost:5002';
export const EDGNET_BASE = import.meta.env.VITE_EDGNET_URL || 'http://localhost:5012';
export const SKINMODEL_BASE = import.meta.env.VITE_SKINMODEL_URL || 'http://localhost:5003';
export const YOLO_BASE = import.meta.env.VITE_YOLO_URL || 'http://localhost:5005';
export const PADDLEOCR_BASE = import.meta.env.VITE_PADDLEOCR_URL || 'http://localhost:5006';
export const VL_BASE = import.meta.env.VITE_VL_URL || 'http://localhost:5004';

// Additional OCR Services
export const TESSERACT_BASE = import.meta.env.VITE_TESSERACT_URL || 'http://localhost:5008';
export const TROCR_BASE = import.meta.env.VITE_TROCR_URL || 'http://localhost:5009';
export const ESRGAN_BASE = import.meta.env.VITE_ESRGAN_URL || 'http://localhost:5010';
export const OCR_ENSEMBLE_BASE = import.meta.env.VITE_OCR_ENSEMBLE_URL || 'http://localhost:5011';
export const SURYA_OCR_BASE = import.meta.env.VITE_SURYA_OCR_URL || 'http://localhost:5013';
export const DOCTR_BASE = import.meta.env.VITE_DOCTR_URL || 'http://localhost:5014';
export const EASYOCR_BASE = import.meta.env.VITE_EASYOCR_URL || 'http://localhost:5015';

// Knowledge & P&ID Services
export const KNOWLEDGE_BASE = import.meta.env.VITE_KNOWLEDGE_URL || 'http://localhost:5007';
export const LINE_DETECTOR_BASE = import.meta.env.VITE_LINE_DETECTOR_URL || 'http://localhost:5016';
export const PID_ANALYZER_BASE = import.meta.env.VITE_PID_ANALYZER_URL || 'http://localhost:5018';
export const DESIGN_CHECKER_BASE = import.meta.env.VITE_DESIGN_CHECKER_URL || 'http://localhost:5019';
export const BLUEPRINT_AI_BOM_BASE = import.meta.env.VITE_BLUEPRINT_AI_BOM_URL || 'http://localhost:5020';
export const PID_COMPOSER_BASE = import.meta.env.VITE_PID_COMPOSER_URL || 'http://localhost:5021';
export const TABLE_DETECTOR_BASE = import.meta.env.VITE_TABLE_DETECTOR_URL || 'http://localhost:5022';

// Axios 인스턴스 생성
const gatewayAPI = axios.create({ baseURL: API_BASE });
const edocr2API = axios.create({ baseURL: EDOCR2_BASE });
const edocr2V2API = axios.create({ baseURL: EDOCR2_V2_BASE });
const edgnetAPI = axios.create({ baseURL: EDGNET_BASE });
const skinmodelAPI = axios.create({ baseURL: SKINMODEL_BASE });
const yoloAPI = axios.create({ baseURL: YOLO_BASE });
const paddleocrAPI = axios.create({ baseURL: PADDLEOCR_BASE });
const vlAPI = axios.create({ baseURL: VL_BASE });

// Additional OCR Services (used for health checks via individual API calls)
// Note: Health checks now use silentHealthCheck() with URL constants directly
const suryaOcrAPI = axios.create({ baseURL: SURYA_OCR_BASE });
const doctrAPI = axios.create({ baseURL: DOCTR_BASE });
const easyocrAPI = axios.create({ baseURL: EASYOCR_BASE });

// Unused axios instances (health checks use fetch API now)
// const tesseractAPI = axios.create({ baseURL: TESSERACT_BASE });
// const trocrAPI = axios.create({ baseURL: TROCR_BASE });
// const esrganAPI = axios.create({ baseURL: ESRGAN_BASE });
// const ocrEnsembleAPI = axios.create({ baseURL: OCR_ENSEMBLE_BASE });
// const knowledgeAPI = axios.create({ baseURL: KNOWLEDGE_BASE });
// const lineDetectorAPI = axios.create({ baseURL: LINE_DETECTOR_BASE });
// const pidAnalyzerAPI = axios.create({ baseURL: PID_ANALYZER_BASE });
// const designCheckerAPI = axios.create({ baseURL: DESIGN_CHECKER_BASE });
// const blueprintAiBomAPI = axios.create({ baseURL: BLUEPRINT_AI_BOM_BASE });
// const pidComposerAPI = axios.create({ baseURL: PID_COMPOSER_BASE });

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
