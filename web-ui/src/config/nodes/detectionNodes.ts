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
          'pid_class_agnostic',
          'pid_class_aware',
        ],
        description: '모델 선택: bom_detector(전력설비 27종), engineering(기계도면 14종), pid_symbol(P&ID 60종)',
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
      '도면 이미지 → YOLO (pid_symbol) → 60가지 P&ID 심볼 검출',
      '전력 설비 도면 → YOLO (bom_detector) → 27가지 전력 설비 심볼 검출 → BOM 생성',
    ],
    usageTips: [
      '기계도면: model_type=engineering, confidence=0.25',
      'P&ID: model_type=pid_symbol, confidence=0.1 (SAHI 자동)',
      '전력 설비: model_type=bom_detector, confidence=0.4, iou=0.5, imgsz=1024',
      '검출된 영역을 eDOCr2나 PaddleOCR의 입력으로 사용하면 해당 영역만 정밀 분석할 수 있습니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면 이미지를 입력받아 심볼과 텍스트 영역을 검출합니다',
      },
    ],
  },
  yolopid: {
    type: 'yolopid',
    label: '[DEPRECATED] YOLO-PID',
    category: 'detection',
    color: '#6b7280',
    icon: 'CircuitBoard',
    deprecated: true,
    deprecatedMessage: '통합 YOLO API 사용: YOLO 노드에서 model_type=pid_symbol 선택',
    description: '⚠️ DEPRECATED - YOLO 노드의 model_type=pid_symbol 사용 권장. P&ID 심볼 검출.',
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 P&ID 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'symbols',
        type: 'PIDSymbol[]',
        description: '🔧 검출된 P&ID 심볼 목록 (위치, 종류, 신뢰도)',
      },
      {
        name: 'symbol_counts',
        type: 'object',
        description: '📊 심볼 타입별 개수',
      },
    ],
    parameters: [
      {
        name: 'confidence',
        type: 'number',
        default: 0.10,
        min: 0.05,
        max: 0.50,
        step: 0.05,
        description: '신뢰도 임계값 (낮을수록 더 많은 심볼 검출)',
      },
      {
        name: 'slice_height',
        type: 'select',
        default: '512',
        options: ['256', '512', '768', '1024', '4096'],
        description: 'SAHI 슬라이스 높이 (4096=슬라이스 없음, 가장 빠름)',
      },
      {
        name: 'slice_width',
        type: 'select',
        default: '512',
        options: ['256', '512', '768', '1024', '4096'],
        description: 'SAHI 슬라이스 너비 (4096=슬라이스 없음)',
      },
      {
        name: 'overlap_ratio',
        type: 'number',
        default: 0.25,
        min: 0.1,
        max: 0.5,
        step: 0.05,
        description: '슬라이스 오버랩 비율 (높을수록 경계 누락↓)',
      },
      {
        name: 'class_agnostic',
        type: 'boolean',
        default: false,
        description: 'Class-agnostic 모드 (true=모든 심볼을 Symbol로, false=32클래스 분류)',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: true,
        description: '검출 결과 시각화 생성',
      },
    ],
    examples: [
      'ImageInput → YOLO-PID → 밸브, 펌프, 계기 검출',
      'YOLO-PID + Line Detector → PID Analyzer → 연결 분석',
    ],
    usageTips: [
      '⭐ SAHI 기반으로 대형 P&ID 도면에서 작은 심볼도 정확히 검출',
      '💡 32종의 P&ID 심볼을 분류합니다 (밸브, 펌프, 계기, 열교환기 등)',
      '💡 슬라이스 크기를 256으로 설정하면 최정밀 검출, 1024는 빠른 검출',
      '💡 confidence를 낮추면 더 많은 심볼을 검출하지만 오탐 가능성 증가',
      '💡 Line Detector와 함께 사용하여 PID Analyzer로 연결 관계를 분석하세요',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: 'P&ID 도면 이미지에서 심볼을 검출합니다',
      },
      {
        from: 'esrgan',
        field: 'image',
        reason: '저해상도 P&ID 도면 업스케일 후 검출 정확도 향상',
      },
    ],
  },
};
