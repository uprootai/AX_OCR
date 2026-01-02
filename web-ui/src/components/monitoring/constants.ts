/**
 * API Status Monitor Constants
 * 모니터링 상수 정의
 */

import type { APIInfo } from './types';

// localStorage key for deleted APIs
export const DELETED_APIS_KEY = 'deleted-api-ids';

// 기본 API 정의 (실제 Docker 컨테이너 기준 - 22개 서비스)
export const DEFAULT_APIS: APIInfo[] = [
  // Orchestrator
  { id: 'gateway', name: 'gateway', display_name: 'Gateway API', base_url: 'http://localhost:8000', port: 8000, status: 'unknown', category: 'orchestrator', description: 'API Gateway & Orchestrator', icon: '🚀', color: '#6366f1', last_check: null },
  // Detection
  { id: 'yolo', name: 'yolo', display_name: 'YOLO (통합)', base_url: 'http://localhost:5005', port: 5005, status: 'unknown', category: 'detection', description: '기계도면 14종 + P&ID 60종 심볼 검출', icon: '🎯', color: '#ef4444', last_check: null },
  // OCR
  { id: 'edocr2', name: 'edocr2', display_name: 'eDOCr2', base_url: 'http://localhost:5002', port: 5002, status: 'unknown', category: 'ocr', description: '한국어 치수 인식', icon: '📐', color: '#3b82f6', last_check: null },
  { id: 'paddleocr', name: 'paddleocr', display_name: 'PaddleOCR', base_url: 'http://localhost:5006', port: 5006, status: 'unknown', category: 'ocr', description: '다국어 OCR', icon: '🔤', color: '#3b82f6', last_check: null },
  { id: 'tesseract', name: 'tesseract', display_name: 'Tesseract', base_url: 'http://localhost:5008', port: 5008, status: 'unknown', category: 'ocr', description: '문서 OCR', icon: '📄', color: '#3b82f6', last_check: null },
  { id: 'trocr', name: 'trocr', display_name: 'TrOCR', base_url: 'http://localhost:5009', port: 5009, status: 'unknown', category: 'ocr', description: '필기체 OCR', icon: '✍️', color: '#3b82f6', last_check: null },
  { id: 'ocr_ensemble', name: 'ocr_ensemble', display_name: 'OCR Ensemble', base_url: 'http://localhost:5011', port: 5011, status: 'unknown', category: 'ocr', description: '4엔진 가중 투표', icon: '🗳️', color: '#3b82f6', last_check: null },
  { id: 'surya_ocr', name: 'surya_ocr', display_name: 'Surya OCR', base_url: 'http://localhost:5013', port: 5013, status: 'unknown', category: 'ocr', description: '90+ 언어, 레이아웃 분석', icon: '🌞', color: '#3b82f6', last_check: null },
  { id: 'doctr', name: 'doctr', display_name: 'DocTR', base_url: 'http://localhost:5014', port: 5014, status: 'unknown', category: 'ocr', description: '2단계 파이프라인 OCR', icon: '📑', color: '#3b82f6', last_check: null },
  { id: 'easyocr', name: 'easyocr', display_name: 'EasyOCR', base_url: 'http://localhost:5015', port: 5015, status: 'unknown', category: 'ocr', description: '80+ 언어, CPU 친화적', icon: '👁️', color: '#3b82f6', last_check: null },
  // Segmentation
  { id: 'edgnet', name: 'edgnet', display_name: 'EDGNet', base_url: 'http://localhost:5012', port: 5012, status: 'unknown', category: 'segmentation', description: '엣지 기반 세그멘테이션', icon: '🔲', color: '#22c55e', last_check: null },
  { id: 'line_detector', name: 'line_detector', display_name: 'Line Detector', base_url: 'http://localhost:5016', port: 5016, status: 'unknown', category: 'segmentation', description: 'P&ID 라인 검출', icon: '📏', color: '#22c55e', last_check: null },
  // Preprocessing
  { id: 'esrgan', name: 'esrgan', display_name: 'ESRGAN', base_url: 'http://localhost:5010', port: 5010, status: 'unknown', category: 'preprocessing', description: '4x 이미지 업스케일링', icon: '🔍', color: '#f59e0b', last_check: null },
  // Analysis
  { id: 'skinmodel', name: 'skinmodel', display_name: 'SkinModel', base_url: 'http://localhost:5003', port: 5003, status: 'unknown', category: 'analysis', description: '공차 분석 & 제조성 예측', icon: '📊', color: '#8b5cf6', last_check: null },
  { id: 'pid_analyzer', name: 'pid_analyzer', display_name: 'PID Analyzer', base_url: 'http://localhost:5018', port: 5018, status: 'unknown', category: 'analysis', description: 'P&ID 연결 분석, BOM 생성', icon: '🔗', color: '#8b5cf6', last_check: null },
  { id: 'design_checker', name: 'design_checker', display_name: 'Design Checker', base_url: 'http://localhost:5019', port: 5019, status: 'unknown', category: 'analysis', description: 'P&ID 설계 규칙 검증', icon: '✅', color: '#8b5cf6', last_check: null },
  // Knowledge
  { id: 'knowledge', name: 'knowledge', display_name: 'Knowledge', base_url: 'http://localhost:5007', port: 5007, status: 'unknown', category: 'knowledge', description: 'Neo4j + GraphRAG', icon: '🧠', color: '#10b981', last_check: null },
  // AI
  { id: 'vl', name: 'vl', display_name: 'VL (Vision-Language)', base_url: 'http://localhost:5004', port: 5004, status: 'unknown', category: 'ai', description: 'Vision-Language 멀티모달', icon: '🤖', color: '#06b6d4', last_check: null },
  // Blueprint AI BOM
  { id: 'blueprint_ai_bom', name: 'blueprint_ai_bom', display_name: 'Blueprint AI BOM', base_url: 'http://localhost:5020', port: 5020, status: 'unknown', category: 'analysis', description: 'Human-in-the-Loop 도면 BOM 생성', icon: '📋', color: '#8b5cf6', last_check: null },
  // Visualization
  { id: 'pid_composer', name: 'pid_composer', display_name: 'PID Composer', base_url: 'http://localhost:5021', port: 5021, status: 'unknown', category: 'analysis', description: 'P&ID 레이어 합성, SVG 오버레이', icon: '🎨', color: '#8b5cf6', last_check: null },
];
