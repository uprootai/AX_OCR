// eDOCr2 API — OCR (v1, v2, Enhanced)

import axios, { type AxiosProgressEvent } from 'axios';
import type { HealthCheckResponse, OCRResult } from '../../types/api';
import type { ProgressCallback } from '../apiTypes';
import { EDOCR2_BASE, EDOCR2_V2_BASE } from './urls';

const edocr2API = axios.create({ baseURL: EDOCR2_BASE });
const edocr2V2API = axios.create({ baseURL: EDOCR2_V2_BASE });

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
