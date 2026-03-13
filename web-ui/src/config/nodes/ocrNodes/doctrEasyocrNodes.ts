/**
 * OCR Nodes — DocTR & EasyOCR
 */

import type { NodeDefinition } from '../types';

export const doctrEasyocrNodes: Record<string, NodeDefinition> = {
  doctr: {
    type: 'doctr',
    label: 'DocTR',
    category: 'ocr',
    color: '#0ea5e9',
    icon: 'FileText',
    description: 'DocTR (Document Text Recognition) - 문서 OCR 특화, 정규화된 bbox 출력.',
    profiles: {
      default: 'general',
      available: [
        {
          name: 'general',
          label: '일반',
          description: 'ResNet50 기반 고정밀 인식',
          params: { det_arch: 'db_resnet50', reco_arch: 'crnn_vgg16_bn', straighten_pages: false },
        },
        {
          name: 'fast',
          label: '빠른 처리',
          description: 'MobileNet 기반 빠른 인식',
          params: { det_arch: 'db_mobilenet_v3_large', reco_arch: 'crnn_mobilenet_v3_small', straighten_pages: false },
        },
        {
          name: 'skewed',
          label: '기울임 보정',
          description: '기울어진 스캔 자동 보정',
          params: { det_arch: 'db_resnet50', reco_arch: 'crnn_vgg16_bn', straighten_pages: true },
        },
      ],
    },
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 문서 또는 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'texts',
        type: 'OCRResult[]',
        description: '📝 인식된 텍스트 목록 (정규화 bbox)',
      },
      {
        name: 'full_text',
        type: 'string',
        description: '📄 전체 텍스트',
      },
    ],
    parameters: [
      {
        name: 'det_arch',
        type: 'select',
        default: 'db_resnet50',
        options: ['db_resnet50', 'db_mobilenet_v3_large', 'linknet_resnet18'],
        description: '텍스트 검출 모델 아키텍처',
      },
      {
        name: 'reco_arch',
        type: 'select',
        default: 'crnn_vgg16_bn',
        options: ['crnn_vgg16_bn', 'crnn_mobilenet_v3_small', 'master', 'sar_resnet31'],
        description: '텍스트 인식 모델 아키텍처',
      },
      {
        name: 'straighten_pages',
        type: 'boolean',
        default: false,
        description: '기울어진 페이지 자동 보정',
      },
      {
        name: 'export_as_xml',
        type: 'boolean',
        default: false,
        description: 'XML 형식으로 내보내기',
      },
    ],
    examples: [
      'ImageInput → DocTR → 문서 텍스트 추출',
      '기울어진 스캔 → DocTR (straighten=true) → 보정된 OCR',
    ],
    usageTips: [
      '💡 문서 OCR에 특화되어 있으며 정확한 bbox를 제공합니다',
      '💡 straighten_pages=true로 기울어진 스캔 보정 가능',
      '💡 db_resnet50이 가장 정확하고, db_mobilenet이 가장 빠릅니다',
      '💡 기계 도면보다는 일반 문서에 더 적합합니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '문서 이미지에서 텍스트를 추출합니다',
      },
    ],
  },
  easyocr: {
    type: 'easyocr',
    label: 'EasyOCR',
    category: 'ocr',
    color: '#22c55e',
    icon: 'Languages',
    description: 'EasyOCR - 80+ 언어 지원, CPU 친화적, 한국어 지원 우수.',
    profiles: {
      default: 'general',
      available: [
        {
          name: 'general',
          label: '일반',
          description: '한영 기본 인식',
          params: { languages: 'ko,en', detail: true, paragraph: false },
        },
        {
          name: 'paragraph',
          label: '문단 단위',
          description: '문단 단위로 텍스트 결합',
          params: { languages: 'ko,en', detail: true, paragraph: true },
        },
        {
          name: 'fast',
          label: '빠른 처리',
          description: '배치 처리로 빠른 인식',
          params: { languages: 'ko,en', detail: false, paragraph: false, batch_size: 8 },
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
        name: 'languages',
        type: 'string',
        default: 'ko,en',
        description: '인식 언어 (쉼표 구분, ko/en/ja/ch_sim 등)',
      },
      {
        name: 'detail',
        type: 'boolean',
        default: true,
        description: '상세 결과 (bbox 포함)',
      },
      {
        name: 'paragraph',
        type: 'boolean',
        default: false,
        description: '문단 단위로 결합',
      },
      {
        name: 'batch_size',
        type: 'number',
        default: 1,
        min: 1,
        max: 32,
        step: 1,
        description: '배치 크기 (높을수록 빠름, 메모리 증가)',
      },
    ],
    examples: [
      'ImageInput → EasyOCR → 한국어 도면 텍스트 추출',
      'CPU 환경에서 빠른 OCR 처리',
    ],
    usageTips: [
      '💡 CPU에서도 빠르게 동작하여 GPU 없는 환경에 적합합니다',
      '💡 80+ 언어를 지원하며 한국어 인식이 우수합니다',
      '💡 paragraph=true로 문단 단위 텍스트 결합 가능',
      '⚠️ 작은 글자나 기술 용어는 Surya OCR보다 정확도가 낮을 수 있습니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '다국어 도면에서 텍스트를 추출합니다',
      },
      {
        from: 'esrgan',
        field: 'image',
        reason: '저해상도 이미지 업스케일 후 OCR 정확도 향상',
      },
    ],
  },
};
