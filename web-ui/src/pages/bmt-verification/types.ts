export type VerdictType = 'exact' | 'fuzzy' | 'qty_mismatch' | 'prefix' | 'synonym' | 'drawing_only' | 'bom_only' | 'manual';

export type SeverityLevel = 'OK' | 'WARN' | 'REVIEW' | 'CRITICAL';

export type VerificationAction = 'approve' | 'reject' | 'edit' | 'skip';

export interface CroppedView {
  id: string;
  viewName: string;  // e.g. "FRONT VIEW", "TOP VIEW"
  imagePath: string;
  tags: ExtractedTag[];
}

export interface ExtractedTag {
  id: string;
  tagCode: string;         // e.g. "V01", "V06", "PI02"
  partName: string;        // e.g. "Gas Control Valve"
  confidence: number;      // 0-1
  ocrEngine: string;       // e.g. "PaddleOCR", "Tesseract"
  boundingBox?: { x: number; y: number; w: number; h: number };
}

export interface MatchResult {
  id: string;
  tag: ExtractedTag;
  partListCode: string;    // from Part List Excel
  erpBomCode: string;      // from ERP BOM Excel
  erpBomName: string;
  drawingQty: number;
  erpQty: number;
  verdict: VerdictType;
  severity: SeverityLevel;
  detail: string;          // human-readable explanation
  verificationAction?: VerificationAction;
  editedPartNo?: string;
  notes?: string;
}

export interface VerificationSummary {
  total: number;
  approved: number;
  rejected: number;
  edited: number;
  pending: number;
  matchRate: number;
}
