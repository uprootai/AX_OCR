/**
 * Dimension Updater Node
 * 기존 BOM 세션에 eDOCr2 치수 비동기 추가
 */

import type { NodeDefinition } from '../types';

export const dimensionUpdaterNode: Record<string, NodeDefinition> = {
  dimension_updater: {
    type: 'dimension_updater',
    label: 'Dimension Updater',
    category: 'analysis',
    color: '#6366f1',
    icon: 'RefreshCw',
    description:
      '기존 BOM 세션에 eDOCr2 치수를 비동기 추가합니다. eager 실행 모드에서 aibom이 먼저 완료된 후 edocr2 결과를 세션에 import합니다.',
    inputs: [
      {
        name: 'session_id',
        type: 'string',
        description: 'AI BOM 세션 ID (aibom 노드 출력)',
      },
      {
        name: 'dimensions',
        type: 'Dimension[]',
        description: 'eDOCr2 치수 데이터',
        optional: true,
      },
    ],
    outputs: [
      {
        name: 'session_id',
        type: 'string',
        description: 'BOM 세션 ID (pass-through)',
      },
      {
        name: 'imported_count',
        type: 'number',
        description: 'import된 치수 개수',
      },
      {
        name: 'dimensions',
        type: 'Dimension[]',
        description: '치수 데이터 (pass-through)',
      },
    ],
    parameters: [],
    examples: ['aibom + edocr2 -> dimension_updater -> skinmodel'],
    usageTips: [
      'eager 실행 모드와 함께 사용하면 aibom이 먼저 완료되어 Human-in-the-Loop 시작 시간이 단축됩니다',
      'aibom과 edocr2 양쪽에서 엣지를 연결해야 합니다',
    ],
    recommendedInputs: [
      {
        from: 'blueprint-ai-bom',
        field: 'session_id',
        reason: 'BOM 세션 ID를 받아 치수를 추가할 대상 지정',
      },
      {
        from: 'edocr2',
        field: 'dimensions',
        reason: '추출된 치수 데이터를 세션에 import',
      },
    ],
  },
};
