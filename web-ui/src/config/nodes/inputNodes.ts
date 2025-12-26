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
        default: ['dimension_ocr', 'dimension_verification', 'gt_comparison'],
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
