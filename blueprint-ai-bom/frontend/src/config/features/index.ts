/**
 * Features Module - Blueprint AI BOM
 *
 * web-ui/src/config/features와 동기화되어 있습니다.
 * 원본: /home/uproot/ax/poc/web-ui/src/config/features/
 */

export {
  FEATURE_DEFINITIONS,
  FEATURE_GROUPS,
  FEATURE_KEYS,
  IMPLEMENTATION_STATUS,
  getFeaturesByGroup,
  getGroupedFeatures,
  getRecommendedNodes,
  getGroupImplementationStats,
  getAllGroupsImplementationStats,
  formatImplementationCount,
  getImplementationStatusIcon,
  getImplementationStatusLabel,
  type FeatureDefinition,
  type FeatureGroup,
  type FeatureKey,
  type ImplementationStatus,
  type GroupImplementationStats,
} from './featureDefinitions';

// ============================================================
// Blueprint AI BOM 전용 헬퍼 (레거시 호환)
// ============================================================

import { FEATURE_DEFINITIONS } from './featureDefinitions';

export interface BadgeConfig {
  icon: string;
  label: string;
  bgClass: string;
  textClass: string;
}

/**
 * Feature 배지 설정 가져오기 (레거시 호환)
 */
export function getFeatureBadge(key: string): BadgeConfig | undefined {
  const feature = FEATURE_DEFINITIONS[key];
  if (!feature) return undefined;

  return {
    icon: feature.icon,
    label: feature.label,
    bgClass: feature.badgeBgClass,
    textClass: feature.badgeTextClass,
  };
}

/**
 * 유효한 feature 키인지 확인
 */
export function isValidFeatureKey(key: string): boolean {
  return key in FEATURE_DEFINITIONS;
}

/**
 * Feature 배지 설정 맵 (레거시 호환)
 */
export const FEATURE_BADGE_CONFIG: Record<string, BadgeConfig> = Object.fromEntries(
  Object.entries(FEATURE_DEFINITIONS).map(([key, def]) => [
    key,
    {
      icon: def.icon,
      label: def.label,
      bgClass: def.badgeBgClass,
      textClass: def.badgeTextClass,
    },
  ])
);
