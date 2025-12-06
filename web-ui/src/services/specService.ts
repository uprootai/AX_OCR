/**
 * API Spec Service
 * Gateway의 /api/v1/specs 엔드포인트에서 API 스펙을 가져와
 * BlueprintFlow NodeDefinition으로 변환
 */

import type { NodeDefinition, NodeParameter, RecommendedInput } from '../config/nodeDefinitions';

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000';

export interface APISpec {
  apiVersion: string;
  kind: string;
  metadata: {
    id: string;
    name: string;
    version: string;
    port: number;
    description?: string;
    author?: string;
    tags?: string[];
  };
  server: {
    endpoint: string;
    method: string;
    contentType?: string;
    timeout?: number;
    healthEndpoint?: string;
  };
  blueprintflow: {
    category: string;
    color: string;
    icon: string;
    requiresImage?: boolean;
    recommendedInputs?: RecommendedInput[];
  };
  inputs?: {
    name: string;
    type: string;
    required?: boolean;
    description?: string;
  }[];
  outputs?: {
    name: string;
    type: string;
    description?: string;
  }[];
  parameters?: {
    name: string;
    type: string;
    default: any;
    min?: number;
    max?: number;
    step?: number;
    options?: string[];
    description?: string;
    required?: boolean;
  }[];
  mappings?: {
    input?: Record<string, string>;
    output?: Record<string, string>;
  };
  i18n?: {
    ko?: {
      label?: string;
      description?: string;
      parameters?: Record<string, string>;
    };
    en?: {
      label?: string;
      description?: string;
      parameters?: Record<string, string>;
    };
  };
  examples?: string[];
  usageTips?: string[];
}

/**
 * API 스펙을 NodeDefinition으로 변환
 */
export function specToNodeDefinition(spec: APISpec, lang: 'ko' | 'en' = 'ko'): NodeDefinition {
  const metadata = spec.metadata;
  const blueprintflow = spec.blueprintflow;
  const i18n = spec.i18n?.[lang] || spec.i18n?.['ko'] || {};

  // 카테고리 타입 매핑
  const categoryMap: Record<string, NodeDefinition['category']> = {
    input: 'input',
    detection: 'detection',
    ocr: 'ocr',
    segmentation: 'segmentation',
    preprocessing: 'preprocessing',
    analysis: 'analysis',
    knowledge: 'knowledge',
    ai: 'ai',
    control: 'control',
  };

  // 파라미터 변환
  const parameters: NodeParameter[] = (spec.parameters || []).map(param => ({
    name: param.name,
    type: param.type as NodeParameter['type'],
    default: param.default,
    min: param.min,
    max: param.max,
    step: param.step,
    options: param.options,
    description: i18n.parameters?.[param.name] || param.description || '',
  }));

  return {
    type: metadata.id,
    label: i18n.label || metadata.name,
    category: categoryMap[blueprintflow.category] || 'detection',
    color: blueprintflow.color,
    icon: blueprintflow.icon,
    description: i18n.description || metadata.description || '',
    inputs: (spec.inputs || []).map(input => ({
      name: input.name,
      type: input.type,
      description: input.description || '',
    })),
    outputs: (spec.outputs || []).map(output => ({
      name: output.name,
      type: output.type,
      description: output.description || '',
    })),
    parameters,
    examples: spec.examples || [],
    usageTips: spec.usageTips,
    recommendedInputs: blueprintflow.recommendedInputs,
  };
}

/**
 * 모든 API 스펙 가져오기
 */
export async function fetchAllSpecs(): Promise<Record<string, APISpec>> {
  try {
    const response = await fetch(`${GATEWAY_URL}/api/v1/specs`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return data.specs || {};
  } catch (error) {
    console.error('Failed to fetch API specs:', error);
    return {};
  }
}

/**
 * 특정 API 스펙 가져오기
 */
export async function fetchSpec(apiId: string): Promise<APISpec | null> {
  try {
    const response = await fetch(`${GATEWAY_URL}/api/v1/specs/${apiId}`);

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    return data.spec || null;
  } catch (error) {
    console.error(`Failed to fetch spec for ${apiId}:`, error);
    return null;
  }
}

/**
 * BlueprintFlow 노드 메타데이터 가져오기
 */
export async function fetchBlueprintFlowMeta(apiId: string): Promise<NodeDefinition | null> {
  try {
    const response = await fetch(`${GATEWAY_URL}/api/v1/specs/${apiId}/blueprintflow`);

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    const node = data.node;

    if (!node) return null;

    // 서버 응답을 NodeDefinition으로 변환
    return {
      type: node.type,
      label: node.label,
      category: node.category,
      color: node.color,
      icon: node.icon,
      description: node.description,
      inputs: node.inputs || [],
      outputs: node.outputs || [],
      parameters: node.parameters || [],
      examples: [],
      usageTips: [],
      recommendedInputs: [],
    };
  } catch (error) {
    console.error(`Failed to fetch blueprintflow meta for ${apiId}:`, error);
    return null;
  }
}

/**
 * 모든 API 스펙을 NodeDefinition으로 변환
 */
export async function fetchAllNodeDefinitions(lang: 'ko' | 'en' = 'ko'): Promise<Record<string, NodeDefinition>> {
  const specs = await fetchAllSpecs();
  const definitions: Record<string, NodeDefinition> = {};

  for (const [apiId, spec] of Object.entries(specs)) {
    try {
      definitions[apiId] = specToNodeDefinition(spec, lang);
    } catch (error) {
      console.error(`Failed to convert spec ${apiId}:`, error);
    }
  }

  return definitions;
}

/**
 * 로컬 nodeDefinitions와 동적 스펙 병합
 */
export async function mergeWithDynamicSpecs(
  staticDefinitions: Record<string, NodeDefinition>,
  lang: 'ko' | 'en' = 'ko'
): Promise<Record<string, NodeDefinition>> {
  const dynamicDefinitions = await fetchAllNodeDefinitions(lang);

  // 정적 정의가 우선 (수동으로 정의된 노드 유지)
  // 동적 스펙은 정적 정의가 없는 경우에만 추가
  return {
    ...dynamicDefinitions,
    ...staticDefinitions,
  };
}

export default {
  fetchAllSpecs,
  fetchSpec,
  fetchBlueprintFlowMeta,
  fetchAllNodeDefinitions,
  mergeWithDynamicSpecs,
  specToNodeDefinition,
};
