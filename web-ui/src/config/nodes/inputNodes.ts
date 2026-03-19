/**
 * Input Nodes
 * 워크플로우 입력 노드 정의
 *
 * 2025-12-24: 기능 기반 재설계 (v2)
 * 2025-12-26: SSOT 리팩토링 - features 정의를 config/features에서 import
 */

import type { NodeDefinition } from './types';
import {
  FEATURE_DEFINITIONS,
  toBOMFeatures,
  toNodeRecommendations,
  toCheckboxGroupOptions,
  getRecommendedNodes as getRecommendedNodesFromSST,
} from '../features';

// ============================================================
// 레거시 호환 exports (SSOT에서 생성)
// ============================================================

/**
 * 기능 목록 (Blueprint AI BOM이 제공하는 모든 기능)
 * @deprecated FEATURE_DEFINITIONS 직접 사용 권장
 */
export const BOM_FEATURES = toBOMFeatures();

export type BOMFeature = keyof typeof FEATURE_DEFINITIONS;

/**
 * features 기반 추천 노드 매핑
 * @deprecated toNodeRecommendations() 직접 사용 권장
 */
export const FEATURE_NODE_RECOMMENDATIONS = toNodeRecommendations();

/**
 * 추천 노드 목록 계산 (features 기반)
 */
export function getRecommendedNodes(features: string[]): string[] {
  return getRecommendedNodesFromSST(features);
}

// ============================================================
// Input Nodes 정의
// ============================================================

export const inputNodes: Record<string, NodeDefinition> = {
  imageinput: {
    type: 'imageinput',
    label: 'Image Input',
    category: 'input',
    color: '#f97316',
    icon: 'Image',
    description:
      '워크플로우의 시작점. 업로드된 이미지를 다른 노드로 전달합니다. 활성화할 기능을 선택하면 필요한 노드를 추천합니다.',
    inputs: [],
    outputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 업로드된 도면 이미지',
      },
      {
        name: 'features',
        type: 'string[]',
        description: '🔧 활성화된 기능 목록',
      },
    ],
    parameters: [
      {
        name: 'features',
        type: 'checkboxGroup',
        // Primary features만 선택하면 impliedBy로 하위 기능 자동 활성화
        // symbol_detection → symbol_verification, gt_comparison
        // dimension_ocr → dimension_verification
        default: ['symbol_detection', 'dimension_ocr'],
        // SSOT에서 자동 생성된 옵션 사용
        options: toCheckboxGroupOptions(),
        description: '🔧 활성화 기능',
        tooltip:
          '세션 UI에 표시될 기능들을 선택합니다. 선택한 기능에 맞는 노드가 추천됩니다.',
      },
    ],
    examples: [
      '모든 워크플로우의 시작점으로 사용',
      'YOLO, eDOCr2 등 API 노드의 입력 소스',
      '이미지 업로드 후 자동으로 데이터 제공',
      '기능 선택 → 추천 노드 확인 → 파이프라인 구성',
    ],
  },
  reference_drawing: {
    type: 'reference_drawing',
    label: 'Reference Drawing',
    category: 'input',
    color: '#a855f7',
    icon: 'BookOpen',
    description:
      '참조 도면 유형과 참조 세트를 설정합니다. 도면 유형(drawing_type)을 선택하고, 심볼 검증에 사용할 참조 이미지 세트를 지정합니다. 커스텀 참조 세트를 ZIP으로 업로드할 수도 있습니다.',
    inputs: [],
    outputs: [
      {
        name: 'drawing_type',
        type: 'string',
        description: '📐 도면 유형 (electrical_panel, pid, dimension, assembly 등)',
      },
      {
        name: 'reference_set_id',
        type: 'string',
        description: '📚 참조 세트 ID (기본 제공 또는 커스텀)',
      },
    ],
    parameters: [
      {
        name: 'drawing_type',
        type: 'select',
        default: 'auto',
        options: [
          { value: 'auto', label: '자동 감지 (VLM)', description: 'VLM이 도면 유형을 자동 분류' },
          { value: 'electrical_panel', label: '전기 제어판', description: 'MCP Panel, 배전반 등 전력 설비 도면' },
          { value: 'pid', label: 'P&ID (배관계장도)', description: '배관 계장도, 공정 흐름도' },
          { value: 'dimension', label: '치수 도면', description: '기계 부품 치수 도면 (OD/ID/W 분석)' },
          { value: 'assembly', label: '조립도', description: '부품 조립 구성도' },
          { value: 'dimension_bom', label: '치수 + BOM', description: '치수 도면과 BOM이 포함된 도면' },
        ],
        description: '도면 유형 — 분석 파이프라인과 UI 기능을 결정합니다',
        tooltip: '세션 생성 시 drawing_type으로 전달됩니다. "auto"를 선택하면 VLM이 자동으로 분류합니다.',
      },
      {
        name: 'reference_set',
        type: 'select',
        default: 'electrical',
        options: [
          { value: 'electrical', label: '전기 도면 심볼', description: '전기 회로도, 배선도 심볼 (기본 제공)' },
          { value: 'pid', label: 'P&ID 심볼', description: '배관 계장도 심볼 (기본 제공)' },
          { value: 'sld', label: 'SLD 심볼', description: '단선 결선도 심볼 (기본 제공)' },
          { value: 'mechanical', label: '기계 도면 심볼', description: '기계 부품도 심볼 (기본 제공)' },
        ],
        description: '참조 이미지 세트 — 심볼 검증 시 비교 대상으로 표시됩니다',
        tooltip: '커스텀 세트는 /reference-sets API로 ZIP 업로드 후 사용 가능합니다.',
      },
    ],
    examples: [
      '파나시아 MCP Panel → drawing_type: electrical_panel, reference_set: electrical',
      'DSE Bearing → drawing_type: dimension, reference_set: mechanical',
      'P&ID 도면 → drawing_type: pid, reference_set: pid',
    ],
    usageTips: [
      '📐 도면 유형은 세션에서 활성화할 기능과 UI 섹션을 결정합니다',
      '📚 참조 세트는 심볼 검증 시 오른쪽 패널에 표시되는 참조 이미지입니다',
      '📦 커스텀 참조 세트: ZIP 파일 업로드 (파일명 = 클래스명)',
      '🔗 Image Input과 함께 사용하여 도면 유형을 명시적으로 설정하세요',
    ],
  },
  textinput: {
    type: 'textinput',
    label: 'Text Input',
    category: 'input',
    color: '#8b5cf6',
    icon: 'Type',
    description:
      '텍스트 입력 노드. 사용자가 직접 입력한 텍스트를 다른 노드로 전달합니다.',
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
