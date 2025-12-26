/**
 * API Spec to Hyperparameter Definitions Converter
 *
 * api_specs/*.yaml의 parameters를 Dashboard 하이퍼파라미터 UI로 변환합니다.
 */

import axios from 'axios';

const GATEWAY_URL = import.meta.env.VITE_GATEWAY_URL || 'http://localhost:8000';

export interface HyperparamDefinition {
  key: string;
  label: string;
  type: 'number' | 'boolean' | 'select' | 'text';
  min?: number;
  max?: number;
  step?: number;
  options?: { value: string; label: string }[];
  description: string;
}

export interface APISpecParameter {
  name: string;
  type: string;
  default: string | number | boolean;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
  description?: string;
  uiType?: string;
}

interface CachedSpec {
  parameters: APISpecParameter[];
  timestamp: number;
}

// Cache for loaded specs
const specCache = new Map<string, CachedSpec>();
const CACHE_TTL = 60000; // 1 minute

/**
 * Convert API spec parameter type to UI type
 */
const mapParamType = (param: APISpecParameter): 'number' | 'boolean' | 'select' | 'text' => {
  // If explicit uiType is provided, use it
  if (param.uiType) {
    if (param.uiType === 'checkbox') return 'boolean';
    if (param.uiType === 'select') return 'select';
    if (param.uiType === 'slider' || param.uiType === 'number') return 'number';
    if (param.uiType === 'text') return 'text';
  }

  // Infer from type
  const type = param.type?.toLowerCase() || '';
  if (type === 'boolean') return 'boolean';
  if (type === 'select' || param.options?.length) return 'select';
  if (type === 'number' || type === 'integer' || type === 'float') return 'number';
  if (type === 'string' && !param.options?.length) return 'text';

  // Default based on value type
  if (typeof param.default === 'boolean') return 'boolean';
  if (typeof param.default === 'number') return 'number';
  if (param.options?.length) return 'select';

  return 'text';
};

/**
 * Convert API spec parameter to UI definition
 */
const convertParamToDefinition = (param: APISpecParameter): HyperparamDefinition => {
  const uiType = mapParamType(param);

  const def: HyperparamDefinition = {
    key: param.name,
    label: param.description || param.name,
    type: uiType,
    description: param.description || '',
  };

  if (uiType === 'number') {
    def.min = param.min;
    def.max = param.max;
    def.step = param.step || (param.max && param.max <= 1 ? 0.05 : 1);
  }

  if (uiType === 'select' && param.options) {
    def.options = param.options.map(opt => ({
      value: String(opt),
      label: String(opt),
    }));
  }

  return def;
};

/**
 * Fetch parameters for an API from spec
 */
export const fetchSpecParameters = async (apiId: string): Promise<APISpecParameter[]> => {
  // Check cache
  const cached = specCache.get(apiId);
  if (cached && (Date.now() - cached.timestamp) < CACHE_TTL) {
    return cached.parameters;
  }

  try {
    // Convert API ID to spec ID (underscore to hyphen)
    const specId = apiId.replace(/_/g, '-');
    const response = await axios.get(`${GATEWAY_URL}/api/v1/specs/${specId}`);
    const params = response.data.spec?.parameters || [];

    // Update cache
    specCache.set(apiId, {
      parameters: params,
      timestamp: Date.now(),
    });

    return params;
  } catch (error) {
    console.warn(`Failed to fetch spec for ${apiId}:`, error);
    return [];
  }
};

/**
 * Get hyperparameter definitions from API spec
 * Note: Array type parameters are filtered out as Dashboard UI doesn't support them
 */
export const getHyperparamDefinitions = async (apiId: string): Promise<HyperparamDefinition[]> => {
  const params = await fetchSpecParameters(apiId);
  // Filter out array type parameters - Dashboard UI doesn't support complex multi-select
  const simpleParams = params.filter(p => p.type?.toLowerCase() !== 'array');
  return simpleParams.map(convertParamToDefinition);
};

/**
 * Get default hyperparameter values from API spec
 * Note: Array type parameters are filtered out as Dashboard UI doesn't support them
 */
export const getDefaultHyperparams = async (apiId: string): Promise<Record<string, unknown>> => {
  const params = await fetchSpecParameters(apiId);
  // Filter out array type parameters - Dashboard UI doesn't support complex multi-select
  const simpleParams = params.filter(p => p.type?.toLowerCase() !== 'array');
  return Object.fromEntries(
    simpleParams.map(p => [p.name, p.default])
  );
};

/**
 * Get hyperparameter definitions with fallback to hardcoded
 */
export const getHyperparamDefinitionsWithFallback = async (
  apiId: string,
  hardcodedDefinitions: Record<string, HyperparamDefinition[]>
): Promise<HyperparamDefinition[]> => {
  try {
    const specDefs = await getHyperparamDefinitions(apiId);
    if (specDefs.length > 0) {
      return specDefs;
    }
  } catch (error) {
    console.warn(`Using fallback definitions for ${apiId}`);
  }

  // Fallback to hardcoded
  return hardcodedDefinitions[apiId] || [];
};

/**
 * Get default hyperparams with fallback to hardcoded
 */
export const getDefaultHyperparamsWithFallback = async (
  apiId: string,
  hardcodedDefaults: Record<string, Record<string, unknown>>
): Promise<Record<string, unknown>> => {
  try {
    const specDefaults = await getDefaultHyperparams(apiId);
    if (Object.keys(specDefaults).length > 0) {
      return specDefaults;
    }
  } catch (error) {
    console.warn(`Using fallback defaults for ${apiId}`);
  }

  // Fallback to hardcoded
  return hardcodedDefaults[apiId] || {};
};

/**
 * Clear cache
 */
export const clearSpecCache = (): void => {
  specCache.clear();
};

export default {
  fetchSpecParameters,
  getHyperparamDefinitions,
  getDefaultHyperparams,
  getHyperparamDefinitionsWithFallback,
  getDefaultHyperparamsWithFallback,
  clearSpecCache,
};
