/**
 * React Hook for Dynamic API Registry
 *
 * 백엔드에서 API 정의를 동적으로 로드하는 훅입니다.
 * 컴포넌트에서 쉽게 API 목록, 매핑, 파라미터를 가져올 수 있습니다.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  fetchAPIRegistry,
  getAPIParameters,
  getDefaultParameters,
  clearCache,
  CONTROL_NODES,
  type APIDefinition,
  type APIParameter,
  type NodeCategory,
} from '../services/apiRegistryService';

interface UseAPIRegistryResult {
  // Data
  apis: APIDefinition[];
  isLoading: boolean;
  error: Error | null;

  // Mappings (computed from apis)
  nodeToContainer: Record<string, string>;
  apiToContainer: Record<string, string>;
  apiToSpecId: Record<string, string>;

  // Methods
  getById: (id: string) => APIDefinition | undefined;
  getByNodeType: (nodeType: string) => APIDefinition | undefined;
  getByCategory: (category: NodeCategory) => APIDefinition[];
  refresh: () => Promise<void>;
}

/**
 * Hook to access the dynamic API registry
 */
export function useAPIRegistry(): UseAPIRegistryResult {
  const [apis, setApis] = useState<APIDefinition[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadAPIs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchAPIRegistry();
      setApis(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to load API registry'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAPIs();
  }, [loadAPIs]);

  // Computed mappings
  const nodeToContainer = useMemo(() => {
    return Object.fromEntries(
      apis
        .filter(api => api.id !== 'gateway')
        .map(api => [api.nodeType, api.containerName])
    );
  }, [apis]);

  const apiToContainer = useMemo(() => {
    return Object.fromEntries(
      apis.map(api => [api.id, api.containerName])
    );
  }, [apis]);

  const apiToSpecId = useMemo(() => {
    return Object.fromEntries(
      apis.map(api => [api.id, api.specId])
    );
  }, [apis]);

  // Methods
  const getById = useCallback(
    (id: string) => apis.find(api => api.id === id),
    [apis]
  );

  const getByNodeType = useCallback(
    (nodeType: string) => apis.find(api => api.nodeType === nodeType),
    [apis]
  );

  const getByCategory = useCallback(
    (category: NodeCategory) => apis.filter(api => api.category === category),
    [apis]
  );

  const refresh = useCallback(async () => {
    clearCache();
    await loadAPIs();
  }, [loadAPIs]);

  return {
    apis,
    isLoading,
    error,
    nodeToContainer,
    apiToContainer,
    apiToSpecId,
    getById,
    getByNodeType,
    getByCategory,
    refresh,
  };
}

interface UseAPIParametersResult {
  parameters: APIParameter[];
  defaults: Record<string, unknown>;
  isLoading: boolean;
  error: Error | null;
}

/**
 * Hook to get parameters for a specific API
 */
export function useAPIParameters(apiId: string): UseAPIParametersResult {
  const [parameters, setParameters] = useState<APIParameter[]>([]);
  const [defaults, setDefaults] = useState<Record<string, unknown>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!apiId) {
      setParameters([]);
      setDefaults({});
      setIsLoading(false);
      return;
    }

    const loadParams = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [params, defaultValues] = await Promise.all([
          getAPIParameters(apiId),
          getDefaultParameters(apiId),
        ]);
        setParameters(params);
        setDefaults(defaultValues);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to load parameters'));
      } finally {
        setIsLoading(false);
      }
    };

    loadParams();
  }, [apiId]);

  return { parameters, defaults, isLoading, error };
}

/**
 * Hook to check if a node requires a container
 */
export function useRequiresContainer(nodeType: string): boolean {
  return !CONTROL_NODES.includes(nodeType);
}

export { CONTROL_NODES };
export type { APIDefinition, APIParameter, NodeCategory };
