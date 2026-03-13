// API Base URLs — 로컬/외부 자동 감지 + 프록시 경로 분기

// @AX:ANCHOR — 런타임 로컬/외부 감지 + API URL 분기
const isLocal = typeof window !== 'undefined' &&
  ['localhost', '127.0.0.1'].some(h => window.location.hostname === h);

/**
 * 로컬 접속: http://localhost:PORT 직접 호출
 * 외부 접속(ngrok/cloudflare): /svc/{name}/ 프록시 경유
 */
export function resolve(envVar: string | undefined, localFallback: string, proxyPath: string): string {
  if (isLocal) return envVar || localFallback;
  return proxyPath;
}

// Core API Base URLs
export const API_BASE = resolve(import.meta.env.VITE_GATEWAY_URL, 'http://localhost:8000', '/svc/gateway');
export const GATEWAY_URL = API_BASE;
export const EDOCR2_BASE = resolve(import.meta.env.VITE_EDOCR2_URL, 'http://localhost:5001', '/svc/edocr2');
export const EDOCR2_V2_BASE = resolve(import.meta.env.VITE_EDOCR2_V2_URL, 'http://localhost:5002', '/svc/edocr2-v2');
export const EDGNET_BASE = resolve(import.meta.env.VITE_EDGNET_URL, 'http://localhost:5012', '/svc/edgnet');
export const SKINMODEL_BASE = resolve(import.meta.env.VITE_SKINMODEL_URL, 'http://localhost:5003', '/svc/skinmodel');
export const YOLO_BASE = resolve(import.meta.env.VITE_YOLO_URL, 'http://localhost:5005', '/svc/yolo');
export const PADDLEOCR_BASE = resolve(import.meta.env.VITE_PADDLEOCR_URL, 'http://localhost:5006', '/svc/paddleocr');
export const VL_BASE = resolve(import.meta.env.VITE_VL_URL, 'http://localhost:5004', '/svc/vl');

// Additional OCR Services
export const TESSERACT_BASE = resolve(import.meta.env.VITE_TESSERACT_URL, 'http://localhost:5008', '/svc/tesseract');
export const TROCR_BASE = resolve(import.meta.env.VITE_TROCR_URL, 'http://localhost:5009', '/svc/trocr');
export const ESRGAN_BASE = resolve(import.meta.env.VITE_ESRGAN_URL, 'http://localhost:5010', '/svc/esrgan');
export const OCR_ENSEMBLE_BASE = resolve(import.meta.env.VITE_OCR_ENSEMBLE_URL, 'http://localhost:5011', '/svc/ocr-ensemble');
export const SURYA_OCR_BASE = resolve(import.meta.env.VITE_SURYA_OCR_URL, 'http://localhost:5013', '/svc/surya-ocr');
export const DOCTR_BASE = resolve(import.meta.env.VITE_DOCTR_URL, 'http://localhost:5014', '/svc/doctr');
export const EASYOCR_BASE = resolve(import.meta.env.VITE_EASYOCR_URL, 'http://localhost:5015', '/svc/easyocr');

// Knowledge & P&ID Services
export const KNOWLEDGE_BASE = resolve(import.meta.env.VITE_KNOWLEDGE_URL, 'http://localhost:5007', '/svc/knowledge');
export const LINE_DETECTOR_BASE = resolve(import.meta.env.VITE_LINE_DETECTOR_URL, 'http://localhost:5016', '/svc/line-detector');
export const PID_ANALYZER_BASE = resolve(import.meta.env.VITE_PID_ANALYZER_URL, 'http://localhost:5018', '/svc/pid-analyzer');
export const DESIGN_CHECKER_BASE = resolve(import.meta.env.VITE_DESIGN_CHECKER_URL, 'http://localhost:5019', '/svc/design-checker');
export const BLUEPRINT_AI_BOM_BASE = resolve(import.meta.env.VITE_BLUEPRINT_AI_BOM_URL, 'http://localhost:5020', '/svc/bom');
export const PID_COMPOSER_BASE = resolve(import.meta.env.VITE_PID_COMPOSER_URL, 'http://localhost:5021', '/svc/pid-composer');
export const TABLE_DETECTOR_BASE = resolve(import.meta.env.VITE_TABLE_DETECTOR_URL, 'http://localhost:5022', '/svc/table-detector');
