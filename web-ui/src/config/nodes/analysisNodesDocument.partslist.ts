/**
 * Document Analysis Nodes — Parts List
 * 도면 Parts List 파싱 노드
 */

import type { NodeDefinition } from './types';

export const partslistNode: NodeDefinition = {
  type: 'partslist',
  label: 'Parts List Parser',
  category: 'analysis',
  color: '#10b981',
  icon: 'Table',
  description:
    '도면 Parts List 테이블에서 부품번호, 품명, 재질, 수량 등 구조화된 정보를 자동 추출합니다. DSE Bearing 도면에 최적화되어 있습니다.',
  profiles: {
    default: 'bearing',
    available: [
      {
        name: 'bearing',
        label: '베어링 도면',
        description: 'DSE Bearing 도면 Parts List 최적화',
        params: {
          table_position: 'auto',
          ocr_engine: 'paddle',
          normalize_material: true,
          normalize_headers: true,
        },
      },
      {
        name: 'generic',
        label: '일반 도면',
        description: '범용 Parts List 파싱',
        params: {
          table_position: 'auto',
          ocr_engine: 'tesseract',
          normalize_material: true,
          normalize_headers: true,
        },
      },
      {
        name: 'korean',
        label: '한글 도면',
        description: '한글 헤더 Parts List',
        params: {
          table_position: 'auto',
          ocr_engine: 'paddle',
          normalize_material: true,
          normalize_headers: true,
        },
      },
    ],
  },
  inputs: [
    {
      name: 'image',
      type: 'Image',
      description: '📄 도면 이미지 (Parts List 포함)',
    },
    {
      name: 'tables',
      type: 'Table[]',
      description: '📊 Table Detector 결과 (재사용)',
      optional: true,
    },
  ],
  outputs: [
    {
      name: 'parts_list',
      type: 'PartsListData',
      description: '📋 파싱된 Parts List 데이터',
    },
    {
      name: 'parts',
      type: 'Part[]',
      description: '🔧 부품 목록 배열',
    },
    {
      name: 'parts_count',
      type: 'number',
      description: '📊 추출된 부품 개수',
    },
    {
      name: 'headers',
      type: 'string[]',
      description: '📝 정규화된 헤더 목록',
    },
    {
      name: 'confidence',
      type: 'number',
      description: '📊 추출 신뢰도 (0-1)',
    },
  ],
  parameters: [
    {
      name: 'table_position',
      type: 'select',
      default: 'auto',
      options: [
        { value: 'auto', label: '자동 검출', description: 'Parts List 위치 자동 탐색' },
        { value: 'top_left', label: '좌상단', description: '좌측 상단 영역' },
        { value: 'top_right', label: '우상단', description: '우측 상단 영역' },
        { value: 'bottom_left', label: '좌하단', description: '좌측 하단 영역' },
        { value: 'bottom_right', label: '우하단', description: '우측 하단 영역' },
      ],
      description: 'Parts List 위치 (auto=자동 검출)',
    },
    {
      name: 'ocr_engine',
      type: 'select',
      default: 'paddle',
      options: [
        { value: 'paddle', label: 'PaddleOCR', description: '한글 지원, 권장' },
        { value: 'tesseract', label: 'Tesseract', description: '영문 기본' },
        { value: 'easyocr', label: 'EasyOCR', description: '다국어 지원' },
      ],
      description: 'OCR 엔진 (paddle 권장 - 한글 지원)',
    },
    {
      name: 'normalize_material',
      type: 'boolean',
      default: true,
      description: '재질 코드 자동 정규화 (SF440 → SF440A)',
    },
    {
      name: 'normalize_headers',
      type: 'boolean',
      default: true,
      description: "헤더 자동 정규화 (MAT'L → material)",
    },
    {
      name: 'expected_headers',
      type: 'checkboxGroup',
      default: ['no', 'part_name', 'material', 'quantity'],
      options: [
        { value: 'no', label: '번호', description: '부품 번호' },
        { value: 'part_name', label: '품명', description: '부품 이름' },
        { value: 'material', label: '재질', description: '재질 코드' },
        { value: 'quantity', label: '수량', description: '부품 수량' },
        { value: 'remarks', label: '비고', description: '비고 사항' },
        { value: 'drawing_no', label: '도면번호', description: '관련 도면 번호' },
        { value: 'weight', label: '중량', description: '부품 무게' },
        { value: 'specification', label: '규격', description: '부품 규격' },
      ],
      description: '예상되는 헤더 필드',
    },
  ],
  examples: [
    '도면 이미지 → Parts List Parser → 부품 목록 추출',
    'Parts List Parser → BOM Matcher → 자동 BOM 매칭',
  ],
  usageTips: [
    '⭐ DSE Bearing 도면은 "bearing" 프로파일 사용 권장',
    '💡 normalize_material=true로 재질 코드 자동 통일 (SF440→SF440A)',
    '🔗 Title Block Parser와 함께 사용하여 완전한 도면 정보 추출',
    '📊 parts_count로 추출된 부품 개수 확인',
    '🔍 Table Detector 결과를 입력으로 받으면 처리 속도 향상',
  ],
  recommendedInputs: [
    {
      from: 'imageinput',
      field: 'image',
      reason: '⭐ 도면 이미지 입력 (Parts List 포함)',
    },
    {
      from: 'tabledetector',
      field: 'tables',
      reason: 'Table Detector 결과 재사용으로 처리 속도 향상',
    },
    {
      from: 'titleblock',
      field: 'title_block',
      reason: 'Title Block 정보와 함께 완전한 도면 데이터 구성',
    },
  ],
};
