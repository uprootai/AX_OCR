/**
 * Document Analysis Nodes
 * 도면 문서 분석 (Title Block, Parts List, Dimension) 노드
 */

import type { NodeDefinition } from './types';

export const documentNodes: Record<string, NodeDefinition> = {
  titleblock: {
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
  },

  partslist: {
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
        description: '헤더 자동 정규화 (MAT\'L → material)',
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
  },

  dimensionparser: {
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
  },
};
