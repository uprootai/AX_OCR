/**
 * PID Analysis Nodes
 * P&ID 분석, 설계 검증, 레이어 합성 노드
 */

import type { NodeDefinition } from './types';

export const pidNodes: Record<string, NodeDefinition> = {
  pidanalyzer: {
    type: 'pidanalyzer',
    label: 'P&ID Analyzer',
    category: 'analysis',
    color: '#7c3aed',
    icon: 'Network',
    description: 'P&ID 심볼과 라인을 분석하여 연결 관계, BOM, 장비 목록을 생성합니다.',
    profiles: {
      default: 'general',
      available: [
        {
          name: 'general',
          label: '일반 분석',
          description: '기본 연결성 분석 (모든 출력 포함)',
          params: { generate_bom: true, generate_valve_list: true, generate_equipment_list: true, enable_ocr: true, visualize: true },
        },
        {
          name: 'connectivity_only',
          label: '연결성만',
          description: '연결 관계만 분석 (BOM 생성 안함)',
          params: { generate_bom: false, generate_valve_list: false, generate_equipment_list: false, enable_ocr: false, visualize: false },
        },
        {
          name: 'bom_export',
          label: 'BOM 추출',
          description: 'BOM 및 장비 리스트 추출용',
          params: { generate_bom: true, generate_valve_list: true, generate_equipment_list: true, enable_ocr: true, visualize: false },
        },
        {
          name: 'bwms',
          label: 'BWMS 분석',
          description: 'Ballast Water Management System 전용',
          params: { generate_bom: true, generate_valve_list: true, generate_equipment_list: true, enable_ocr: true, visualize: true },
        },
      ],
    },
    inputs: [
      {
        name: 'symbols',
        type: 'PIDSymbol[]',
        description: '🔧 YOLO가 검출한 심볼 목록 (model_type=pid_class_aware)',
      },
      {
        name: 'lines',
        type: 'Line[]',
        description: '📏 Line Detector가 검출한 라인 목록',
      },
    ],
    outputs: [
      {
        name: 'connections',
        type: 'Connection[]',
        description: '🔗 심볼 간 연결 관계 그래프',
      },
      {
        name: 'bom',
        type: 'BOMEntry[]',
        description: '📋 BOM (Bill of Materials) 부품 목록',
      },
      {
        name: 'valve_signal_list',
        type: 'ValveSignal[]',
        description: '🎛️ 밸브 시그널 리스트',
      },
      {
        name: 'equipment_list',
        type: 'Equipment[]',
        description: '⚙️ 장비 목록',
      },
      {
        name: 'detected_equipment_tags',
        type: 'EquipmentTag[]',
        description: '🏭 산업별 장비 태그 (프로파일 기반 검출)',
      },
    ],
    parameters: [
      {
        name: 'analysis_type',
        type: 'select',
        default: 'full',
        options: ['connectivity', 'bom', 'valve_signals', 'equipment', 'full'],
        description: '분석 유형 (full: 전체 분석)',
      },
      {
        name: 'connection_threshold',
        type: 'number',
        default: 50,
        min: 20,
        max: 200,
        step: 10,
        description: '심볼-라인 연결 거리 임계값 (픽셀)',
      },
      {
        name: 'enable_ocr',
        type: 'boolean',
        default: true,
        description: '🔤 OCR 기반 계기 태그 검출 (FC, TI, LC, PC 등)',
      },
      {
        name: 'generate_bom',
        type: 'boolean',
        default: true,
        description: '📋 BOM (Bill of Materials) 생성',
      },
      {
        name: 'generate_valve_list',
        type: 'boolean',
        default: true,
        description: '🎛️ 밸브 시그널 리스트 생성',
      },
      {
        name: 'generate_equipment_list',
        type: 'boolean',
        default: true,
        description: '⚙️ 장비 리스트 생성',
      },
      {
        name: 'detect_equipment_tags',
        type: 'boolean',
        default: false,
        description: '🏭 OCR 기반 산업별 장비 태그 인식 (프로파일 선택 필요)',
      },
      {
        name: 'equipment_profile',
        type: 'select',
        default: 'bwms',
        options: ['bwms', 'hvac', 'process'],
        description:
          '장비 프로파일: bwms(선박 평형수 처리), hvac(공조), process(일반 공정)',
      },
      {
        name: 'export_equipment_excel',
        type: 'boolean',
        default: false,
        description: '📑 검출된 장비 목록을 Excel로 내보내기',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: true,
        description: '📊 연결 그래프 시각화',
      },
    ],
    examples: [
      'YOLO (P&ID 모델) + Line Detector → PID Analyzer → BOM 생성',
      'PID Analyzer → Design Checker → 설계 오류 검출',
    ],
    usageTips: [
      '⭐ YOLO (P&ID 모델)와 Line Detector의 결과를 함께 입력해야 정확한 분석이 가능합니다',
      '💡 BOM 생성으로 도면에서 부품 목록을 자동 추출합니다',
      '💡 Design Checker와 연결하여 설계 오류를 자동 검출할 수 있습니다',
      '🏭 detect_equipment_tags로 산업별 장비 태그를 인식합니다 (BWMS, HVAC, 공정 프로파일 지원)',
      '🎛️ Valve Signal 추출은 별도 API (/api/v1/valve-signal/extract)를 사용하세요',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: '⭐ YOLO (model_type=pid_class_aware)로 검출된 심볼의 연결 관계를 분석합니다',
      },
      {
        from: 'linedetector',
        field: 'lines',
        reason: '⭐ 라인 정보로 심볼 간 연결성을 파악합니다',
      },
    ],
  },
  designchecker: {
    type: 'designchecker',
    label: 'Design Checker',
    category: 'analysis',
    color: '#ef4444',
    icon: 'ShieldCheck',
    description: 'P&ID 설계 오류 검출 및 규정 검증. ISO 10628, ISA 5.1 등 표준 준수 여부 확인.',
    inputs: [
      {
        name: 'symbols',
        type: 'PIDSymbol[]',
        description: '🔧 P&ID 심볼 목록',
      },
      {
        name: 'connections',
        type: 'Connection[]',
        description: '🔗 심볼 연결 관계',
      },
      {
        name: 'texts',
        type: 'Text[]',
        description: '📝 OCR 텍스트 (BWMS 규칙 검사용)',
        optional: true,
      },
    ],
    outputs: [
      {
        name: 'violations',
        type: 'Violation[]',
        description: '⚠️ 검출된 규칙 위반 목록',
      },
      {
        name: 'summary',
        type: 'CheckSummary',
        description: '📊 검사 결과 요약 (오류/경고/정보 개수)',
      },
      {
        name: 'compliance_score',
        type: 'number',
        description: '✅ 규정 준수율 (0-100%)',
      },
    ],
    parameters: [
      {
        name: 'categories',
        type: 'select',
        default: 'all',
        options: ['all', 'connectivity', 'symbol', 'labeling', 'specification', 'standard', 'safety', 'bwms'],
        description: '검사할 규칙 카테고리 (bwms: TECHCROSS 전용 규칙)',
      },
      {
        name: 'severity_threshold',
        type: 'select',
        default: 'info',
        options: ['error', 'warning', 'info'],
        description: '보고할 최소 심각도',
      },
      {
        name: 'include_bwms',
        type: 'boolean',
        default: true,
        description: '🚢 BWMS 규칙 포함 (TECHCROSS 전용 7개 규칙: FMU-ECU 순서, GDS 위치 등)',
      },
    ],
    examples: [
      'PID Analyzer → Design Checker → 설계 오류 리포트',
      'YOLO (P&ID 모델) → Design Checker → 심볼 규격 검증',
    ],
    usageTips: [
      '⭐ 27개 설계 규칙을 자동 검사합니다 (연결, 심볼, 라벨링, 사양, 표준, 안전, BWMS)',
      '💡 ISO 10628, ISA 5.1, ASME, IEC 61511 등 주요 표준 지원',
      '🚢 BWMS 규칙: FMU-ECU 순서, GDS 위치, ECS 밸브 위치 등 TECHCROSS 전용 7개 규칙',
      '💡 compliance_score로 전체 설계 품질을 수치화합니다',
      '💡 severity_threshold를 error로 설정하면 중요한 오류만 표시됩니다',
      '⚠️ 압력용기 안전밸브 누락, 태그번호 중복 등 중요 오류를 검출합니다',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: 'YOLO (model_type=pid_class_aware)로 검출된 심볼의 규격 준수 여부를 검사합니다',
      },
      {
        from: 'pidanalyzer',
        field: 'connections',
        reason: '⭐ 심볼 연결 관계를 분석하여 설계 오류를 검출합니다',
      },
      {
        from: 'paddleocr',
        field: 'texts',
        reason: '🚢 BWMS 규칙 검사에 필요한 텍스트 정보를 제공합니다 (Mixing Pump 용량 검증 등)',
      },
    ],
  },
  pidcomposer: {
    type: 'pidcomposer',
    label: 'PID Composer',
    category: 'analysis',
    color: '#8b5cf6',
    icon: 'Layers',
    description:
      'P&ID 도면에 심볼, 라인, 텍스트, 영역 레이어를 합성하여 시각화합니다. 서버 사이드 이미지 렌더링 및 클라이언트용 SVG 오버레이 생성을 지원합니다.',
    profiles: {
      default: 'general',
      available: [
        {
          name: 'general',
          label: '일반',
          description: '기본 SVG 오버레이',
          params: { show_symbols: true, show_lines: true, show_texts: true, stroke_width: 2, opacity: 0.8 },
        },
        {
          name: 'review',
          label: '도면 검토',
          description: '도면 검토용 (모든 요소 강조)',
          params: { show_symbols: true, show_lines: true, show_texts: true, stroke_width: 3, opacity: 0.9 },
        },
        {
          name: 'symbols_only',
          label: '심볼만',
          description: '심볼만 표시',
          params: { show_symbols: true, show_lines: false, show_texts: false, stroke_width: 2, opacity: 0.8 },
        },
        {
          name: 'print',
          label: '인쇄용',
          description: '인쇄 최적화 (고대비)',
          params: { show_symbols: true, show_lines: true, show_texts: true, stroke_width: 1, opacity: 1.0 },
        },
      ],
    },
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 원본 P&ID 이미지',
      },
      {
        name: 'symbols',
        type: 'Symbol[]',
        description: '🔧 심볼 레이어 데이터 (YOLO 검출 결과)',
        optional: true,
      },
      {
        name: 'lines',
        type: 'Line[]',
        description: '📏 라인 레이어 데이터 (Line Detector 결과)',
        optional: true,
      },
      {
        name: 'texts',
        type: 'Text[]',
        description: '📝 텍스트 레이어 데이터 (OCR 결과)',
        optional: true,
      },
      {
        name: 'regions',
        type: 'Region[]',
        description: '📐 영역 레이어 데이터',
        optional: true,
      },
    ],
    outputs: [
      {
        name: 'composed_image',
        type: 'Image',
        description: '🎨 합성된 이미지 (Base64)',
      },
      {
        name: 'svg_overlay',
        type: 'string',
        description: '📊 SVG 오버레이 (프론트엔드용)',
      },
      {
        name: 'statistics',
        type: 'ComposerStats',
        description: '📈 합성 통계 (레이어별 개수 등)',
      },
    ],
    parameters: [
      {
        name: 'enabled_layers',
        type: 'checkboxGroup',
        default: ['symbols', 'lines', 'texts', 'regions'],
        options: [
          { value: 'symbols', label: '심볼', icon: '🔧', description: '심볼 박스 및 라벨' },
          { value: 'lines', label: '라인', icon: '📏', description: '파이프/신호 라인' },
          { value: 'texts', label: '텍스트', icon: '📝', description: 'OCR 텍스트 영역' },
          { value: 'regions', label: '영역', icon: '📐', description: '점선 영역 박스' },
        ],
        description: '활성화할 레이어',
      },
      {
        name: 'output_format',
        type: 'select',
        default: 'png',
        options: ['png', 'jpg', 'webp'],
        description: '출력 이미지 형식',
      },
      {
        name: 'include_svg',
        type: 'boolean',
        default: true,
        description: 'SVG 오버레이 생성 (프론트엔드 인터랙티브 뷰어용)',
      },
      {
        name: 'include_legend',
        type: 'boolean',
        default: false,
        description: '범례 포함 (레이어별 개수 표시)',
      },
      {
        name: 'symbol_color',
        type: 'string',
        default: '#FF7800',
        description: '심볼 색상 (Hex)',
      },
      {
        name: 'symbol_thickness',
        type: 'number',
        default: 2,
        min: 1,
        max: 10,
        step: 1,
        description: '심볼 테두리 두께',
      },
      {
        name: 'show_symbol_labels',
        type: 'boolean',
        default: true,
        description: '심볼 라벨 표시 (클래스명, 신뢰도)',
      },
      {
        name: 'line_thickness',
        type: 'number',
        default: 2,
        min: 1,
        max: 10,
        step: 1,
        description: '라인 두께',
      },
      {
        name: 'show_flow_arrows',
        type: 'boolean',
        default: false,
        description: '플로우 화살표 표시 (라인 중간점)',
      },
    ],
    examples: [
      'YOLO + Line Detector + OCR → PID Composer → 합성 이미지',
      'P&ID 분석 결과 → PID Composer → 시각화 리포트',
    ],
    usageTips: [
      '⭐ YOLO, Line Detector, OCR 결과를 입력하면 종합 시각화 생성',
      '📊 include_svg=true로 프론트엔드에서 인터랙티브 뷰 가능',
      '🎨 symbol_color로 심볼 하이라이트 색상 커스터마이징',
      '📏 레이어별로 활성화/비활성화 가능',
      '💡 include_legend=true로 레이어별 개수 범례 추가',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: '⭐ 심볼 레이어: YOLO 검출 결과를 시각화',
      },
      {
        from: 'linedetector',
        field: 'lines',
        reason: '라인 레이어: 파이프/신호 라인 시각화',
      },
      {
        from: 'edocr2',
        field: 'text_results',
        reason: '텍스트 레이어: OCR 결과 영역 시각화',
      },
    ],
  },
};
