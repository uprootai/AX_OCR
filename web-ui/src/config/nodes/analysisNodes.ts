/**
 * Analysis Nodes - Barrel Re-export
 * 분석 및 검증 노드 정의 (도메인별 분리)
 */

import type { NodeDefinition } from './types';
import { pidNodes } from './analysisNodesPid';
import { documentNodes } from './analysisNodesDocument';
import { bomAnalysisNodes } from './analysisNodesBom';
import { qualityNodes } from './analysisNodesQuality';

export const analysisNodes: Record<string, NodeDefinition> = {
  ...pidNodes,
  ...documentNodes,
  ...bomAnalysisNodes,
  ...qualityNodes,
};
