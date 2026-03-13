// EDGNet API — Segmentation + Vectorization
// SkinModel API — Tolerance Prediction + GD&T Validation

import axios, { type AxiosProgressEvent } from 'axios';
import type { HealthCheckResponse, SegmentationResult, ToleranceResult, GenericAPIResponse } from '../../types/api';
import type { ProgressCallback } from '../apiTypes';
import { EDGNET_BASE, SKINMODEL_BASE } from './urls';

const edgnetAPI = axios.create({ baseURL: EDGNET_BASE });
const skinmodelAPI = axios.create({ baseURL: SKINMODEL_BASE });

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
