/**
 * Document Analysis Nodes — Title Block
 * 도면 Title Block 파싱 노드
 */

import type { NodeDefinition } from './types';

export const titleblockNode: NodeDefinition = {
  type: 'titleblock',
  label: 'Title Block Parser',
  category: 'analysis',
  color: '#6366f1',
  icon: 'FileText',
  description:
    '도면 Title Block에서 도면번호, Rev, 품명, 재질 등 구조화된 정보를 자동 추출합니다. DSE Bearing 도면에 최적화되어 있습니다.',
  profiles: {
    default: 'bearing',
    available: [
      {
        name: 'bearing',
        label: '베어링 도면',
        description: 'DSE Bearing 도면 최적화 (DOOSAN 템플릿)',
        params: {
          detection_method: 'auto',
          title_block_position: 'bottom_right',
          ocr_engine: 'paddle',
          company_template: 'doosan',
        },
      },
      {
        name: 'generic',
        label: '일반 도면',
        description: '범용 Title Block 파싱',
        params: {
          detection_method: 'table_detector',
          title_block_position: 'auto',
          ocr_engine: 'tesseract',
          company_template: 'generic',
        },
      },
      {
        name: 'fast',
        label: '빠른 추출',
        description: '도면번호/Rev만 빠르게 추출',
        params: {
          detection_method: 'template',
          title_block_position: 'bottom_right',
          ocr_engine: 'tesseract',
          company_template: 'auto',
        },
      },
    ],
  },
  inputs: [
    {
      name: 'image',
      type: 'Image',
      description: '📄 도면 이미지 (Title Block 포함)',
    },
    {
      name: 'tables',
      type: 'Table[]',
      description: '📊 Table Detector 결과 (Title Block 영역 재사용)',
      optional: true,
    },
  ],
  outputs: [
    {
      name: 'title_block',
      type: 'TitleBlockData',
      description: '📋 파싱된 Title Block 필드 딕셔너리',
    },
    {
      name: 'drawing_number',
      type: 'string',
      description: '🔢 도면번호 (예: TD0062018)',
    },
    {
      name: 'revision',
      type: 'string',
      description: '🔄 리비전 (예: A, B, C)',
    },
    {
      name: 'part_name',
      type: 'string',
      description: '🏷️ 품명 (예: BEARING CASING ASSY)',
    },
    {
      name: 'material',
      type: 'string',
      description: '🔩 재질 (예: SF440A, SS400)',
    },
    {
      name: 'weight',
      type: 'string',
      description: '⚖️ 중량 (예: 882 kg)',
    },
    {
      name: 'scale',
      type: 'string',
      description: '📐 축척 (예: 1:1, 1:2)',
    },
    {
      name: 'confidence',
      type: 'number',
      description: '📊 파싱 신뢰도 (0-1)',
    },
    {
      name: 'raw_text',
      type: 'string',
      description: '📝 OCR 원본 텍스트',
    },
  ],
  parameters: [
    {
      name: 'detection_method',
      type: 'select',
      default: 'auto',
      options: [
        { value: 'auto', label: '자동 선택', description: '상황에 맞게 자동 선택' },
        { value: 'table_detector', label: 'Table Detector', description: '테이블 구조 검출 후 파싱' },
        { value: 'template', label: '템플릿 기반', description: '좌표 기반 영역 추출' },
      ],
      description: 'Title Block 검출 방식',
    },
    {
      name: 'title_block_position',
      type: 'select',
      default: 'bottom_right',
      options: [
        { value: 'bottom_right', label: '우하단', description: '대부분의 도면 (기본값)' },
        { value: 'bottom_left', label: '좌하단', description: '일부 도면' },
        { value: 'top_right', label: '우상단', description: '특수 도면' },
        { value: 'auto', label: '자동 검출', description: '위치 자동 탐색' },
      ],
      description: 'Title Block 위치 (대부분 우하단)',
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
      name: 'company_template',
      type: 'select',
      default: 'auto',
      options: [
        { value: 'auto', label: '자동', description: '자동 템플릿 선택' },
        { value: 'doosan', label: 'DOOSAN', description: 'DSE Bearing 도면' },
        { value: 'generic', label: '범용', description: '일반 Title Block' },
      ],
      description: '회사별 Title Block 템플릿',
    },
    {
      name: 'extract_fields',
      type: 'checkboxGroup',
      default: ['drawing_number', 'revision', 'part_name', 'material'],
      options: [
        { value: 'drawing_number', label: '도면번호', description: '도면 고유 번호' },
        { value: 'revision', label: '리비전', description: '도면 버전' },
        { value: 'part_name', label: '품명', description: '부품 이름' },
        { value: 'material', label: '재질', description: '재질 코드' },
        { value: 'weight', label: '중량', description: '부품 무게' },
        { value: 'scale', label: '축척', description: '도면 축척' },
        { value: 'date', label: '작성일', description: '도면 작성 날짜' },
        { value: 'author', label: '작성자', description: '도면 작성자' },
      ],
      description: '추출할 필드 선택',
    },
  ],
  examples: [
    '도면 이미지 → Title Block Parser → 도면번호, 품명, 재질 추출',
    '베어링 도면 → Title Block Parser → BOM Matcher 연결',
  ],
  usageTips: [
    '⭐ DSE Bearing 도면은 "bearing" 프로파일 사용 권장',
    '💡 DOOSAN 도면은 company_template=doosan으로 정확도 향상',
    '🔗 BOM Matcher 노드와 연결하여 자동 BOM 매칭',
    '📊 confidence 값이 0.7 이하면 수동 확인 권장',
    '🔍 raw_text 출력으로 OCR 결과 직접 확인 가능',
  ],
  recommendedInputs: [
    {
      from: 'imageinput',
      field: 'image',
      reason: '⭐ 도면 이미지 입력 (Title Block 포함)',
    },
    {
      from: 'tabledetector',
      field: 'tables',
      reason: 'Table Detector 결과로 Title Block 영역 재사용 가능',
    },
  ],
};
