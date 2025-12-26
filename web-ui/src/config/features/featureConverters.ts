/**
 * Feature Converters
 *
 * FEATURE_DEFINITIONS를 각 컴포넌트에서 필요한 형식으로 변환하는 헬퍼 함수들
 */

import {
  FEATURE_DEFINITIONS,
  FEATURE_GROUPS,
  type FeatureDefinition,
  type FeatureGroup,
} from './featureDefinitions';

// ============================================================
// CheckboxGroup 옵션 형식 (NodeDetailPanel용)
// ============================================================

export interface CheckboxGroupOption {
  value: string;
  label: string;
  hint: string;
  icon: string;
  description: string;
  group: string;
}

/**
 * FEATURE_DEFINITIONS를 checkboxGroup options 형식으로 변환
 * @returns NodeDetailPanel의 checkboxGroup에서 사용하는 옵션 배열
 */
export function toCheckboxGroupOptions(): CheckboxGroupOption[] {
  const groupOrder: FeatureGroup[] = [
    FEATURE_GROUPS.BASIC_DETECTION,
    FEATURE_GROUPS.GDT_MECHANICAL,
    FEATURE_GROUPS.PID,
    FEATURE_GROUPS.BOM_GENERATION,
    FEATURE_GROUPS.LONG_TERM,
  ];

  const options: CheckboxGroupOption[] = [];

  for (const group of groupOrder) {
    const featuresInGroup = Object.values(FEATURE_DEFINITIONS).filter(
      (f) => f.group === group
    );

    for (const feature of featuresInGroup) {
      options.push({
        value: feature.key,
        label: feature.label,
        hint: feature.hint,
        icon: feature.icon,
        description: feature.description,
        group: feature.group,
      });
    }
  }

  return options;
}

// ============================================================
// BOM_FEATURES 형식 (레거시 호환)
// ============================================================

export interface BOMFeatureEntry {
  label: string;
  hint: string;
  icon: string;
}

/**
 * FEATURE_DEFINITIONS를 BOM_FEATURES 형식으로 변환
 * @returns { [key: string]: { label, hint, icon } }
 */
export function toBOMFeatures(): Record<string, BOMFeatureEntry> {
  const result: Record<string, BOMFeatureEntry> = {};

  for (const [key, feature] of Object.entries(FEATURE_DEFINITIONS)) {
    result[key] = {
      label: feature.label,
      hint: feature.hint,
      icon: feature.icon,
    };
  }

  return result;
}

// ============================================================
// FEATURE_NODE_RECOMMENDATIONS 형식 (레거시 호환)
// ============================================================

export interface NodeRecommendation {
  nodes: string[];
  description: string;
}

/**
 * FEATURE_DEFINITIONS를 FEATURE_NODE_RECOMMENDATIONS 형식으로 변환
 * @returns { [key: string]: { nodes, description } }
 */
export function toNodeRecommendations(): Record<string, NodeRecommendation> {
  const result: Record<string, NodeRecommendation> = {};

  for (const [key, feature] of Object.entries(FEATURE_DEFINITIONS)) {
    result[key] = {
      nodes: feature.recommendedNodes,
      description: feature.description,
    };
  }

  return result;
}

// ============================================================
// Badge Config 형식 (ActiveFeaturesSection용)
// ============================================================

export interface BadgeConfig {
  icon: string;
  label: string;
  bgClass: string;
  textClass: string;
}

/**
 * FEATURE_DEFINITIONS를 FEATURE_CONFIG (배지) 형식으로 변환
 * @returns { [key: string]: { icon, label, bgClass, textClass } }
 */
export function toBadgeConfig(): Record<string, BadgeConfig> {
  const result: Record<string, BadgeConfig> = {};

  for (const [key, feature] of Object.entries(FEATURE_DEFINITIONS)) {
    result[key] = {
      icon: feature.icon,
      label: feature.label,
      bgClass: feature.badgeBgClass,
      textClass: feature.badgeTextClass,
    };
  }

  return result;
}

// ============================================================
// bomNodes.ts용 옵션 형식
// ============================================================

export interface BOMNodeOption {
  value: string;
  label: string;
  icon: string;
  description: string;
  group: string;
}

/**
 * FEATURE_DEFINITIONS를 bomNodes.ts checkboxGroup 형식으로 변환
 * @returns bomNodes.ts의 features options에 사용하는 배열
 */
export function toBOMNodeOptions(): BOMNodeOption[] {
  const groupOrder: FeatureGroup[] = [
    FEATURE_GROUPS.BASIC_DETECTION,
    FEATURE_GROUPS.GDT_MECHANICAL,
    FEATURE_GROUPS.PID,
    FEATURE_GROUPS.BOM_GENERATION,
    FEATURE_GROUPS.LONG_TERM,
  ];

  const options: BOMNodeOption[] = [];

  for (const group of groupOrder) {
    const featuresInGroup = Object.values(FEATURE_DEFINITIONS).filter(
      (f) => f.group === group
    );

    for (const feature of featuresInGroup) {
      options.push({
        value: feature.key,
        label: `${feature.icon} ${feature.label}`,
        icon: feature.icon,
        description: feature.description,
        group: feature.group,
      });
    }
  }

  return options;
}

// ============================================================
// Feature 검증 유틸리티
// ============================================================

/**
 * 주어진 키가 유효한 feature인지 확인
 */
export function isValidFeatureKey(key: string): key is keyof typeof FEATURE_DEFINITIONS {
  return key in FEATURE_DEFINITIONS;
}

/**
 * 유효한 feature 키만 필터링
 */
export function filterValidFeatures(keys: string[]): string[] {
  return keys.filter(isValidFeatureKey);
}

/**
 * Feature 정보 가져오기 (없으면 undefined)
 */
export function getFeatureInfo(key: string): FeatureDefinition | undefined {
  return FEATURE_DEFINITIONS[key];
}
