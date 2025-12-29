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
          'pid_class_aware',
          'pid_class_agnostic',
        ],
        description: '모델 선택: bom_detector(전력설비 27종), engineering(기계도면 14종), pid_class_aware(P&ID 32종 분류), pid_class_agnostic(P&ID 위치만)',
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
      '도면 이미지 → YOLO (pid_class_aware) → 32가지 P&ID 심볼 검출 및 분류',
      '전력 설비 도면 → YOLO (bom_detector) → 27가지 전력 설비 심볼 검출 → BOM 생성',
    ],
    usageTips: [
      '기계도면: model_type=engineering, confidence=0.25, imgsz=1280',
      'P&ID 분류: model_type=pid_class_aware, confidence=0.25, use_sahi=true',
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
};
