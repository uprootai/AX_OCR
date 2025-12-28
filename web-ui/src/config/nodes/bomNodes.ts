/**
 * BOM Nodes
 * Bill of Materials 생성 노드 정의
 *
 * 2025-12-22: 역할 재정의 - 세션 생성 + 기능 선택 용도
 * 2025-12-26: SSOT 리팩토링 - features 정의를 config/features에서 import
 */

import type { NodeDefinition } from './types';
import { toBOMNodeOptions } from '../features';

export const bomNodes: Record<string, NodeDefinition> = {
  'blueprint-ai-bom': {
    type: 'blueprint-ai-bom',
    label: 'Blueprint AI BOM',
    category: 'bom',
    color: '#f59e0b', // 주황/앰버 - Analysis 카테고리 색상과 일치
    icon: '📋', // 이모지 아이콘 (DynamicNode 호환)
    description:
      'BOM 세션 생성 및 Human-in-the-Loop 검증 UI. 검출 결과를 검토하고 부품 명세서를 생성합니다. 도면 타입은 ImageInput에서 선택하세요.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 분석할 도면 이미지',
      },
      {
        name: 'detections',
        type: 'DetectionResult[]',
        description: '🎯 검출 결과 (YOLO 노드 연결 필요)',
      },
    ],
    outputs: [
      {
        name: 'bom_data',
        type: 'BOMData',
        description: '📊 생성된 BOM 데이터 (품목별 수량, 단가, 합계)',
      },
      {
        name: 'items',
        type: 'BOMItem[]',
        description: '📋 BOM 항목 목록',
      },
      {
        name: 'summary',
        type: 'BOMSummary',
        description: '💰 BOM 요약 (총 수량, 소계, 부가세, 합계)',
      },
      {
        name: 'approved_count',
        type: 'number',
        description: '✅ 승인된 검출 수',
      },
      {
        name: 'session_id',
        type: 'string',
        description: '🔑 생성된 세션 ID',
      },
      {
        name: 'verification_url',
        type: 'string',
        description: '🔗 검증 UI URL',
      },
    ],
    parameters: [
      {
        name: 'features',
        type: 'checkboxGroup',
        default: ['symbol_detection', 'title_block_ocr', 'vlm_auto_classification'],
        // SSOT에서 자동 생성된 옵션 사용
        options: toBOMNodeOptions(),
        description: '🛠️ 워크플로우에서 활성화할 기능 선택',
        tooltip:
          '선택한 기능만 워크플로우 페이지(localhost:3000)에 표시됩니다. 도면 타입에 따라 적절한 기능을 선택하세요.',
      },
    ],
    examples: [
      '기계 부품도: ImageInput → YOLO → AI BOM → 검증 UI',
      'P&ID 도면: ImageInput → YOLO (P&ID 모델) → AI BOM → 검증 UI',
    ],
    usageTips: [
      '⭐ 검출 노드 연결 필수 (YOLO)',
      '📐 도면 타입은 ImageInput에서 먼저 선택하세요',
      '💡 세션 생성 후 검증 UI(localhost:3000)에서 BOM 생성',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: '검출 결과를 BOM 검증 입력으로 사용합니다 (model_type으로 도면 타입 선택)',
      },
      {
        from: 'imageinput',
        field: 'image',
        reason: '원본 도면 이미지를 업로드합니다',
      },
    ],
  },
};
