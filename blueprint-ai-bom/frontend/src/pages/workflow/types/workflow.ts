/**
 * Workflow Page Types
 * 워크플로우 페이지에서 사용하는 모든 인터페이스 정의
 */

// Dimension types
export interface Dimension {
  id: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  value: string;
  raw_text: string;
  unit: string | null;
  tolerance: string | null;
  dimension_type: string;
  confidence: number;
  verification_status: 'pending' | 'approved' | 'rejected' | 'modified' | 'manual';
  modified_value: string | null;
  linked_to: string | null;
}

export interface DimensionStats {
  pending: number;
  approved: number;
  rejected: number;
  modified: number;
  manual: number;
}

export interface AnalysisOptionsData {
  enable_symbol_detection: boolean;
  enable_dimension_ocr: boolean;
  enable_line_detection: boolean;
  enable_text_extraction: boolean;
  ocr_engine: string;
  confidence_threshold: number;
  symbol_model_type: string;
  preset: string | null;
  // Detectron2 옵션
  detection_backend: 'yolo' | 'detectron2';
  return_masks: boolean;
  return_polygons: boolean;
}

// 도면 타입별 섹션 가시성 설정
export interface SectionVisibility {
  symbolDetection: boolean;
  dimensionOCR: boolean;
  lineDetection: boolean;
  gdtParsing: boolean;
  relationExtraction: boolean;
  pidConnectivity: boolean;
  titleBlockOcr: boolean;
  weldingSymbolParsing: boolean;
  surfaceRoughnessParsing: boolean;
  quantityExtraction: boolean;
  balloonMatching: boolean;
  drawingRegionSegmentation: boolean;
  notesExtraction: boolean;
  revisionComparison: boolean;
  vlmAutoClassification: boolean;
  // P&ID 분석 기능
  valveSignalList: boolean;      // pid_valve_detection
  equipmentList: boolean;        // pid_equipment_detection
  bwmsChecklist: boolean;        // pid_design_checklist (내부 변수명 유지)
  deviationList: boolean;        // pid_deviation_analysis
  // 추가 기능 (2025-12-31 P1 매핑 완성)
  gtComparison: boolean;              // gt_comparison - GT 비교
  bomGeneration: boolean;             // bom_generation - BOM 생성
  industryEquipmentDetection: boolean; // industry_equipment_detection - 산업 장비 검출
  tableExtraction: boolean;              // table_extraction - 테이블 추출
}

// Line detection
export interface LineData {
  id: string;
  start: { x: number; y: number };
  end: { x: number; y: number };
  length: number;
  angle: number;
  line_type: string;
  line_style: string;
  color?: string;
  confidence: number;
  thickness?: number;
}

export interface IntersectionData {
  id: string;
  point: { x: number; y: number };
  line_ids: string[];
  intersection_type?: string;
}

// VLM Classification
export interface ClassificationData {
  drawing_type: string;
  confidence: number;
  suggested_preset: string;
  provider: string;
}

// Class examples
export interface ClassExample {
  class_name: string;
  image_base64: string;
}

// Detection stats
export interface DetectionStats {
  total: number;
  approved: number;
  rejected: number;
  pending: number;
  manual: number;
}
