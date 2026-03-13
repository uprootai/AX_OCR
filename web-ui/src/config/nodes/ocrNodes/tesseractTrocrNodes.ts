/**
 * OCR Nodes — Tesseract & TrOCR
 */

import type { NodeDefinition } from '../types';

export const tesseractTrocrNodes: Record<string, NodeDefinition> = {
  tesseract: {
    type: 'tesseract',
    label: 'Tesseract OCR',
    category: 'ocr',
    color: '#059669',
    icon: 'ScanText',
    description: 'Google Tesseract 기반 OCR. 문서 텍스트 인식, 다국어 지원.',
    profiles: {
      default: 'general',
      available: [
        {
          name: 'general',
          label: '일반',
          description: '범용 텍스트 인식 (자동 레이아웃)',
          params: { lang: 'eng', psm: '3', output_type: 'data' },
        },
        {
          name: 'korean',
          label: '한국어',
          description: '한영 혼합 문서 인식',
          params: { lang: 'eng+kor', psm: '3', output_type: 'data' },
        },
        {
          name: 'single_block',
          label: '단일 블록',
          description: '단일 텍스트 블록 인식',
          params: { lang: 'eng', psm: '6', output_type: 'data' },
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
        description: '📝 인식된 텍스트 목록',
      },
      {
        name: 'full_text',
        type: 'string',
        description: '📄 전체 텍스트',
      },
    ],
    parameters: [
      {
        name: 'lang',
        type: 'select',
        default: 'eng',
        options: ['eng', 'kor', 'jpn', 'chi_sim', 'eng+kor'],
        description: '인식 언어',
      },
      {
        name: 'psm',
        type: 'select',
        default: '3',
        options: ['0', '1', '3', '4', '6', '7', '11', '12', '13'],
        description: 'Page Segmentation Mode (3: 자동, 6: 단일 블록)',
      },
      {
        name: 'output_type',
        type: 'select',
        default: 'data',
        options: ['string', 'data'],
        description: '출력 형식 (string: 텍스트만, data: 위치정보 포함)',
      },
    ],
    examples: [
      'ImageInput → Tesseract → 영문 도면 텍스트 추출',
      'OCR Ensemble의 구성 엔진 (15% 가중치)',
    ],
    usageTips: [
      '💡 다국어 도면은 lang=eng+kor로 설정하세요',
      '💡 OCR Ensemble과 함께 사용하면 정확도가 향상됩니다',
      '💡 psm=6은 단일 텍스트 블록에 적합합니다',
    ],
  },
  trocr: {
    type: 'trocr',
    label: 'TrOCR',
    category: 'ocr',
    color: '#7c3aed',
    icon: 'Wand2',
    description: 'Microsoft TrOCR (Transformer OCR). Scene Text Recognition에 강점.',
    profiles: {
      default: 'printed',
      available: [
        {
          name: 'printed',
          label: '인쇄체',
          description: '인쇄된 텍스트 인식',
          params: { model_type: 'printed', max_length: 64, num_beams: 4 },
        },
        {
          name: 'handwritten',
          label: '필기체',
          description: '손글씨 텍스트 인식',
          params: { model_type: 'handwritten', max_length: 64, num_beams: 4 },
        },
        {
          name: 'fast',
          label: '빠른 처리',
          description: '빠른 인식 (빔 검색 축소)',
          params: { model_type: 'printed', max_length: 32, num_beams: 1 },
        },
      ],
    },
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 텍스트 라인 이미지 (크롭 권장)',
      },
    ],
    outputs: [
      {
        name: 'texts',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트',
      },
    ],
    parameters: [
      {
        name: 'model_type',
        type: 'select',
        default: 'printed',
        options: ['printed', 'handwritten'],
        description: '모델 타입 (printed: 인쇄체, handwritten: 필기체)',
      },
      {
        name: 'max_length',
        type: 'number',
        default: 64,
        min: 16,
        max: 256,
        step: 16,
        description: '최대 출력 길이',
      },
      {
        name: 'num_beams',
        type: 'number',
        default: 4,
        min: 1,
        max: 10,
        step: 1,
        description: 'Beam Search 빔 수 (높을수록 정확, 느림)',
      },
    ],
    examples: [
      'YOLO 검출 영역 → TrOCR → 개별 텍스트 인식',
      'OCR Ensemble의 구성 엔진 (10% 가중치)',
    ],
    usageTips: [
      '💡 단일 텍스트 라인 이미지에 최적화되어 있습니다',
      '💡 전체 문서는 YOLO로 텍스트 영역 검출 후 개별 처리 권장',
      '💡 손글씨 스타일 텍스트에 handwritten 모델 사용',
    ],
  },
};
