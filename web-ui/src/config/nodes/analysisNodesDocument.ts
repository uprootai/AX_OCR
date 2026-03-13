/**
 * Document Analysis Nodes — Barrel
 * 도면 문서 분석 노드 (Title Block, Parts List, Dimension Parser)
 *
 * 개별 모듈:
 *   analysisNodesDocument.titleblock.ts
 *   analysisNodesDocument.partslist.ts
 *   analysisNodesDocument.dimensionparser.ts
 */

import type { NodeDefinition } from './types';
import { titleblockNode } from './analysisNodesDocument.titleblock';
import { partslistNode } from './analysisNodesDocument.partslist';
import { dimensionparserNode } from './analysisNodesDocument.dimensionparser';

export const documentNodes: Record<string, NodeDefinition> = {
  titleblock: titleblockNode,
  partslist: partslistNode,
  dimensionparser: dimensionparserNode,
};
