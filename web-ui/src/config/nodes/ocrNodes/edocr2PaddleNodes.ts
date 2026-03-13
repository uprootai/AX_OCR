/**
 * OCR Nodes — eDOCr2 & PaddleOCR
 */

import type { NodeDefinition } from '../types';

export const edocr2PaddleNodes: Record<string, NodeDefinition> = {
  edocr2: {
    type: 'edocr2',
    label: 'eDOCr2 Korean OCR',
    category: 'ocr',
    color: '#3b82f6',
    icon: 'FileText',
    description: '한국어 텍스트 인식 전문 OCR. 도면의 치수, 공차, 주석 등을 정확하게 읽습니다.',
    profiles: {
      default: 'general',
      available: [
        {
          name: 'general',
          label: '일반 OCR',
          description: '범용 텍스트 인식',
          params: { extract_dimensions: true, extract_gdt: true, extract_text: true, extract_tables: true },
        },
        {
          name: 'dimension',
          label: '치수 인식',
          description: '치수/공차 인식 최적화',
          params: { extract_dimensions: true, extract_gdt: true, extract_text: false, extract_tables: false },
        },
        {
          name: 'engineering',
          label: '도면용',
          description: '도면 텍스트 전체 인식',
          params: { extract_dimensions: true, extract_gdt: true, extract_text: true, extract_tables: true },
        },
        {
          name: 'crop_upscale',
          label: '크롭 업스케일',
          description: '4분할 크롭 + 2x 업스케일 OCR (고정밀)',
          params: { extract_dimensions: true, extract_gdt: true, extract_text: true, enable_crop_upscale: true, crop_preset: 'quadrants', upscale_scale: '2' },
        },
      ],
    },
    inputs: [
      {
        name: 'image',
        type: 'Image | DetectionResult[]',
        description: '📄 도면 이미지 또는 🎯 YOLO 검출 영역',
      },
    ],
    outputs: [
      {
        name: 'text_results',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트 목록 (내용, 위치, 정확도)',
      },
    ],
    parameters: [
      {
        name: 'language',
        type: 'select',
        default: 'eng',
        options: ['eng', 'kor', 'jpn', 'chi_sim'],
        description: '인식 언어 (eng: 영어, kor: 한국어, jpn: 일본어, chi_sim: 중국어)',
      },
      {
        name: 'extract_dimensions',
        type: 'boolean',
        default: true,
        description: '치수 정보 추출 (φ476, 10±0.5, R20 등)',
      },
      {
        name: 'extract_gdt',
        type: 'boolean',
        default: true,
        description: 'GD&T 정보 추출 (평행도, 직각도, 위치도 등)',
      },
      {
        name: 'extract_text',
        type: 'boolean',
        default: true,
        description: '텍스트 정보 추출 (도면 번호, 재질, 주석 등)',
      },
      {
        name: 'extract_tables',
        type: 'boolean',
        default: true,
        description: '표 정보 추출 (BOM, 치수 표 등)',
      },
      {
        name: 'cluster_threshold',
        type: 'number',
        default: 20,
        min: 5,
        max: 100,
        step: 5,
        description: '텍스트 클러스터링 임계값 (픽셀 단위)',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: true,
        description: 'OCR 결과 시각화 이미지 생성',
      },
      {
        name: 'enable_crop_upscale',
        type: 'boolean',
        default: false,
        description: '치수 영역 크롭 + ESRGAN 업스케일 (고정밀 OCR)',
      },
      {
        name: 'crop_preset',
        type: 'select',
        default: 'quadrants',
        options: ['quadrants'],
        description: '크롭 프리셋 (quadrants: 도면 4분할)',
      },
      {
        name: 'upscale_scale',
        type: 'select',
        default: '2',
        options: ['2', '4'],
        description: 'ESRGAN 업스케일 배율 (2 권장)',
      },
      {
        name: 'upscale_denoise',
        type: 'number',
        default: 0.3,
        min: 0,
        max: 1,
        step: 0.1,
        description: '업스케일 노이즈 제거 강도 (0~1)',
      },
    ],
    examples: [
      'YOLO 검출 → eDOCr2 → 한글/숫자 치수 인식',
      '공차 표기 (±0.05), 주석 텍스트 추출',
    ],
    usageTips: [
      '한국어가 포함된 도면은 language=kor로 설정하세요',
      'YOLO의 검출 영역을 입력으로 받으면 특정 영역만 정밀 분석할 수 있습니다',
      'visualize=true로 설정하면 인식된 텍스트의 위치를 시각적으로 확인할 수 있습니다',
      '⭐ SkinModel 노드와 연결 시 텍스트 위치 정보가 자동으로 활용되어 치수 매칭 정확도가 향상됩니다',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: 'YOLO가 검출한 텍스트 영역만 정밀 분석하여 처리 속도와 정확도를 높입니다',
      },
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면 이미지에서 모든 텍스트를 추출합니다',
      },
    ],
  },
  paddleocr: {
    type: 'paddleocr',
    label: 'PaddleOCR',
    category: 'ocr',
    color: '#06b6d4',
    icon: 'FileSearch',
    description: '다국어 지원 OCR. 영어, 숫자 인식에 강점. eDOCr2의 대안으로 사용.',
    profiles: {
      default: 'general',
      available: [
        {
          name: 'general',
          label: '일반',
          description: '범용 텍스트 인식',
          params: { det_db_thresh: 0.3, det_db_box_thresh: 0.5, use_angle_cls: true },
        },
        {
          name: 'engineering',
          label: '도면용',
          description: '도면 텍스트 인식 최적화',
          params: { det_db_thresh: 0.25, det_db_box_thresh: 0.4, use_angle_cls: false },
        },
        {
          name: 'document',
          label: '문서용',
          description: '문서 텍스트 인식',
          params: { det_db_thresh: 0.3, det_db_box_thresh: 0.5, use_angle_cls: true },
        },
      ],
    },
    inputs: [
      {
        name: 'image',
        type: 'Image | DetectionResult[]',
        description: '📄 도면 이미지 또는 🎯 특정 검출 영역',
      },
    ],
    outputs: [
      {
        name: 'text_results',
        type: 'OCRResult[]',
        description: '📝 인식된 영문/숫자 텍스트 목록',
      },
    ],
    parameters: [
      {
        name: 'lang',
        type: 'select',
        default: 'en',
        options: ['en', 'ch', 'korean', 'japan', 'french'],
        description: '인식 언어',
      },
      {
        name: 'det_db_thresh',
        type: 'number',
        default: 0.3,
        min: 0,
        max: 1,
        step: 0.05,
        description: '텍스트 검출 임계값 (낮을수록 더 많이 검출)',
      },
      {
        name: 'det_db_box_thresh',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.05,
        description: '박스 임계값 (높을수록 정확한 박스만)',
      },
      {
        name: 'use_angle_cls',
        type: 'boolean',
        default: true,
        description: '회전된 텍스트 감지 여부 (90도, 180도, 270도)',
      },
      {
        name: 'min_confidence',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.05,
        description: '최소 신뢰도 (이 값 이하는 필터링)',
      },
      {
        name: 'visualize',
        type: 'boolean',
        default: true,
        description: 'OCR 결과 시각화 이미지 생성 (바운딩 박스 + 텍스트)',
      },
    ],
    examples: [
      '영문 도면 → PaddleOCR → 영어 텍스트 추출',
      'IF 노드로 eDOCr2 실패 시 대안으로 사용',
    ],
    usageTips: [
      '영문/숫자가 많은 도면은 eDOCr2 대신 PaddleOCR을 사용하면 더 정확합니다',
      '✨ visualize=true로 설정하면 인식된 텍스트의 바운딩 박스와 위치를 시각적으로 확인할 수 있습니다',
      'IF 노드와 함께 사용하여 eDOCr2 실패 시 자동 fallback으로 활용할 수 있습니다',
      'SkinModel과 연결 시 텍스트 위치 정보가 자동으로 활용되어 치수 분석 정확도가 향상됩니다',
    ],
    recommendedInputs: [
      {
        from: 'yolo',
        field: 'detections',
        reason: 'YOLO가 검출한 텍스트 영역만 정밀 분석하여 처리 속도를 높입니다',
      },
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면에서 영문/숫자 텍스트를 추출합니다',
      },
      {
        from: 'edgnet',
        field: 'segmented_image',
        reason: '전처리된 선명한 이미지에서 텍스트를 인식하면 정확도가 향상됩니다',
      },
    ],
  },
};
