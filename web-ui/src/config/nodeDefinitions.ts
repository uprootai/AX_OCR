/**
 * Node Definitions
 *
 * 노드 정의가 카테고리별로 분리되었습니다:
 * - src/config/nodes/inputNodes.ts
 * - src/config/nodes/detectionNodes.ts
 * - src/config/nodes/ocrNodes.ts
 * - src/config/nodes/segmentationNodes.ts
 * - src/config/nodes/preprocessingNodes.ts
 * - src/config/nodes/analysisNodes.ts
 * - src/config/nodes/knowledgeNodes.ts
 * - src/config/nodes/aiNodes.ts
 * - src/config/nodes/controlNodes.ts
 * - src/config/nodes/bomNodes.ts
 *
 * 이 파일은 하위 호환성을 위해 모든 export를 re-export합니다.
 */

export type { NodeParameter, RecommendedInput, NodeDefinition } from './nodes';
export { nodeDefinitions, getNodeDefinition, getAllNodeDefinitions } from './nodes';

// Category exports for direct access
export {
  inputNodes,
  detectionNodes,
  ocrNodes,
  segmentationNodes,
  preprocessingNodes,
  analysisNodes,
  knowledgeNodes,
  aiNodes,
  controlNodes,
  bomNodes,
} from './nodes';
