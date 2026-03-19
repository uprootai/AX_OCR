/**
 * Dimension Lab — 공유 타입
 */
export type GtRole = 'od' | 'id' | 'w';

export interface GtAnnotation {
  role: GtRole;
  value: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
}

export type LabStep = 'annotate' | 'running' | 'results';

export const ROLE_COLORS: Record<GtRole, string> = {
  od: '#ef4444', // red
  id: '#3b82f6', // blue
  w: '#22c55e',  // green
};

export const ROLE_LABELS: Record<GtRole, string> = {
  od: 'OD (외경)',
  id: 'ID (내경)',
  w: 'W (폭)',
};

export const ENGINE_LABELS: Record<string, string> = {
  paddleocr: 'PaddleOCR',
  paddleocr_tiled: 'PaddleOCR Tiled',
  edocr2: 'eDOCr2',
  easyocr: 'EasyOCR',
  trocr: 'TrOCR',
  suryaocr: 'SuryaOCR',
  doctr: 'DocTR',
};

export const METHOD_LABELS: Record<string, string> = {
  diameter_symbol: 'A. Ø기호+크기',
  dimension_type: 'B. dimension_type',
  catalog: 'C. 카탈로그',
  composite_signal: 'D. 복합시그널',
  position_width: 'E. 위치기반W',
  session_ref: 'F. 세션명검증',
  tolerance_fit: 'G. 공차/끼워맞춤',
  value_ranking: 'H. 값크기순위',
  heuristic: 'I. 휴리스틱',
  full_pipeline: 'J. 전체파이프라인',
  geometry_guided: 'K. 기하학기반',
  endpoint_topology: 'L. 끝점토폴로지',
  symbol_search: 'M. 심볼검색',
  center_raycast: 'N. 중심레이캐스트',
};

export const GEOMETRY_METHODS = [
  'geometry_guided', 'endpoint_topology', 'symbol_search', 'center_raycast',
];

export interface MethodInfo {
  id: string;
  label: string;
  description: string;
  category: 'symbol' | 'statistical' | 'pipeline' | 'geometry';
}

export const METHOD_INFO: MethodInfo[] = [
  { id: 'diameter_symbol', label: 'A. Ø기호+크기', category: 'symbol',
    description: 'OCR에서 Ø 접두사 치수를 찾아 최대값 → OD, 차대값 → ID. ≤30은 볼트홀로 제외.' },
  { id: 'dimension_type', label: 'B. dimension_type', category: 'symbol',
    description: 'OCR 파서가 판단한 diameter 타입 중 최대 → OD, 20~80% 범위 최소 → ID.' },
  { id: 'catalog', label: 'C. 카탈로그', category: 'symbol',
    description: 'ISO 355 / JIS B 1512 표준 베어링 치수와 OD 대조 → 표준 ID 추정.' },
  { id: 'composite_signal', label: 'D. 복합시그널', category: 'statistical',
    description: 'OD 비율, 값 반복 빈도, 공차 보유, 중앙 위치 등 7개 시그널 합산으로 ID 추정.' },
  { id: 'position_width', label: 'E. 위치기반W', category: 'statistical',
    description: '도면 좌측/상단의 큰 가로 치수 → 폭(W). OD/ID 확정 후 남은 값에서 최대값 선택.' },
  { id: 'session_ref', label: 'F. 세션명검증', category: 'pipeline',
    description: '세션 파일명에서 OD/ID/W 기준값 파싱 → 분류 결과와 교차 검증.' },
  { id: 'tolerance_fit', label: 'G. 공차/끼워맞춤', category: 'statistical',
    description: '공차(H7, ±0.05)가 있는 치수 = 기능치수. 공차 보유 최대 → OD, 차대 → ID.' },
  { id: 'value_ranking', label: 'H. 값크기순위', category: 'statistical',
    description: '전체 수치 치수를 크기 내림차순 정렬. 1위 → OD, 2위 → ID, 3위 → W.' },
  { id: 'heuristic', label: 'I. 휴리스틱', category: 'pipeline',
    description: '타입 → 접두사 → 위치 → 크기 순서 규칙. Ø>80=OD, 30~80=ID, 상단 가로=W.' },
  { id: 'full_pipeline', label: 'J. 전체파이프라인', category: 'pipeline',
    description: '프로덕션 경로: OpenCV OD/ID/W → 휴리스틱 fallback → OCR 보정 순차 적용.' },
  { id: 'geometry_guided', label: 'K. 기하학기반', category: 'geometry',
    description: '원 검출 → 치수선 추적 → ROI 크롭 OCR → 역할 자동 결정. 독립 파이프라인.' },
  { id: 'endpoint_topology', label: 'L. 끝점토폴로지', category: 'geometry',
    description: '치수선 끝점이 원 중심 근처 → R(반지름), 양 끝점 원주 → Ø(직경) 판별.' },
  { id: 'symbol_search', label: 'M. 심볼검색', category: 'geometry',
    description: 'OCR 텍스트에서 R/Ø 접두사 정규식 검색. R → value×2 직경 변환.' },
  { id: 'center_raycast', label: 'N. 중심레이캐스트', category: 'geometry',
    description: '원 중심에서 8방향 ray 발사 → 치수 교차 거리와 반지름 비교로 R vs Ø 판별.' },
];

const CATEGORY_LABELS: Record<string, string> = {
  symbol: '기호 기반',
  statistical: '통계/위치',
  pipeline: '파이프라인',
  geometry: '기하학',
};

const CATEGORY_COLORS: Record<string, string> = {
  symbol: '#8b5cf6',
  statistical: '#f59e0b',
  pipeline: '#10b981',
  geometry: '#06b6d4',
};

export { CATEGORY_LABELS, CATEGORY_COLORS };

export interface CircleInfo {
  cx: number; cy: number; radius: number; confidence: number;
}

export interface DimLineInfo {
  x1: number; y1: number; x2: number; y2: number;
  near_center: boolean; endpoint_type: string;
}

export interface RoiInfo {
  x: number; y: number; w: number; h: number;
  ocr_text: string; symbol: string;
}

export interface RayCastInfo {
  origin_cx: number; origin_cy: number;
  angle_deg: number; hit_x: number; hit_y: number; distance: number;
}

export interface GeometryDebugInfo {
  circles: CircleInfo[];
  dim_lines: DimLineInfo[];
  rois: RoiInfo[];
  rays: RayCastInfo[];
  symbols_found: Array<{ text: string; x: number; y: number; type: string }>;
}

export const ALL_ENGINES = Object.keys(ENGINE_LABELS);
export const ALL_METHODS = Object.keys(METHOD_LABELS);
