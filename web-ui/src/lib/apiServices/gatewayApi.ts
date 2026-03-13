// Gateway API — 통합 분석 및 견적

import axios, { type AxiosProgressEvent } from 'axios';
import type { HealthCheckResponse, AnalysisResult, QuoteResult } from '../../types/api';
import type { ProgressCallback } from '../apiTypes';
import { API_BASE } from './urls';

const gatewayAPI = axios.create({ baseURL: API_BASE });

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
