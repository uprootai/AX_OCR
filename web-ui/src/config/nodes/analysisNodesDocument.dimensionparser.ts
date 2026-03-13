/**
 * Document Analysis Nodes — Dimension Parser
 * 베어링 도면 치수 파싱 노드
 */

import type { NodeDefinition } from './types';

export const dimensionparserNode: NodeDefinition = {
  type: 'dimensionparser',
  label: 'Dimension Parser',
  category: 'analysis',
  color: '#f59e0b',
  icon: 'Ruler',
  description:
    '베어링 도면 치수를 구조화된 형태로 파싱합니다. OD/ID, 공차, GD&T 기호를 자동 인식합니다.',
  profiles: {
    default: 'bearing',
    available: [
      {
        name: 'bearing',
        label: '베어링 치수',
        description: 'DSE Bearing 도면 치수 최적화',
        params: {
          dimension_type: 'bearing',
          parse_tolerance: true,
          parse_gdt: true,
          extract_od_id: true,
        },
      },
      {
        name: 'general',
        label: '일반 치수',
        description: '범용 치수 파싱',
        params: {
          dimension_type: 'general',
          parse_tolerance: true,
          parse_gdt: true,
          extract_od_id: false,
        },
      },
      {
        name: 'precision',
        label: '정밀 치수',
        description: '정밀 공차 중심 파싱',
        params: {
          dimension_type: 'general',
          parse_tolerance: true,
          parse_gdt: true,
          extract_od_id: false,
        },
      },
    ],
  },
  inputs: [
    {
      name: 'text_results',
      type: 'TextResult[]',
      description: '📝 eDOCr2 OCR 결과 (텍스트 + bbox)',
      optional: true,
    },
    {
      name: 'dimensions',
      type: 'string[]',
      description: '📐 치수 텍스트 목록 (직접 입력)',
      optional: true,
    },
    {
      name: 'image',
      type: 'Image',
      description: '📄 도면 이미지 (패스스루)',
      optional: true,
    },
  ],
  outputs: [
    {
      name: 'parsed_dimensions',
      type: 'BearingDimension[]',
      description: '📊 구조화된 베어링 치수 목록',
    },
    {
      name: 'bearing_specs',
      type: 'BearingSpec',
      description: '⚙️ 종합 베어링 사양 (OD, ID, Length)',
    },
    {
      name: 'tolerances',
      type: 'Tolerance[]',
      description: '📏 추출된 공차 목록',
    },
    {
      name: 'gdt_symbols',
      type: 'GDTSymbol[]',
      description: '🔣 추출된 GD&T 기호',
    },
    {
      name: 'dimensions_count',
      type: 'number',
      description: '📊 파싱된 치수 개수',
    },
    {
      name: 'confidence',
      type: 'number',
      description: '📊 파싱 신뢰도 (0-1)',
    },
  ],
  parameters: [
    {
      name: 'dimension_type',
      type: 'select',
      default: 'bearing',
      options: [
        { value: 'bearing', label: '베어링', description: 'OD/ID 자동 분류' },
        { value: 'general', label: '일반', description: '범용 치수' },
        { value: 'shaft', label: '축', description: '축 관련 치수' },
        { value: 'housing', label: '하우징', description: '하우징 치수' },
      ],
      description: '치수 유형 (bearing=OD/ID 자동 분류)',
    },
    {
      name: 'parse_tolerance',
      type: 'boolean',
      default: true,
      description: '공차 파싱 (H7, ±0.1 등)',
    },
    {
      name: 'parse_gdt',
      type: 'boolean',
      default: true,
      description: 'GD&T 기호 파싱 (⌀, ⊥, // 등)',
    },
    {
      name: 'extract_od_id',
      type: 'boolean',
      default: true,
      description: 'OD/ID 자동 분류 (베어링 전용)',
    },
    {
      name: 'unit',
      type: 'select',
      default: 'mm',
      options: [
        { value: 'mm', label: 'mm', description: '밀리미터' },
        { value: 'inch', label: 'inch', description: '인치' },
        { value: 'auto', label: '자동', description: '자동 감지' },
      ],
      description: '치수 단위',
    },
  ],
  examples: [
    'eDOCr2 → Dimension Parser → 구조화된 베어링 치수',
    'OD670×ID440 → {outer_diameter: 670, inner_diameter: 440}',
    'Ø25H7 → {diameter: 25, tolerance: "H7"}',
  ],
  usageTips: [
    '⭐ eDOCr2 출력을 입력으로 연결하면 자동으로 치수 파싱',
    '💡 extract_od_id=true로 외경/내경 자동 분류',
    '📐 GD&T 기호 (⌀, ⊥, //) 자동 인식',
    '🔗 SkinModel과 연결하여 공차 분석 가능',
    '📊 bearing_specs로 종합 베어링 사양 확인',
  ],
  recommendedInputs: [
    {
      from: 'edocr2',
      field: 'text_results',
      reason: '⭐ eDOCr2 치수 인식 결과를 구조화',
    },
    {
      from: 'paddleocr',
      field: 'text_results',
      reason: 'PaddleOCR 결과도 활용 가능',
    },
  ],
};
