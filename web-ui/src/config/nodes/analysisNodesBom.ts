/**
 * BOM & Quote Nodes
 * BOM 매칭, 견적 생성, 치수 업데이트, PDF 내보내기 노드
 */

import type { NodeDefinition } from './types';

export const bomAnalysisNodes: Record<string, NodeDefinition> = {
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

  quotegenerator: {
    type: 'quotegenerator',
    label: 'Quote Generator',
    category: 'analysis',
    color: '#dc2626',
    icon: 'Calculator',
    description:
      'BOM 기반 자동 견적 생성. 재료비, 가공비, 마진율을 적용하여 견적서를 생성합니다.',
    profiles: {
      default: 'bearing',
      available: [
        {
          name: 'bearing',
          label: '베어링 견적',
          description: 'DSE Bearing 견적 최적화',
          params: {
            currency: 'KRW',
            material_markup: 15,
            labor_markup: 20,
            tax_rate: 10,
            include_tax: true,
            quantity_discount: true,
          },
        },
        {
          name: 'standard',
          label: '표준 견적',
          description: '일반 기계 부품 견적',
          params: {
            currency: 'KRW',
            material_markup: 10,
            labor_markup: 15,
            tax_rate: 10,
            include_tax: true,
            quantity_discount: false,
          },
        },
        {
          name: 'export',
          label: '수출용 견적',
          description: '해외 수출용 (USD)',
          params: {
            currency: 'USD',
            material_markup: 20,
            labor_markup: 25,
            tax_rate: 0,
            include_tax: false,
            quantity_discount: true,
          },
        },
      ],
    },
    inputs: [
      {
        name: 'bom',
        type: 'BOMEntry[]',
        description: '📋 BOM Matcher 출력 (부품 목록)',
      },
      {
        name: 'drawing_info',
        type: 'DrawingInfo',
        description: '📄 도면 메타 정보 (도면번호, 품명)',
        optional: true,
      },
      {
        name: 'pricing_table',
        type: 'PricingTable',
        description: '💰 커스텀 단가 테이블 (미입력 시 기본값)',
        optional: true,
      },
    ],
    outputs: [
      {
        name: 'quote',
        type: 'QuoteDocument',
        description: '📜 견적서 문서',
      },
      {
        name: 'line_items',
        type: 'QuoteLineItem[]',
        description: '📝 견적 항목 목록',
      },
      {
        name: 'summary',
        type: 'QuoteSummary',
        description: '📊 견적 요약 (총액, 세금 등)',
      },
      {
        name: 'total_cost',
        type: 'number',
        description: '💵 총 견적 금액',
      },
      {
        name: 'quote_number',
        type: 'string',
        description: '🔢 견적 번호',
      },
    ],
    parameters: [
      {
        name: 'currency',
        type: 'select',
        default: 'KRW',
        options: [
          { value: 'KRW', label: '원화 (₩)', description: '한국 원' },
          { value: 'USD', label: '달러 ($)', description: '미국 달러' },
          { value: 'EUR', label: '유로 (€)', description: '유럽 유로' },
          { value: 'JPY', label: '엔화 (¥)', description: '일본 엔' },
        ],
        description: '통화 단위',
      },
      {
        name: 'material_markup',
        type: 'number',
        default: 15,
        min: 0,
        max: 100,
        step: 1,
        description: '재료비 마진율 (%)',
      },
      {
        name: 'labor_markup',
        type: 'number',
        default: 20,
        min: 0,
        max: 100,
        step: 1,
        description: '가공비 마진율 (%)',
      },
      {
        name: 'tax_rate',
        type: 'number',
        default: 10,
        min: 0,
        max: 30,
        step: 0.5,
        description: '부가세율 (%)',
      },
      {
        name: 'include_tax',
        type: 'boolean',
        default: true,
        description: '부가세 포함 여부',
      },
      {
        name: 'quantity_discount',
        type: 'boolean',
        default: true,
        description: '수량 할인 적용 (10개↑ 5%, 50개↑ 10%)',
      },
      {
        name: 'validity_days',
        type: 'number',
        default: 30,
        min: 7,
        max: 90,
        step: 1,
        description: '견적 유효 기간 (일)',
      },
      {
        name: 'output_format',
        type: 'select',
        default: 'json',
        options: [
          { value: 'json', label: 'JSON', description: '구조화된 데이터' },
          { value: 'pdf', label: 'PDF', description: '견적서 PDF' },
          { value: 'excel', label: 'Excel', description: '견적서 Excel' },
        ],
        description: '출력 형식',
      },
    ],
    examples: [
      'BOM Matcher → Quote Generator → 견적서 JSON',
      '도면 분석 → BOM → 견적서 PDF 생성',
      '부품 10개, 재료비 500만원 → 견적 700만원 (마진 포함)',
    ],
    usageTips: [
      '⭐ BOM Matcher 출력을 입력으로 연결',
      '💰 material_markup/labor_markup으로 마진율 조정',
      '📊 수량 할인: 10개↑ 5%, 20개↑ 7%, 50개↑ 10%, 100개↑ 15%',
      '📄 PDF/Excel 출력으로 고객 제출용 견적서 생성',
      '🔧 pricing_table로 커스텀 단가 적용 가능',
    ],
    recommendedInputs: [
      {
        from: 'bommatcher',
        field: 'bom',
        reason: '⭐ BOM Matcher 출력 (부품 목록)',
      },
      {
        from: 'bommatcher',
        field: 'drawing_info',
        reason: '도면 메타 정보 (도면번호)',
      },
    ],
  },

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

  /**
   * PDF Export Node
   * P&ID 분석 결과를 PDF 리포트로 내보내기
   */
  pdfexport: {
    type: 'pdfexport',
    label: 'PDF Export',
    category: 'analysis',
    color: '#dc2626',
    icon: 'FileText',
    description:
      'P&ID 분석 결과를 전문적인 PDF 리포트로 내보냅니다. Equipment, Valve, Checklist, Deviation 목록과 요약 통계를 포함합니다.',
    inputs: [
      {
        name: 'session_data',
        type: 'SessionData',
        description: '📊 워크플로우 분석 결과 (Equipment, Valve, Checklist 등)',
      },
      {
        name: 'image',
        type: 'Image',
        description: '📄 원본 이미지 (도면 번호 참조용)',
        optional: true,
      },
    ],
    outputs: [
      {
        name: 'pdf_url',
        type: 'string',
        description: '📁 생성된 PDF 파일 다운로드 URL',
      },
      {
        name: 'filename',
        type: 'string',
        description: '📝 PDF 파일명',
      },
      {
        name: 'summary',
        type: 'ExportSummary',
        description: '📊 내보내기 요약 (포함된 항목 수, 검증 상태 등)',
      },
    ],
    parameters: [
      {
        name: 'export_type',
        type: 'select',
        default: 'all',
        options: [
          { value: 'all', label: '전체', description: 'Equipment + Valve + Checklist + Deviation 모두 포함' },
          { value: 'valve', label: 'Valve List', description: '밸브 신호 목록만' },
          { value: 'equipment', label: 'Equipment List', description: '장비 목록만' },
          { value: 'checklist', label: 'Checklist', description: '설계 체크리스트만' },
          { value: 'deviation', label: 'Deviation', description: '편차 목록만' },
        ],
        description: '내보내기 범위 선택',
      },
      {
        name: 'project_name',
        type: 'string',
        default: '',
        description: 'PDF 표지에 표시될 프로젝트명',
        placeholder: '예: BWMS Project Alpha',
      },
      {
        name: 'drawing_no',
        type: 'string',
        default: '',
        description: '도면 번호',
        placeholder: '예: PID-001-A',
      },
      {
        name: 'include_rejected',
        type: 'boolean',
        default: false,
        description: '거부된 항목도 포함할지 여부',
      },
    ],
    examples: [
      'PID Analyzer → PDF Export → 전체 분석 리포트',
      'Design Checker → PDF Export → 체크리스트 리포트',
      'Equipment/Valve 검출 → PDF Export → 목록 리포트',
    ],
    usageTips: [
      '⭐ PID Analyzer 또는 Blueprint AI BOM 노드 출력을 연결하세요',
      '📋 export_type="all"로 전체 리포트를 한 번에 생성 가능',
      '🏢 project_name과 drawing_no를 입력하면 표지에 표시됩니다',
      '❌ include_rejected=false로 거부된 항목을 제외하면 최종 리포트에 적합',
      '📊 Executive Summary 섹션에서 검증 진행률과 Pass/Fail 현황 확인',
    ],
    recommendedInputs: [
      {
        from: 'pidanalyzer',
        field: 'session_data',
        reason: '⭐ P&ID 분석 결과 (Equipment, Valve, Connection 등) 포함',
      },
      {
        from: 'designchecker',
        field: 'checklist',
        reason: '설계 검증 체크리스트 결과 포함',
      },
      {
        from: 'blueprint-ai-bom',
        field: 'session',
        reason: 'Human-in-the-Loop 검증 결과 포함',
      },
    ],
  },
};
