/**
 * Preprocessing Nodes
 * 이미지 전처리 노드 정의
 */

import type { NodeDefinition } from './types';

export const preprocessingNodes: Record<string, NodeDefinition> = {
  esrgan: {
    type: 'esrgan',
    label: 'ESRGAN Upscaler',
    category: 'preprocessing',
    color: '#dc2626',
    icon: 'Maximize2',
    description: 'Real-ESRGAN 기반 4x 이미지 업스케일링. 저품질 스캔 도면 전처리.',
    profiles: {
      default: 'general',
      available: [
        {
          name: 'general',
          label: '일반',
          description: '기본 4x 업스케일링',
          params: { scale: 4, denoise_strength: 0.5 },
        },
        {
          name: 'drawing',
          label: '도면용',
          description: '도면 이미지 최적화 (선명한 선)',
          params: { scale: 4, denoise_strength: 0.3 },
        },
        {
          name: 'fast',
          label: '빠른 처리',
          description: '빠른 처리 (2x)',
          params: { scale: 2, denoise_strength: 0.5 },
        },
        {
          name: 'quality',
          label: '고품질',
          description: '고품질 처리',
          params: { scale: 4, denoise_strength: 0.5 },
        },
      ],
    },
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 저해상도 도면 이미지',
      },
    ],
    outputs: [
      {
        name: 'image',
        type: 'Image',
        description: '✨ 4x 업스케일된 고해상도 이미지',
      },
    ],
    parameters: [
      {
        name: 'scale',
        type: 'select',
        default: '4',
        options: ['2', '4'],
        description: '업스케일 배율',
      },
      {
        name: 'denoise_strength',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.1,
        description: '노이즈 제거 강도 (0: 없음, 1: 최대)',
      },
    ],
    examples: [
      '저품질 스캔 → ESRGAN → 고해상도 → OCR',
      '흐릿한 도면 → ESRGAN 2x → EDGNet → eDOCr2',
    ],
    usageTips: [
      '💡 저품질 스캔 도면에 먼저 적용하면 OCR 정확도가 크게 향상됩니다',
      '💡 scale=2로도 충분한 경우가 많습니다 (4x는 처리 시간 증가)',
      '💡 denoise_strength를 높이면 노이즈가 줄어들지만 디테일도 손실될 수 있습니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '저해상도 원본 도면을 업스케일링합니다',
      },
    ],
  },
};
