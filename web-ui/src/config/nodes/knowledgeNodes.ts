/**
 * Knowledge Nodes
 * 지식 엔진 및 GraphRAG 노드 정의
 */

import type { NodeDefinition } from './types';

export const knowledgeNodes: Record<string, NodeDefinition> = {
  knowledge: {
    type: 'knowledge',
    label: 'Knowledge Engine',
    category: 'knowledge',
    color: '#9333ea',
    icon: 'Database',
    description: 'Neo4j 그래프DB + RAG 기반 도메인 지식 엔진. 유사 부품 검색, ISO/ASME 규격 검증, 비용 추정 지원.',
    profiles: {
      default: 'general',
      available: [
        {
          name: 'general',
          label: '일반',
          description: 'Hybrid 검색 (GraphRAG + VectorRAG)',
          params: { search_mode: 'hybrid', graph_weight: 0.6, top_k: 5, validate_standards: true, include_cost: true },
        },
        {
          name: 'similarity',
          label: '유사도 검색',
          description: 'VectorRAG 기반 유사 부품 검색',
          params: { search_mode: 'vector', top_k: 10, validate_standards: false, include_cost: true },
        },
        {
          name: 'graph',
          label: '그래프 검색',
          description: 'GraphRAG 기반 관계 중심 검색',
          params: { search_mode: 'graph', top_k: 5, validate_standards: true, include_cost: false },
        },
        {
          name: 'validation',
          label: '규격 검증',
          description: 'ISO/ASME 규격 검증 전용',
          params: { search_mode: 'graph', top_k: 3, validate_standards: true, include_cost: false },
        },
      ],
    },
    inputs: [
      {
        name: 'ocr_results',
        type: 'OCRResult[]',
        description: '📝 OCR 결과 (치수, 공차, 재질 정보 포함)',
      },
      {
        name: 'query',
        type: 'string',
        description: '🔍 검색 쿼리 (예: "SUS304 Ø50 H7")',
      },
    ],
    outputs: [
      {
        name: 'similar_parts',
        type: 'SimilarPart[]',
        description: '🔎 유사 부품 목록 (과거 제조 이력, 비용 정보 포함)',
      },
      {
        name: 'validation_result',
        type: 'ValidationResult',
        description: '✅ ISO/ASME 규격 검증 결과',
      },
      {
        name: 'cost_estimate',
        type: 'CostEstimate',
        description: '💰 비용 추정 결과 (유사 부품 기반)',
      },
    ],
    parameters: [
      {
        name: 'search_mode',
        type: 'select',
        default: 'hybrid',
        options: ['graph', 'vector', 'hybrid'],
        description: '검색 모드 (graph: Neo4j 그래프, vector: FAISS 벡터, hybrid: 가중 결합)',
      },
      {
        name: 'graph_weight',
        type: 'number',
        default: 0.6,
        min: 0,
        max: 1,
        step: 0.1,
        description: 'Hybrid 모드에서 GraphRAG 가중치 (나머지는 VectorRAG)',
      },
      {
        name: 'top_k',
        type: 'number',
        default: 5,
        min: 1,
        max: 20,
        step: 1,
        description: '반환할 유사 부품 수',
      },
      {
        name: 'validate_standards',
        type: 'boolean',
        default: true,
        description: 'ISO/ASME 규격 자동 검증 활성화',
      },
      {
        name: 'include_cost',
        type: 'boolean',
        default: true,
        description: '유사 부품 기반 비용 추정 포함',
      },
      {
        name: 'material_filter',
        type: 'select',
        default: 'all',
        options: ['all', 'steel', 'stainless', 'aluminum', 'plastic', 'composite'],
        description: '재질 필터 (유사 부품 검색 시)',
      },
    ],
    examples: [
      'eDOCr2 OCR → Knowledge → 유사 부품 5개 검색',
      'TextInput("M10 H7") → Knowledge → ISO 규격 검증',
      '과거 제조 이력 기반 비용 추정',
    ],
    usageTips: [
      '⭐ eDOCr2나 PaddleOCR의 결과를 입력하면 치수/공차/재질 정보를 자동으로 추출합니다',
      '💡 Hybrid 모드가 가장 정확합니다 (GraphRAG 60% + VectorRAG 40%)',
      '💡 ISO 1101, ISO 286-2, ASME Y14.5 등 주요 규격을 자동 검증합니다',
      '💡 과거 유사 부품 제조 이력을 활용해 정확한 비용을 추정합니다',
      '💡 TextInput과 연결하여 직접 쿼리 검색도 가능합니다',
    ],
    recommendedInputs: [
      {
        from: 'edocr2',
        field: 'text_results',
        reason: '⭐ OCR 결과에서 치수, 공차, 재질 정보를 추출하여 유사 부품을 검색합니다',
      },
      {
        from: 'paddleocr',
        field: 'text_results',
        reason: 'PaddleOCR 결과도 동일하게 활용 가능합니다',
      },
      {
        from: 'textinput',
        field: 'text',
        reason: '직접 검색 쿼리를 입력하여 유사 부품을 검색합니다',
      },
      {
        from: 'skinmodel',
        field: 'tolerance_report',
        reason: '공차 분석 결과를 활용해 더 정밀한 유사 부품 검색이 가능합니다',
      },
    ],
  },
};
