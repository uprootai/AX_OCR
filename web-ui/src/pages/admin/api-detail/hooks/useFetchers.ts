/**
 * Data fetching callbacks for useAPIDetail hook
 */

import { useState, useCallback } from 'react';
import axios from 'axios';
import { ADMIN_ENDPOINTS } from '../../../../config/api';
import { getHyperparamDefinitions, getDefaultHyperparams, type HyperparamDefinition } from '../../../../utils/specToHyperparams';
import { DEFAULT_APIS } from '../../../../components/monitoring/constants';
import type { APIInfo } from '../../../../components/monitoring/types';
import { apiKeyApi, GATEWAY_URL, type AllAPIKeySettings } from '../../../../lib/api';
import { DEFAULT_HYPERPARAMS } from '../config/defaultHyperparams';
import type { APIConfig, GPUInfo, ContainerStatus, HyperParams } from './types';

export interface FetchersState {
  apiInfo: APIInfo | null;
  logs: string;
  gpuInfo: GPUInfo | null;
  containerStatus: ContainerStatus | null;
  apiKeySettings: AllAPIKeySettings | null;
  dynamicHyperparamDefs: HyperparamDefinition[];
  loading: boolean;
}

export interface FetchersActions {
  setApiInfo: React.Dispatch<React.SetStateAction<APIInfo | null>>;
  setLogs: React.Dispatch<React.SetStateAction<string>>;
  setGpuInfo: React.Dispatch<React.SetStateAction<GPUInfo | null>>;
  setContainerStatus: React.Dispatch<React.SetStateAction<ContainerStatus | null>>;
  setApiKeySettings: React.Dispatch<React.SetStateAction<AllAPIKeySettings | null>>;
  setDynamicHyperparamDefs: React.Dispatch<React.SetStateAction<HyperparamDefinition[]>>;
  setLoading: React.Dispatch<React.SetStateAction<boolean>>;
  setConfig: React.Dispatch<React.SetStateAction<APIConfig>>;
}

export function useFetchers(apiId: string | undefined) {
  const [apiInfo, setApiInfo] = useState<APIInfo | null>(null);
  const [logs, setLogs] = useState<string>('');
  const [gpuInfo, setGpuInfo] = useState<GPUInfo | null>(null);
  const [containerStatus, setContainerStatus] = useState<ContainerStatus | null>(null);
  const [apiKeySettings, setApiKeySettings] = useState<AllAPIKeySettings | null>(null);
  const [dynamicHyperparamDefs, setDynamicHyperparamDefs] = useState<HyperparamDefinition[]>([]);
  const [loading, setLoading] = useState(true);

  // setConfig is passed in via the setter returned from the parent hook's useState
  // We need a way to wire setConfig — expose a setter reference pattern
  // Instead, fetch functions that need setConfig will accept it as a parameter.

  const fetchAPIInfo = useCallback(
    async (setConfig: React.Dispatch<React.SetStateAction<APIConfig>>) => {
      if (!apiId) return;

      const normalizedId = apiId.replace(/-/g, '_');

      try {
        let api: APIInfo | undefined;

        // 1. Find in DEFAULT_APIS first
        api = DEFAULT_APIS.find((a) =>
          a.id === apiId || a.name === apiId || a.id === normalizedId || a.name === normalizedId
        );

        // 2. Try Gateway Registry for additional info
        try {
          const response = await axios.get(`${GATEWAY_URL}/api/v1/registry/list`, { timeout: 3000 });
          const registryApis = response.data.apis || [];
          const registryApi = registryApis.find((a: APIInfo) =>
            a.id === apiId || a.name === apiId || a.id === normalizedId || a.name === normalizedId
          );

          if (registryApi) {
            api = {
              ...registryApi,
              base_url: registryApi.base_url?.replace(/-(api|api):/, '-api:').replace(/http:\/\/[^:]+:/, 'http://localhost:'),
            };
          }
        } catch {
          // Continue with DEFAULT_APIS if registry fails
        }

        if (api) {
          setApiInfo(api);

          // Load saved configurations
          const savedConfigs = localStorage.getItem('serviceConfigs');
          const savedHyperParams = localStorage.getItem('hyperParameters');
          const effectiveApiId = api.id;

          let loadedConfig: APIConfig = {
            enabled: api.status === 'healthy' || api.status === 'unknown',
            device: 'cpu',
            memory_limit: '2g',
            hyperparams: DEFAULT_HYPERPARAMS[effectiveApiId] || DEFAULT_HYPERPARAMS[normalizedId] || {},
          };

          if (savedConfigs) {
            try {
              const configs = JSON.parse(savedConfigs);
              const saved = configs.find((c: { name: string }) =>
                c.name === `${apiId}-api` || c.name === apiId
              );
              if (saved) {
                loadedConfig = {
                  ...loadedConfig,
                  enabled: saved.enabled ?? true,
                  device: saved.device || 'cpu',
                  memory_limit: saved.memory_limit || '2g',
                  gpu_memory: saved.gpu_memory,
                };
              }
            } catch (e) {
              console.error('Failed to load saved config:', e);
            }
          }

          if (savedHyperParams) {
            try {
              const hyperParams = JSON.parse(savedHyperParams);
              const updatedHyperparams = { ...loadedConfig.hyperparams };
              Object.entries(hyperParams).forEach(([key, value]) => {
                if (key.startsWith(apiId.replace(/_/g, '_'))) {
                  const paramName = key.replace(`${apiId}_`, '').replace(`${apiId.replace(/_/g, '')}_`, '');
                  updatedHyperparams[paramName] = value as number | boolean | string;
                }
              });
              loadedConfig.hyperparams = updatedHyperparams;
            } catch (e) {
              console.error('Failed to load saved hyperparams:', e);
            }
          }

          setConfig(loadedConfig);
        }
      } catch (error) {
        console.error('Failed to fetch API info:', error);
      } finally {
        setLoading(false);
      }
    },
    [apiId]
  );

  const fetchLogs = useCallback(async () => {
    if (!apiId) return;

    try {
      const response = await axios.get(ADMIN_ENDPOINTS.logs(apiId));
      setLogs(response.data.logs || '로그가 없습니다.');
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      setLogs('로그를 불러올 수 없습니다.');
    }
  }, [apiId]);

  const fetchGPUInfo = useCallback(async () => {
    try {
      const response = await axios.get(ADMIN_ENDPOINTS.status, { timeout: 5000 });
      const gpu = response.data.gpu;
      if (gpu && gpu.available && gpu.device_name) {
        setGpuInfo({
          name: gpu.device_name,
          total_mb: gpu.total_memory,
          used_mb: gpu.used_memory,
          free_mb: gpu.free_memory,
          utilization: gpu.utilization,
        });
      }
    } catch (error) {
      console.warn('Failed to fetch GPU info:', error);
    }
  }, []);

  const fetchContainerStatus = useCallback(
    async (setConfig: React.Dispatch<React.SetStateAction<APIConfig>>) => {
      if (!apiId) return;
      try {
        const response = await axios.get(
          `${ADMIN_ENDPOINTS.status.replace('/status', '')}/container/status/${apiId}`,
          { timeout: 5000 }
        );
        setContainerStatus(response.data);
        if (response.data) {
          setConfig(prev => ({
            ...prev,
            device: response.data.gpu_enabled ? 'cuda' : 'cpu',
          }));
        }
      } catch (error) {
        console.warn('Failed to fetch container status:', error);
      }
    },
    [apiId]
  );

  const fetchApiKeySettings = useCallback(async () => {
    try {
      const settings = await apiKeyApi.getAllSettings();
      setApiKeySettings(settings);
    } catch (error) {
      console.warn('Failed to fetch API key settings:', error);
    }
  }, []);

  const loadSpecParams = useCallback(
    async (setConfig: React.Dispatch<React.SetStateAction<APIConfig>>) => {
      if (!apiId) return;
      try {
        const [defs, defaults] = await Promise.all([
          getHyperparamDefinitions(apiId),
          getDefaultHyperparams(apiId),
        ]);

        if (defs.length > 0) {
          setDynamicHyperparamDefs(defs);
          setConfig(prev => ({
            ...prev,
            hyperparams: {
              ...(defaults as HyperParams),
              ...prev.hyperparams,
            },
          }));
        }
      } catch (error) {
        console.warn('Failed to load spec parameters, using fallback:', error);
      }
    },
    [apiId]
  );

  return {
    // State
    apiInfo,
    setApiInfo,
    logs,
    setLogs,
    gpuInfo,
    containerStatus,
    setContainerStatus,
    apiKeySettings,
    setApiKeySettings,
    dynamicHyperparamDefs,
    loading,
    setLoading,
    // Fetch functions
    fetchAPIInfo,
    fetchLogs,
    fetchGPUInfo,
    fetchContainerStatus,
    fetchApiKeySettings,
    loadSpecParams,
  };
}
