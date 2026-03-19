/**
 * Analysis API - 선 검출, P&ID 연결성, 표제란, 중기 로드맵 기능
 */

import { api } from './client';

// ==================== Line Detection Types ====================

export interface Line {
  id: string;
  type: string;
  start: { x: number; y: number };
  end: { x: number; y: number };
  length: number;
  angle: number;
}

export interface Intersection {
  id: string;
  point: { x: number; y: number };
  line_ids: string[];
}

export interface LineDetectionResult {
  session_id: string;
  lines: Line[];
  intersections: Intersection[];
  statistics: {
    total_lines: number;
    horizontal_lines: number;
    vertical_lines: number;
    diagonal_lines: number;
    intersections: number;
  };
}

// ==================== Connectivity Types ====================

export interface ConnectivityNode {
  id: string;
  class_name: string;
  center: { x: number; y: number };
  bbox: { x1: number; y1: number; x2: number; y2: number };
  connections: string[];
  connected_lines: string[];
  tag?: string | null;
}

export interface ConnectivityConnection {
  id: string;
  source_id: string;
  target_id: string;
  line_ids: string[];
  connection_type: string;
  confidence: number;
  path_length: number;
}

export interface ConnectivityResult {
  nodes: Record<string, ConnectivityNode>;
  connections: ConnectivityConnection[];
  orphan_symbols: string[];
  statistics: {
    total_symbols: number;
    total_connections: number;
    orphan_count: number;
    connectivity_ratio: number;
    avg_connections_per_symbol: number;
    connection_distribution: Record<string, number>;
    class_statistics: Record<string, { count: number; connected: number }>;
    connection_type_distribution: Record<string, number>;
  };
}

// ==================== Title Block Types ====================

export interface TitleBlockData {
  drawing_number?: string | null;
  drawing_title?: string | null;
  revision?: string | null;
  date?: string | null;
  scale?: string | null;
  material?: string | null;
  surface_finish?: string | null;
  tolerance?: string | null;
  company?: string | null;
  drawn_by?: string | null;
  checked_by?: string | null;
  approved_by?: string | null;
  raw_text?: string | null;
  custom_fields?: Record<string, string> | null;
}

// ==================== Welding Symbol Types ====================

export type WeldingType = 'fillet' | 'groove' | 'plug' | 'slot' | 'spot' | 'seam' | 'back' | 'surfacing' | 'flange' | 'unknown';
export type WeldingLocation = 'arrow_side' | 'other_side' | 'both_sides';

export interface WeldingSymbol {
  id: string;
  welding_type: WeldingType;
  location: WeldingLocation;
  size?: string | null;
  length?: string | null;
  pitch?: string | null;
  depth?: string | null;
  root_opening?: string | null;
  groove_angle?: string | null;
  field_weld: boolean;
  all_around: boolean;
  contour?: string | null;
  process?: string | null;
  bbox?: number[] | null;
  confidence: number;
  raw_text?: string | null;
}

export interface WeldingParsingResult {
  session_id: string;
  welding_symbols: WeldingSymbol[];
  total_count: number;
  by_type: Record<string, number>;
  processing_time_ms: number;
}

// ==================== Surface Roughness Types ====================

export type RoughnessType = 'Ra' | 'Rz' | 'Rmax' | 'Rq' | 'Rt' | 'unknown';
export type MachiningMethod = 'turning' | 'milling' | 'grinding' | 'lapping' | 'honing' | 'polishing' | 'casting' | 'forging' | 'any' | 'unknown';
export type LayDirection = 'parallel' | 'perpendicular' | 'crossed' | 'multidirectional' | 'circular' | 'radial' | 'unknown';

export interface SurfaceRoughness {
  id: string;
  roughness_type: RoughnessType;
  value?: number | null;
  unit: string;
  upper_limit?: number | null;
  lower_limit?: number | null;
  sampling_length?: number | null;
  machining_method: MachiningMethod;
  machining_allowance?: number | null;
  lay_direction: LayDirection;
  bbox?: number[] | null;
  confidence: number;
  raw_text?: string | null;
}

export interface SurfaceRoughnessResult {
  session_id: string;
  roughness_symbols: SurfaceRoughness[];
  total_count: number;
  by_type: Record<string, number>;
  processing_time_ms: number;
}

// ==================== Quantity Types ====================

export type QuantitySource = 'balloon' | 'table' | 'note' | 'inline' | 'unknown';

export interface QuantityItem {
  id: string;
  quantity: number;
  unit?: string | null;
  part_number?: string | null;
  balloon_number?: string | null;
  symbol_id?: string | null;
  source: QuantitySource;
  pattern_matched?: string | null;
  bbox?: number[] | null;
  confidence: number;
  raw_text?: string | null;
}

export interface QuantityExtractionResult {
  session_id: string;
  quantities: QuantityItem[];
  total_items: number;
  total_quantity: number;
  by_source: Record<string, number>;
  processing_time_ms: number;
}

// ==================== Balloon Types ====================

export type BalloonShape = 'circle' | 'triangle' | 'square' | 'hexagon' | 'diamond' | 'unknown';

export interface Balloon {
  id: string;
  number: string;
  numeric_value?: number | null;
  shape: BalloonShape;
  matched_symbol_id?: string | null;
  matched_symbol_class?: string | null;
  leader_line_endpoint?: number[] | null;
  bom_item?: Record<string, unknown> | null;
  center?: number[] | null;
  bbox?: number[] | null;
  confidence: number;
}

export interface BalloonMatchingResult {
  session_id: string;
  balloons: Balloon[];
  total_balloons: number;
  matched_count: number;
  unmatched_count: number;
  match_rate: number;
  processing_time_ms: number;
}

// ==================== Dimension Lab Types ====================

export interface DimensionBBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface DimensionItem {
  id: string;
  bbox: DimensionBBox;
  value: string;
  raw_text: string;
  unit?: string | null;
  tolerance?: string | null;
  dimension_type: string;
  confidence: number;
  model_id: string;
  material_role?: string | null;
  ocr_corrected: boolean;
}

export interface EngineResult {
  engine: string;
  dimensions: DimensionItem[];
  count: number;
  processing_time_ms: number;
  error?: string | null;
}

export interface DimensionCompareRequest {
  session_id: string;
  ocr_engines: string[];
  confidence_threshold: number;
  classify_roles: boolean;
}

export interface DimensionCompareResponse {
  session_id: string;
  image_width: number;
  image_height: number;
  engine_results: EngineResult[];
}

// ==================== Method Compare Types ====================

export interface MethodDimension {
  value: string;
  confidence: number;
  role?: string | null;
  bbox?: { x1: number; y1: number; x2: number; y2: number } | null;
}

export interface MethodResult {
  method_id: string;
  method_name: string;
  description: string;
  od?: string | null;
  id_val?: string | null;
  width?: string | null;
  od_confidence: number;
  id_confidence: number;
  width_confidence: number;
  classified_dims: MethodDimension[];
}

export interface RawDimension {
  id: string;
  value: string;
  confidence: number;
  dimension_type: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
}

export interface MethodCompareResponse {
  session_id: string;
  image_width: number;
  image_height: number;
  ocr_engine: string;
  ocr_time_ms: number;
  total_dims: number;
  raw_dimensions: RawDimension[];
  method_results: MethodResult[];
}

// ==================== Batch Eval Types ====================

export interface SessionEvalRow {
  session_id: string;
  filename: string;
  status: 'pending' | 'running' | 'done' | 'error';
  geometry_od: string | null;
  geometry_id: string | null;
  geometry_w: string | null;
  ranking_od: string | null;
  ranking_id: string | null;
  ranking_w: string | null;
  od: string | null;
  id_val: string | null;
  width: string | null;
  od_correct: boolean | null;
  id_correct: boolean | null;
  w_correct: boolean | null;
  has_gt: boolean;
  error: string | null;
}

export interface BatchEvalStatus {
  batch_id: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  total: number;
  completed: number;
  failed: number;
  rows: SessionEvalRow[];
}

// ==================== Analysis API ====================

// ==================== Ground Truth Types ====================

export interface GroundTruthDimension {
  role: 'od' | 'id' | 'w';
  value: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
}

export interface GroundTruthResponse {
  session_id: string;
  dimensions: GroundTruthDimension[];
  image_width: number;
  image_height: number;
}

// ==================== Full Compare Types ====================

export interface ClassifiedDim {
  value: string;
  role: string | null;
  confidence: number;
  bbox: { x1: number; y1: number; x2: number; y2: number } | null;
  diameter_from_radius?: boolean;
}

export interface GeometryDebugInfoApi {
  circles: Array<{ cx: number; cy: number; radius: number; confidence: number }>;
  dim_lines: Array<{ x1: number; y1: number; x2: number; y2: number; near_center: boolean; endpoint_type: string }>;
  rois: Array<{ x: number; y: number; w: number; h: number; ocr_text: string; symbol: string }>;
  rays: Array<{ origin_cx: number; origin_cy: number; angle_deg: number; hit_x: number; hit_y: number; distance: number }>;
  symbols_found: Array<{ text: string; x: number; y: number; type: string }>;
}

export interface CellResult {
  engine: string;
  method_id: string;
  od: string | null;
  id_val: string | null;
  width: string | null;
  od_match: boolean | null;
  id_match: boolean | null;
  w_match: boolean | null;
  score: number;
  classified_dims: ClassifiedDim[];
  geometry_debug: GeometryDebugInfoApi | null;
}

export interface FullCompareResponse {
  session_id: string;
  image_width: number;
  image_height: number;
  ground_truth: GroundTruthDimension[];
  engine_times: Record<string, number>;
  matrix: CellResult[];
  total_engines: number;
  total_methods: number;
}

// ==================== Analysis API ====================

export const analysisApi = {
  /** 선 검출 실행 */
  detectLines: async (sessionId: string): Promise<LineDetectionResult> => {
    const { data } = await api.post(`/analysis/lines/${sessionId}`);
    return data;
  },

  /** 선 검출 결과 조회 */
  getLines: async (sessionId: string): Promise<LineDetectionResult> => {
    const { data } = await api.get(`/analysis/lines/${sessionId}`);
    return data;
  },

  /** P&ID 연결성 분석 실행 */
  analyzeConnectivity: async (sessionId: string): Promise<{
    success: boolean;
    connectivity_graph: ConnectivityResult;
  }> => {
    const { data } = await api.post(`/analysis/connectivity/${sessionId}`);
    return data;
  },

  /** P&ID 연결성 결과 조회 */
  getConnectivity: async (sessionId: string): Promise<ConnectivityResult> => {
    const { data } = await api.get(`/analysis/connectivity/${sessionId}`);
    return data;
  },

  /** P&ID 경로 찾기 */
  findPath: async (
    sessionId: string,
    startSymbolId: string,
    endSymbolId: string
  ): Promise<{
    path: string[];
    path_length: number;
    connections: ConnectivityConnection[];
  }> => {
    const { data } = await api.get(`/analysis/connectivity/${sessionId}/path`, {
      params: { start_symbol_id: startSymbolId, end_symbol_id: endSymbolId },
    });
    return data;
  },

  /** 심볼 연결 컴포넌트 조회 */
  getConnectedComponent: async (
    sessionId: string,
    symbolId: string
  ): Promise<{
    symbol_id: string;
    connected_symbols: string[];
    connections: ConnectivityConnection[];
  }> => {
    const { data } = await api.get(`/analysis/connectivity/${sessionId}/component/${symbolId}`);
    return data;
  },

  /** 표제란 OCR 실행 */
  extractTitleBlock: async (sessionId: string): Promise<{
    success: boolean;
    message: string;
    title_block: TitleBlockData | null;
    region?: Record<string, unknown>;
  }> => {
    const { data } = await api.post(`/analysis/title-block/${sessionId}/extract`);
    return data;
  },

  /** 표제란 정보 조회 */
  getTitleBlock: async (sessionId: string): Promise<{
    success: boolean;
    title_block: TitleBlockData | null;
  }> => {
    const { data } = await api.get(`/analysis/title-block/${sessionId}`);
    return data;
  },

  /** 표제란 정보 수정 */
  updateTitleBlock: async (
    sessionId: string,
    update: Partial<TitleBlockData>
  ): Promise<{
    success: boolean;
    title_block: TitleBlockData;
  }> => {
    const { data } = await api.put(`/analysis/title-block/${sessionId}`, update);
    return data;
  },

  // ==================== 중기 로드맵 기능 ====================

  /** 용접 기호 파싱 */
  parseWeldingSymbols: async (sessionId: string): Promise<WeldingParsingResult> => {
    const { data } = await api.post(`/analysis/welding-symbols/${sessionId}/parse`);
    return data;
  },

  /** 용접 기호 조회 */
  getWeldingSymbols: async (sessionId: string): Promise<WeldingParsingResult> => {
    const { data } = await api.get(`/analysis/welding-symbols/${sessionId}`);
    return data;
  },

  /** 용접 기호 수정 */
  updateWeldingSymbol: async (
    sessionId: string,
    symbolId: string,
    update: Partial<WeldingSymbol>
  ): Promise<{ success: boolean; symbol: WeldingSymbol }> => {
    const { data } = await api.put(`/analysis/welding-symbols/${sessionId}/${symbolId}`, update);
    return data;
  },

  /** 표면 거칠기 파싱 */
  parseSurfaceRoughness: async (sessionId: string): Promise<SurfaceRoughnessResult> => {
    const { data } = await api.post(`/analysis/surface-roughness/${sessionId}/parse`);
    return data;
  },

  /** 표면 거칠기 조회 */
  getSurfaceRoughness: async (sessionId: string): Promise<SurfaceRoughnessResult> => {
    const { data } = await api.get(`/analysis/surface-roughness/${sessionId}`);
    return data;
  },

  /** 표면 거칠기 수정 */
  updateSurfaceRoughness: async (
    sessionId: string,
    symbolId: string,
    update: Partial<SurfaceRoughness>
  ): Promise<{ success: boolean; symbol: SurfaceRoughness }> => {
    const { data } = await api.put(`/analysis/surface-roughness/${sessionId}/${symbolId}`, update);
    return data;
  },

  /** 수량 추출 */
  extractQuantities: async (sessionId: string): Promise<QuantityExtractionResult> => {
    const { data } = await api.post(`/analysis/quantity/${sessionId}/extract`);
    return data;
  },

  /** 수량 조회 */
  getQuantities: async (sessionId: string): Promise<QuantityExtractionResult> => {
    const { data } = await api.get(`/analysis/quantity/${sessionId}`);
    return data;
  },

  /** 수량 수정 */
  updateQuantity: async (
    sessionId: string,
    quantityId: string,
    update: Partial<QuantityItem>
  ): Promise<{ success: boolean; quantity: QuantityItem }> => {
    const { data } = await api.put(`/analysis/quantity/${sessionId}/${quantityId}`, update);
    return data;
  },

  /** 벌룬 매칭 실행 */
  matchBalloons: async (sessionId: string): Promise<BalloonMatchingResult> => {
    const { data } = await api.post(`/analysis/balloon/${sessionId}/match`);
    return data;
  },

  /** 벌룬 매칭 결과 조회 */
  getBalloons: async (sessionId: string): Promise<BalloonMatchingResult> => {
    const { data } = await api.get(`/analysis/balloon/${sessionId}`);
    return data;
  },

  /** 벌룬 정보 수정 */
  updateBalloon: async (
    sessionId: string,
    balloonId: string,
    update: Partial<Balloon>
  ): Promise<{ success: boolean; balloon: Balloon }> => {
    const { data } = await api.put(`/analysis/balloon/${sessionId}/${balloonId}`, update);
    return data;
  },

  /** 벌룬-심볼 수동 연결 */
  linkBalloonToSymbol: async (
    sessionId: string,
    balloonId: string,
    symbolId: string
  ): Promise<{ success: boolean; balloon: Balloon }> => {
    const { data } = await api.post(`/analysis/balloon/${sessionId}/${balloonId}/link?symbol_id=${symbolId}`);
    return data;
  },

  /** OCR 엔진 비교 (Dimension Lab) */
  compareDimensions: async (
    request: DimensionCompareRequest
  ): Promise<DimensionCompareResponse> => {
    const { data } = await api.post('/analysis/dimensions/compare', request, {
      timeout: 300_000,
    });
    return data;
  },

  /** 분류 방법론 비교 (Dimension Lab) */
  compareMethods: async (
    sessionId: string,
    ocrEngine: string = 'paddleocr',
    confidenceThreshold: number = 0.5,
  ): Promise<MethodCompareResponse> => {
    const { data } = await api.post('/analysis/dimensions/compare-methods', null, {
      params: { session_id: sessionId, ocr_engine: ocrEngine, confidence_threshold: confidenceThreshold },
      timeout: 300_000,
    });
    return data;
  },

  /** Ground Truth 저장 */
  saveGroundTruth: async (
    sessionId: string,
    dimensions: GroundTruthDimension[],
  ): Promise<GroundTruthResponse> => {
    const { data } = await api.post(`/analysis/dimensions/${sessionId}/ground-truth`, { dimensions });
    return data;
  },

  /** Ground Truth 조회 */
  getGroundTruth: async (sessionId: string): Promise<GroundTruthResponse> => {
    const { data } = await api.get(`/analysis/dimensions/${sessionId}/ground-truth`);
    return data;
  },

  // ==================== 배치 평가 (Dimension Lab) ====================

  /** 배치 평가 시작 */
  startBatchEval: async (
    count: number = 10,
    sessionIds?: string[],
  ): Promise<{ batch_id: string; total: number; session_ids: string[] }> => {
    const { data } = await api.post('/analysis/dimensions/batch-eval', {
      count,
      session_ids: sessionIds ?? null,
    });
    return data;
  },

  /** 배치 평가 상태/결과 조회 */
  getBatchEvalStatus: async (batchId: string): Promise<BatchEvalStatus> => {
    const { data } = await api.get(`/analysis/dimensions/batch-eval/${batchId}/status`);
    return data;
  },

  /** 후행 평가 저장 */
  saveBatchSessionEval: async (
    batchId: string,
    sessionId: string,
    evalData: { od_correct?: boolean | null; id_correct?: boolean | null; w_correct?: boolean | null },
  ): Promise<{ ok: boolean }> => {
    const { data } = await api.patch(
      `/analysis/dimensions/batch-eval/${batchId}/sessions/${sessionId}/eval`,
      evalData,
    );
    return data;
  },

  /** 전체 비교 (엔진 × 방법) — methods 필터로 개별 실행 가능 */
  fullCompare: async (
    sessionId: string,
    ocrEngines?: string[],
    confidenceThreshold: number = 0.5,
    methods?: string[],
  ): Promise<FullCompareResponse> => {
    const { data } = await api.post('/analysis/dimensions/full-compare', {
      session_id: sessionId,
      ocr_engines: ocrEngines ?? ['paddleocr', 'edocr2', 'easyocr', 'trocr', 'suryaocr', 'doctr', 'paddleocr_tiled'],
      confidence_threshold: confidenceThreshold,
      methods: methods ?? null,
    }, { timeout: 600_000 });
    return data;
  },
};
