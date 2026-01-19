/**
 * Node Definition Types
 * BlueprintFlow 노드 정의를 위한 타입 인터페이스
 */

export interface SelectOption {
  value: string;
  label: string;
  description?: string;  // 개별 옵션 툴팁
  icon?: string;         // 옵션별 아이콘 (이모지 또는 lucide 아이콘명)
  disabled?: boolean;    // 옵션 비활성화 (Phase 2 기능 등)
}

export interface CheckboxOption {
  value: string;
  label: string;
  hint?: string;        // 힌트 텍스트 (예: "YOLO 노드 필요")
  icon?: string;        // 이모지 아이콘
  description?: string; // 마우스 hover 시 표시되는 상세 설명
  group?: string;       // 옵션 그룹화 (예: "기본 검출", "GD&T / 기계")
  /** 구현 상태: implemented, partial, stub, planned */
  implementationStatus?: 'implemented' | 'partial' | 'stub' | 'planned';
  /** 구현 위치 (파일 경로) */
  implementationLocation?: string;
}

export interface NodeParameter {
  name: string;
  type: 'number' | 'string' | 'boolean' | 'select' | 'textarea' | 'multiselect' | 'checkboxGroup';
  default: string | number | boolean | string[];  // multiselect, checkboxGroup은 string[] 기본값
  min?: number;
  max?: number;
  step?: number;
  options?: string[] | SelectOption[] | CheckboxOption[];  // 단순 문자열, 상세 옵션 또는 체크박스 옵션
  linkedTo?: string;  // 다른 파라미터와 연동 (예: drawing_type → features 자동 업데이트)
  description: string;
  placeholder?: string;
  tooltip?: string;  // 파라미터 전체에 대한 상세 툴팁
}

export interface RecommendedInput {
  from: string;
  field: string;
  reason: string;
}

/**
 * 프로파일 정의
 * API 스펙의 profiles 섹션과 동기화
 */
export interface ProfileDefinition {
  name: string;
  label: string;
  description: string;
  params: Record<string, string | number | boolean>;
}

export interface ProfilesConfig {
  default: string;
  available: ProfileDefinition[];
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
  /** 프로파일 기반 기본값 (MODEL_DEFAULTS 패턴) */
  profiles?: ProfilesConfig;
}
