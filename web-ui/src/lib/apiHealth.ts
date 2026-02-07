// API Health Check - 헬스체크, 동적 API 클라이언트

import axios from 'axios';
import type { HealthCheckResponse, GenericAPIResponse } from '../types/api';
import type { DynamicAPIClient } from './apiTypes';
import {
  API_BASE,
  YOLO_BASE,
  EDOCR2_V2_BASE,
  PADDLEOCR_BASE,
  TESSERACT_BASE,
  TROCR_BASE,
  ESRGAN_BASE,
  OCR_ENSEMBLE_BASE,
  SURYA_OCR_BASE,
  DOCTR_BASE,
  EASYOCR_BASE,
  EDGNET_BASE,
  LINE_DETECTOR_BASE,
  SKINMODEL_BASE,
  PID_ANALYZER_BASE,
  DESIGN_CHECKER_BASE,
  KNOWLEDGE_BASE,
  VL_BASE,
  BLUEPRINT_AI_BOM_BASE,
  PID_COMPOSER_BASE,
  TABLE_DETECTOR_BASE,
} from './apiServices';

// Silent health check using fetch (no console errors for failed requests)
const silentHealthCheck = async (url: string, timeout = 3000): Promise<boolean> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      method: 'GET',
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response.ok;
  } catch {
    clearTimeout(timeoutId);
    return false;
  }
};

// API ID -> Health Check URL 매핑
const API_HEALTH_URLS: Record<string, string> = {
  gateway: `${API_BASE}/api/v1/health`,
  yolo: `${YOLO_BASE}/api/v1/health`,
  edocr2: `${EDOCR2_V2_BASE}/api/v1/health`,
  paddleocr: `${PADDLEOCR_BASE}/health`,
  tesseract: `${TESSERACT_BASE}/health`,
  trocr: `${TROCR_BASE}/health`,
  ocr_ensemble: `${OCR_ENSEMBLE_BASE}/health`,
  surya_ocr: `${SURYA_OCR_BASE}/health`,
  doctr: `${DOCTR_BASE}/health`,
  easyocr: `${EASYOCR_BASE}/health`,
  edgnet: `${EDGNET_BASE}/health`,
  line_detector: `${LINE_DETECTOR_BASE}/health`,
  esrgan: `${ESRGAN_BASE}/health`,
  skinmodel: `${SKINMODEL_BASE}/health`,
  pid_analyzer: `${PID_ANALYZER_BASE}/health`,
  design_checker: `${DESIGN_CHECKER_BASE}/health`,
  knowledge: `${KNOWLEDGE_BASE}/health`,
  vl: `${VL_BASE}/health`,
  blueprint_ai_bom: `${BLUEPRINT_AI_BOM_BASE}/health`,
  pid_composer: `${PID_COMPOSER_BASE}/health`,
  table_detector: `${TABLE_DETECTOR_BASE}/health`,
};

// Container name -> API ID 매핑
const CONTAINER_TO_API: Record<string, string> = {
  'gateway-api': 'gateway',
  'yolo-api': 'yolo',
  'edocr2-v2-api': 'edocr2',
  'paddleocr-api': 'paddleocr',
  'tesseract-api': 'tesseract',
  'trocr-api': 'trocr',
  'ocr-ensemble-api': 'ocr_ensemble',
  'surya-ocr-api': 'surya_ocr',
  'doctr-api': 'doctr',
  'easyocr-api': 'easyocr',
  'edgnet-api': 'edgnet',
  'line-detector-api': 'line_detector',
  'esrgan-api': 'esrgan',
  'skinmodel-api': 'skinmodel',
  'pid-analyzer-api': 'pid_analyzer',
  'design-checker-api': 'design_checker',
  'knowledge-api': 'knowledge',
  'vl-api': 'vl',
  'blueprint-ai-bom-backend': 'blueprint_ai_bom',
  'pid-composer-api': 'pid_composer',
  'table-detector-api': 'table_detector',
};

// 모든 서비스 헬스체크 (실행 중인 컨테이너만 체크 - 콘솔 에러 방지)
export const checkAllServices = async () => {
  const results: Record<string, boolean> = {};

  // 모든 API를 기본적으로 false로 초기화
  Object.keys(API_HEALTH_URLS).forEach(apiId => {
    results[apiId] = false;
  });

  try {
    // 1. Gateway에서 실행 중인 컨테이너 목록 가져오기
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${API_BASE}/api/v1/containers`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      // Gateway 실패 시 모든 API를 false로 반환
      return results;
    }

    const data = await response.json();
    const containers = data.containers || [];

    // 2. 실행 중인 컨테이너만 필터링
    const runningContainers = containers
      .filter((c: { status: string }) => c.status === 'running')
      .map((c: { name: string }) => c.name);

    // 3. 실행 중인 컨테이너에 대해서만 health check
    const runningApiIds = runningContainers
      .map((name: string) => CONTAINER_TO_API[name])
      .filter((id: string | undefined): id is string => !!id);

    // Gateway는 항상 체크 (위 요청이 성공했으면 running)
    results['gateway'] = true;

    // 4. 실행 중인 API들만 health check
    const healthPromises = runningApiIds
      .filter((id: string) => id !== 'gateway') // gateway는 이미 체크됨
      .map(async (apiId: string) => {
        const url = API_HEALTH_URLS[apiId];
        if (url) {
          const healthy = await silentHealthCheck(url);
          return { apiId, healthy };
        }
        return { apiId, healthy: false };
      });

    const healthResults = await Promise.all(healthPromises);
    healthResults.forEach(({ apiId, healthy }) => {
      results[apiId] = healthy;
    });

  } catch {
    // Gateway 연결 실패 시 모든 API를 false로 유지
  }

  return results;
};

// ==================== Dynamic API Client Creation ====================

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

  // 커스텀 API URL 정보 가져오기
  const customAPIsJSON = localStorage.getItem('custom-apis-storage');
  if (!customAPIsJSON) {
    return baseResults;
  }

  try {
    const storage = JSON.parse(customAPIsJSON);
    const customAPIs: Array<{ id: string; enabled: boolean; baseUrl: string }> = storage.state?.customAPIs || [];

    // 커스텀 API 헬스체크 (silentHealthCheck 사용 - 콘솔 에러 방지)
    const customHealthChecks = customAPIs
      .filter(api => api.enabled)
      .map(async (api) => {
        // 각 custom API의 health endpoint URL 추정
        const healthUrl = `${api.baseUrl}/api/v1/health`;
        const healthy = await silentHealthCheck(healthUrl);
        return { id: api.id, healthy };
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
  } catch {
    return baseResults;
  }
};
