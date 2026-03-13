/**
 * OCR Nodes — OCR Ensemble & Surya OCR
 */

import type { NodeDefinition } from '../types';

export const ensembleAdvancedNodes: Record<string, NodeDefinition> = {
  ocr_ensemble: {
    type: 'ocr_ensemble',
    label: 'OCR Ensemble',
    category: 'ocr',
    color: '#0891b2',
    icon: 'Layers',
    description: '4개 OCR 엔진 가중 투표 앙상블 (eDOCr2 40% + PaddleOCR 35% + Tesseract 15% + TrOCR 10%)',
    profiles: {
      default: 'balanced',
      available: [
        {
          name: 'balanced',
          label: '균형',
          description: '기본 가중치 (eDOCr2 40%, PaddleOCR 35%)',
          params: { edocr2_weight: 0.40, paddleocr_weight: 0.35, tesseract_weight: 0.15, trocr_weight: 0.10 },
        },
        {
          name: 'edocr2_focus',
          label: 'eDOCr2 중심',
          description: 'eDOCr2 가중치 강화 (한국어 도면용)',
          params: { edocr2_weight: 0.60, paddleocr_weight: 0.25, tesseract_weight: 0.10, trocr_weight: 0.05 },
        },
        {
          name: 'paddle_focus',
          label: 'PaddleOCR 중심',
          description: 'PaddleOCR 가중치 강화 (영문 도면용)',
          params: { edocr2_weight: 0.25, paddleocr_weight: 0.55, tesseract_weight: 0.15, trocr_weight: 0.05 },
        },
      ],
    },
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'results',
        type: 'EnsembleResult[]',
        description: '📝 앙상블 결과 (가중 투표 기반)',
      },
      {
        name: 'full_text',
        type: 'string',
        description: '📄 전체 텍스트',
      },
      {
        name: 'engine_results',
        type: 'object',
        description: '🔍 각 엔진별 원본 결과',
      },
    ],
    parameters: [
      {
        name: 'edocr2_weight',
        type: 'number',
        default: 0.40,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'eDOCr2 가중치 (기본 40%)',
      },
      {
        name: 'paddleocr_weight',
        type: 'number',
        default: 0.35,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'PaddleOCR 가중치 (기본 35%)',
      },
      {
        name: 'tesseract_weight',
        type: 'number',
        default: 0.15,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'Tesseract 가중치 (기본 15%)',
      },
      {
        name: 'trocr_weight',
        type: 'number',
        default: 0.10,
        min: 0,
        max: 1,
        step: 0.05,
        description: 'TrOCR 가중치 (기본 10%)',
      },
      {
        name: 'similarity_threshold',
        type: 'number',
        default: 0.7,
        min: 0.5,
        max: 1,
        step: 0.05,
        description: '텍스트 유사도 임계값 (결과 그룹화 기준)',
      },
    ],
    examples: [
      'ImageInput → OCR Ensemble → 최고 정확도 OCR 결과',
      'ESRGAN → OCR Ensemble → 저품질 도면도 정확히 인식',
    ],
    usageTips: [
      '⭐ 단일 OCR 엔진보다 훨씬 높은 정확도를 제공합니다',
      '💡 가중치를 조정하여 특정 엔진에 더 높은 신뢰도 부여 가능',
      '💡 여러 엔진이 동의하는 결과는 신뢰도가 더 높습니다',
      '💡 처리 시간이 단일 엔진보다 길지만 정확도가 훨씬 높습니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면에서 4개 OCR 엔진으로 텍스트를 추출합니다',
      },
      {
        from: 'esrgan',
        field: 'image',
        reason: '⭐ 업스케일된 이미지로 OCR 정확도를 극대화합니다',
      },
      {
        from: 'edgnet',
        field: 'segmented_image',
        reason: '전처리된 이미지에서 더 정확한 결과를 얻습니다',
      },
    ],
  },
  suryaocr: {
    type: 'suryaocr',
    label: 'Surya OCR',
    category: 'ocr',
    color: '#8b5cf6',
    icon: 'ScanText',
    description: 'Surya OCR - 90+ 언어 지원, 레이아웃 분석, 높은 정확도. 기계 도면에 최적화.',
    profiles: {
      default: 'general',
      available: [
        {
          name: 'general',
          label: '일반',
          description: '한영 기본 인식',
          params: { languages: 'ko,en', detect_layout: false },
        },
        {
          name: 'layout',
          label: '레이아웃 분석',
          description: '테이블/단락 구조 분석 포함',
          params: { languages: 'ko,en', detect_layout: true },
        },
        {
          name: 'multilingual',
          label: '다국어',
          description: '다국어 도면 인식 (한중일영)',
          params: { languages: 'ko,en,ja,zh', detect_layout: false },
        },
      ],
    },
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 도면 또는 문서 이미지',
      },
    ],
    outputs: [
      {
        name: 'texts',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트 목록 (bbox 포함)',
      },
      {
        name: 'full_text',
        type: 'string',
        description: '📄 전체 텍스트',
      },
      {
        name: 'layout',
        type: 'LayoutElement[]',
        description: '📐 레이아웃 요소 (선택적)',
      },
    ],
    parameters: [
      {
        name: 'languages',
        type: 'string',
        default: 'ko,en',
        description: '인식 언어 (쉼표 구분, 90+ 언어 지원)',
      },
      {
        name: 'detect_layout',
        type: 'boolean',
        default: false,
        description: '레이아웃 분석 활성화 (테이블, 단락 감지)',
      },
    ],
    examples: [
      'ImageInput → Surya OCR → 다국어 도면 텍스트 추출',
      'ESRGAN → Surya OCR → 고정밀 OCR',
    ],
    usageTips: [
      '⭐ 기계 도면 OCR에서 가장 높은 정확도를 제공합니다',
      '💡 90+ 언어를 지원하여 다국어 도면에 적합합니다',
      '💡 detect_layout=true로 테이블/단락 구조 분석 가능',
      '💡 DocTR, EasyOCR보다 기술 도면에서 정확도가 높습니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '전체 도면에서 텍스트를 추출합니다',
      },
      {
        from: 'esrgan',
        field: 'image',
        reason: '⭐ 업스케일된 이미지로 OCR 정확도를 극대화합니다',
      },
    ],
  },
};
