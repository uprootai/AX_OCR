// Vision APIs — YOLOv11 Detection + PaddleOCR + VL (Vision Language)

import axios, { type AxiosProgressEvent } from 'axios';
import type { HealthCheckResponse, GenericAPIResponse } from '../../types/api';
import type { ProgressCallback } from '../apiTypes';
import { YOLO_BASE, PADDLEOCR_BASE, VL_BASE } from './urls';

const yoloAPI = axios.create({ baseURL: YOLO_BASE });
const paddleocrAPI = axios.create({ baseURL: PADDLEOCR_BASE });
const vlAPI = axios.create({ baseURL: VL_BASE });

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
