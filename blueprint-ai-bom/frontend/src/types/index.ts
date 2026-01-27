/**
 * Blueprint AI BOM - Type Definitions
 */

// Session Types
export type SessionStatus =
  | 'created'
  | 'uploaded'
  | 'detecting'
  | 'detected'
  | 'verifying'
  | 'verified'
  | 'generating_bom'
  | 'completed'
  | 'error';

// Drawing Types (빌더에서 설정 - 2025-12-22 세분화)
export type DrawingType =
  // 주요 타입 (빌더 동기화)
  | 'dimension'          // 치수 도면 (shaft, 플랜지) - OCR만 사용
  | 'electrical_panel'   // 전기 제어판 (MCP Panel) - YOLO 14클래스
  | 'pid'                // P&ID (배관계장도) - YOLO (model_type=pid_class_aware)
  | 'assembly'           // 조립도 - YOLO + eDOCr2
  | 'dimension_bom'      // 치수 + BOM - OCR + 수동 라벨링
  // 레거시 타입 (하위 호환)
  | 'auto'               // VLM 자동 분류
  | 'mechanical'         // (deprecated) → dimension 또는 electrical_panel
  | 'mechanical_part'    // (deprecated) → dimension
  | 'electrical'         // (deprecated) → electrical_panel
  | 'electrical_circuit' // 전기 회로도 (지원 제한적)
  | 'architectural'      // 건축 도면 (지원 제한적)
  | 'unknown';           // VLM 분류 실패

export interface Session {
  session_id: string;
  filename: string;
  file_path: string;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
  detection_count: number;
  verified_count: number;
  bom_generated: boolean;
  error_message?: string;

  // 도면 분류 정보 (빌더에서 설정)
  drawing_type?: DrawingType;
  drawing_type_source?: 'builder' | 'vlm' | 'manual' | 'pending';
  drawing_type_confidence?: number;

  // 활성화된 기능 목록 (2025-12-24: 기능 기반 재설계)
  features?: string[];

  // BlueprintFlow Builder 정보
  template_id?: string;
  template_name?: string;
  workflow_definition?: { nodes?: unknown[] };
  workflow_locked?: boolean;
}

export interface SessionDetail extends Session {
  detections: Detection[];
  verification_status: Record<string, VerificationStatus>;
  approved_count: number;
  rejected_count: number;
  bom_data?: BOMData;
  image_width?: number;
  image_height?: number;
  image_base64?: string;
}

// Detection Types
export type VerificationStatus = 'pending' | 'approved' | 'rejected' | 'modified' | 'manual';

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

// Mask RLE (Run-Length Encoding) for Detectron2
export interface MaskRLE {
  size: [number, number]; // [height, width]
  counts: number[];
}

export interface Detection {
  id: string;
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: BoundingBox;
  model_id: string;
  verification_status: VerificationStatus;
  modified_class_name?: string;
  modified_bbox?: BoundingBox;
  // Detectron2 마스킹 출력
  mask?: MaskRLE;
  polygons?: number[][][]; // [[[x1,y1], [x2,y2], ...]]
}

// 검출 백엔드 타입
export type DetectionBackend = 'yolo' | 'detectron2';

export interface DetectionConfig {
  confidence: number;
  iou_threshold: number;
  model_type?: string;
  device?: string;
  // Detectron2 통합 옵션
  backend?: DetectionBackend;
  return_masks?: boolean;
  return_polygons?: boolean;
}

export interface DetectionResult {
  session_id: string;
  detections: Detection[];
  total_count: number;
  model_id: string;
  processing_time_ms: number;
  image_width: number;
  image_height: number;
}

// BOM Types
export type ExportFormat = 'excel' | 'pdf' | 'json' | 'csv';

export interface BOMItem {
  item_no: number;
  class_id: number;
  class_name: string;
  model_name?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  avg_confidence: number;
  detection_ids: string[];
  lead_time?: string;
  supplier?: string;
  remarks?: string;
  dimensions?: string[];
  linked_dimension_ids?: string[];
}

export interface BOMSummary {
  total_items: number;
  total_quantity: number;
  subtotal: number;
  vat: number;
  total: number;
}

export interface BOMData {
  session_id: string;
  created_at: string;
  items: BOMItem[];
  summary: BOMSummary;
  filename?: string;
  model_id?: string;
  detection_count: number;
  approved_count: number;
}

// API Response Types
export interface UploadResponse {
  session_id: string;
  filename: string;
  file_path: string;
  status: string;
  message: string;
}

export interface VerificationUpdate {
  detection_id: string;
  status: VerificationStatus;
  modified_class_name?: string;
  modified_bbox?: BoundingBox;
}

export interface BOMExportRequest {
  session_id: string;
  format: ExportFormat;
  include_image?: boolean;
  customer_name?: string;
}

export interface BOMExportResponse {
  session_id: string;
  format: ExportFormat;
  filename: string;
  file_path: string;
  file_size: number;
  created_at: string;
}

// Relation Types (Phase 2)
export type RelationMethod = 'dimension_line' | 'extension_line' | 'proximity' | 'manual';
export type RelationType = 'distance' | 'diameter' | 'radius' | 'angle' | 'tolerance' | 'surface_finish' | 'unknown';

export interface DimensionRelation {
  id: string;
  dimension_id: string;
  target_type: 'symbol' | 'edge' | 'region' | 'none';
  target_id: string | null;
  target_bbox: BoundingBox | null;
  relation_type: RelationType;
  method: RelationMethod;
  confidence: number;
  direction: 'horizontal' | 'vertical' | null;
  notes: string | null;
}

export interface RelationStatistics {
  total: number;
  by_method: Record<string, number>;
  by_confidence: {
    high: number;
    medium: number;
    low: number;
  };
  linked_count: number;
  unlinked_count: number;
}

export interface RelationExtractionResult {
  session_id: string;
  relations: DimensionRelation[];
  statistics: RelationStatistics;
  processing_time_ms: number;
}

// Phase 2C: 이미지별 Human-in-the-Loop
export type ImageReviewStatus =
  | 'pending'
  | 'processed'
  | 'approved'
  | 'rejected'
  | 'modified'
  | 'manual_labeled';

export interface SessionImage {
  image_id: string;
  filename: string;
  file_path: string;
  review_status: ImageReviewStatus;
  detections: Detection[];
  detection_count: number;
  verified_count: number;
  approved_count: number;
  rejected_count: number;
  image_width?: number;
  image_height?: number;
  thumbnail_base64?: string;
  reviewed_at?: string;
  reviewed_by?: string;
  review_notes?: string;
  order_index: number;
}

export interface SessionImageProgress {
  total_images: number;
  pending_count: number;
  processed_count: number;
  approved_count: number;
  rejected_count: number;
  modified_count: number;
  manual_labeled_count: number;
  progress_percent: number;
  all_reviewed: boolean;
  export_ready: boolean;
}

export interface ImageReviewUpdate {
  review_status: ImageReviewStatus;
  reviewed_by?: string;
  review_notes?: string;
}

// UI Types
export interface ClassInfo {
  id: number;
  name: string;
  display_name: string;
  unit_price: number;
  color: string;
}
