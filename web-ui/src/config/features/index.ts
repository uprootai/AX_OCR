/**
 * Features Module - Single Source of Truth (SSOT)
 *
 * 모든 feature 관련 정의와 유틸리티를 export합니다.
 *
 * 사용 예시:
 * ```typescript
 * import {
 *   FEATURE_DEFINITIONS,
 *   FEATURE_GROUPS,
 *   toCheckboxGroupOptions,
 *   toBadgeConfig,
 *   getRecommendedNodes,
 * } from '@/config/features';
 * ```
 */

// Core definitions
export {
  FEATURE_DEFINITIONS,
  FEATURE_GROUPS,
  FEATURE_KEYS,
  getFeaturesByGroup,
  getGroupedFeatures,
  getRecommendedNodes,
  type FeatureDefinition,
  type FeatureGroup,
  type FeatureKey,
} from './featureDefinitions';

// Converters
export {
  toCheckboxGroupOptions,
  toBOMFeatures,
  toNodeRecommendations,
  toBadgeConfig,
  toBOMNodeOptions,
  isValidFeatureKey,
  filterValidFeatures,
  getFeatureInfo,
  type CheckboxGroupOption,
  type BOMFeatureEntry,
  type NodeRecommendation,
  type BadgeConfig,
  type BOMNodeOption,
} from './featureConverters';
