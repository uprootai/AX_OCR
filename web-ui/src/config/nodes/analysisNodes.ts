/**
 * Analysis Nodes
 * 분석 및 검증 노드 정의
 */

import type { NodeDefinition } from './types';

export const analysisNodes: Record<string, NodeDefinition> = {
  skinmodel: {
    type: 'skinmodel',
    label: 'Tolerance Analysis',
    category: 'analysis',
    color: '#f59e0b',
    icon: 'Ruler',
    description: '인식된 치수 데이터를 분석하여 공차를 계산하고 제조 가능성을 평가합니다.',
    inputs: [
      {
        name: 'dimensions',
        type: 'Dimension[]',
        description: '📝 OCR에서 추출된 치수 데이터 (예: [{nominal: 50, tolerance: 0.1}])',
        optional: true,
      },
    ],
    outputs: [
      {
        name: 'tolerance_report',
        type: 'ToleranceReport',
        description: '📊 제조 가능 여부, 난이도, 예상 비용 분석 결과',
      },
    ],
    parameters: [
      {
        name: 'dimensions_manual',
        type: 'textarea',
        default: '',
        description: '수동 치수 입력 (JSON 배열). 예: [{"value": 50, "tolerance": 0.1, "type": "length", "unit": "mm"}]',
        placeholder: '[{"value": 50, "tolerance": 0.1, "type": "length"}]',
      },
      {
        name: 'material_type',
        type: 'select',
        default: 'steel',
        options: ['aluminum', 'steel', 'plastic', 'composite'],
        description: '재질 선택 (공차 계산에 영향)',
      },
      {
        name: 'manufacturing_process',
        type: 'select',
        default: 'machining',
        options: ['machining', 'casting', '3d_printing', 'welding', 'sheet_metal'],
        description: '제조 공정 (공차 허용 범위 결정)',
      },
      {
        name: 'correlation_length',
        type: 'number',
        default: 1.0,
        min: 0.1,
        max: 10.0,
        step: 0.1,
        description: 'Random Field 상관 길이 (불확실성 모델링, 기본값 1.0)',
      },
      {
        name: 'task',
        type: 'select',
        default: 'tolerance',
        options: ['tolerance', 'validate', 'manufacturability'],
        description: '분석 작업 (공차 예측 vs GD&T 검증 vs 제조성 분석)',
      },
    ],
    examples: [
      'OCR 결과 → SkinModel → 공차 계산',
      '제조 난이도 평가 및 비용 추정',
    ],
    usageTips: [
      '⭐ eDOCr2의 출력을 입력으로 받으면 텍스트 위치 정보가 자동으로 활용됩니다',
      '위치 정보 덕분에 치수와 공차가 정확히 매칭되어 분석 정확도가 크게 향상됩니다',
      '💡 OCR 연결 없이 테스트하려면 dimensions_manual에 JSON을 직접 입력하세요',
      'material_type과 manufacturing_process를 정확히 설정하면 더 정확한 제조성 평가를 받을 수 있습니다',
    ],
    recommendedInputs: [
      {
        from: 'edocr2',
        field: 'text_results',
        reason: '⭐ 텍스트 위치 정보(bbox)를 활용해 치수와 공차를 정확히 매칭합니다. 이것이 핵심 패턴입니다!',
      },
      {
        from: 'paddleocr',
        field: 'text_results',
        reason: 'PaddleOCR 결과도 위치 정보를 포함하므로 활용 가능합니다',
      },
    ],
  },
  pidanalyzer: {
    type: 'pidanalyzer',
    label: 'P&ID Analyzer',
    category: 'analysis',
    color: '#7c3aed',
    icon: 'Network',
    description: 'P&ID 심볼과 라인을 분석하여 연결 관계, BOM, 밸브 시그널 리스트, 장비 목록을 생성합니다.',
    inputs: [
      {
        name: 'symbols',
        type: 'PIDSymbol[]',
        description: '🔧 YOLO가 검출한 심볼 목록 (model_type=pid_symbol)',
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
      '💡 밸브 시그널 리스트로 제어 시스템 연동 정보를 추출합니다',
      '💡 Design Checker와 연결하여 설계 오류를 자동 검출할 수 있습니다',
      '🏭 detect_equipment_tags로 산업별 장비 태그를 인식합니다 (BWMS, HVAC, 공정 프로파일 지원)',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: '⭐ YOLO (model_type=pid_symbol)로 검출된 심볼의 연결 관계를 분석합니다',
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
        options: ['all', 'connectivity', 'symbol', 'labeling', 'specification', 'standard', 'safety'],
        description: '검사할 규칙 카테고리',
      },
      {
        name: 'severity_threshold',
        type: 'select',
        default: 'info',
        options: ['error', 'warning', 'info'],
        description: '보고할 최소 심각도',
      },
    ],
    examples: [
      'PID Analyzer → Design Checker → 설계 오류 리포트',
      'YOLO (P&ID 모델) → Design Checker → 심볼 규격 검증',
    ],
    usageTips: [
      '⭐ 20+ 설계 규칙을 자동으로 검사합니다 (연결, 심볼, 라벨링, 사양, 표준, 안전)',
      '💡 ISO 10628, ISA 5.1, ASME, IEC 61511 등 주요 표준 지원',
      '💡 compliance_score로 전체 설계 품질을 수치화합니다',
      '💡 severity_threshold를 error로 설정하면 중요한 오류만 표시됩니다',
      '⚠️ 압력용기 안전밸브 누락, 태그번호 중복 등 중요 오류를 검출합니다',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: 'YOLO (model_type=pid_symbol)로 검출된 심볼의 규격 준수 여부를 검사합니다',
      },
      {
        from: 'pidanalyzer',
        field: 'connections',
        reason: '⭐ 심볼 연결 관계를 분석하여 설계 오류를 검출합니다',
      },
    ],
  },
};
