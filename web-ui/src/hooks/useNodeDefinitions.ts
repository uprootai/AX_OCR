/**
 * useNodeDefinitions Hook
 * 정적 nodeDefinitions와 동적 API 스펙을 병합하여 제공
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { nodeDefinitions } from '../config/nodeDefinitions';
import type { NodeDefinition } from '../config/nodeDefinitions';
import { fetchAllNodeDefinitions } from '../services/specService';
import { useTranslation } from 'react-i18next';

interface UseNodeDefinitionsOptions {
  /**
   * 동적 스펙 로딩 활성화 (기본: true)
   */
  enableDynamicSpecs?: boolean;

  /**
   * 새로고침 간격 (밀리초, 0이면 비활성화)
   */
  refreshInterval?: number;
}

interface UseNodeDefinitionsResult {
  /**
   * 병합된 노드 정의
   */
  definitions: Record<string, NodeDefinition>;

  /**
   * 로딩 상태
   */
  isLoading: boolean;

  /**
   * 에러 메시지
   */
  error: string | null;

  /**
   * 수동 새로고침
   */
  refresh: () => Promise<void>;

  /**
   * 카테고리별 노드 그룹
   */
  categorizedNodes: Record<string, NodeDefinition[]>;

  /**
   * 특정 타입의 노드 정의 가져오기
   */
  getDefinition: (type: string) => NodeDefinition | undefined;
}

/**
 * 노드 정의 관리 훅
 */
export function useNodeDefinitions(
  options: UseNodeDefinitionsOptions = {}
): UseNodeDefinitionsResult {
  const { enableDynamicSpecs = true, refreshInterval = 0 } = options;

  const { i18n } = useTranslation();
  const lang = (i18n.language === 'ko' ? 'ko' : 'en') as 'ko' | 'en';

  const [dynamicDefs, setDynamicDefs] = useState<Record<string, NodeDefinition>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 동적 스펙 로드
  const loadDynamicSpecs = useCallback(async () => {
    if (!enableDynamicSpecs) return;

    setIsLoading(true);
    setError(null);

    try {
      const specs = await fetchAllNodeDefinitions(lang);
      setDynamicDefs(specs);
    } catch (err) {
      console.error('Failed to load dynamic specs:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [enableDynamicSpecs, lang]);

  // 초기 로드
  useEffect(() => {
    loadDynamicSpecs();
  }, [loadDynamicSpecs]);

  // 자동 새로고침
  useEffect(() => {
    if (refreshInterval > 0 && enableDynamicSpecs) {
      const intervalId = setInterval(loadDynamicSpecs, refreshInterval);
      return () => clearInterval(intervalId);
    }
  }, [refreshInterval, enableDynamicSpecs, loadDynamicSpecs]);

  // 정적 + 동적 병합 (정적이 우선)
  const definitions = useMemo(() => {
    return {
      ...dynamicDefs,
      ...nodeDefinitions, // 정적 정의가 우선
    };
  }, [dynamicDefs]);

  // 카테고리별 그룹화
  const categorizedNodes = useMemo(() => {
    const categories: Record<string, NodeDefinition[]> = {};

    for (const def of Object.values(definitions)) {
      if (!categories[def.category]) {
        categories[def.category] = [];
      }
      categories[def.category].push(def);
    }

    // 각 카테고리 내 정렬
    for (const category of Object.keys(categories)) {
      categories[category].sort((a, b) => a.label.localeCompare(b.label));
    }

    return categories;
  }, [definitions]);

  // 타입으로 정의 가져오기
  const getDefinition = (type: string): NodeDefinition | undefined => {
    return definitions[type];
  };

  return {
    definitions,
    isLoading,
    error,
    refresh: loadDynamicSpecs,
    categorizedNodes,
    getDefinition,
  };
}

/**
 * 간단한 노드 정의 접근 훅 (동적 로딩 없이)
 */
export function useStaticNodeDefinitions(): Record<string, NodeDefinition> {
  return nodeDefinitions;
}

export default useNodeDefinitions;
