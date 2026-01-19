/**
 * AI Nodes
 * Vision-Language 및 AI 모델 노드 정의
 */

import type { NodeDefinition } from './types';

export const aiNodes: Record<string, NodeDefinition> = {
  vl: {
    type: 'vl',
    label: 'Vision Language Model',
    category: 'ai',
    color: '#ec4899',
    icon: 'Sparkles',
    description: '이미지와 텍스트를 함께 이해하는 Vision-Language 모델. 이미지에 대한 질문-답변(VQA) 또는 일반 분석 수행.',
    profiles: {
      default: 'general',
      available: [
        {
          name: 'general',
          label: '일반',
          description: '기본 VLM 분석',
          params: { model: 'gpt-4o-mini', max_tokens: 1000, temperature: 0.3 },
        },
        {
          name: 'classify',
          label: '분류',
          description: '도면 유형 분류',
          params: { model: 'gpt-4o-mini', max_tokens: 50, temperature: 0.1 },
        },
        {
          name: 'detailed',
          label: '상세 분석',
          description: '상세 정보 추출',
          params: { model: 'gpt-4o', max_tokens: 2000, temperature: 0.2 },
        },
        {
          name: 'pid',
          label: 'P&ID 분석',
          description: 'P&ID 전용 분석',
          params: { model: 'gpt-4o', max_tokens: 2000, temperature: 0.2 },
        },
      ],
    },
    inputs: [
      {
        name: 'image',
        type: 'Image',
        description: '📄 분석할 도면 이미지',
      },
      {
        name: 'text',
        type: 'string',
        description: '❓ 질문 또는 분석 요청 (선택사항)',
      },
    ],
    outputs: [
      {
        name: 'mode',
        type: 'string',
        description: '🔍 분석 모드 (vqa: 질문-답변, captioning: 일반 설명)',
      },
      {
        name: 'answer',
        type: 'string',
        description: '💬 질문에 대한 답변 (VQA 모드)',
      },
      {
        name: 'caption',
        type: 'string',
        description: '📝 이미지 설명 (캡셔닝 모드)',
      },
      {
        name: 'confidence',
        type: 'number',
        description: '📊 답변 신뢰도 (0-1)',
      },
    ],
    parameters: [
      {
        name: 'model',
        type: 'select',
        default: 'claude-3-5-sonnet-20241022',
        options: ['claude-3-5-sonnet-20241022', 'gpt-4o', 'gpt-4-turbo'],
        description: 'Vision Language 모델 선택 (Claude: 정확/도면 특화, GPT-4o: 빠름)',
      },
      {
        name: 'temperature',
        type: 'number',
        default: 0.0,
        min: 0,
        max: 1,
        step: 0.1,
        description: '생성 다양성 (0=정확/일관성, 1=창의적/다양)',
      },
    ],
    examples: [
      'ImageInput + TextInput("치수 추출") → VL → 정확한 치수 정보',
      'ImageInput만 → VL → 일반적인 도면 설명',
      '용접 기호 찾기, 공차 정보 추출 등 특정 질문',
    ],
    usageTips: [
      '💡 TextInput과 함께 사용하면 훨씬 정확한 정보를 얻을 수 있습니다 (정확도 30% → 90%)',
      '💡 프롬프트 없이 사용 시: 일반 이미지 캡셔닝 모드',
      '💡 프롬프트와 함께 사용 시: 질문-답변(VQA) 모드로 자동 전환',
      '💡 "이 도면의 치수를 알려줘", "용접 기호를 모두 찾아줘" 같은 구체적 질문 가능',
      'Claude 모델은 도면 분석에 특화되어 있고, GPT-4o는 처리 속도가 빠릅니다',
    ],
    recommendedInputs: [
      {
        from: 'imageinput',
        field: 'image',
        reason: '분석할 도면 이미지를 제공합니다',
      },
      {
        from: 'textinput',
        field: 'text',
        reason: '⭐ 특정 질문이나 분석 요청을 전달하여 정확도를 크게 향상시킵니다',
      },
      {
        from: 'edgnet',
        field: 'segmented_image',
        reason: '선명하게 처리된 이미지에서 더 정확한 분석 결과를 얻을 수 있습니다',
      },
    ],
  },
};
