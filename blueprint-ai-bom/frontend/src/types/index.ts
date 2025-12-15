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
}

export interface DetectionConfig {
  confidence: number;
  iou_threshold: number;
  model_id: string;
  device?: string;
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

// UI Types
export interface ClassInfo {
  id: number;
  name: string;
  display_name: string;
  unit_price: number;
  color: string;
}
