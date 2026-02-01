/**
 * Section Configuration
 * features 배열 기반 섹션 가시성 설정
 *
 * 2025-12-26: drawing_type 기반 로직 제거, features만 사용
 * 2025-12-30: Feature 의존성 검증 및 이름 호환성 추가
 * 2026-01-04: Feature Implication 시스템 추가 (implies/impliedBy)
 */

import type { SectionVisibility } from '../types/workflow';

// 기본 기능 (features가 비어있을 때 사용)
const DEFAULT_FEATURES = ['symbol_detection', 'title_block_ocr', 'vlm_auto_classification', 'dimension_ocr'];

// ============================================================
// Feature Implication (자동 활성화)
// key: 트리거 feature, value: 자동 활성화되는 features
// ============================================================
export const FEATURE_IMPLICATIONS: Record<string, string[]> = {
  // 심볼 검출 → 검증, GT비교 자동 활성화
  symbol_detection: ['symbol_verification', 'gt_comparison'],
  // 치수 OCR → 치수 검증 자동 활성화
  dimension_ocr: ['dimension_verification'],
  // P&ID 연결성 → TECHCROSS 기능들 자동 활성화
  pid_connectivity: ['techcross_valve_signal', 'techcross_equipment', 'techcross_checklist', 'techcross_deviation'],
  // 장비 태그 인식 → 장비 목록 내보내기 자동 활성화
  industry_equipment_detection: ['equipment_list_export'],
};

// 역방향 매핑: impliedBy (어떤 feature에 의해 활성화되는지)
export const FEATURE_IMPLIED_BY: Record<string, string[]> = {
  symbol_verification: ['symbol_detection'],
  gt_comparison: ['symbol_detection'],
  dimension_verification: ['dimension_ocr'],
  techcross_valve_signal: ['pid_connectivity'],
  techcross_equipment: ['pid_connectivity'],
  techcross_checklist: ['pid_connectivity'],
  techcross_deviation: ['pid_connectivity'],
  equipment_list_export: ['industry_equipment_detection'],
};

// 모든 기능 비활성화 기본값 (외부에서 사용 가능)
export const ALL_FEATURES_DISABLED: SectionVisibility = {
  symbolDetection: false,
  dimensionOCR: false,
  lineDetection: false,
  gdtParsing: false,
  relationExtraction: false,
  pidConnectivity: false,
  titleBlockOcr: false,
  weldingSymbolParsing: false,
  surfaceRoughnessParsing: false,
  quantityExtraction: false,
  balloonMatching: false,
  drawingRegionSegmentation: false,
  notesExtraction: false,
  revisionComparison: false,
  vlmAutoClassification: false,
  // BWMS P&ID
  valveSignalList: false,
  equipmentList: false,
  bwmsChecklist: false,
  deviationList: false,
  // 추가 기능 (2025-12-31 P1 매핑 완성)
  gtComparison: false,
  bomGeneration: false,
  industryEquipmentDetection: false,
};

/**
 * Feature 의존성 정의
 * key: feature ID, value: 필수 의존 feature 목록
 *
 * 2025-12-30: P2 일관성 작업 - 누락된 의존성 추가
 */
export const FEATURE_DEPENDENCIES: Record<string, { requires?: string[]; requiresAtLeastOne?: string[] }> = {
  // === 기본 검출 ===
  // 검증 기능은 검출 기능 필요
  symbol_verification: { requires: ['symbol_detection'] },
  dimension_verification: { requires: ['dimension_ocr'] },

  // GT 비교는 심볼 검출 필요 (검출 결과와 정답 비교)
  gt_comparison: { requires: ['symbol_detection'] },

  // === GD&T/기계 ===
  // GD&T/기계 기능은 심볼 검출 필요
  gdt_parsing: { requires: ['symbol_detection'] },
  welding_symbol_parsing: { requires: ['symbol_detection'] },
  surface_roughness_parsing: { requires: ['symbol_detection'] },

  // 관계 추출은 심볼+치수 필요
  relation_extraction: { requires: ['symbol_detection', 'dimension_ocr'] },

  // === P&ID ===
  // P&ID 연결성은 라인 검출 권장
  pid_connectivity: { requiresAtLeastOne: ['line_detection', 'symbol_detection'] },

  // 산업 장비 태그 인식: 심볼 검출 또는 P&ID 연결성 필요
  industry_equipment_detection: { requiresAtLeastOne: ['symbol_detection', 'pid_connectivity'] },

  // 장비 목록 내보내기: 장비 검출 필요
  equipment_list_export: { requires: ['industry_equipment_detection'] },

  // P&ID 분석 기능은 연결성 또는 심볼 검출 필요
  pid_valve_detection: { requiresAtLeastOne: ['pid_connectivity', 'symbol_detection'] },
  pid_equipment_detection: { requiresAtLeastOne: ['pid_connectivity', 'symbol_detection'] },
  pid_design_checklist: { requiresAtLeastOne: ['pid_connectivity', 'symbol_detection'] },
  pid_deviation_analysis: { requiresAtLeastOne: ['pid_connectivity', 'symbol_detection'] },

  // TECHCROSS 별칭 (web-ui 호환성)
  techcross_valve_signal: { requiresAtLeastOne: ['pid_connectivity', 'symbol_detection'] },
  techcross_equipment: { requiresAtLeastOne: ['pid_connectivity', 'symbol_detection'] },
  techcross_checklist: { requiresAtLeastOne: ['pid_connectivity', 'symbol_detection'] },
  techcross_deviation: { requiresAtLeastOne: ['pid_connectivity', 'symbol_detection'] },

  // === BOM 생성 ===
  // BOM 생성: 심볼 검출 필요 (치수 OCR은 선택)
  bom_generation: { requires: ['symbol_detection'] },

  // 벌룬 매칭은 심볼+치수 필요
  balloon_matching: { requires: ['symbol_detection', 'dimension_ocr'] },

  // 수량 추출: 치수 OCR 필요 (수량 텍스트 인식)
  quantity_extraction: { requires: ['dimension_ocr'] },
};

/**
 * Feature 이름 별칭 매핑 (web-ui ↔ blueprint-ai-bom 호환성)
 */
const FEATURE_ALIASES: Record<string, string> = {
  // TECHCROSS (web-ui) → pid_* (blueprint-ai-bom)
  techcross_valve_signal: 'pid_valve_detection',
  techcross_equipment: 'pid_equipment_detection',
  techcross_checklist: 'pid_design_checklist',
  techcross_deviation: 'pid_deviation_analysis',
};

/**
 * Feature 의존성 검증 결과
 */
export interface DependencyValidationResult {
  valid: boolean;
  warnings: Array<{
    feature: string;
    message: string;
    missingDependencies: string[];
  }>;
}

/**
 * Feature 의존성 검증
 */
export const validateFeatureDependencies = (features: string[]): DependencyValidationResult => {
  const normalizedFeatures = normalizeFeatures(features);
  const warnings: DependencyValidationResult['warnings'] = [];

  for (const feature of features) {
    const deps = FEATURE_DEPENDENCIES[feature];
    if (!deps) continue;

    // requires: 모든 의존성이 필요
    if (deps.requires) {
      const missing = deps.requires.filter(dep => !normalizedFeatures.includes(dep));
      if (missing.length > 0) {
        warnings.push({
          feature,
          message: `"${feature}" 기능은 다음 기능이 필요합니다: ${missing.join(', ')}`,
          missingDependencies: missing,
        });
      }
    }

    // requiresAtLeastOne: 하나 이상 필요
    if (deps.requiresAtLeastOne) {
      const hasAny = deps.requiresAtLeastOne.some(dep => normalizedFeatures.includes(dep));
      if (!hasAny) {
        warnings.push({
          feature,
          message: `"${feature}" 기능은 다음 중 하나 이상이 필요합니다: ${deps.requiresAtLeastOne.join(', ')}`,
          missingDependencies: deps.requiresAtLeastOne,
        });
      }
    }
  }

  return {
    valid: warnings.length === 0,
    warnings,
  };
};

/**
 * Feature 이름 정규화 (별칭 → 표준 이름)
 */
const normalizeFeatures = (features: string[]): string[] => {
  return features.map(f => FEATURE_ALIASES[f] || f);
};

/**
 * features 배열을 SectionVisibility 객체로 변환
 * web-ui와 blueprint-ai-bom 양쪽 이름 모두 지원
 *
 * 2026-01-04: impliedBy 체크 추가 - 트리거 feature가 있으면 자동 활성화
 */
const featuresToVisibility = (features: string[]): SectionVisibility => {
  const normalized = normalizeFeatures(features);

  /**
   * Feature 활성 여부 확인 (직접 선택 OR impliedBy로 자동 활성화)
   */
  const hasFeature = (key: string): boolean => {
    // 1. 직접 활성화된 경우
    if (normalized.includes(key) || features.includes(key)) {
      return true;
    }

    // 2. impliedBy로 자동 활성화되는 경우
    const impliers = FEATURE_IMPLIED_BY[key];
    if (impliers) {
      return impliers.some(implier =>
        normalized.includes(implier) || features.includes(implier)
      );
    }

    return false;
  };

  return {
    symbolDetection: hasFeature('symbol_detection'),
    dimensionOCR: hasFeature('dimension_ocr'),
    lineDetection: hasFeature('line_detection'),
    gdtParsing: hasFeature('gdt_parsing'),
    relationExtraction: hasFeature('relation_extraction'),
    pidConnectivity: hasFeature('pid_connectivity'),
    titleBlockOcr: hasFeature('title_block_ocr'),
    weldingSymbolParsing: hasFeature('welding_symbol_parsing'),
    surfaceRoughnessParsing: hasFeature('surface_roughness_parsing'),
    quantityExtraction: hasFeature('quantity_extraction'),
    balloonMatching: hasFeature('balloon_matching'),
    drawingRegionSegmentation: hasFeature('drawing_region_segmentation'),
    notesExtraction: hasFeature('notes_extraction'),
    revisionComparison: hasFeature('revision_comparison'),
    vlmAutoClassification: hasFeature('vlm_auto_classification'),
    // P&ID 분석 기능: pid_* 또는 techcross_* 모두 지원
    valveSignalList: hasFeature('pid_valve_detection') || features.includes('techcross_valve_signal'),
    equipmentList: hasFeature('pid_equipment_detection') || features.includes('techcross_equipment'),
    bwmsChecklist: hasFeature('pid_design_checklist') || features.includes('techcross_checklist'),
    deviationList: hasFeature('pid_deviation_analysis') || features.includes('techcross_deviation'),
    // 추가 기능 (2025-12-31 P1 매핑 완성)
    gtComparison: hasFeature('gt_comparison'),
    bomGeneration: hasFeature('bom_generation'),
    industryEquipmentDetection: hasFeature('industry_equipment_detection'),
  };
};

/**
 * 섹션 가시성 헬퍼 함수
 * features 배열 기반으로 가시성 결정 (drawing_type 미사용)
 *
 * @param _drawingType - 더 이상 사용하지 않음 (하위 호환성 유지)
 * @param features - 활성화된 기능 목록
 */
export const getSectionVisibility = (
  _drawingType?: string,
  features?: string[]
): SectionVisibility => {
  // features가 제공된 경우 features 기반 가시성 사용
  if (features && features.length > 0) {
    return featuresToVisibility(features);
  }

  // features가 비어있으면 기본 기능만 활성화
  return featuresToVisibility(DEFAULT_FEATURES);
};

/**
 * 모든 기능 목록 (UI에서 기능 선택 시 사용)
 */
export const ALL_AVAILABLE_FEATURES = [
  // 기본 검출
  { id: 'symbol_detection', label: '🎯 심볼 검출', group: '기본 검출' },
  { id: 'dimension_ocr', label: '📏 치수 OCR', group: '기본 검출' },
  { id: 'line_detection', label: '📐 선 검출', group: '기본 검출' },
  { id: 'gt_comparison', label: '📊 GT 비교', group: '기본 검출' },
  // GD&T / 기계
  { id: 'gdt_parsing', label: '🔧 GD&T 파싱', group: 'GD&T / 기계' },
  { id: 'relation_extraction', label: '🔗 심볼-치수 관계', group: 'GD&T / 기계' },
  { id: 'welding_symbol_parsing', label: '⚡ 용접 기호 파싱', group: 'GD&T / 기계' },
  { id: 'surface_roughness_parsing', label: '🔲 표면 거칠기 파싱', group: 'GD&T / 기계' },
  // P&ID
  { id: 'pid_connectivity', label: '🔀 P&ID 연결성', group: 'P&ID' },
  { id: 'industry_equipment_detection', label: '🏭 장비 태그 인식', group: 'P&ID' },
  // P&ID 분석
  { id: 'pid_valve_detection', label: '🎛️ 밸브 검출', group: 'P&ID 분석' },
  { id: 'pid_equipment_detection', label: '⚙️ 장비 검출', group: 'P&ID 분석' },
  { id: 'pid_design_checklist', label: '✅ 설계 체크리스트', group: 'P&ID 분석' },
  { id: 'pid_deviation_analysis', label: '📝 편차 분석', group: 'P&ID 분석' },
  // BOM 생성
  { id: 'bom_generation', label: '📋 BOM 생성', group: 'BOM 생성' },
  { id: 'title_block_ocr', label: '📝 표제란 OCR', group: 'BOM 생성' },
  { id: 'quantity_extraction', label: '🔢 수량 추출', group: 'BOM 생성' },
  { id: 'balloon_matching', label: '🎈 벌룬 매칭', group: 'BOM 생성' },
  // 장기 로드맵
  { id: 'drawing_region_segmentation', label: '🗺️ 영역 세분화', group: '장기 로드맵' },
  { id: 'notes_extraction', label: '📋 노트 추출', group: '장기 로드맵' },
  { id: 'revision_comparison', label: '🔄 리비전 비교', group: '장기 로드맵' },
  { id: 'vlm_auto_classification', label: '🤖 VLM 자동 분류', group: '장기 로드맵' },
] as const;

// 하위 호환성을 위해 빈 객체 export (더 이상 사용하지 않음)
export const DRAWING_TYPE_SECTIONS: Record<string, SectionVisibility> = {};

// 페이지당 아이템 수
export const ITEMS_PER_PAGE = 7;
