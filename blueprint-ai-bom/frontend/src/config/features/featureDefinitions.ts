/**
 * Feature Definitions - Single Source of Truth (SSOT)
 *
 * ⚠️ 동기화 필요: 이 파일은 web-ui/src/config/features/featureDefinitions.ts의 미러 복사본입니다.
 * 원본 파일이 수정되면 이 파일도 동일하게 업데이트해야 합니다.
 *
 * 원본 위치: /home/uproot/ax/poc/web-ui/src/config/features/featureDefinitions.ts
 * 마지막 동기화: 2025-12-26
 *
 * @see ActiveFeaturesSection.tsx - 배지 표시에 사용
 */

// ============================================================
// Feature Groups
// ============================================================

export const FEATURE_GROUPS = {
  BASIC_DETECTION: '기본 검출',
  GDT_MECHANICAL: 'GD&T / 기계',
  PID: 'P&ID',
  BOM_GENERATION: 'BOM 생성',
  LONG_TERM: '장기 로드맵',
} as const;

export type FeatureGroup = (typeof FEATURE_GROUPS)[keyof typeof FEATURE_GROUPS];

// ============================================================
// Badge Config Type (ActiveFeaturesSection용)
// ============================================================

export interface BadgeConfig {
  icon: string;
  label: string;
  bgClass: string;
  textClass: string;
}

// ============================================================
// Feature Badge Configs (FEATURE_CONFIG 대체)
// ============================================================

export const FEATURE_BADGE_CONFIG: Record<string, BadgeConfig> = {
  // === 기본 검출 ===
  symbol_detection: {
    icon: '🎯',
    label: '심볼 검출',
    bgClass: 'bg-purple-100 dark:bg-purple-900/30',
    textClass: 'text-purple-700 dark:text-purple-300',
  },
  symbol_verification: {
    icon: '✅',
    label: '심볼 검증',
    bgClass: 'bg-green-100 dark:bg-green-900/30',
    textClass: 'text-green-700 dark:text-green-300',
  },
  dimension_ocr: {
    icon: '📏',
    label: '치수 OCR',
    bgClass: 'bg-blue-100 dark:bg-blue-900/30',
    textClass: 'text-blue-700 dark:text-blue-300',
  },
  dimension_verification: {
    icon: '✅',
    label: '치수 검증',
    bgClass: 'bg-teal-100 dark:bg-teal-900/30',
    textClass: 'text-teal-700 dark:text-teal-300',
  },
  gt_comparison: {
    icon: '📊',
    label: 'GT 비교',
    bgClass: 'bg-orange-100 dark:bg-orange-900/30',
    textClass: 'text-orange-700 dark:text-orange-300',
  },

  // === GD&T / 기계 ===
  gdt_parsing: {
    icon: '🔧',
    label: 'GD&T 파싱',
    bgClass: 'bg-indigo-100 dark:bg-indigo-900/30',
    textClass: 'text-indigo-700 dark:text-indigo-300',
  },
  line_detection: {
    icon: '📐',
    label: '선 검출',
    bgClass: 'bg-cyan-100 dark:bg-cyan-900/30',
    textClass: 'text-cyan-700 dark:text-cyan-300',
  },
  relation_extraction: {
    icon: '🔗',
    label: '심볼-치수 관계',
    bgClass: 'bg-violet-100 dark:bg-violet-900/30',
    textClass: 'text-violet-700 dark:text-violet-300',
  },
  welding_symbol_parsing: {
    icon: '⚡',
    label: '용접 기호 파싱',
    bgClass: 'bg-red-100 dark:bg-red-900/30',
    textClass: 'text-red-700 dark:text-red-300',
  },
  surface_roughness_parsing: {
    icon: '🔲',
    label: '표면 거칠기 파싱',
    bgClass: 'bg-stone-100 dark:bg-stone-900/30',
    textClass: 'text-stone-700 dark:text-stone-300',
  },

  // === P&ID ===
  pid_connectivity: {
    icon: '🔀',
    label: 'P&ID 연결성',
    bgClass: 'bg-rose-100 dark:bg-rose-900/30',
    textClass: 'text-rose-700 dark:text-rose-300',
  },

  // === BOM 생성 ===
  bom_generation: {
    icon: '📋',
    label: 'BOM 생성',
    bgClass: 'bg-amber-100 dark:bg-amber-900/30',
    textClass: 'text-amber-700 dark:text-amber-300',
  },
  title_block_ocr: {
    icon: '📝',
    label: '표제란 OCR',
    bgClass: 'bg-slate-100 dark:bg-slate-900/30',
    textClass: 'text-slate-700 dark:text-slate-300',
  },
  quantity_extraction: {
    icon: '🔢',
    label: '수량 추출',
    bgClass: 'bg-emerald-100 dark:bg-emerald-900/30',
    textClass: 'text-emerald-700 dark:text-emerald-300',
  },
  balloon_matching: {
    icon: '🎈',
    label: '벌룬 매칭',
    bgClass: 'bg-pink-100 dark:bg-pink-900/30',
    textClass: 'text-pink-700 dark:text-pink-300',
  },

  // === 장기 로드맵 ===
  drawing_region_segmentation: {
    icon: '🗺️',
    label: '영역 세분화',
    bgClass: 'bg-sky-100 dark:bg-sky-900/30',
    textClass: 'text-sky-700 dark:text-sky-300',
  },
  notes_extraction: {
    icon: '📋',
    label: '노트 추출',
    bgClass: 'bg-lime-100 dark:bg-lime-900/30',
    textClass: 'text-lime-700 dark:text-lime-300',
  },
  revision_comparison: {
    icon: '🔄',
    label: '리비전 비교',
    bgClass: 'bg-fuchsia-100 dark:bg-fuchsia-900/30',
    textClass: 'text-fuchsia-700 dark:text-fuchsia-300',
  },
  vlm_auto_classification: {
    icon: '🤖',
    label: 'VLM 자동 분류',
    bgClass: 'bg-yellow-100 dark:bg-yellow-900/30',
    textClass: 'text-yellow-700 dark:text-yellow-300',
  },
};

// ============================================================
// Helper Functions
// ============================================================

/**
 * 주어진 키가 유효한 feature인지 확인
 */
export function isValidFeatureKey(
  key: string
): key is keyof typeof FEATURE_BADGE_CONFIG {
  return key in FEATURE_BADGE_CONFIG;
}

/**
 * Feature 배지 설정 가져오기 (없으면 undefined)
 */
export function getFeatureBadge(key: string): BadgeConfig | undefined {
  return FEATURE_BADGE_CONFIG[key];
}

/**
 * 모든 feature 키 목록
 */
export const FEATURE_KEYS = Object.keys(
  FEATURE_BADGE_CONFIG
) as (keyof typeof FEATURE_BADGE_CONFIG)[];
