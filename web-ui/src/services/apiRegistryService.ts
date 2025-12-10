/**
 * Dynamic API Registry Service
 *
 * 백엔드 api_specs/*.yaml에서 동적으로 API 정의를 로드합니다.
 * apiRegistry.ts (정적)을 대체하여 Dashboard에서 추가한 API도 자동 반영됩니다.
 */

import axios from 'axios';

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000';

export type NodeCategory =
  | 'input'
  | 'detection'
  | 'ocr'
  | 'segmentation'
  | 'preprocessing'
  | 'analysis'
  | 'knowledge'
  | 'ai'
  | 'control';

export interface APIParameter {
  name: string;
  type: string;
  default: string | number | boolean;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
  description?: string;
  uiType?: string;
  required?: boolean;
}

export interface APIDefinition {
  id: string;
  nodeType: string;
  displayName: string;
  containerName: string;
  specId: string;
  port: number;
  category: NodeCategory;
  description: string;
  icon: string;
  color: string;
  gpuEnabled: boolean;
  // Extended fields from YAML
  endpoint?: string;
  method?: string;
  parameters?: APIParameter[];
  inputs?: Array<{ name: string; type: string; required?: boolean; description?: string }>;
  outputs?: Array<{ name: string; type: string; description?: string }>;
}

interface APISpec {
  apiVersion: string;
  kind: string;
  metadata: {
    id: string;
    name: string;
    version?: string;
    host?: string;
    port: number;
    description?: string;
    author?: string;
    tags?: string[];
  };
  server?: {
    endpoint?: string;
    method?: string;
    contentType?: string;
    timeout?: number;
    healthEndpoint?: string;
  };
  blueprintflow?: {
    category?: string;
    color?: string;
    icon?: string;
    requiresImage?: boolean;
  };
  inputs?: Array<{ name: string; type: string; required?: boolean; description?: string }>;
  outputs?: Array<{ name: string; type: string; description?: string }>;
  parameters?: APIParameter[];
  resources?: {
    gpu?: { vram?: string; minVram?: number };
    cpu?: { ram?: string; minRam?: number };
  };
}

// Cache for API definitions
let cachedAPIs: APIDefinition[] | null = null;
let cacheTimestamp = 0;
const CACHE_TTL = 60000; // 1 minute

/**
 * Convert spec ID to node type (remove hyphens, lowercase)
 */
const specIdToNodeType = (specId: string): string => {
  return specId.replace(/-/g, '').toLowerCase();
};

/**
 * Convert spec ID to container name
 */
const specIdToContainerName = (specId: string): string => {
  return `${specId}-api`;
};

/**
 * Convert API spec to APIDefinition
 */
const convertSpecToDefinition = (specId: string, spec: APISpec): APIDefinition => {
  const metadata = spec.metadata;
  const blueprintflow = spec.blueprintflow || {};
  const server = spec.server || {};
  const resources = spec.resources || {};

  return {
    id: metadata.id,
    nodeType: specIdToNodeType(metadata.id),
    displayName: metadata.name,
    containerName: metadata.host || specIdToContainerName(specId),
    specId: specId,
    port: metadata.port,
    category: (blueprintflow.category as NodeCategory) || 'analysis',
    description: metadata.description || '',
    icon: blueprintflow.icon || 'Server',
    color: blueprintflow.color || '#6366f1',
    gpuEnabled: !!(resources.gpu?.minVram),
    endpoint: server.endpoint,
    method: server.method,
    parameters: spec.parameters || [],
    inputs: spec.inputs || [],
    outputs: spec.outputs || [],
  };
};

/**
 * Fetch all API definitions from backend
 */
export const fetchAPIRegistry = async (forceRefresh = false): Promise<APIDefinition[]> => {
  const now = Date.now();

  // Return cached data if valid
  if (!forceRefresh && cachedAPIs && (now - cacheTimestamp) < CACHE_TTL) {
    return cachedAPIs;
  }

  try {
    const response = await axios.get(`${GATEWAY_URL}/api/v1/specs`);
    const specs = response.data.specs as Record<string, APISpec>;

    const definitions: APIDefinition[] = [];

    for (const [specId, spec] of Object.entries(specs)) {
      definitions.push(convertSpecToDefinition(specId, spec));
    }

    // Add gateway (not in specs but needed)
    definitions.unshift({
      id: 'gateway',
      nodeType: 'gateway',
      displayName: 'Gateway API',
      containerName: 'gateway-api',
      specId: 'gateway',
      port: 8000,
      category: 'control',
      description: 'API Gateway & Orchestrator',
      icon: 'Server',
      color: '#6366f1',
      gpuEnabled: false,
    });

    // Update cache
    cachedAPIs = definitions;
    cacheTimestamp = now;

    return definitions;
  } catch (error) {
    console.error('Failed to fetch API registry:', error);
    // Return cached data if available, even if stale
    if (cachedAPIs) {
      return cachedAPIs;
    }
    throw error;
  }
};

/**
 * Get API definition by ID
 */
export const getAPIById = async (id: string): Promise<APIDefinition | undefined> => {
  const apis = await fetchAPIRegistry();
  return apis.find(api => api.id === id);
};

/**
 * Get API definition by node type
 */
export const getAPIByNodeType = async (nodeType: string): Promise<APIDefinition | undefined> => {
  const apis = await fetchAPIRegistry();
  return apis.find(api => api.nodeType === nodeType);
};

/**
 * Get APIs by category
 */
export const getAPIsByCategory = async (category: NodeCategory): Promise<APIDefinition[]> => {
  const apis = await fetchAPIRegistry();
  return apis.filter(api => api.category === category);
};

/**
 * Get NODE_TO_CONTAINER mapping (for backward compatibility)
 */
export const getNodeToContainerMap = async (): Promise<Record<string, string>> => {
  const apis = await fetchAPIRegistry();
  return Object.fromEntries(
    apis
      .filter(api => api.id !== 'gateway')
      .map(api => [api.nodeType, api.containerName])
  );
};

/**
 * Get API_TO_CONTAINER mapping (for backward compatibility)
 */
export const getApiToContainerMap = async (): Promise<Record<string, string>> => {
  const apis = await fetchAPIRegistry();
  return Object.fromEntries(
    apis.map(api => [api.id, api.containerName])
  );
};

/**
 * Get API_TO_SPEC_ID mapping (for backward compatibility)
 */
export const getApiToSpecIdMap = async (): Promise<Record<string, string>> => {
  const apis = await fetchAPIRegistry();
  return Object.fromEntries(
    apis.map(api => [api.id, api.specId])
  );
};

/**
 * Get parameters for an API (for Dashboard settings)
 */
export const getAPIParameters = async (apiId: string): Promise<APIParameter[]> => {
  const api = await getAPIById(apiId);
  return api?.parameters || [];
};

/**
 * Get default parameter values for an API
 */
export const getDefaultParameters = async (apiId: string): Promise<Record<string, unknown>> => {
  const params = await getAPIParameters(apiId);
  return Object.fromEntries(
    params.map(p => [p.name, p.default])
  );
};

/**
 * Clear cache (useful after adding new API)
 */
export const clearCache = (): void => {
  cachedAPIs = null;
  cacheTimestamp = 0;
};

/**
 * Control nodes that don't need containers
 */
export const CONTROL_NODES = ['imageinput', 'textinput', 'if', 'loop', 'merge'];

/**
 * Check if node requires container
 */
export const requiresContainer = (nodeType: string): boolean => {
  return !CONTROL_NODES.includes(nodeType);
};

export default {
  fetchAPIRegistry,
  getAPIById,
  getAPIByNodeType,
  getAPIsByCategory,
  getNodeToContainerMap,
  getApiToContainerMap,
  getApiToSpecIdMap,
  getAPIParameters,
  getDefaultParameters,
  clearCache,
  CONTROL_NODES,
  requiresContainer,
};
