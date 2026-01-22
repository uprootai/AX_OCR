/**
 * Detection Nodes
 * 객체 검출 노드 정의 (YOLO 기반)
 */

import type { NodeDefinition } from './types';

export const detectionNodes: Record<string, NodeDefinition> = {
  yolo: {
    type: 'yolo',
    label: 'YOLO (통합)',
    category: 'detection',
    color: '#10b981',
    icon: 'Target',
    description: '통합 YOLO API - 기계도면(14종) 및 P&ID(60종) 심볼을 검출합니다. 모델 선택으로 용도에 맞게 사용하세요.',
    profiles: {
      default: 'bom_detector',
      available: [
        {
          name: 'bom_detector',
          label: 'BOM 검출기',
          description: '전력설비 27종 심볼 검출 (BOM 생성용)',
          params: { model_type: 'bom_detector', confidence: 0.4, iou: 0.5, imgsz: 1024, visualize: true },
        },
        {
          name: 'engineering',
          label: '기계도면',
          description: '기계도면 14종 심볼 검출',
          params: { model_type: 'engineering', confidence: 0.25, imgsz: 1280, visualize: true },
        },
        {
          name: 'pid_sahi',
          label: 'P&ID (SAHI)',
          description: 'P&ID 32종 심볼 SAHI 슬라이싱 검출',
          params: { model_type: 'pid_symbol', confidence: 0.1, use_sahi: true, slice_height: 512, slice_width: 512, visualize: true },
        },
        {
          name: 'pid_precision',
          label: 'P&ID 고정밀',
          description: 'P&ID 32종 심볼 고정밀 검출 및 분류',
          params: { model_type: 'pid_class_aware', confidence: 0.25, use_sahi: true, visualize: true },
        },
      ],
    },
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 도면 이미지 파일 (JPG, PNG 등)',
      },
    ],
    outputs: [
      {
        name: 'detections',
        type: 'DetectionResult[]',
        description: '🎯 검출된 심볼 목록 (위치, 종류, 신뢰도 포함)',
      },
    ],
    parameters: [
      {
        name: 'model_type',
        type: 'select',
        default: 'bom_detector',
        options: [
          'bom_detector',
          'engineering',
          'pid_symbol',
          'pid_class_aware',
          'pid_class_agnostic',
        ],
        description: '모델 선택: bom_detector(전력설비 27종), engineering(기계도면 14종), pid_symbol(P&ID 32종 SAHI), pid_class_aware(P&ID 32종 고정밀), pid_class_agnostic(P&ID 위치만)',
      },
      {
        name: 'confidence',
        type: 'number',
        default: 0.4,
        min: 0.05,
        max: 1,
        step: 0.05,
        description: '검출 신뢰도 임계값 (bom_detector: 0.4, P&ID: 0.1, engineering: 0.25)',
      },
      {
        name: 'iou',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'NMS IoU 임계값 (bom_detector: 0.5 권장)',
      },
      {
        name: 'imgsz',
        type: 'number',
        default: 1024,
        min: 320,
        max: 3520,
        step: 32,
        description: '입력 이미지 크기 (bom_detector: 1024 권장)',
      },
      {
        name: 'use_sahi',
        type: 'boolean',
        default: false,
        description: 'SAHI 슬라이싱 활성화 (P&ID 모델은 자동 활성화)',
      },
      {
        name: 'slice_height',
        type: 'number',
        default: 512,
        min: 256,
        max: 2048,
        step: 128,
        description: 'SAHI 슬라이스 높이 (작을수록 정밀)',
      },
      {
        name: 'slice_width',
        type: 'number',
        default: 512,
        min: 256,
        max: 2048,
        step: 128,
        description: 'SAHI 슬라이스 너비 (작을수록 정밀)',
      },
      {
        name: 'overlap_ratio',
        type: 'number',
        default: 0.25,
        min: 0.1,
        max: 0.5,
        step: 0.05,
        description: 'SAHI 슬라이스 오버랩 비율',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: true,
        description: '검출 결과 시각화 이미지 생성',
      },
      {
        name: 'task',
        type: 'select',
        default: 'detect',
        options: ['detect', 'segment'],
        description: '작업 종류 (박스 검출 vs 세그멘테이션)',
      },
    ],
    examples: [
      '도면 이미지 → YOLO (engineering) → 14가지 기계 심볼 검출',
      '도면 이미지 → YOLO (pid_symbol) → 32가지 P&ID 심볼 검출 (SAHI 슬라이싱)',
      '도면 이미지 → YOLO (pid_class_aware) → 32가지 P&ID 심볼 검출 및 분류',
      '전력 설비 도면 → YOLO (bom_detector) → 27가지 전력 설비 심볼 검출 → BOM 생성',
    ],
    usageTips: [
      '기계도면: model_type=engineering, confidence=0.25, imgsz=1280',
      'P&ID (SAHI): model_type=pid_symbol, confidence=0.1, use_sahi=true, slice=512',
      'P&ID 고정밀: model_type=pid_class_aware, confidence=0.25, use_sahi=true',
      'P&ID 위치만: model_type=pid_class_agnostic, confidence=0.15',
      '전력 설비: model_type=bom_detector, confidence=0.4, iou=0.5, imgsz=1024',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면 이미지를 입력받아 심볼과 텍스트 영역을 검출합니다',
      },
    ],
  },

  table_detector: {
    type: 'table_detector',
    label: 'Table Detector',
    category: 'detection',
    color: '#10B981',
    icon: 'TableCells',
    description: '테이블 검출 및 구조 추출 - Microsoft TATR과 img2table을 사용하여 도면/문서의 테이블을 검출하고 내용을 추출합니다.',
    profiles: {
      default: 'engineering',
      available: [
        {
          name: 'engineering',
          label: '기계도면 테이블',
          description: 'Parts List, BOM, 치수 테이블 추출',
          params: { mode: 'analyze', ocr_engine: 'tesseract', borderless: true, confidence_threshold: 0.7, min_confidence: 50 },
        },
        {
          name: 'document',
          label: '일반 문서 테이블',
          description: '일반 문서/보고서 테이블 추출',
          params: { mode: 'analyze', ocr_engine: 'paddle', borderless: false, confidence_threshold: 0.5, min_confidence: 40 },
        },
        {
          name: 'detection_only',
          label: '테이블 검출만',
          description: '테이블 영역만 검출 (내용 추출 안함)',
          params: { mode: 'detect', confidence_threshold: 0.6 },
        },
        {
          name: 'korean',
          label: '한글 문서',
          description: '한글 테이블 최적화',
          params: { mode: 'analyze', ocr_engine: 'paddle', borderless: true, confidence_threshold: 0.7, min_confidence: 60 },
        },
      ],
    },
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 테이블이 포함된 이미지 (도면, 문서 등)',
      },
    ],
    outputs: [
      {
        name: 'tables',
        type: 'TableData[]',
        description: '📊 추출된 테이블 목록 (headers, data, html)',
      },
      {
        name: 'regions',
        type: 'BBox[]',
        description: '📍 검출된 테이블 영역 (bounding boxes)',
      },
    ],
    parameters: [
      {
        name: 'mode',
        type: 'select',
        default: 'analyze',
        options: ['detect', 'extract', 'analyze'],
        description: '처리 모드: detect(영역검출), extract(내용추출), analyze(통합)',
      },
      {
        name: 'ocr_engine',
        type: 'select',
        default: 'tesseract',
        options: ['tesseract', 'paddle', 'easyocr'],
        description: 'OCR 엔진 선택',
      },
      {
        name: 'borderless',
        type: 'boolean',
        default: true,
        description: '테두리 없는 테이블 검출 (Parts List 등)',
      },
      {
        name: 'confidence_threshold',
        type: 'number',
        default: 0.7,
        min: 0.1,
        max: 1.0,
        step: 0.1,
        description: '테이블 검출 신뢰도 임계값',
      },
      {
        name: 'min_confidence',
        type: 'number',
        default: 50,
        min: 0,
        max: 100,
        step: 10,
        description: 'OCR 최소 신뢰도 (0-100)',
      },
      {
        name: 'output_format',
        type: 'select',
        default: 'json',
        options: ['json', 'csv', 'html', 'dataframe'],
        description: '출력 형식',
      },
      {
        name: 'auto_crop',
        type: 'select',
        default: 'full',
        options: ['full', 'right_upper', 'right_lower', 'right_full', 'upper_half', 'left_upper', 'left_lower'],
        description: '자동 크롭 영역 (Parts List는 보통 우측 상단에 위치)',
      },
    ],
    examples: [
      '도면 이미지 → Table Detector → Parts List JSON 추출',
      '문서 이미지 → Table Detector (korean) → 한글 테이블 추출',
      '도면 이미지 → Table Detector (detect) → 테이블 영역 bbox 반환',
    ],
    usageTips: [
      '기계도면 Parts List: mode=analyze, borderless=true',
      '한글 문서: ocr_engine=paddle, min_confidence=60',
      '테이블 위치만 확인: mode=detect',
      'BOM 테이블: engineering 프로파일 사용',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '도면/문서 이미지에서 테이블 영역을 검출하고 내용을 추출합니다',
      },
      {
        from: 'esrgan',
        field: 'upscaled_image',
        reason: '업스케일된 이미지로 더 정확한 테이블 인식이 가능합니다',
      },
    ],
  },
};
