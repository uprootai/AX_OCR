/**
 * BOM Nodes
 * Bill of Materials 생성 노드 정의
 */

import type { NodeDefinition } from './types';

export const bomNodes: Record<string, NodeDefinition> = {
  'blueprint-ai-bom': {
    type: 'blueprint-ai-bom',
    label: 'Blueprint AI BOM',
    category: 'bom',
    color: '#8b5cf6',
    icon: 'FileSpreadsheet',
    description: 'AI 기반 도면 분석 및 BOM 생성. Human-in-the-Loop 검증 UI를 통해 검출 결과를 확인하고 부품 명세서를 생성합니다.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 분석할 도면 이미지',
      },
      {
        name: 'detections',
        type: 'DetectionResult[]',
        description: '🎯 YOLO 노드의 검출 결과 (필수 - YOLO 노드 연결 필요)',
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
        name: 'export_url',
        type: 'string',
        description: '📥 BOM 다운로드 URL',
      },
    ],
    parameters: [],
    examples: [
      '도면 이미지 → YOLO 검출 → Blueprint AI BOM → 검증 UI',
    ],
    usageTips: [
      '⭐ YOLO 노드 연결 필수',
      '💡 세션 생성 후 검증 UI(localhost:3000)에서 BOM 생성',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: 'YOLO 검출 결과를 BOM 검증 입력으로 사용합니다',
      },
      {
        from: 'imageinput',
        field: 'image',
        reason: '원본 도면 이미지를 업로드합니다',
      },
    ],
  },
};
