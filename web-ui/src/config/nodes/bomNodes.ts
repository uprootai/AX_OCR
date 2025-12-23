/**
 * BOM Nodes
 * Bill of Materials 생성 노드 정의
 *
 * 역할 재정의 (2025-12-22):
 * - drawing_type은 ImageInput으로 이동됨
 * - AI BOM은 세션 생성 + 기능 선택 용도로 변경
 */

import type { NodeDefinition } from './types';

export const bomNodes: Record<string, NodeDefinition> = {
  'blueprint-ai-bom': {
    type: 'blueprint-ai-bom',
    label: 'Blueprint AI BOM',
    category: 'bom',
    color: '#f59e0b',  // 주황/앰버 - Analysis 카테고리 색상과 일치
    icon: '📋',  // 이모지 아이콘 (DynamicNode 호환)
    description: 'BOM 세션 생성 및 Human-in-the-Loop 검증 UI. 검출 결과를 검토하고 부품 명세서를 생성합니다. 도면 타입은 ImageInput에서 선택하세요.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 분석할 도면 이미지',
      },
      {
        name: 'detections',
        type: 'DetectionResult[]',
        description: '🎯 검출 결과 (YOLO 또는 YOLO-PID 노드 연결 필요)',
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
        type: 'multiselect',
        default: ['verification'],
        options: [
          {
            value: 'verification',
            label: '✅ Human-in-the-Loop 검증',
            icon: '✅',
            description: '검출 결과를 수동으로 확인하고 수정합니다. 기본 기능.',
          },
          {
            value: 'gt_comparison',
            label: '📊 GT 비교 분석',
            icon: '📊',
            description: 'Ground Truth와 비교하여 Precision, Recall, F1 Score를 표시합니다.',
          },
          {
            value: 'dimension_extraction',
            label: '📏 치수 추출',
            icon: '📏',
            description: 'OCR로 치수 텍스트를 추출합니다. (Phase 2 - 개발 중)',
            disabled: true,
          },
          {
            value: 'relation_analysis',
            label: '🔗 심볼-치수 관계 분석',
            icon: '🔗',
            description: '심볼과 치수 간의 관계를 분석합니다. (Phase 2 - 개발 중)',
            disabled: true,
          },
        ],
        description: '🛠️ 활성화할 기능',
        tooltip: '검증 UI에서 사용할 기능을 선택합니다. 기본적으로 Human-in-the-Loop 검증이 활성화됩니다.',
      },
    ],
    examples: [
      '기계 부품도: ImageInput → YOLO → AI BOM → 검증 UI',
      'P&ID 도면: ImageInput → YOLO-PID → AI BOM → 검증 UI',
    ],
    usageTips: [
      '⭐ 검출 노드 연결 필수 (YOLO 또는 YOLO-PID)',
      '📐 도면 타입은 ImageInput에서 먼저 선택하세요',
      '💡 세션 생성 후 검증 UI(localhost:3000)에서 BOM 생성',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: '기계 부품도 검출 결과를 BOM 검증 입력으로 사용합니다',
      },
      {
        from: 'yolo-pid',
        field: 'detections',
        reason: 'P&ID 도면 검출 결과를 BOM 검증 입력으로 사용합니다',
      },
      {
        from: 'imageinput',
        field: 'image',
        reason: '원본 도면 이미지를 업로드합니다',
      },
    ],
  },
};
