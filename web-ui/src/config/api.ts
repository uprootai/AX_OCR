/**
 * API Configuration
 * 모든 API 엔드포인트를 중앙에서 관리
 * 하드코딩 방지 및 환경별 설정 지원
 */

export interface APIEndpoint {
  name: string;
  displayName: string;
  url: string;
  port: number;
  description: string;
  features: string[];
  gpuEnabled: boolean;
  version: string;
}

export interface ModelInfo {
  type: string;
  displayName: string;
  description: string;
  framework: string;
  inputFormats: string[];
  outputFormat: string;
  endpoint: string;
}

// 환경 변수에서 API URL 가져오기
const getApiUrl = (key: string, defaultValue: string): string => {
  return import.meta.env[key] || defaultValue;
};

/**
 * API 엔드포인트 설정
 */
export const API_ENDPOINTS: Record<string, APIEndpoint> = {
  gateway: {
    name: 'gateway',
    displayName: 'Gateway API',
    url: getApiUrl('VITE_GATEWAY_URL', 'http://localhost:8000'),
    port: 8000,
    description: '통합 API 게이트웨이 - 모든 서비스를 하나의 엔드포인트로 통합',
    features: ['통합 라우팅', '로드 밸런싱', '헬스 체크'],
    gpuEnabled: false,
    version: '1.0.0',
  },
  edocr2: {
    name: 'edocr2',
    displayName: 'eDOCr2 API',
    url: getApiUrl('VITE_EDOCR2_URL', 'http://localhost:5001'),
    port: 5001,
    description: '한글 OCR 엔진 - GPU 가속 전처리 지원',
    features: ['한글 OCR', 'GPU 전처리', 'CLAHE', 'Gaussian Blur'],
    gpuEnabled: true,
    version: '2.0.0',
  },
  edgnet: {
    name: 'edgnet',
    displayName: 'EDGNet API',
    url: getApiUrl('VITE_EDGNET_URL', 'http://localhost:5012'),
    port: 5012,
    description: '도면 세그멘테이션 엔진 - PyTorch GPU 가속',
    features: ['도면 분할', '영역 감지', '레이아웃 분석', 'GPU 가속'],
    gpuEnabled: true,
    version: '1.0.0',
  },
  skinmodel: {
    name: 'skinmodel',
    displayName: 'Skin Model API',
    url: getApiUrl('VITE_SKINMODEL_URL', 'http://localhost:5003'),
    port: 5003,
    description: '공차 예측 모델 - XGBoost 기반',
    features: ['Flatness 예측', 'Cylindricity 예측', 'Position 예측'],
    gpuEnabled: false,
    version: '2.0.0',
  },
  vl: {
    name: 'vl',
    displayName: 'VL API',
    url: getApiUrl('VITE_VL_URL', 'http://localhost:5004'),
    port: 5004,
    description: '멀티모달 비전-언어 모델',
    features: ['이미지 분석', '텍스트 생성', '멀티모달 처리'],
    gpuEnabled: false,
    version: '1.0.0',
  },
  yolo: {
    name: 'yolo',
    displayName: 'YOLO API',
    url: getApiUrl('VITE_YOLO_URL', 'http://localhost:5005'),
    port: 5005,
    description: '객체 탐지 엔진 - YOLOv11 GPU 가속',
    features: ['실시간 객체 탐지', 'GPU 가속', 'YOLOv11'],
    gpuEnabled: true,
    version: '11.0.0',
  },
  paddleocr: {
    name: 'paddleocr',
    displayName: 'PaddleOCR API',
    url: getApiUrl('VITE_PADDLEOCR_URL', 'http://localhost:5006'),
    port: 5006,
    description: 'PaddlePaddle OCR 엔진 - GPU 가속',
    features: ['다국어 OCR', 'GPU 가속', '각도 분류', '텍스트 인식'],
    gpuEnabled: true,
    version: '2.0.0',
  },
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
 * 모델 정보
 */
export const MODEL_INFO: Record<string, ModelInfo> = {
  yolo: {
    type: 'yolo',
    displayName: 'YOLOv11',
    description: '실시간 객체 탐지 모델',
    framework: 'PyTorch',
    inputFormats: ['image/jpeg', 'image/png', 'application/pdf'],
    outputFormat: 'application/json',
    endpoint: 'yolo',
  },
  edocr2: {
    type: 'edocr2',
    displayName: 'eDOCr v2',
    description: '한글 OCR 엔진',
    framework: 'TensorFlow',
    inputFormats: ['image/jpeg', 'image/png', 'application/pdf'],
    outputFormat: 'application/json',
    endpoint: 'edocr2',
  },
  edgnet: {
    type: 'edgnet',
    displayName: 'EDGNet',
    description: '도면 세그멘테이션',
    framework: 'PyTorch',
    inputFormats: ['image/jpeg', 'image/png'],
    outputFormat: 'application/json',
    endpoint: 'edgnet',
  },
  skinmodel: {
    type: 'skinmodel',
    displayName: 'Skin Model',
    description: '공차 예측 모델',
    framework: 'XGBoost',
    inputFormats: ['application/json'],
    outputFormat: 'application/json',
    endpoint: 'skinmodel',
  },
};

/**
 * API 헬스 체크 URL
 */
export const getHealthCheckUrl = (apiName: string): string => {
  const endpoint = API_ENDPOINTS[apiName];
  return endpoint ? `${endpoint.url}/api/v1/health` : '';
};

/**
 * 모든 API 목록 가져오기
 */
export const getAllAPIs = (): APIEndpoint[] => {
  return Object.values(API_ENDPOINTS);
};

/**
 * GPU 지원 API 목록
 */
export const getGPUEnabledAPIs = (): APIEndpoint[] => {
  return Object.values(API_ENDPOINTS).filter((api) => api.gpuEnabled);
};

/**
 * API 이름으로 엔드포인트 가져오기
 */
export const getAPIEndpoint = (name: string): APIEndpoint | undefined => {
  return API_ENDPOINTS[name];
};

/**
 * 모델 타입별 설정
 */
export const MODEL_TYPES = {
  SKINMODEL: 'skinmodel',
  EDGNET: 'edgnet',
  YOLO: 'yolo',
  EDOCR2: 'edocr2',
} as const;

/**
 * 학습 가능한 모델 목록
 */
export const TRAINABLE_MODELS = [
  {
    type: 'edgnet_large',
    displayName: 'EDGNet Large',
    description: '대규모 데이터셋으로 프로덕션급 모델 학습',
    estimatedTime: '2-3시간',
    gpuRequired: true,
  },
  {
    type: 'yolo_custom',
    displayName: 'YOLO Custom',
    description: '실제 도면 데이터셋으로 커스텀 학습',
    estimatedTime: '1-2시간',
    gpuRequired: true,
  },
  {
    type: MODEL_TYPES.SKINMODEL,
    displayName: 'Skin Model (XGBoost)',
    description: 'Flatness, Cylindricity, Position 예측 모델',
    estimatedTime: '~14초',
    gpuRequired: false,
  },
  {
    type: MODEL_TYPES.EDGNET,
    displayName: 'EDGNet Simple',
    description: '간단한 테스트용 모델 학습',
    estimatedTime: '~5분',
    gpuRequired: false,
  },
];

/**
 * Docker 서비스 목록
 */
export const DOCKER_SERVICES = [
  { name: 'gateway', displayName: 'Gateway', gpuEnabled: false },
  { name: 'yolo', displayName: 'YOLO', gpuEnabled: true },
  { name: 'edocr2-v1', displayName: 'eDOCr v1', gpuEnabled: true },
  { name: 'edocr2-v2', displayName: 'eDOCr v2', gpuEnabled: true },
  { name: 'paddleocr', displayName: 'PaddleOCR', gpuEnabled: true },
  { name: 'surya-ocr', displayName: 'Surya OCR', gpuEnabled: true },
  { name: 'doctr', displayName: 'DocTR', gpuEnabled: true },
  { name: 'easyocr', displayName: 'EasyOCR', gpuEnabled: false },
  { name: 'edgnet', displayName: 'EDGNet', gpuEnabled: true },
  { name: 'skinmodel', displayName: 'Skin Model', gpuEnabled: false },
  { name: 'vl', displayName: 'VL API', gpuEnabled: true },
];

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
  API_ENDPOINTS,
  ADMIN_API_URL,
  ADMIN_ENDPOINTS,
  MODEL_INFO,
  MODEL_TYPES,
  TRAINABLE_MODELS,
  DOCKER_SERVICES,
  SYSTEM_CONFIG,
  getAllAPIs,
  getGPUEnabledAPIs,
  getAPIEndpoint,
  getHealthCheckUrl,
};
