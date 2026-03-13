/**
 * OCR Nodes — barrel re-export
 * 텍스트 인식 노드 정의 (8개 OCR 엔진)
 *
 * 상세 구현:
 *   ./ocrNodes/edocr2PaddleNodes.ts    — eDOCr2, PaddleOCR
 *   ./ocrNodes/tesseractTrocrNodes.ts  — Tesseract, TrOCR
 *   ./ocrNodes/ensembleAdvancedNodes.ts — OCR Ensemble, Surya OCR
 *   ./ocrNodes/doctrEasyocrNodes.ts    — DocTR, EasyOCR
 */

import type { NodeDefinition } from './types';
import { edocr2PaddleNodes } from './ocrNodes/edocr2PaddleNodes';
import { tesseractTrocrNodes } from './ocrNodes/tesseractTrocrNodes';
import { ensembleAdvancedNodes } from './ocrNodes/ensembleAdvancedNodes';
import { doctrEasyocrNodes } from './ocrNodes/doctrEasyocrNodes';

export const ocrNodes: Record<string, NodeDefinition> = {
  ...edocr2PaddleNodes,
  ...tesseractTrocrNodes,
  ...ensembleAdvancedNodes,
  ...doctrEasyocrNodes,
};
