// Extended OCR APIs — Surya OCR, DocTR, EasyOCR

import axios from 'axios';
import type { HealthCheckResponse } from '../../types/api';
import { SURYA_OCR_BASE, DOCTR_BASE, EASYOCR_BASE } from './urls';

const suryaOcrAPI = axios.create({ baseURL: SURYA_OCR_BASE });
const doctrAPI = axios.create({ baseURL: DOCTR_BASE });
const easyocrAPI = axios.create({ baseURL: EASYOCR_BASE });

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
