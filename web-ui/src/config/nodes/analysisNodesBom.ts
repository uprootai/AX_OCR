/**
 * BOM & Quote Nodes — barrel re-export
 * BOM 매칭, 견적 생성, 치수 업데이트, PDF 내보내기 노드
 *
 * 실제 구현: ./analysisNodesBom/
 */

import type { NodeDefinition } from './types';
import {
  bomMatcherNode,
  quoteGeneratorNode,
  dimensionUpdaterNode,
  pdfExportNode,
} from './analysisNodesBom/index';

export const bomAnalysisNodes: Record<string, NodeDefinition> = {
  ...bomMatcherNode,
  ...quoteGeneratorNode,
  ...dimensionUpdaterNode,
  ...pdfExportNode,
};
