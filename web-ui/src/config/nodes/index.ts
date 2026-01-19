/**
 * Node Definitions Index
 * 모든 노드 정의 통합 및 export
 */

// Types
export type { NodeParameter, RecommendedInput, NodeDefinition, ProfileDefinition, ProfilesConfig } from './types';

// Node definitions by category
export { inputNodes } from './inputNodes';
export { detectionNodes } from './detectionNodes';
export { ocrNodes } from './ocrNodes';
export { segmentationNodes } from './segmentationNodes';
export { preprocessingNodes } from './preprocessingNodes';
export { analysisNodes } from './analysisNodes';
export { knowledgeNodes } from './knowledgeNodes';
export { aiNodes } from './aiNodes';
export { controlNodes } from './controlNodes';
export { bomNodes } from './bomNodes';

// Import all for combined export
import { inputNodes } from './inputNodes';
import { detectionNodes } from './detectionNodes';
import { ocrNodes } from './ocrNodes';
import { segmentationNodes } from './segmentationNodes';
import { preprocessingNodes } from './preprocessingNodes';
import { analysisNodes } from './analysisNodes';
import { knowledgeNodes } from './knowledgeNodes';
import { aiNodes } from './aiNodes';
import { controlNodes } from './controlNodes';
import { bomNodes } from './bomNodes';
import type { NodeDefinition } from './types';

/**
 * 모든 정적 노드 정의 (카테고리별 병합)
 */
export const nodeDefinitions: Record<string, NodeDefinition> = {
  ...inputNodes,
  ...detectionNodes,
  ...ocrNodes,
  ...segmentationNodes,
  ...preprocessingNodes,
  ...analysisNodes,
  ...knowledgeNodes,
  ...aiNodes,
  ...controlNodes,
  ...bomNodes,
};

/**
 * 노드 타입으로 정의 조회
 */
export function getNodeDefinition(type: string): NodeDefinition | undefined {
  return nodeDefinitions[type];
}

/**
 * 커스텀 API를 포함한 모든 노드 정의 반환
 * localStorage의 customAPIs를 읽어서 동적으로 추가
 */
export function getAllNodeDefinitions(): Record<string, NodeDefinition> {
  // 기본 노드 정의
  const allDefinitions = { ...nodeDefinitions };

  // 커스텀 API 로드
  try {
    const customAPIsJSON = localStorage.getItem('custom-apis-storage');
    if (customAPIsJSON) {
      const storage = JSON.parse(customAPIsJSON);
      const customAPIs = storage.state?.customAPIs || [];

      // 각 커스텀 API를 노드 정의로 변환
      customAPIs.forEach((api: {
        id: string;
        enabled: boolean;
        displayName: string;
        category: NodeDefinition['category'];
        color: string;
        icon: string;
        description: string;
        inputs?: NodeDefinition['inputs'];
        outputs?: NodeDefinition['outputs'];
        parameters?: NodeDefinition['parameters'];
      }) => {
        if (api.enabled) {
          allDefinitions[api.id] = {
            type: api.id,
            label: api.displayName,
            category: api.category,
            color: api.color,
            icon: api.icon,
            description: api.description,
            inputs: api.inputs || [
              {
                name: 'input',
                type: 'any',
                description: '📥 입력 데이터',
              },
            ],
            outputs: api.outputs || [
              {
                name: 'output',
                type: 'any',
                description: '📤 출력 데이터',
              },
            ],
            parameters: api.parameters || [],
            examples: [],
          };
        }
      });
    }
  } catch (error) {
    console.error('Failed to load custom API node definitions:', error);
  }

  return allDefinitions;
}
