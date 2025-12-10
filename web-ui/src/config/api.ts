/**
 * API Configuration
 * 관리 API 엔드포인트 설정
 *
 * NOTE: API 매핑 및 레지스트리는 apiRegistry.ts를 사용하세요.
 * @see ./apiRegistry.ts - 중앙화된 API 정의
 */

// 환경 변수에서 API URL 가져오기
const getApiUrl = (key: string, defaultValue: string): string => {
  return import.meta.env[key] || defaultValue;
};

/**
 * 관리 API 설정 (Gateway API 사용)
 */
export const ADMIN_API_URL = getApiUrl('VITE_GATEWAY_URL', 'http://localhost:8000');

export const ADMIN_ENDPOINTS = {
  status: `${ADMIN_API_URL}/admin/status`,
  gpuStats: `${ADMIN_API_URL}/admin/status`,  // GPU 정보는 status에 포함
  allModels: `${ADMIN_API_URL}/admin/models`,  // 모든 모델 경로
  models: (modelType: string) => `${ADMIN_API_URL}/admin/models/${modelType}`,
  logs: (service: string) => `${ADMIN_API_URL}/admin/logs/${service}`,
  docker: (action: string, service: string) =>
    `${ADMIN_API_URL}/admin/docker/${action}/${service}`,
  dockerPs: `${ADMIN_API_URL}/admin/docker/ps`,
};

/**
 * 시스템 설정
 */
export const SYSTEM_CONFIG = {
  // 자동 갱신 간격 (밀리초)
  AUTO_REFRESH_INTERVAL: 5000,

  // API 타임아웃 (밀리초)
  API_TIMEOUT: 60000,

  // 로그 조회 기본 줄 수
  DEFAULT_LOG_LINES: 200,

  // GPU 메모리 경고 임계값 (%)
  GPU_MEMORY_WARNING_THRESHOLD: 80,

  // CPU 경고 임계값 (%)
  CPU_WARNING_THRESHOLD: 80,

  // 메모리 경고 임계값 (%)
  MEMORY_WARNING_THRESHOLD: 85,
};

export default {
  ADMIN_API_URL,
  ADMIN_ENDPOINTS,
  SYSTEM_CONFIG,
};
