/**
 * Feature Helpers
 *
 * 그룹별 조회, 추천 노드 계산, 구현 상태 통계, Feature 의존 관계 유틸리티
 */

import { FEATURE_GROUPS } from './types';
import type { FeatureGroup, FeatureDefinition, ImplementationStatus, GroupImplementationStats } from './types';
import { FEATURE_DEFINITIONS } from './definitions';

// ============================================================
// Helper: 그룹별 Features 가져오기
// ============================================================

export function getFeaturesByGroup(group: FeatureGroup): FeatureDefinition[] {
  return Object.values(FEATURE_DEFINITIONS).filter((f) => f.group === group);
}

export function getGroupedFeatures(): Record<FeatureGroup, FeatureDefinition[]> {
  const grouped: Record<string, FeatureDefinition[]> = {};
  for (const group of Object.values(FEATURE_GROUPS)) {
    grouped[group] = getFeaturesByGroup(group);
  }
  return grouped as Record<FeatureGroup, FeatureDefinition[]>;
}

// ============================================================
// Helper: 추천 노드 계산
// ============================================================

export function getRecommendedNodes(featureKeys: string[]): string[] {
  const nodes = new Set<string>();
  for (const key of featureKeys) {
    const feature = FEATURE_DEFINITIONS[key];
    if (feature) {
      feature.recommendedNodes.forEach((node) => nodes.add(node));
    }
  }
  return Array.from(nodes);
}

// ============================================================
// Helper: 그룹별 구현 상태 카운트
// ============================================================

/**
 * 그룹별 구현 상태 통계 계산
 */
export function getGroupImplementationStats(group: FeatureGroup): GroupImplementationStats {
  const features = getFeaturesByGroup(group);
  return {
    total: features.length,
    implemented: features.filter((f) => f.implementationStatus === 'implemented').length,
    partial: features.filter((f) => f.implementationStatus === 'partial').length,
    stub: features.filter((f) => f.implementationStatus === 'stub').length,
    planned: features.filter((f) => f.implementationStatus === 'planned').length,
  };
}

/**
 * 모든 그룹의 구현 상태 통계
 */
export function getAllGroupsImplementationStats(): Record<FeatureGroup, GroupImplementationStats> {
  const result: Record<string, GroupImplementationStats> = {};
  for (const group of Object.values(FEATURE_GROUPS)) {
    result[group] = getGroupImplementationStats(group);
  }
  return result as Record<FeatureGroup, GroupImplementationStats>;
}

/**
 * 구현 상태에 따른 표시 포맷
 * @param stats 그룹 통계
 * @returns "구현됨/전체" 형식의 문자열
 */
export function formatImplementationCount(stats: GroupImplementationStats): string {
  // implemented + partial을 "구현됨"으로 카운트
  const implementedCount = stats.implemented + stats.partial;
  return `${implementedCount}/${stats.total}`;
}

/**
 * 구현 상태에 따른 아이콘
 */
export function getImplementationStatusIcon(status: ImplementationStatus): string {
  switch (status) {
    case 'implemented':
      return '✅';
    case 'partial':
      return '🔶';
    case 'stub':
      return '📋';
    case 'planned':
      return '📅';
    default:
      return '❓';
  }
}

/**
 * 구현 상태에 따른 라벨
 */
export function getImplementationStatusLabel(status: ImplementationStatus): string {
  switch (status) {
    case 'implemented':
      return '완전 구현';
    case 'partial':
      return '부분 구현';
    case 'stub':
      return '스텁만';
    case 'planned':
      return '계획됨';
    default:
      return '알 수 없음';
  }
}

// ============================================================
// Helper: Feature Implication (자동 활성화)
// ============================================================

/**
 * 주어진 features에서 implied features를 재귀적으로 추가하여 반환
 * @param features 입력 features 배열
 * @returns 모든 implied features가 포함된 배열
 */
export function getImpliedFeatures(features: string[]): string[] {
  const result = new Set<string>(features);
  const processed = new Set<string>();

  function processFeature(featureKey: string): void {
    if (processed.has(featureKey)) return;
    processed.add(featureKey);

    const feature = FEATURE_DEFINITIONS[featureKey];
    if (feature?.implies) {
      for (const implied of feature.implies) {
        result.add(implied);
        processFeature(implied); // 재귀적으로 처리
      }
    }
  }

  for (const featureKey of features) {
    processFeature(featureKey);
  }

  return Array.from(result);
}

/**
 * 특정 feature가 활성화되어야 하는지 확인 (impliedBy 체크)
 * @param featureKey 확인할 feature 키
 * @param activeFeatures 현재 활성화된 features
 * @returns feature가 직접 또는 impliedBy로 활성화되어야 하면 true
 */
export function shouldFeatureBeActive(featureKey: string, activeFeatures: string[]): boolean {
  // 직접 활성화된 경우
  if (activeFeatures.includes(featureKey)) {
    return true;
  }

  // impliedBy로 활성화되는 경우
  const feature = FEATURE_DEFINITIONS[featureKey];
  if (feature?.impliedBy) {
    return feature.impliedBy.some((implier) => activeFeatures.includes(implier));
  }

  return false;
}

/**
 * 활성화된 features와 implied features를 모두 포함한 전체 활성 features 반환
 * @param features 직접 선택된 features
 * @returns 모든 활성 features (직접 선택 + implied)
 */
export function getAllActiveFeatures(features: string[]): string[] {
  return getImpliedFeatures(features);
}

// ============================================================
// Helper: Primary Features (사용자 선택 가능한 핵심 기능)
// ============================================================

/**
 * Primary features만 반환 (사용자가 직접 선택 가능한 핵심 기능)
 */
export function getPrimaryFeatures(): FeatureDefinition[] {
  return Object.values(FEATURE_DEFINITIONS).filter((f) => f.isPrimary === true);
}

/**
 * 그룹별 Primary features 반환
 */
export function getPrimaryFeaturesByGroup(): Record<FeatureGroup, FeatureDefinition[]> {
  const result: Record<string, FeatureDefinition[]> = {};
  for (const group of Object.values(FEATURE_GROUPS)) {
    result[group] = Object.values(FEATURE_DEFINITIONS).filter(
      (f) => f.group === group && f.isPrimary === true
    );
  }
  return result as Record<FeatureGroup, FeatureDefinition[]>;
}

/**
 * Feature 의존 관계 다이어그램 생성 (디버깅/문서화용)
 */
export function getFeatureRelationshipDiagram(): string {
  const lines: string[] = ['Feature Relationships:', ''];

  for (const [key, feature] of Object.entries(FEATURE_DEFINITIONS)) {
    if (feature.implies && feature.implies.length > 0) {
      lines.push(`${feature.isPrimary ? '🎯 ' : ''}${key}`);
      for (const implied of feature.implies) {
        lines.push(`  └─→ ${implied}`);
      }
      lines.push('');
    }
  }

  return lines.join('\n');
}
