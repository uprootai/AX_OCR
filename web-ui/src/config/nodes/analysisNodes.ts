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
    description: 'P&ID 심볼과 라인을 분석하여 연결 관계, BOM, 장비 목록을 생성합니다.',
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
   * Excel Export Node
   * P&ID 분석 결과를 Excel 파일로 내보내기
   */
  excelexport: {
    type: 'excelexport',
    label: 'Excel Export',
    category: 'analysis',
    color: '#16a34a',
    icon: 'FileSpreadsheet',
    description:
      'P&ID 분석 결과를 Excel 파일로 내보냅니다. Equipment, Valve, Checklist, Deviation을 각 시트에 정리합니다.',
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
        name: 'excel_url',
        type: 'string',
        description: '📁 생성된 Excel 파일 다운로드 URL',
      },
      {
        name: 'filename',
        type: 'string',
        description: '📝 Excel 파일명',
      },
      {
        name: 'summary',
        type: 'ExportSummary',
        description: '📊 내보내기 요약 (시트별 항목 수)',
      },
    ],
    parameters: [
      {
        name: 'export_type',
        type: 'select',
        default: 'all',
        options: [
          { value: 'all', label: '전체', description: '모든 데이터를 각 시트에 포함' },
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
        description: '프로젝트명 (파일명에 포함)',
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
      'PID Analyzer → Excel Export → 분석 결과 스프레드시트',
      'YOLO + OCR → Excel Export → 검출 결과 정리',
    ],
    usageTips: [
      '⭐ PDF보다 데이터 가공이 필요한 경우 Excel 사용 권장',
      '📊 export_type="all"로 모든 데이터를 각 시트에 분리',
      '🔄 Excel 파일은 후처리/분석에 용이합니다',
      '📁 열 너비가 자동 조정되어 가독성이 좋습니다',
    ],
    recommendedInputs: [
      {
        from: 'pidanalyzer',
        field: 'session_data',
        reason: '⭐ P&ID 분석 결과를 Excel로 정리',
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
};
