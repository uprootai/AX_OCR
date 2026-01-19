/**
 * Feature Definitions 테스트
 *
 * Feature Implication 시스템과 헬퍼 함수들 테스트
 */

import { describe, it, expect } from 'vitest';
import {
  FEATURE_DEFINITIONS,
  FEATURE_GROUPS,
  FEATURE_KEYS,
  getFeaturesByGroup,
  getGroupedFeatures,
  getRecommendedNodes,
  getGroupImplementationStats,
  getAllGroupsImplementationStats,
  // Feature Implication
  getImpliedFeatures,
  shouldFeatureBeActive,
  getAllActiveFeatures,
  getPrimaryFeatures,
  getPrimaryFeaturesByGroup,
  getFeatureRelationshipDiagram,
} from './featureDefinitions';

describe('featureDefinitions', () => {
  describe('FEATURE_DEFINITIONS', () => {
    it('should have all required properties for each feature', () => {
      for (const [key, feature] of Object.entries(FEATURE_DEFINITIONS)) {
        expect(feature.key).toBe(key);
        expect(feature.icon).toBeDefined();
        expect(feature.label).toBeDefined();
        expect(feature.group).toBeDefined();
        expect(feature.description).toBeDefined();
        expect(feature.recommendedNodes).toBeInstanceOf(Array);
        expect(feature.implementationStatus).toBeDefined();
      }
    });

    it('should have valid groups for all features', () => {
      const validGroups = Object.values(FEATURE_GROUPS);
      for (const feature of Object.values(FEATURE_DEFINITIONS)) {
        expect(validGroups).toContain(feature.group);
      }
    });

    it('should have valid implementation statuses', () => {
      const validStatuses = ['implemented', 'partial', 'stub', 'planned'];
      for (const feature of Object.values(FEATURE_DEFINITIONS)) {
        expect(validStatuses).toContain(feature.implementationStatus);
      }
    });
  });

  describe('FEATURE_KEYS', () => {
    it('should contain all feature keys', () => {
      expect(FEATURE_KEYS.length).toBe(Object.keys(FEATURE_DEFINITIONS).length);
      for (const key of FEATURE_KEYS) {
        expect(FEATURE_DEFINITIONS[key]).toBeDefined();
      }
    });
  });

  describe('getFeaturesByGroup', () => {
    it('should return features for a valid group', () => {
      const basicDetection = getFeaturesByGroup(FEATURE_GROUPS.BASIC_DETECTION);
      expect(basicDetection.length).toBeGreaterThan(0);
      expect(basicDetection.every((f) => f.group === FEATURE_GROUPS.BASIC_DETECTION)).toBe(true);
    });

    it('should return empty array for invalid group', () => {
      const invalid = getFeaturesByGroup('invalid_group' as typeof FEATURE_GROUPS.BASIC_DETECTION);
      expect(invalid).toEqual([]);
    });
  });

  describe('getGroupedFeatures', () => {
    it('should return features grouped by all groups', () => {
      const grouped = getGroupedFeatures();
      for (const group of Object.values(FEATURE_GROUPS)) {
        expect(grouped[group]).toBeDefined();
        expect(grouped[group]).toBeInstanceOf(Array);
      }
    });
  });

  describe('getRecommendedNodes', () => {
    it('should return unique recommended nodes', () => {
      const nodes = getRecommendedNodes(['symbol_detection', 'dimension_ocr']);
      expect(nodes).toContain('yolo');
      expect(nodes).toContain('edocr2');
      // Check uniqueness
      expect(nodes.length).toBe(new Set(nodes).size);
    });

    it('should return empty array for unknown features', () => {
      const nodes = getRecommendedNodes(['unknown_feature']);
      expect(nodes).toEqual([]);
    });
  });
});

describe('Feature Implication System', () => {
  describe('implies and impliedBy consistency', () => {
    it('all implies relations should have matching impliedBy', () => {
      for (const [key, feature] of Object.entries(FEATURE_DEFINITIONS)) {
        if (feature.implies) {
          for (const implied of feature.implies) {
            const impliedFeature = FEATURE_DEFINITIONS[implied];
            expect(impliedFeature).toBeDefined();
            expect(impliedFeature.impliedBy).toBeDefined();
            expect(impliedFeature.impliedBy).toContain(key);
          }
        }
      }
    });

    it('all impliedBy relations should have matching implies', () => {
      for (const [key, feature] of Object.entries(FEATURE_DEFINITIONS)) {
        if (feature.impliedBy) {
          for (const implier of feature.impliedBy) {
            const implierFeature = FEATURE_DEFINITIONS[implier];
            expect(implierFeature).toBeDefined();
            expect(implierFeature.implies).toBeDefined();
            expect(implierFeature.implies).toContain(key);
          }
        }
      }
    });
  });

  describe('getImpliedFeatures', () => {
    it('symbol_detection should imply symbol_verification and gt_comparison', () => {
      const implied = getImpliedFeatures(['symbol_detection']);
      expect(implied).toContain('symbol_detection');
      expect(implied).toContain('symbol_verification');
      expect(implied).toContain('gt_comparison');
    });

    it('dimension_ocr should imply dimension_verification', () => {
      const implied = getImpliedFeatures(['dimension_ocr']);
      expect(implied).toContain('dimension_ocr');
      expect(implied).toContain('dimension_verification');
    });

    it('pid_connectivity should imply all TECHCROSS features', () => {
      const implied = getImpliedFeatures(['pid_connectivity']);
      expect(implied).toContain('pid_connectivity');
      expect(implied).toContain('techcross_valve_signal');
      expect(implied).toContain('techcross_equipment');
      expect(implied).toContain('techcross_checklist');
      expect(implied).toContain('techcross_deviation');
    });

    it('industry_equipment_detection should imply equipment_list_export', () => {
      const implied = getImpliedFeatures(['industry_equipment_detection']);
      expect(implied).toContain('industry_equipment_detection');
      expect(implied).toContain('equipment_list_export');
    });

    it('should not duplicate features', () => {
      const implied = getImpliedFeatures(['symbol_detection', 'symbol_verification']);
      const unique = new Set(implied);
      expect(implied.length).toBe(unique.size);
    });

    it('should return original features if no implications', () => {
      const implied = getImpliedFeatures(['gdt_parsing']);
      expect(implied).toContain('gdt_parsing');
      expect(implied.length).toBe(1);
    });

    it('should handle empty array', () => {
      const implied = getImpliedFeatures([]);
      expect(implied).toEqual([]);
    });
  });

  describe('shouldFeatureBeActive', () => {
    it('should return true for directly activated feature', () => {
      expect(shouldFeatureBeActive('symbol_detection', ['symbol_detection'])).toBe(true);
    });

    it('should return true for impliedBy feature', () => {
      expect(shouldFeatureBeActive('symbol_verification', ['symbol_detection'])).toBe(true);
      expect(shouldFeatureBeActive('gt_comparison', ['symbol_detection'])).toBe(true);
    });

    it('should return false for non-activated feature', () => {
      expect(shouldFeatureBeActive('symbol_detection', ['dimension_ocr'])).toBe(false);
    });

    it('should return false for feature without impliedBy when implier not present', () => {
      expect(shouldFeatureBeActive('symbol_verification', ['dimension_ocr'])).toBe(false);
    });
  });

  describe('getAllActiveFeatures', () => {
    it('should return all active features including implied', () => {
      const active = getAllActiveFeatures(['symbol_detection', 'dimension_ocr']);
      expect(active).toContain('symbol_detection');
      expect(active).toContain('symbol_verification');
      expect(active).toContain('gt_comparison');
      expect(active).toContain('dimension_ocr');
      expect(active).toContain('dimension_verification');
    });
  });
});

describe('Primary Features', () => {
  describe('getPrimaryFeatures', () => {
    it('should return only features with isPrimary=true', () => {
      const primary = getPrimaryFeatures();
      expect(primary.length).toBeGreaterThan(0);
      expect(primary.every((f) => f.isPrimary === true)).toBe(true);
    });

    it('should include known primary features', () => {
      const primary = getPrimaryFeatures();
      const keys = primary.map((f) => f.key);
      expect(keys).toContain('symbol_detection');
      expect(keys).toContain('dimension_ocr');
      expect(keys).toContain('pid_connectivity');
      expect(keys).toContain('bom_generation');
    });
  });

  describe('getPrimaryFeaturesByGroup', () => {
    it('should return primary features grouped by group', () => {
      const grouped = getPrimaryFeaturesByGroup();
      for (const group of Object.values(FEATURE_GROUPS)) {
        expect(grouped[group]).toBeDefined();
        expect(grouped[group]).toBeInstanceOf(Array);
        expect(grouped[group].every((f) => f.isPrimary === true && f.group === group)).toBe(true);
      }
    });
  });
});

describe('Implementation Stats', () => {
  describe('getGroupImplementationStats', () => {
    it('should return valid stats for a group', () => {
      const stats = getGroupImplementationStats(FEATURE_GROUPS.BASIC_DETECTION);
      expect(stats.total).toBeGreaterThan(0);
      expect(stats.implemented + stats.partial + stats.stub + stats.planned).toBe(stats.total);
    });
  });

  describe('getAllGroupsImplementationStats', () => {
    it('should return stats for all groups', () => {
      const allStats = getAllGroupsImplementationStats();
      for (const group of Object.values(FEATURE_GROUPS)) {
        expect(allStats[group]).toBeDefined();
        expect(allStats[group].total).toBeGreaterThan(0);
      }
    });
  });
});

describe('getFeatureRelationshipDiagram', () => {
  it('should return a non-empty string diagram', () => {
    const diagram = getFeatureRelationshipDiagram();
    expect(diagram).toBeDefined();
    expect(diagram.length).toBeGreaterThan(0);
    expect(diagram).toContain('Feature Relationships:');
    expect(diagram).toContain('symbol_detection');
  });
});
