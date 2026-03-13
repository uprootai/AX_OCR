/**
 * Feature Types & Constants
 *
 * Feature 그룹, 구현 상태, 타입 정의
 */

// ============================================================
// Feature Groups (그룹 정의)
// ============================================================

export const FEATURE_GROUPS = {
  BASIC_DETECTION: '기본 검출',
  GDT_MECHANICAL: 'GD&T / 기계',
  PID: 'P&ID',
  TECHCROSS: 'TECHCROSS BWMS',
  BOM_GENERATION: 'BOM 생성',
  LONG_TERM: '장기 로드맵',
} as const;

export type FeatureGroup = (typeof FEATURE_GROUPS)[keyof typeof FEATURE_GROUPS];

// ============================================================
// Implementation Status Type
// ============================================================

export const IMPLEMENTATION_STATUS = {
  IMPLEMENTED: 'implemented',
  PARTIAL: 'partial',
  STUB: 'stub',
  PLANNED: 'planned',
} as const;

export type ImplementationStatus = (typeof IMPLEMENTATION_STATUS)[keyof typeof IMPLEMENTATION_STATUS];

// ============================================================
// Feature Definition Type
// ============================================================

export interface FeatureDefinition {
  /** Feature 고유 키 */
  key: string;
  /** 표시 아이콘 (이모지) */
  icon: string;
  /** 표시 라벨 (한글) */
  label: string;
  /** 그룹 분류 */
  group: FeatureGroup;
  /** 힌트 텍스트 (노드 추천 등) */
  hint: string;
  /** 상세 설명 (툴팁) */
  description: string;
  /** 추천 노드 목록 */
  recommendedNodes: string[];
  /** 배지 배경색 (Tailwind 클래스) */
  badgeBgClass: string;
  /** 배지 텍스트색 (Tailwind 클래스) */
  badgeTextClass: string;
  /** 구현 상태: implemented, partial, stub, planned */
  implementationStatus: ImplementationStatus;
  /** 구현 위치 (라우터 파일 경로) */
  implementationLocation?: string;

  // === Feature 관계 정의 (자동 활성화) ===
  /**
   * 이 feature가 활성화되면 자동으로 함께 활성화되는 features
   * 예: symbol_detection → ['symbol_verification', 'gt_comparison']
   */
  implies?: string[];
  /**
   * 이 features 중 하나라도 있으면 현재 feature가 자동 활성화됨
   * 예: gt_comparison.impliedBy = ['symbol_detection']
   */
  impliedBy?: string[];
  /**
   * Primary feature 여부 (그룹의 핵심 기능, UI에서 선택 가능)
   * true인 feature만 사용자가 직접 선택, 나머지는 자동 활성화
   */
  isPrimary?: boolean;
}

// ============================================================
// Group Implementation Stats
// ============================================================

export interface GroupImplementationStats {
  total: number;
  implemented: number;
  partial: number;
  stub: number;
  planned: number;
}
