/**
 * BOM Matcher Node
 * Title Block, Parts List, Dimension 통합 BOM 생성
 */

import type { NodeDefinition } from '../types';

export const bomMatcherNode: Record<string, NodeDefinition> = {
  bommatcher: {
    type: 'bommatcher',
    label: 'BOM Matcher',
    category: 'analysis',
    color: '#059669',
    icon: 'Package',
    description:
      '도면 분석 결과(Title Block, Parts List, Dimension)를 통합하여 완전한 BOM(Bill of Materials)을 자동 생성합니다.',
    profiles: {
      default: 'bearing',
      available: [
        {
          name: 'bearing',
          label: '베어링 BOM',
          description: 'DSE Bearing 도면 BOM 최적화',
          params: {
            match_strategy: 'hybrid',
            confidence_threshold: 0.7,
            include_dimensions: true,
            include_tolerances: true,
            validate_material: true,
          },
        },
        {
          name: 'general',
          label: '일반 BOM',
          description: '범용 BOM 생성',
          params: {
            match_strategy: 'fuzzy',
            confidence_threshold: 0.6,
            include_dimensions: false,
            include_tolerances: false,
            validate_material: false,
          },
        },
        {
          name: 'strict',
          label: '정밀 BOM',
          description: '높은 신뢰도 매칭',
          params: {
            match_strategy: 'strict',
            confidence_threshold: 0.9,
            include_dimensions: true,
            include_tolerances: true,
            validate_material: true,
          },
        },
      ],
    },
    inputs: [
      {
        name: 'titleblock_data',
        type: 'TitleBlockData',
        description: '📋 Title Block Parser 출력 (도면번호, Rev, 품명)',
        optional: true,
      },
      {
        name: 'partslist_data',
        type: 'PartsListData',
        description: '🔧 Parts List Parser 출력 (부품 목록)',
        optional: true,
      },
      {
        name: 'dimension_data',
        type: 'BearingSpec',
        description: '📐 Dimension Parser 출력 (치수 정보)',
        optional: true,
      },
      {
        name: 'yolo_detections',
        type: 'Detection[]',
        description: '🎯 YOLO 검출 결과 (심볼, 영역)',
        optional: true,
      },
    ],
    outputs: [
      {
        name: 'bom',
        type: 'BOMEntry[]',
        description: '📋 통합 BOM 목록',
      },
      {
        name: 'drawing_info',
        type: 'DrawingInfo',
        description: '📄 도면 메타 정보',
      },
      {
        name: 'match_confidence',
        type: 'number',
        description: '📊 매칭 신뢰도 (0-1)',
      },
      {
        name: 'unmatched_items',
        type: 'string[]',
        description: '⚠️ 미매칭 항목 목록',
      },
      {
        name: 'warnings',
        type: 'string[]',
        description: '💬 처리 중 경고 메시지',
      },
    ],
    parameters: [
      {
        name: 'match_strategy',
        type: 'select',
        default: 'hybrid',
        options: [
          { value: 'strict', label: '정확 매칭', description: '정확한 필드 일치만 매칭' },
          { value: 'fuzzy', label: '유사 매칭', description: '유사도 기반 매칭' },
          { value: 'hybrid', label: '복합 매칭', description: '정확 매칭 우선, 실패 시 유사 매칭' },
        ],
        description: '매칭 전략',
      },
      {
        name: 'confidence_threshold',
        type: 'number',
        default: 0.7,
        min: 0,
        max: 1,
        step: 0.05,
        description: '매칭 최소 신뢰도',
      },
      {
        name: 'include_dimensions',
        type: 'boolean',
        default: true,
        description: '치수 정보 포함 (OD/ID/Length)',
      },
      {
        name: 'include_tolerances',
        type: 'boolean',
        default: true,
        description: '공차 정보 포함',
      },
      {
        name: 'validate_material',
        type: 'boolean',
        default: true,
        description: '재질 코드 검증 및 정규화',
      },
      {
        name: 'output_format',
        type: 'select',
        default: 'json',
        options: [
          { value: 'json', label: 'JSON', description: '구조화된 JSON 형식' },
          { value: 'excel', label: 'Excel', description: 'Excel 파일 다운로드' },
          { value: 'csv', label: 'CSV', description: 'CSV 파일 다운로드' },
        ],
        description: '출력 형식',
      },
    ],
    examples: [
      'Title Block + Parts List + Dimension → BOM Matcher → 통합 BOM',
      '도면 이미지 → 전체 파이프라인 → 완전한 BOM JSON',
    ],
    usageTips: [
      '⭐ Title Block → Parts List → Dimension → BOM Matcher 순서 연결',
      '💡 match_strategy=hybrid로 최적 매칭 (정확 우선, 유사 보완)',
      '📋 validate_material=true로 재질 코드 자동 정규화',
      '🔗 Excel Export와 연결하여 고객 제출용 BOM 생성',
      '📊 unmatched_items로 수동 확인 필요 항목 파악',
    ],
    recommendedInputs: [
      {
        from: 'titleblock',
        field: 'title_block',
        reason: '⭐ 도면 메타 정보 (도면번호, Rev)',
      },
      {
        from: 'partslist',
        field: 'parts_list',
        reason: '⭐ 부품 목록 (품번, 품명, 재질)',
      },
      {
        from: 'dimensionparser',
        field: 'bearing_specs',
        reason: '치수 정보 (OD/ID, 공차)',
      },
      {
        from: 'yolo',
        field: 'detections',
        reason: 'YOLO 검출 결과로 추가 매칭',
      },
    ],
  },
};
