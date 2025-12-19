/**
 * Node Definition Types
 * BlueprintFlow 노드 정의를 위한 타입 인터페이스
 */

export interface NodeParameter {
  name: string;
  type: 'number' | 'string' | 'boolean' | 'select' | 'textarea';
  default: string | number | boolean;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
  description: string;
  placeholder?: string;
}

export interface RecommendedInput {
  from: string;
  field: string;
  reason: string;
}

export interface NodeDefinition {
  type: string;
  label: string;
  category: 'input' | 'bom' | 'detection' | 'ocr' | 'segmentation' | 'preprocessing' | 'analysis' | 'knowledge' | 'ai' | 'control';
  color: string;
  icon: string;
  description: string;
  deprecated?: boolean;
  deprecatedMessage?: string;
  inputs: {
    name: string;
    type: string;
    description: string;
    optional?: boolean;
  }[];
  outputs: {
    name: string;
    type: string;
    description: string;
  }[];
  parameters: NodeParameter[];
  examples: string[];
  usageTips?: string[];
  recommendedInputs?: RecommendedInput[];
}
