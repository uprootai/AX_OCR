/**
 * API Registry - Centralized API Configuration
 *
 * 새 API 추가 시 이 파일만 업데이트하면 됩니다.
 * 다른 파일들은 이 파일에서 import하여 사용합니다.
 *
 * @see CLAUDE.md "새 API 추가" 섹션
 */

export type NodeCategory =
  | 'input'
  | 'detection'
  | 'ocr'
  | 'segmentation'
  | 'preprocessing'
  | 'analysis'
  | 'knowledge'
  | 'ai'
  | 'control';

export interface APIDefinition {
  /** API ID (언더스코어 형식, 예: ocr_ensemble) */
  id: string;
  /** 노드 타입 ID (언더스코어 없음, 예: paddleocr) */
  nodeType: string;
  /** 표시 이름 */
  displayName: string;
  /** Docker 컨테이너 이름 */
  containerName: string;
  /** API 스펙 파일 ID (하이픈 형식, 예: ocr-ensemble) */
  specId: string;
  /** 포트 번호 */
  port: number;
  /** 카테고리 */
  category: NodeCategory;
  /** 설명 */
  description: string;
  /** 아이콘 (이모지) */
  icon: string;
  /** 색상 (hex) */
  color: string;
  /** GPU 지원 여부 */
  gpuEnabled: boolean;
}

/**
 * 전체 API 정의 목록 (19개 서비스)
 *
 * 새 API 추가 시 여기에 추가하세요.
 */
export const API_REGISTRY: APIDefinition[] = [
  // Orchestrator
  {
    id: 'gateway',
    nodeType: 'gateway',
    displayName: 'Gateway API',
    containerName: 'gateway-api',
    specId: 'gateway',
    port: 8000,
    category: 'control',
    description: 'API Gateway & Orchestrator',
    icon: '🚀',
    color: '#6366f1',
    gpuEnabled: false,
  },
  // Detection
  {
    id: 'yolo',
    nodeType: 'yolo',
    displayName: 'YOLOv11',
    containerName: 'yolo-api',
    specId: 'yolo',
    port: 5005,
    category: 'detection',
    description: '14가지 도면 심볼 검출',
    icon: '🎯',
    color: '#ef4444',
    gpuEnabled: true,
  },
  // OCR
  {
    id: 'edocr2',
    nodeType: 'edocr2',
    displayName: 'eDOCr2',
    containerName: 'edocr2-v2-api',
    specId: 'edocr2',
    port: 5002,
    category: 'ocr',
    description: '한국어 치수 인식',
    icon: '📐',
    color: '#3b82f6',
    gpuEnabled: true,
  },
  {
    id: 'paddleocr',
    nodeType: 'paddleocr',
    displayName: 'PaddleOCR',
    containerName: 'paddleocr-api',
    specId: 'paddleocr',
    port: 5006,
    category: 'ocr',
    description: '다국어 OCR',
    icon: '🔤',
    color: '#3b82f6',
    gpuEnabled: true,
  },
  {
    id: 'tesseract',
    nodeType: 'tesseract',
    displayName: 'Tesseract',
    containerName: 'tesseract-api',
    specId: 'tesseract',
    port: 5008,
    category: 'ocr',
    description: '문서 OCR',
    icon: '📄',
    color: '#3b82f6',
    gpuEnabled: false,
  },
  {
    id: 'trocr',
    nodeType: 'trocr',
    displayName: 'TrOCR',
    containerName: 'trocr-api',
    specId: 'trocr',
    port: 5009,
    category: 'ocr',
    description: '필기체 OCR',
    icon: '✍️',
    color: '#3b82f6',
    gpuEnabled: true,
  },
  {
    id: 'ocr_ensemble',
    nodeType: 'ocr_ensemble',
    displayName: 'OCR Ensemble',
    containerName: 'ocr-ensemble-api',
    specId: 'ocr-ensemble',
    port: 5011,
    category: 'ocr',
    description: '4엔진 가중 투표',
    icon: '🗳️',
    color: '#3b82f6',
    gpuEnabled: true,
  },
  {
    id: 'surya_ocr',
    nodeType: 'suryaocr',
    displayName: 'Surya OCR',
    containerName: 'surya-ocr-api',
    specId: 'suryaocr',
    port: 5013,
    category: 'ocr',
    description: '90+ 언어, 레이아웃 분석',
    icon: '🌞',
    color: '#3b82f6',
    gpuEnabled: true,
  },
  {
    id: 'doctr',
    nodeType: 'doctr',
    displayName: 'DocTR',
    containerName: 'doctr-api',
    specId: 'doctr',
    port: 5014,
    category: 'ocr',
    description: '2단계 파이프라인 OCR',
    icon: '📑',
    color: '#3b82f6',
    gpuEnabled: true,
  },
  {
    id: 'easyocr',
    nodeType: 'easyocr',
    displayName: 'EasyOCR',
    containerName: 'easyocr-api',
    specId: 'easyocr',
    port: 5015,
    category: 'ocr',
    description: '80+ 언어, CPU 친화적',
    icon: '👁️',
    color: '#3b82f6',
    gpuEnabled: false,
  },
  // Segmentation
  {
    id: 'edgnet',
    nodeType: 'edgnet',
    displayName: 'EDGNet',
    containerName: 'edgnet-api',
    specId: 'edgnet',
    port: 5012,
    category: 'segmentation',
    description: '엣지 기반 세그멘테이션',
    icon: '🔲',
    color: '#22c55e',
    gpuEnabled: true,
  },
  {
    id: 'line_detector',
    nodeType: 'linedetector',
    displayName: 'Line Detector',
    containerName: 'line-detector-api',
    specId: 'line-detector',
    port: 5016,
    category: 'segmentation',
    description: 'P&ID 라인 검출',
    icon: '📏',
    color: '#22c55e',
    gpuEnabled: true,
  },
  // Preprocessing
  {
    id: 'esrgan',
    nodeType: 'esrgan',
    displayName: 'ESRGAN',
    containerName: 'esrgan-api',
    specId: 'esrgan',
    port: 5010,
    category: 'preprocessing',
    description: '4x 이미지 업스케일링',
    icon: '🔍',
    color: '#f59e0b',
    gpuEnabled: true,
  },
  // Analysis
  {
    id: 'skinmodel',
    nodeType: 'skinmodel',
    displayName: 'SkinModel',
    containerName: 'skinmodel-api',
    specId: 'skinmodel',
    port: 5003,
    category: 'analysis',
    description: '공차 분석 & 제조성 예측',
    icon: '📊',
    color: '#8b5cf6',
    gpuEnabled: false,
  },
  {
    id: 'pid_analyzer',
    nodeType: 'pidanalyzer',
    displayName: 'PID Analyzer',
    containerName: 'pid-analyzer-api',
    specId: 'pid-analyzer',
    port: 5018,
    category: 'analysis',
    description: 'P&ID 연결 분석, BOM 생성',
    icon: '🔗',
    color: '#8b5cf6',
    gpuEnabled: false,
  },
  {
    id: 'design_checker',
    nodeType: 'designchecker',
    displayName: 'Design Checker',
    containerName: 'design-checker-api',
    specId: 'design-checker',
    port: 5019,
    category: 'analysis',
    description: 'P&ID 설계 규칙 검증',
    icon: '✅',
    color: '#8b5cf6',
    gpuEnabled: false,
  },
  // Knowledge
  {
    id: 'knowledge',
    nodeType: 'knowledge',
    displayName: 'Knowledge',
    containerName: 'knowledge-api',
    specId: 'knowledge',
    port: 5007,
    category: 'knowledge',
    description: 'Neo4j + GraphRAG',
    icon: '🧠',
    color: '#10b981',
    gpuEnabled: false,
  },
  // AI
  {
    id: 'vl',
    nodeType: 'vl',
    displayName: 'VL (Vision-Language)',
    containerName: 'vl-api',
    specId: 'vl',
    port: 5004,
    category: 'ai',
    description: 'Vision-Language 멀티모달',
    icon: '🤖',
    color: '#06b6d4',
    gpuEnabled: true,
  },
  // Blueprint AI BOM
  {
    id: 'blueprint_ai_bom',
    nodeType: 'blueprintaibom',
    displayName: 'Blueprint AI BOM',
    containerName: 'blueprint-ai-bom-backend',
    specId: 'blueprint-ai-bom',
    port: 5020,
    category: 'analysis',
    description: 'Human-in-the-Loop 도면 BOM 생성',
    icon: '📋',
    color: '#8b5cf6',
    gpuEnabled: true,
  },
  // PID Composer (Visualization)
  {
    id: 'pid_composer',
    nodeType: 'pidcomposer',
    displayName: 'PID Composer',
    containerName: 'pid-composer-api',
    specId: 'pid-composer',
    port: 5021,
    category: 'analysis',
    description: 'P&ID 레이어 합성, SVG 오버레이 생성',
    icon: '🎨',
    color: '#8b5cf6',
    gpuEnabled: false,
  },
];

// ============ 유틸리티 함수들 ============

/**
 * 노드 타입 → 컨테이너 이름 매핑
 * BlueprintFlowBuilder, NodePalette에서 사용
 */
export const NODE_TO_CONTAINER: Record<string, string> = Object.fromEntries(
  API_REGISTRY
    .filter(api => api.id !== 'gateway')
    .map(api => [api.nodeType, api.containerName])
);

/**
 * API ID → 컨테이너 이름 매핑
 * APIStatusMonitor에서 사용
 */
export const API_TO_CONTAINER: Record<string, string> = Object.fromEntries(
  API_REGISTRY.map(api => [api.id, api.containerName])
);

/**
 * API ID → 스펙 ID 매핑
 * APIStatusMonitor에서 사용
 */
export const API_TO_SPEC_ID: Record<string, string> = Object.fromEntries(
  API_REGISTRY.map(api => [api.id, api.specId])
);

/**
 * API ID로 정의 찾기
 */
export const getAPIById = (id: string): APIDefinition | undefined =>
  API_REGISTRY.find(api => api.id === id);

/**
 * 노드 타입으로 정의 찾기
 */
export const getAPIByNodeType = (nodeType: string): APIDefinition | undefined =>
  API_REGISTRY.find(api => api.nodeType === nodeType);

/**
 * 카테고리별 API 필터링
 */
export const getAPIsByCategory = (category: NodeCategory): APIDefinition[] =>
  API_REGISTRY.filter(api => api.category === category);

/**
 * GPU 지원 API 목록
 */
export const getGPUEnabledAPIs = (): APIDefinition[] =>
  API_REGISTRY.filter(api => api.gpuEnabled);

/**
 * 컨트롤 노드 (컨테이너 불필요)
 */
export const CONTROL_NODES = ['imageinput', 'textinput', 'if', 'loop', 'merge'];

/**
 * 컨테이너 필요 여부 확인
 */
export const requiresContainer = (nodeType: string): boolean =>
  !CONTROL_NODES.includes(nodeType);

export default {
  API_REGISTRY,
  NODE_TO_CONTAINER,
  API_TO_CONTAINER,
  API_TO_SPEC_ID,
  CONTROL_NODES,
  getAPIById,
  getAPIByNodeType,
  getAPIsByCategory,
  getGPUEnabledAPIs,
  requiresContainer,
};
