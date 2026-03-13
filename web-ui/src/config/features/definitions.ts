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

import { FEATURE_GROUPS } from './types';
import type { FeatureDefinition } from './types';

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
    // 🔗 관계: 심볼 검출 → 검증, GT비교 자동 활성화
    isPrimary: true,
    implies: ['symbol_verification', 'gt_comparison'],
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
    // 🔗 관계: symbol_detection에 의해 자동 활성화
    impliedBy: ['symbol_detection'],
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
    // 🔗 관계: 치수 OCR → 치수 검증 자동 활성화
    isPrimary: true,
    implies: ['dimension_verification'],
    impliedBy: ['material_allowance'],
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
    // 🔗 관계: dimension_ocr에 의해 자동 활성화
    impliedBy: ['dimension_ocr'],
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
    implementationStatus: 'implemented',
    implementationLocation: 'groundTruth API (api_server.py)',
    // 🔗 관계: symbol_detection에 의해 자동 활성화
    impliedBy: ['symbol_detection'],
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
    isPrimary: true,
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
    isPrimary: true,
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
    recommendedNodes: ['pid-analyzer', 'line-detector', 'yolo'],
    badgeBgClass: 'bg-rose-100 dark:bg-rose-900/30',
    badgeTextClass: 'text-rose-700 dark:text-rose-300',
    implementationStatus: 'implemented',
    implementationLocation: 'line_router.py (connectivity analysis)',
    isPrimary: true,
    // 🔗 관계: P&ID 연결성 → TECHCROSS 기능들 자동 활성화
    implies: ['techcross_valve_signal', 'techcross_equipment', 'techcross_checklist', 'techcross_deviation'],
  },
  industry_equipment_detection: {
    key: 'industry_equipment_detection',
    icon: '🏭',
    label: '장비 태그 인식',
    group: FEATURE_GROUPS.PID,
    isPrimary: true,
    hint: 'OCR + 패턴 매칭',
    description:
      'P&ID 도면에서 산업별 장비 태그(예: ECU-001, FMU-002, PUMP-101 등)를 OCR과 정규식 패턴 매칭으로 자동 인식합니다. 장비 프로파일을 선택하여 다양한 산업 분야에 적용 가능합니다.',
    recommendedNodes: ['pid-analyzer', 'ocr-ensemble'],
    badgeBgClass: 'bg-rose-100 dark:bg-rose-900/30',
    badgeTextClass: 'text-rose-700 dark:text-rose-300',
    implementationStatus: 'implemented',
    implementationLocation: 'pid-analyzer-api/equipment_analyzer.py',
    // 🔗 관계: 장비 태그 인식 → 장비 목록 내보내기 자동 활성화
    implies: ['equipment_list_export'],
  },
  equipment_list_export: {
    key: 'equipment_list_export',
    icon: '📑',
    label: '장비 목록 내보내기',
    group: FEATURE_GROUPS.PID,
    hint: 'Excel 출력',
    description:
      '인식된 장비 태그를 정리하여 Equipment List Excel 파일로 내보냅니다. 태그, 타입, 설명, 수량 등을 포함한 표준 형식으로 출력됩니다.',
    recommendedNodes: ['pid-analyzer'],
    badgeBgClass: 'bg-rose-100 dark:bg-rose-900/30',
    badgeTextClass: 'text-rose-700 dark:text-rose-300',
    implementationStatus: 'implemented',
    implementationLocation: 'pid-analyzer-api/equipment_analyzer.py',
    // 🔗 관계: industry_equipment_detection에 의해 자동 활성화
    impliedBy: ['industry_equipment_detection'],
  },

  // === TECHCROSS BWMS (1-1 ~ 1-4) ===
  techcross_valve_signal: {
    key: 'techcross_valve_signal',
    icon: '🎛️',
    label: 'Valve Signal List',
    group: FEATURE_GROUPS.TECHCROSS,
    hint: '1-2: BWMS 밸브 추출',
    description:
      'P&ID 도면에서 "SIGNAL FOR BWMS" 영역의 밸브 ID를 자동 추출합니다. Human-in-the-Loop으로 검토/승인 후 Excel 내보내기.',
    recommendedNodes: ['blueprint-ai-bom', 'pid-analyzer', 'line-detector'],
    badgeBgClass: 'bg-orange-100 dark:bg-orange-900/30',
    badgeTextClass: 'text-orange-700 dark:text-orange-300',
    implementationStatus: 'implemented',
    implementationLocation: 'blueprint-ai-bom/routers/pid_features_router.py',
    // 🔗 관계: pid_connectivity에 의해 자동 활성화
    impliedBy: ['pid_connectivity'],
  },
  techcross_equipment: {
    key: 'techcross_equipment',
    icon: '⚙️',
    label: 'Equipment List',
    group: FEATURE_GROUPS.TECHCROSS,
    hint: '1-3: BWMS 장비 검출',
    description:
      'P&ID 도면에서 BWMS 장비 태그(ECU, FMU, ANU, TSU, APU, GDS 등)를 검출합니다. 검증 후 Equipment List Excel 내보내기.',
    recommendedNodes: ['blueprint-ai-bom', 'pid-analyzer', 'paddleocr'],
    badgeBgClass: 'bg-orange-100 dark:bg-orange-900/30',
    badgeTextClass: 'text-orange-700 dark:text-orange-300',
    implementationStatus: 'implemented',
    implementationLocation: 'blueprint-ai-bom/routers/pid_features_router.py',
    // 🔗 관계: pid_connectivity에 의해 자동 활성화
    impliedBy: ['pid_connectivity'],
  },
  techcross_checklist: {
    key: 'techcross_checklist',
    icon: '✅',
    label: 'BWMS Checklist',
    group: FEATURE_GROUPS.TECHCROSS,
    hint: '1-1: 60개 항목 검증',
    description:
      'TECHCROSS BWMS 60개 체크리스트 항목을 자동 검증합니다. AI 판정 후 Human-in-the-Loop으로 최종 승인. FMU-ECU 순서, TSU-APU 거리 등 규칙 검사.',
    recommendedNodes: ['blueprint-ai-bom', 'design-checker', 'yolo'],
    badgeBgClass: 'bg-orange-100 dark:bg-orange-900/30',
    badgeTextClass: 'text-orange-700 dark:text-orange-300',
    implementationStatus: 'implemented',
    implementationLocation: 'blueprint-ai-bom/routers/pid_features_router.py',
    // 🔗 관계: pid_connectivity에 의해 자동 활성화
    impliedBy: ['pid_connectivity'],
  },
  techcross_deviation: {
    key: 'techcross_deviation',
    icon: '📝',
    label: 'Deviation List',
    group: FEATURE_GROUPS.TECHCROSS,
    hint: '1-4: POR 대비 편차',
    description:
      'POR(Purchase Order Requirement) 대비 편차 항목을 관리합니다. 구매자 결정사항 입력 및 추적.',
    recommendedNodes: ['blueprint-ai-bom'],
    badgeBgClass: 'bg-orange-100 dark:bg-orange-900/30',
    badgeTextClass: 'text-orange-700 dark:text-orange-300',
    implementationStatus: 'implemented',
    implementationLocation: 'blueprint-ai-bom/routers/pid_features/deviation_router.py',
    // 🔗 관계: pid_connectivity에 의해 자동 활성화
    impliedBy: ['pid_connectivity'],
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
    isPrimary: true,
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
    isPrimary: true,
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
  material_allowance: {
    key: 'material_allowance',
    icon: '📐',
    label: '여유치 자동 계산',
    group: FEATURE_GROUPS.BOM_GENERATION,
    hint: 'OD/ID/Length 여유치 자동 적용',
    description:
      '도면 치수에 가공 여유치를 자동 적용하여 소재 발주 사이즈를 계산합니다. ' +
      '기본값: OD +10mm, ID -5mm, Length +5mm. 프로젝트별 커스텀 설정 가능.',
    recommendedNodes: ['edocr2', 'blueprintaibom'],
    badgeBgClass: 'bg-amber-100 dark:bg-amber-900/30',
    badgeTextClass: 'text-amber-700 dark:text-amber-300',
    implementationStatus: 'implemented',
    implementationLocation: 'cost_calculator.py (apply_allowance)',
    implies: ['dimension_ocr'],
    isPrimary: true,
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
    isPrimary: true,
  },
};

// ============================================================
// Feature Keys (타입 안전성)
// ============================================================

export type FeatureKey = keyof typeof FEATURE_DEFINITIONS;

export const FEATURE_KEYS = Object.keys(FEATURE_DEFINITIONS) as FeatureKey[];
