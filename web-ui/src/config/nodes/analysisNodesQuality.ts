/**
 * Quality & Verification Nodes
 * 품질 분석, GT 비교, 통합 검출, 검증 큐 노드
 */

import type { NodeDefinition } from './types';

export const qualityNodes: Record<string, NodeDefinition> = {
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
