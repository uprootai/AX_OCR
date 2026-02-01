/**
 * Node Palette Constants
 * 노드 팔레트의 기본 노드 설정 및 상수
 */

import {
  Image,
  Target,
  FileText,
  Network,
  Ruler,
  FileSearch,
  Eye,
  GitBranch,
  Repeat,
  Merge as MergeIcon,
  Type,
  Database,
  ScanText,
  Wand2,
  Maximize2,
  Layers,
  Minus,
  ShieldCheck,
  FileSpreadsheet,
  ClipboardCheck,
  Workflow,
  Table,
} from 'lucide-react';
import type { NodeConfig } from './types';

/**
 * 기본 노드 설정
 * 모든 기본 노드 타입과 해당 메타데이터
 */
export const baseNodeConfigs: NodeConfig[] = [
  // Input Nodes
  {
    type: 'imageinput',
    label: 'Image Input',
    description: 'Workflow starting point',
    icon: Image,
    color: '#f97316',
    category: 'input',
  },
  {
    type: 'textinput',
    label: 'Text Input',
    description: 'Text input for non-image APIs',
    icon: Type,
    color: '#8b5cf6',
    category: 'input',
  },
  // BOM Nodes (Human-in-the-Loop 워크플로우)
  {
    type: 'blueprint-ai-bom',
    label: 'Blueprint AI BOM',
    description: 'Human-in-the-Loop BOM 생성',
    icon: FileSpreadsheet,
    color: '#8b5cf6',
    category: 'bom',
  },
  // Detection Nodes
  {
    type: 'yolo',
    label: 'YOLO (통합)',
    description: '기계도면 + P&ID 심볼 검출',
    icon: Target,
    color: '#10b981',
    category: 'detection',
  },
  {
    type: 'table_detector',
    label: 'Table Detector',
    description: '테이블 검출 및 구조 추출',
    icon: Table,
    color: '#10B981',
    category: 'detection',
  },
  {
    type: 'linedetector',
    label: 'Line Detector',
    description: 'P&ID line detection',
    icon: Minus,
    color: '#0d9488',
    category: 'segmentation',
  },
  // OCR Nodes
  {
    type: 'edocr2',
    label: 'eDOCr2',
    description: 'Korean OCR',
    icon: FileText,
    color: '#3b82f6',
    category: 'ocr',
  },
  {
    type: 'paddleocr',
    label: 'PaddleOCR',
    description: 'Multi-language OCR',
    icon: FileSearch,
    color: '#06b6d4',
    category: 'ocr',
  },
  // Segmentation Nodes
  {
    type: 'edgnet',
    label: 'EDGNet',
    description: 'Edge segmentation',
    icon: Network,
    color: '#8b5cf6',
    category: 'segmentation',
  },
  // Analysis Nodes
  {
    type: 'skinmodel',
    label: 'SkinModel',
    description: 'Tolerance analysis',
    icon: Ruler,
    color: '#f59e0b',
    category: 'analysis',
  },
  {
    type: 'pidanalyzer',
    label: 'P&ID Analyzer',
    description: 'BOM & connectivity analysis',
    icon: Network,
    color: '#7c3aed',
    category: 'analysis',
  },
  {
    type: 'designchecker',
    label: 'Design Checker',
    description: 'Design rule validation',
    icon: ShieldCheck,
    color: '#ef4444',
    category: 'analysis',
  },
  {
    type: 'gtcomparison',
    label: 'GT Comparison',
    description: 'Ground Truth comparison',
    icon: '📊',
    color: '#f97316',
    category: 'analysis',
  },
  {
    type: 'pidcomposer',
    label: 'PID Composer',
    description: 'P&ID layer composition',
    icon: Layers,
    color: '#8b5cf6',
    category: 'analysis',
  },
  {
    type: 'pidfeatures',
    label: 'PID Features',
    description: 'TECHCROSS P&ID analysis',
    icon: Workflow,
    color: '#8b5cf6',
    category: 'analysis',
  },
  {
    type: 'pdfexport',
    label: 'PDF Export',
    description: 'Export to PDF report',
    icon: FileText,
    color: '#dc2626',
    category: 'analysis',
  },
  {
    type: 'verificationqueue',
    label: 'Verification Queue',
    description: 'Human-in-the-Loop queue',
    icon: ClipboardCheck,
    color: '#f59e0b',
    category: 'analysis',
  },
  // DSE Bearing Nodes
  {
    type: 'titleblock',
    label: 'Title Block Parser',
    description: 'DSE Bearing 도면 Title Block 파싱',
    icon: FileText,
    color: '#6366f1',
    category: 'analysis',
  },
  {
    type: 'partslist',
    label: 'Parts List Parser',
    description: 'DSE Bearing 도면 부품 목록 파싱',
    icon: Table,
    color: '#10b981',
    category: 'analysis',
  },
  {
    type: 'dimensionparser',
    label: 'Dimension Parser',
    description: '베어링 치수 구조화 파싱',
    icon: Ruler,
    color: '#f59e0b',
    category: 'analysis',
  },
  {
    type: 'bommatcher',
    label: 'BOM Matcher',
    description: '도면 분석 결과 통합 BOM 생성',
    icon: Database,
    color: '#059669',
    category: 'analysis',
  },
  {
    type: 'quotegenerator',
    label: 'Quote Generator',
    description: 'BOM 기반 자동 견적 생성',
    icon: FileSpreadsheet,
    color: '#dc2626',
    category: 'analysis',
  },
  // AI Nodes
  {
    type: 'vl',
    label: 'VL Model',
    description: 'Vision-Language AI',
    icon: Eye,
    color: '#ec4899',
    category: 'ai',
  },
  // Control Nodes
  {
    type: 'if',
    label: 'IF',
    description: 'Conditional branching',
    icon: GitBranch,
    color: '#ef4444',
    category: 'control',
  },
  {
    type: 'loop',
    label: 'Loop',
    description: 'Iterate over items',
    icon: Repeat,
    color: '#f97316',
    category: 'control',
  },
  {
    type: 'merge',
    label: 'Merge',
    description: 'Combine outputs',
    icon: MergeIcon,
    color: '#14b8a6',
    category: 'control',
  },
  // Knowledge Nodes
  {
    type: 'knowledge',
    label: 'Knowledge',
    description: 'Domain knowledge engine',
    icon: Database,
    color: '#9333ea',
    category: 'knowledge',
  },
  // Preprocessing Nodes
  {
    type: 'esrgan',
    label: 'ESRGAN',
    description: '4x image upscaling',
    icon: Maximize2,
    color: '#dc2626',
    category: 'preprocessing',
  },
  // OCR Nodes
  {
    type: 'tesseract',
    label: 'Tesseract',
    description: 'Google Tesseract OCR',
    icon: ScanText,
    color: '#059669',
    category: 'ocr',
  },
  {
    type: 'trocr',
    label: 'TrOCR',
    description: 'Transformer OCR',
    icon: Wand2,
    color: '#7c3aed',
    category: 'ocr',
  },
  {
    type: 'ocr_ensemble',
    label: 'OCR Ensemble',
    description: '4-way OCR voting',
    icon: Layers,
    color: '#0891b2',
    category: 'ocr',
  },
  {
    type: 'suryaocr',
    label: 'Surya OCR',
    description: '90+ language OCR',
    icon: '🌞',
    color: '#f59e0b',
    category: 'ocr',
  },
  {
    type: 'doctr',
    label: 'DocTR',
    description: '2-stage OCR pipeline',
    icon: '📄',
    color: '#6366f1',
    category: 'ocr',
  },
  {
    type: 'easyocr',
    label: 'EasyOCR',
    description: '80+ language OCR',
    icon: '👁️',
    color: '#22c55e',
    category: 'ocr',
  },
];

/**
 * 컨테이너 상태와 무관하게 항상 활성화되는 노드 타입
 */
export const ALWAYS_ACTIVE_NODE_TYPES = ['imageinput', 'textinput', 'if', 'loop', 'merge'];

/**
 * 컨테이너 상태 폴링 간격 (밀리초)
 */
export const CONTAINER_STATUS_POLL_INTERVAL = 5000;
