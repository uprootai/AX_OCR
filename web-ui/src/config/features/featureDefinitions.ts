/**
 * Feature Definitions - Single Source of Truth (SSOT)
 *
 * 이 파일은 모든 features의 정의를 담고 있는 유일한 소스입니다.
 * 다른 파일들은 이 정의를 import하여 사용합니다.
 *
 * 새 feature 추가/수정/삭제 시 이 파일만 수정하면 됩니다.
 *
 * @see inputNodes.ts - ImageInput 노드 checkboxGroup
 * @see bomNodes.ts - Blueprint AI BOM 노드 checkboxGroup
 * @see ActiveFeaturesSection.tsx - 워크플로우 페이지 배지 (blueprint-ai-bom)
 *
 * 동기화 대상:
 * - blueprint-ai-bom/frontend/src/config/features/featureDefinitions.ts
 *   (별도 프로젝트이므로 수동 동기화 필요, 동일 내용 유지)
 *
 * 구현 상태 (implementationStatus):
 * - 'implemented': 백엔드 API 완전 구현됨
 * - 'partial': 기본 구조는 있으나 일부 기능 미완성 (예: 더미 데이터 반환)
 * - 'stub': API 엔드포인트만 존재, 실제 로직 미구현
 * - 'planned': 계획됨, 코드 없음
 */

// ============================================================
// Feature Groups (그룹 정의)
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
}

// ============================================================
// Feature Definitions (모든 features 정의)
// ============================================================

export const FEATURE_DEFINITIONS: Record<string, FeatureDefinition> = {
  // === 기본 검출 ===
  symbol_detection: {
    key: 'symbol_detection',
    icon: '🎯',
    label: '심볼 검출',
    group: FEATURE_GROUPS.BASIC_DETECTION,
    hint: 'YOLO 노드 추천',
    description:
      'YOLO 딥러닝 모델을 사용하여 도면 내 심볼(부품, 기호, 마크 등)을 자동으로 검출합니다. 14가지 심볼 클래스를 지원합니다.',
    recommendedNodes: ['yolo'],
    badgeBgClass: 'bg-purple-100 dark:bg-purple-900/30',
    badgeTextClass: 'text-purple-700 dark:text-purple-300',
    implementationStatus: 'implemented',
    implementationLocation: 'detection_router.py',
  },
  symbol_verification: {
    key: 'symbol_verification',
    icon: '✅',
    label: '심볼 검증',
    group: FEATURE_GROUPS.BASIC_DETECTION,
    hint: '',
    description:
      '검출된 심볼을 사람이 검토하고 승인/거부/수정할 수 있는 Human-in-the-Loop 기능입니다. 검증된 데이터는 모델 재학습에 활용됩니다.',
    recommendedNodes: [],
    badgeBgClass: 'bg-green-100 dark:bg-green-900/30',
    badgeTextClass: 'text-green-700 dark:text-green-300',
    implementationStatus: 'implemented',
    implementationLocation: 'verification_router.py',
  },
  dimension_ocr: {
    key: 'dimension_ocr',
    icon: '📏',
    label: '치수 OCR',
    group: FEATURE_GROUPS.BASIC_DETECTION,
    hint: 'eDOCr2 노드 추천',
    description:
      'eDOCr2 엔진으로 도면의 치수 텍스트(길이, 각도, 공차 등)를 인식합니다. 한국어/영어 혼합 지원, 98% 이상의 정확도.',
    recommendedNodes: ['edocr2'],
    badgeBgClass: 'bg-blue-100 dark:bg-blue-900/30',
    badgeTextClass: 'text-blue-700 dark:text-blue-300',
    implementationStatus: 'implemented',
    implementationLocation: 'dimension_router.py',
  },
  dimension_verification: {
    key: 'dimension_verification',
    icon: '✅',
    label: '치수 검증',
    group: FEATURE_GROUPS.BASIC_DETECTION,
    hint: '',
    description:
      'OCR로 인식된 치수 값을 검토하고 수정할 수 있습니다. 오인식된 값을 직접 수정하여 정확한 BOM 생성에 기여합니다.',
    recommendedNodes: [],
    badgeBgClass: 'bg-teal-100 dark:bg-teal-900/30',
    badgeTextClass: 'text-teal-700 dark:text-teal-300',
    implementationStatus: 'implemented',
    implementationLocation: 'dimension_router.py',
  },
  gt_comparison: {
    key: 'gt_comparison',
    icon: '📊',
    label: 'GT 비교',
    group: FEATURE_GROUPS.BASIC_DETECTION,
    hint: 'GT 파일 필요',
    description:
      'Ground Truth(정답 데이터)와 검출 결과를 비교하여 정밀도(Precision), 재현율(Recall), F1 스코어를 계산합니다.',
    recommendedNodes: [],
    badgeBgClass: 'bg-orange-100 dark:bg-orange-900/30',
    badgeTextClass: 'text-orange-700 dark:text-orange-300',
    implementationStatus: 'partial',
    implementationLocation: 'session (gt_results 저장만)',
  },

  // === GD&T / 기계 ===
  gdt_parsing: {
    key: 'gdt_parsing',
    icon: '🔧',
    label: 'GD&T 파싱',
    group: FEATURE_GROUPS.GDT_MECHANICAL,
    hint: 'SkinModel 노드 추천',
    description:
      '기하공차(GD&T) 기호를 파싱합니다. 위치도, 평행도, 직각도 등 14가지 기하특성과 데이텀 참조를 추출합니다.',
    recommendedNodes: ['skinmodel'],
    badgeBgClass: 'bg-indigo-100 dark:bg-indigo-900/30',
    badgeTextClass: 'text-indigo-700 dark:text-indigo-300',
    implementationStatus: 'implemented',
    implementationLocation: 'gdt_router.py',
  },
  line_detection: {
    key: 'line_detection',
    icon: '📐',
    label: '선 검출',
    group: FEATURE_GROUPS.GDT_MECHANICAL,
    hint: 'Line Detector 노드 추천',
    description:
      '도면의 선(실선, 점선, 쇄선 등)을 검출하고 유형을 분류합니다. 치수선, 중심선, 외형선을 구분하여 관계 분석에 활용됩니다.',
    recommendedNodes: ['line-detector'],
    badgeBgClass: 'bg-cyan-100 dark:bg-cyan-900/30',
    badgeTextClass: 'text-cyan-700 dark:text-cyan-300',
    implementationStatus: 'implemented',
    implementationLocation: 'line_router.py',
  },
  relation_extraction: {
    key: 'relation_extraction',
    icon: '🔗',
    label: '심볼-치수 관계',
    group: FEATURE_GROUPS.GDT_MECHANICAL,
    hint: 'YOLO + eDOCr2 추천',
    description:
      '검출된 심볼과 OCR 치수 간의 공간적 관계를 분석합니다. 어떤 치수가 어떤 심볼에 해당하는지 자동으로 매핑합니다.',
    recommendedNodes: ['yolo', 'edocr2'],
    badgeBgClass: 'bg-violet-100 dark:bg-violet-900/30',
    badgeTextClass: 'text-violet-700 dark:text-violet-300',
    implementationStatus: 'implemented',
    implementationLocation: 'relation_router.py',
  },
  welding_symbol_parsing: {
    key: 'welding_symbol_parsing',
    icon: '⚡',
    label: '용접 기호 파싱',
    group: FEATURE_GROUPS.GDT_MECHANICAL,
    hint: '용접 타입/크기 추출',
    description:
      'AWS/ISO 표준 용접 기호를 파싱합니다. 용접 타입(필렛, 맞대기 등), 크기, 깊이, 위치(화살표측/반대측)를 추출합니다.',
    recommendedNodes: ['yolo', 'edocr2'],
    badgeBgClass: 'bg-red-100 dark:bg-red-900/30',
    badgeTextClass: 'text-red-700 dark:text-red-300',
    implementationStatus: 'partial',
    implementationLocation: 'midterm_router.py (YOLO 모델 학습 필요)',
  },
  surface_roughness_parsing: {
    key: 'surface_roughness_parsing',
    icon: '🔲',
    label: '표면 거칠기 파싱',
    group: FEATURE_GROUPS.GDT_MECHANICAL,
    hint: 'Ra/Rz 값 추출',
    description:
      '표면 거칠기 기호에서 Ra, Rz, Rq 값과 가공 방법, 방향성 패턴을 추출합니다. 제거/비제거 가공 여부도 판별합니다.',
    recommendedNodes: ['yolo', 'edocr2', 'skinmodel'],
    badgeBgClass: 'bg-stone-100 dark:bg-stone-900/30',
    badgeTextClass: 'text-stone-700 dark:text-stone-300',
    implementationStatus: 'partial',
    implementationLocation: 'midterm_router.py (정규식 기반)',
  },

  // === P&ID ===
  pid_connectivity: {
    key: 'pid_connectivity',
    icon: '🔀',
    label: 'P&ID 연결성',
    group: FEATURE_GROUPS.PID,
    hint: 'PID Analyzer 노드 추천',
    description:
      'P&ID(배관계장도) 도면에서 기기 간 연결 관계를 분석합니다. 밸브, 펌프, 탱크 등의 연결 토폴로지를 추출합니다.',
    recommendedNodes: ['pid-analyzer', 'line-detector', 'yolo-pid'],
    badgeBgClass: 'bg-rose-100 dark:bg-rose-900/30',
    badgeTextClass: 'text-rose-700 dark:text-rose-300',
    implementationStatus: 'implemented',
    implementationLocation: 'line_router.py (connectivity analysis)',
  },

  // === BOM 생성 ===
  bom_generation: {
    key: 'bom_generation',
    icon: '📋',
    label: 'BOM 생성',
    group: FEATURE_GROUPS.BOM_GENERATION,
    hint: 'AI BOM 노드 추천',
    description:
      '검증된 심볼과 치수 데이터를 기반으로 Bill of Materials(부품 목록)를 자동 생성합니다. Excel, CSV, JSON 형식으로 내보내기 가능.',
    recommendedNodes: ['blueprint-ai-bom'],
    badgeBgClass: 'bg-amber-100 dark:bg-amber-900/30',
    badgeTextClass: 'text-amber-700 dark:text-amber-300',
    implementationStatus: 'implemented',
    implementationLocation: 'bom_router.py',
  },
  title_block_ocr: {
    key: 'title_block_ocr',
    icon: '📝',
    label: '표제란 OCR',
    group: FEATURE_GROUPS.BOM_GENERATION,
    hint: '도면번호/리비전 추출',
    description:
      '도면 표제란(Title Block)에서 도면번호, 리비전, 작성일, 스케일 등 메타데이터를 자동 추출합니다.',
    recommendedNodes: ['edocr2'],
    badgeBgClass: 'bg-slate-100 dark:bg-slate-900/30',
    badgeTextClass: 'text-slate-700 dark:text-slate-300',
    implementationStatus: 'implemented',
    implementationLocation: 'gdt_router.py (title-block OCR)',
  },
  quantity_extraction: {
    key: 'quantity_extraction',
    icon: '🔢',
    label: '수량 추출',
    group: FEATURE_GROUPS.BOM_GENERATION,
    hint: 'QTY/수량 패턴 인식',
    description:
      '도면 또는 BOM 테이블에서 부품 수량(QTY, EA, 개 등) 정보를 자동 추출합니다. 정규식 패턴과 위치 기반 분석을 결합합니다.',
    recommendedNodes: ['edocr2'],
    badgeBgClass: 'bg-emerald-100 dark:bg-emerald-900/30',
    badgeTextClass: 'text-emerald-700 dark:text-emerald-300',
    implementationStatus: 'partial',
    implementationLocation: 'midterm_router.py (정규식 기반)',
  },
  balloon_matching: {
    key: 'balloon_matching',
    icon: '🎈',
    label: '벌룬 매칭',
    group: FEATURE_GROUPS.BOM_GENERATION,
    hint: '부품번호-심볼 연결',
    description:
      '도면의 벌룬(풍선) 번호와 해당 심볼을 자동 매칭합니다. 부품번호와 실제 부품 위치를 연결하여 BOM 생성에 활용됩니다.',
    recommendedNodes: ['yolo', 'edocr2'],
    badgeBgClass: 'bg-pink-100 dark:bg-pink-900/30',
    badgeTextClass: 'text-pink-700 dark:text-pink-300',
    implementationStatus: 'partial',
    implementationLocation: 'midterm_router.py (근접성 기반)',
  },

  // === 장기 로드맵 ===
  drawing_region_segmentation: {
    key: 'drawing_region_segmentation',
    icon: '🗺️',
    label: '영역 세분화',
    group: FEATURE_GROUPS.LONG_TERM,
    hint: '뷰 영역 자동 구분',
    description:
      '휴리스틱 + VLM 하이브리드 방식으로 도면의 뷰 영역(정면도, 측면도, 단면도, 상세도, 표제란 등)을 자동 구분합니다. 11개 영역 타입 지원.',
    recommendedNodes: ['edgnet', 'vl'],
    badgeBgClass: 'bg-sky-100 dark:bg-sky-900/30',
    badgeTextClass: 'text-sky-700 dark:text-sky-300',
    implementationStatus: 'implemented',
    implementationLocation: 'longterm_router.py + region_segmenter.py (휴리스틱 + VLM)',
  },
  notes_extraction: {
    key: 'notes_extraction',
    icon: '📋',
    label: '노트 추출',
    group: FEATURE_GROUPS.LONG_TERM,
    hint: '재료/공차/열처리 추출',
    description:
      'OCR과 LLM을 결합하여 도면 노트 영역에서 재료 사양, 일반 공차, 열처리 조건, 도장 사양 등을 추출하고 카테고리별로 분류합니다.',
    recommendedNodes: ['edocr2', 'vl'],
    badgeBgClass: 'bg-lime-100 dark:bg-lime-900/30',
    badgeTextClass: 'text-lime-700 dark:text-lime-300',
    implementationStatus: 'implemented',
    implementationLocation: 'longterm_router.py + notes_extractor.py (GPT-4o-mini/OpenAI)',
  },
  revision_comparison: {
    key: 'revision_comparison',
    icon: '🔄',
    label: '리비전 비교',
    group: FEATURE_GROUPS.LONG_TERM,
    hint: '도면 변경점 감지',
    description:
      'SSIM 이미지 비교 + 세션 데이터 비교 + VLM 지능형 비교로 두 리비전 간 변경점을 자동 감지합니다. 심볼, 치수, 노트 변경을 추적합니다.',
    recommendedNodes: ['vl'],
    badgeBgClass: 'bg-fuchsia-100 dark:bg-fuchsia-900/30',
    badgeTextClass: 'text-fuchsia-700 dark:text-fuchsia-300',
    implementationStatus: 'implemented',
    implementationLocation: 'longterm_router.py + revision_comparator.py (SSIM + 데이터 + VLM)',
  },
  vlm_auto_classification: {
    key: 'vlm_auto_classification',
    icon: '🤖',
    label: 'VLM 자동 분류',
    group: FEATURE_GROUPS.LONG_TERM,
    hint: '도면 타입 AI 분류',
    description:
      'Vision-Language 모델이 도면을 분석하여 타입(기계도면, 전기도면, P&ID 등), 산업 분야, 복잡도를 자동 분류하고 적합한 기능을 추천합니다.',
    recommendedNodes: ['vl'],
    badgeBgClass: 'bg-yellow-100 dark:bg-yellow-900/30',
    badgeTextClass: 'text-yellow-700 dark:text-yellow-300',
    implementationStatus: 'implemented',
    implementationLocation: 'longterm_router.py + vlm_classifier.py (GPT-4o-mini/OpenAI)',
  },
};

// ============================================================
// Feature Keys (타입 안전성)
// ============================================================

export type FeatureKey = keyof typeof FEATURE_DEFINITIONS;

export const FEATURE_KEYS = Object.keys(FEATURE_DEFINITIONS) as FeatureKey[];

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

export interface GroupImplementationStats {
  total: number;
  implemented: number;
  partial: number;
  stub: number;
  planned: number;
}

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
