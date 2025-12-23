/**
 * Input Nodes
 * 워크플로우 입력 노드 정의
 */

import type { NodeDefinition } from './types';

/**
 * 도면 타입별 추천 파이프라인 정의
 * ImageInput에서 도면 타입 선택 시 추천 노드를 표시
 *
 * 2025-12-22: 도면 타입 세분화
 * - dimension: 치수 중심 도면 (shaft, flange) - YOLO 불필요
 * - electrical_panel: 전기 제어판 심볼 (14클래스) - YOLO 필요
 * - pid: P&ID 배관계장도 (60클래스) - YOLO-PID 필요
 * - assembly: 조립도 (부품 + 치수) - YOLO + OCR 필요
 */
export const DRAWING_TYPE_RECOMMENDATIONS: Record<string, {
  description: string;
  nodes: string[];
  tips: string;
  warning?: string;
  pipeline?: string;  // 파이프라인 설명
}> = {
  // ========================================
  // 치수 도면 (YOLO 불필요)
  // ========================================
  dimension: {
    description: '치수와 공차 정보 추출 (심볼 검출 없음)',
    nodes: ['edocr2', 'skinmodel'],
    pipeline: 'eDOCr2 (치수 인식) → SkinModel (공차 분석)',
    tips: '치수선, GD&T 기호, 공차 정보를 인식합니다. shaft, 플랜지, 기어 등 기계 부품 상세도에 적합합니다.',
  },

  // ========================================
  // 전기 제어판 (YOLO 14클래스)
  // ========================================
  electrical_panel: {
    description: '전기 패널 심볼 검출 및 BOM 생성',
    nodes: ['yolo', 'blueprint-ai-bom'],
    pipeline: 'YOLO (심볼 검출) → AI BOM (부품 목록 생성)',
    tips: 'YOLO 14클래스: 차단기, DS ASSY, 접촉기, 퓨즈, 터미널, CT, PT, 릴레이 등. MCP Panel, 제어반 도면에 적합합니다.',
  },

  // ========================================
  // P&ID 배관계장도 (YOLO-PID 60클래스)
  // ========================================
  pid: {
    description: 'P&ID 심볼 및 배관 라인 분석',
    nodes: ['yolo-pid', 'line-detector', 'pid-analyzer', 'design-checker'],
    pipeline: 'YOLO-PID (심볼 60종) → Line Detector (라인 추적) → PID Analyzer (연결 분석)',
    tips: '밸브, 펌프, 계기류, 탱크 등 60종 P&ID 심볼을 검출하고 배관 연결 관계를 분석합니다.',
  },

  // ========================================
  // 조립도 (부품 + 치수)
  // ========================================
  assembly: {
    description: '부품 검출 + 치수 인식',
    nodes: ['yolo', 'edocr2', 'blueprint-ai-bom'],
    pipeline: 'YOLO (부품 검출) → eDOCr2 (치수/텍스트) → AI BOM (목록 생성)',
    tips: '부품 번호, 수량, 치수 정보가 함께 있는 조립도면에 적합합니다.',
  },

  // ========================================
  // 치수 + BOM (부품 목록 필요한 경우)
  // ========================================
  dimension_bom: {
    description: '치수 인식 + 수동 BOM 생성',
    nodes: ['edocr2', 'skinmodel', 'blueprint-ai-bom'],
    pipeline: 'eDOCr2 (치수) → SkinModel (공차) → AI BOM (수동 라벨링)',
    tips: '치수 도면이지만 BOM 목록이 필요한 경우. AI BOM에서 수작업으로 부품을 라벨링합니다.',
  },

  // ========================================
  // 자동 분류 (향후 개발)
  // ========================================
  auto: {
    description: 'VL 노드로 도면 타입 자동 분류 (향후 지원)',
    nodes: ['vl'],
    pipeline: 'VL (도면 분류) → 적절한 파이프라인 자동 선택',
    tips: 'Vision-Language 모델이 도면을 분석하여 타입을 자동 분류합니다.',
    warning: '⚠️ GPU 필요. 현재 개발 중인 기능입니다.',
  },

  // ========================================
  // 제한적 지원 (전용 모델 없음)
  // ========================================
  electrical_circuit: {
    description: '전기 회로도 (제한적 지원)',
    nodes: ['paddleocr', 'vl'],
    pipeline: 'OCR (텍스트 추출) + VL (회로 분석)',
    tips: '전기 회로 심볼 전용 모델은 아직 없습니다. 텍스트 추출 위주로 사용하세요.',
    warning: '⚠️ 전용 검출 모델 없음. Phase 2에서 지원 예정.',
  },
  architectural: {
    description: '건축 도면 (제한적 지원)',
    nodes: ['paddleocr', 'vl'],
    pipeline: 'OCR (텍스트/치수) + VL (도면 분석)',
    tips: '건축 심볼 전용 모델은 아직 없습니다. 텍스트 추출 위주로 사용하세요.',
    warning: '⚠️ 전용 검출 모델 없음. Phase 2에서 지원 예정.',
  },
};

export const inputNodes: Record<string, NodeDefinition> = {
  imageinput: {
    type: 'imageinput',
    label: 'Image Input',
    category: 'input',
    color: '#f97316',
    icon: 'Image',
    description: '워크플로우의 시작점. 업로드된 이미지를 다른 노드로 전달합니다. 도면 타입을 선택하면 최적의 노드를 추천합니다.',
    inputs: [],
    outputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 업로드된 도면 이미지',
      },
      {
        name: 'drawing_type',
        type: 'string',
        description: '📐 선택된 도면 타입',
      },
    ],
    parameters: [
      {
        name: 'drawing_type',
        type: 'select',
        default: 'dimension',
        options: [
          // ====== 주요 도면 타입 (권장) ======
          {
            value: 'dimension',
            label: '📏 치수 도면',
            icon: '📏',
            description: 'shaft, 플랜지, 기어 등 치수/공차 중심 도면. YOLO 없이 eDOCr2 → SkinModel 사용.',
          },
          {
            value: 'electrical_panel',
            label: '🔌 전기 제어판',
            icon: '🔌',
            description: 'MCP Panel, 제어반 등. YOLO 14클래스(차단기, DS ASSY 등) → AI BOM.',
          },
          {
            value: 'pid',
            label: '🔬 P&ID (배관계장도)',
            icon: '🔬',
            description: '밸브, 펌프, 계기류 등 60종 심볼. YOLO-PID → Line Detector → PID Analyzer.',
          },
          {
            value: 'assembly',
            label: '🔩 조립도',
            icon: '🔩',
            description: '부품 번호 + 치수 정보. YOLO → eDOCr2 → AI BOM.',
          },
          {
            value: 'dimension_bom',
            label: '📐 치수 + BOM',
            icon: '📐',
            description: '치수 도면이지만 BOM 목록이 필요한 경우. eDOCr2 → SkinModel → AI BOM (수동 라벨링).',
          },
          // ====== 제한적 지원 ======
          {
            value: 'electrical_circuit',
            label: '⚡ 전기 회로도',
            icon: '⚡',
            description: '전용 모델 없음. OCR 텍스트 추출 위주. (Phase 2 예정)',
            disabled: true,
          },
          {
            value: 'architectural',
            label: '🏗️ 건축 도면',
            icon: '🏗️',
            description: '전용 모델 없음. OCR 텍스트 추출 위주. (Phase 2 예정)',
            disabled: true,
          },
          // ====== 자동 분류 (향후) ======
          {
            value: 'auto',
            label: '🤖 자동 분류 (향후)',
            icon: '🤖',
            description: 'VL 노드로 도면 타입 자동 분류. GPU 필요. (개발 중)',
            disabled: true,
          },
        ],
        description: '📐 도면 타입 선택',
        tooltip: '도면 타입에 따라 최적의 분석 파이프라인을 추천합니다. 추천 노드 패널에서 클릭하여 노드를 추가하세요.',
      },
    ],
    examples: [
      '모든 워크플로우의 시작점으로 사용',
      'YOLO, eDOCr2 등 API 노드의 입력 소스',
      '이미지 업로드 후 자동으로 데이터 제공',
      '도면 타입 선택 → 추천 노드 확인 → 파이프라인 구성',
    ],
  },
  textinput: {
    type: 'textinput',
    label: 'Text Input',
    category: 'input',
    color: '#8b5cf6',
    icon: 'Type',
    description: '텍스트 입력 노드. 사용자가 직접 입력한 텍스트를 다른 노드로 전달합니다.',
    inputs: [],
    outputs: [
      {
        name: 'text',
        type: 'string',
        description: '📝 사용자가 입력한 텍스트',
      },
      {
        name: 'length',
        type: 'number',
        description: '📏 텍스트 길이 (문자 수)',
      },
    ],
    parameters: [
      {
        name: 'text',
        type: 'string',
        default: '',
        description: '입력할 텍스트 내용 (최대 10,000자)',
      },
    ],
    examples: [
      'Text-to-Image API의 프롬프트 입력',
      'LLM API의 질문/명령어 입력',
      '검색어, 키워드 등 텍스트 기반 API 입력',
    ],
    usageTips: [
      '💡 이미지가 아닌 텍스트 기반 API와 연결 시 사용',
      '💡 최대 10,000자까지 입력 가능',
      '💡 여러 줄 입력 지원 (줄바꿈 포함)',
    ],
  },
};
