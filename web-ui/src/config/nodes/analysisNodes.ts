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
    profiles: {
      default: 'general',
      available: [
        {
          name: 'general',
          label: '일반 분석',
          description: '기본 공차 분석 (Steel 기준)',
          params: { default_material: 'steel', tolerance_class: 'medium' },
        },
        {
          name: 'precision',
          label: '정밀 부품',
          description: '정밀 가공 부품용 (엄격한 공차)',
          params: { default_material: 'steel', tolerance_class: 'fine' },
        },
        {
          name: 'lightweight',
          label: '경량 부품',
          description: '경량화 부품용 (알루미늄/티타늄)',
          params: { default_material: 'aluminum', tolerance_class: 'medium' },
        },
        {
          name: 'marine',
          label: '선박용',
          description: '선박/해양 부품용 (스테인리스)',
          params: { default_material: 'stainless', tolerance_class: 'medium' },
        },
      ],
    },
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
  gtcomparison: {
    type: 'gtcomparison',
    label: 'GT Comparison',
    category: 'analysis',
    color: '#f97316',
    icon: 'BarChart3',
    description:
      'Ground Truth(정답 라벨)와 검출 결과를 비교하여 정밀도, 재현율, F1 스코어를 계산합니다. 모델 성능 평가에 사용됩니다.',
    inputs: [
      {
        name: 'detections',
        type: 'Detection[]',
        description: '🎯 YOLO 검출 결과 (bbox, class_name, confidence)',
      },
      {
        name: 'image',
        type: 'Image',
        description: '📄 원본 이미지 (GT 파일 매칭용 파일명 필요)',
      },
    ],
    outputs: [
      {
        name: 'metrics',
        type: 'GTMetrics',
        description: '📊 평가 지표 (Precision, Recall, F1, TP, FP, FN)',
      },
      {
        name: 'tp_matches',
        type: 'TPMatch[]',
        description: '✅ True Positive 매칭 목록 (검출-GT 쌍)',
      },
      {
        name: 'fp_detections',
        type: 'Detection[]',
        description: '❌ False Positive (오검출) 목록',
      },
      {
        name: 'fn_labels',
        type: 'GTLabel[]',
        description: '⚠️ False Negative (미검출) GT 목록',
      },
    ],
    parameters: [
      {
        name: 'gt_file',
        type: 'string',
        default: '',
        description: 'GT 파일 경로 (선택). 비워두면 이미지 파일명으로 자동 매칭 (예: sample.png → sample.txt)',
      },
      {
        name: 'iou_threshold',
        type: 'number',
        default: 0.5,
        min: 0.1,
        max: 0.9,
        step: 0.05,
        description: 'IoU 임계값 (기본 0.5). 높을수록 엄격한 매칭',
      },
      {
        name: 'class_agnostic',
        type: 'boolean',
        default: false,
        description: '클래스 무시 모드. true면 위치(IoU)만으로 매칭, 클래스 불일치 허용',
      },
      {
        name: 'model_type',
        type: 'select',
        default: 'bom_detector',
        options: ['bom_detector', 'engineering', 'pid_class_aware', 'pid_symbol', 'custom'],
        description: '모델 타입 (클래스 목록 결정). GT 라벨과 일치해야 정확한 비교 가능',
      },
    ],
    examples: [
      'YOLO → GT Comparison → 성능 평가 리포트',
      '검출 정확도 측정 및 모델 개선 포인트 파악',
    ],
    usageTips: [
      '⭐ YOLO 검출 후 GT Comparison으로 성능을 정량화하세요',
      '💡 IoU threshold 0.5가 일반적. 작은 객체는 0.3~0.4 권장',
      '📊 F1 스코어가 낮으면 FN(미검출)과 FP(오검출) 상세 확인',
      '🎯 class_agnostic=true로 먼저 위치 정확도만 평가 가능',
      '⚠️ GT 파일과 이미지 파일명이 동일해야 자동 매칭됩니다 (예: sample.png → sample.txt)',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: '⭐ YOLO 검출 결과를 GT와 비교하여 정확도를 측정합니다',
      },
      {
        from: 'imageinput',
        field: 'image',
        reason: 'GT 파일 매칭을 위한 이미지 파일명 정보가 필요합니다',
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

  /**
   * PID Features Node
   * TECHCROSS 통합 워크플로우 - Valve/Equipment/Checklist 한 번에 검출
   */
  pidfeatures: {
    type: 'pidfeatures',
    label: 'PID Features',
    category: 'analysis',
    color: '#8b5cf6',
    icon: 'Workflow',
    description:
      'TECHCROSS P&ID 통합 분석 노드. Valve Signal, Equipment, Design Checklist를 한 번에 검출하고 검증 큐를 생성합니다.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 P&ID 도면 이미지',
      },
      {
        name: 'detections',
        type: 'Detection[]',
        description: '🎯 YOLO 검출 결과 (심볼, 텍스트 등)',
        optional: true,
      },
      {
        name: 'ocr_results',
        type: 'OCRResult[]',
        description: '📝 OCR 결과 (태그, 라벨 텍스트)',
        optional: true,
      },
      {
        name: 'lines',
        type: 'Line[]',
        description: '📐 라인 검출 결과',
        optional: true,
      },
    ],
    outputs: [
      {
        name: 'valves',
        type: 'Valve[]',
        description: '🔧 검출된 밸브 목록 (ID, Type, Category, Signal)',
      },
      {
        name: 'equipment',
        type: 'Equipment[]',
        description: '⚙️ 검출된 장비 목록 (Tag, Type, Description)',
      },
      {
        name: 'checklist',
        type: 'ChecklistItem[]',
        description: '✅ 설계 체크리스트 검증 결과',
      },
      {
        name: 'verification_queue',
        type: 'VerificationItem[]',
        description: '📋 검증 대기 큐 (신뢰도 기반)',
      },
      {
        name: 'session_id',
        type: 'string',
        description: '🔑 세션 ID (후속 노드 연결용)',
      },
    ],
    parameters: [
      {
        name: 'features',
        type: 'checkboxGroup',
        default: ['valve_signal', 'equipment', 'checklist'],
        options: [
          { value: 'valve_signal', label: 'Valve Signal', icon: '🔧', description: '밸브 신호 목록 검출' },
          { value: 'equipment', label: 'Equipment', icon: '⚙️', description: '장비 목록 검출' },
          { value: 'checklist', label: 'Checklist', icon: '✅', description: '설계 규칙 검증' },
        ],
        description: '분석할 기능 선택',
      },
      {
        name: 'product_type',
        type: 'select',
        default: 'ALL',
        options: [
          { value: 'ALL', label: '전체', description: '모든 규칙 적용' },
          { value: 'ECS', label: 'ECS', description: '직접 전기분해 방식' },
          { value: 'HYCHLOR', label: 'HYCHLOR', description: '간접 전기분해 방식' },
        ],
        description: 'BWMS 제품 타입 (체크리스트 규칙 필터)',
      },
      {
        name: 'confidence_threshold',
        type: 'number',
        default: 0.7,
        min: 0.1,
        max: 0.99,
        step: 0.05,
        description: '자동 검증 신뢰도 임계값. 이하는 검증 큐로 이동',
      },
      {
        name: 'auto_verify_high_confidence',
        type: 'boolean',
        default: true,
        description: '높은 신뢰도 항목 자동 검증 (threshold 이상)',
      },
    ],
    examples: [
      'Image → YOLO → PID Features → Excel/PDF Export',
      'P&ID 도면 → PID Features → Verification Queue → 최종 리포트',
    ],
    usageTips: [
      '⭐ TECHCROSS BWMS 워크플로우의 핵심 노드입니다',
      '🔧 Valve Signal: 밸브 ID, 타입, 카테고리, Signal 자동 추출',
      '⚙️ Equipment: 장비 태그, 설명, Vendor Supply 여부 추출',
      '✅ Checklist: 60개 설계 규칙 자동 검증',
      '📋 confidence_threshold 이하 항목은 검증 큐로 이동',
      '💡 product_type으로 ECS/HYCHLOR별 규칙 필터링 가능',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: '⭐ P&ID 심볼 검출 결과 (model_type: pid_class_aware)',
      },
      {
        from: 'edocr2',
        field: 'ocr_results',
        reason: '장비 태그, 라벨 텍스트 인식',
      },
      {
        from: 'linedetector',
        field: 'lines',
        reason: '라인 연결 분석용',
      },
    ],
  },

  /**
   * Verification Queue Node
   * Human-in-the-Loop 검증 큐 관리
   */
  verificationqueue: {
    type: 'verificationqueue',
    label: 'Verification Queue',
    category: 'analysis',
    color: '#f59e0b',
    icon: 'ClipboardCheck',
    description:
      'Human-in-the-Loop 검증 큐를 관리합니다. 신뢰도가 낮은 항목을 검토하고 승인/거부/수정합니다.',
    inputs: [
      {
        name: 'session_id',
        type: 'string',
        description: '🔑 세션 ID (PID Features 노드 출력)',
      },
      {
        name: 'verification_queue',
        type: 'VerificationItem[]',
        description: '📋 검증 대기 항목 목록',
        optional: true,
      },
    ],
    outputs: [
      {
        name: 'verified_items',
        type: 'VerifiedItem[]',
        description: '✅ 검증 완료 항목 (승인됨)',
      },
      {
        name: 'rejected_items',
        type: 'RejectedItem[]',
        description: '❌ 거부된 항목',
      },
      {
        name: 'pending_items',
        type: 'PendingItem[]',
        description: '⏳ 아직 검증되지 않은 항목',
      },
      {
        name: 'summary',
        type: 'VerificationSummary',
        description: '📊 검증 현황 요약 (진행률, 통계)',
      },
    ],
    parameters: [
      {
        name: 'queue_filter',
        type: 'select',
        default: 'all',
        options: [
          { value: 'all', label: '전체', description: '모든 타입의 검증 항목' },
          { value: 'valve', label: 'Valve', description: '밸브 항목만' },
          { value: 'equipment', label: 'Equipment', description: '장비 항목만' },
          { value: 'checklist', label: 'Checklist', description: '체크리스트만' },
        ],
        description: '검증 큐 필터',
      },
      {
        name: 'sort_by',
        type: 'select',
        default: 'confidence_asc',
        options: [
          { value: 'confidence_asc', label: '신뢰도 낮은 순', description: '검토 필요 항목 우선' },
          { value: 'confidence_desc', label: '신뢰도 높은 순', description: '확실한 항목 우선' },
          { value: 'type', label: '타입별', description: '항목 유형별 그룹화' },
          { value: 'created', label: '생성 순서', description: '검출 순서대로' },
        ],
        description: '정렬 기준',
      },
      {
        name: 'batch_size',
        type: 'number',
        default: 20,
        min: 5,
        max: 100,
        step: 5,
        description: '한 번에 표시할 검증 항목 수',
      },
      {
        name: 'auto_approve_threshold',
        type: 'number',
        default: 0.95,
        min: 0.8,
        max: 1.0,
        step: 0.01,
        description: '자동 승인 임계값 (이상이면 자동 검증)',
      },
    ],
    examples: [
      'PID Features → Verification Queue → PDF Export',
      '검출 결과 → 검증 큐 → 승인 후 최종 리포트',
    ],
    usageTips: [
      '⭐ Human-in-the-Loop의 핵심: 신뢰도 낮은 항목만 사람이 검토',
      '📊 confidence 낮은 순으로 정렬하면 효율적 검토 가능',
      '✅ 대량 승인/거부로 빠른 처리 가능',
      '🔄 검증 완료 후 PDF/Excel Export로 최종 리포트 생성',
      '💡 auto_approve_threshold=0.95로 확실한 항목은 자동 처리',
    ],
    recommendedInputs: [
      {
        from: 'pidfeatures',
        field: 'verification_queue',
        reason: '⭐ PID Features에서 생성된 검증 큐',
      },
      {
        from: 'pidfeatures',
        field: 'session_id',
        reason: '세션 연결 필수',
      },
    ],
  },

  /**
   * PID Composer Node
   * P&ID 레이어 합성 및 시각화
   */
  /**
   * Title Block Parser Node
   * 도면 Title Block에서 도면번호, Rev, 품명, 재질 등 추출
   */
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

  /**
   * Parts List Parser Node
   * 도면 Parts List에서 부품번호, 품명, 재질, 수량 등 추출
   */
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

  /**
   * Dimension Parser Node
   * 베어링 도면 치수를 구조화된 형태로 파싱
   */
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

  /**
   * BOM Matcher Node
   * Title Block + Parts List + Dimension → 통합 BOM 생성
   */
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

  /**
   * Quote Generator Node
   * BOM → 자동 견적 생성 (재료비, 가공비, 마진 계산)
   */
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
