/**
 * Custom hook for API Detail page state management and data fetching
 * Centralizes all state, API calls, and handlers
 */

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { ADMIN_ENDPOINTS } from '../../../../config/api';
import { getHyperparamDefinitions, getDefaultHyperparams, type HyperparamDefinition } from '../../../../utils/specToHyperparams';
import { DEFAULT_APIS } from '../../../../components/monitoring/constants';
import type { APIInfo } from '../../../../components/monitoring/types';
import { apiKeyApi, type AllAPIKeySettings } from '../../../../lib/api';
import { DEFAULT_HYPERPARAMS } from '../config/defaultHyperparams';
import { HYPERPARAM_DEFINITIONS, type HyperparamDefinitionItem } from '../config/hyperparamDefinitions';

// Toast 알림 타입
export interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

// 로딩 오버레이 타입
export interface LoadingState {
  isLoading: boolean;
  action: 'stop' | 'start' | 'restart' | 'save' | 'delete' | null;
  target: string;
}

// ============================================================================
// Type Definitions
// ============================================================================

export interface HyperParams {
  [key: string]: number | boolean | string;
}

export interface APIConfig {
  enabled: boolean;
  device: 'cpu' | 'cuda';
  memory_limit: string;
  gpu_memory?: string;
  hyperparams: HyperParams;
}

export interface GPUInfo {
  name: string;
  total_mb: number;
  used_mb: number;
  free_mb: number;
  utilization: number;
}

export interface ContainerStatus {
  service: string;
  container_name: string;
  running: boolean;
  gpu_enabled: boolean;
  gpu_count: number;
  memory_limit: string | null;
}

export interface TestResult {
  success: boolean;
  message: string;
}

// APIs that require external API keys
export const API_KEY_REQUIRED_APIS = ['vl', 'ocr_ensemble', 'blueprint_ai_bom', 'blueprint-ai-bom'];

// ============================================================================
// Hook Implementation
// ============================================================================

export function useAPIDetail(apiId: string | undefined) {
  // Core state
  const [apiInfo, setApiInfo] = useState<APIInfo | null>(null);
  const [config, setConfig] = useState<APIConfig>({
    enabled: true,
    device: 'cpu',
    memory_limit: '2g',
    hyperparams: {},
  });
  const [logs, setLogs] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'settings' | 'logs'>('settings');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dockerAction, setDockerAction] = useState<string | null>(null);

  // Dynamic hyperparameter definitions from API spec
  const [dynamicHyperparamDefs, setDynamicHyperparamDefs] = useState<HyperparamDefinition[]>([]);

  // GPU information
  const [gpuInfo, setGpuInfo] = useState<GPUInfo | null>(null);

  // Container status
  const [containerStatus, setContainerStatus] = useState<ContainerStatus | null>(null);

  // API Key management
  const [apiKeySettings, setApiKeySettings] = useState<AllAPIKeySettings | null>(null);
  const [apiKeyInputs, setApiKeyInputs] = useState<Record<string, string>>({});
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({});
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});
  const [savingApiKey, setSavingApiKey] = useState<string | null>(null);

  // Toast 알림 상태
  const [toast, setToast] = useState<ToastState>({ show: false, message: '', type: 'info' });

  // 전역 로딩 오버레이 상태
  const [globalLoading, setGlobalLoading] = useState<LoadingState>({
    isLoading: false,
    action: null,
    target: '',
  });

  // Toast 표시 헬퍼 함수
  const showToast = useCallback((message: string, type: ToastState['type'] = 'info') => {
    setToast({ show: true, message, type });
  }, []);

  // Toast 닫기 헬퍼 함수
  const hideToast = useCallback(() => {
    setToast(prev => ({ ...prev, show: false }));
  }, []);

  // ============================================================================
  // Data Fetching Functions
  // ============================================================================

  // Fetch API info
  const fetchAPIInfo = useCallback(async () => {
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
        const response = await axios.get('http://localhost:8000/api/v1/registry/list', { timeout: 3000 });
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
  }, [apiId]);

  // Fetch logs
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

  // Fetch GPU info
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

  // Fetch container status
  const fetchContainerStatus = useCallback(async () => {
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
  }, [apiId]);

  // Fetch API key settings
  const fetchApiKeySettings = useCallback(async () => {
    try {
      const settings = await apiKeyApi.getAllSettings();
      setApiKeySettings(settings);
    } catch (error) {
      console.warn('Failed to fetch API key settings:', error);
    }
  }, []);

  // ============================================================================
  // Handler Functions
  // ============================================================================

  // Save API key
  const handleSaveApiKey = async (provider: string) => {
    const apiKey = apiKeyInputs[provider];
    if (!apiKey) return;

    setSavingApiKey(provider);
    try {
      await apiKeyApi.setAPIKey({ provider, api_key: apiKey });
      setApiKeyInputs(prev => ({ ...prev, [provider]: '' }));
      await fetchApiKeySettings();
      setTestResults(prev => ({ ...prev, [provider]: { success: true, message: '저장 완료' } }));
    } catch (error) {
      console.error('Failed to save API key:', error);
      setTestResults(prev => ({ ...prev, [provider]: { success: false, message: '저장 실패' } }));
    } finally {
      setSavingApiKey(null);
    }
  };

  // Delete API key
  const handleDeleteApiKey = async (provider: string) => {
    setGlobalLoading({ isLoading: true, action: 'delete', target: `${provider} API Key` });

    try {
      await apiKeyApi.deleteAPIKey(provider);
      await fetchApiKeySettings();
      setTestResults(prev => {
        const newResults = { ...prev };
        delete newResults[provider];
        return newResults;
      });
      showToast(`✓ ${provider} API Key가 삭제되었습니다`, 'success');
    } catch (error) {
      console.error('Failed to delete API key:', error);
      const errorMsg = error instanceof Error ? error.message : '알 수 없는 오류';
      showToast(`✗ API Key 삭제 실패\n${errorMsg}`, 'error');
    } finally {
      setGlobalLoading({ isLoading: false, action: null, target: '' });
    }
  };

  // Test connection
  const handleTestConnection = async (provider: string) => {
    setTestingProvider(provider);
    try {
      const result = await apiKeyApi.testConnection(provider, apiKeyInputs[provider] || undefined);
      setTestResults(prev => ({
        ...prev,
        [provider]: {
          success: result.success,
          message: result.message || result.error || ''
        }
      }));
    } catch {
      setTestResults(prev => ({
        ...prev,
        [provider]: { success: false, message: '테스트 실패' }
      }));
    } finally {
      setTestingProvider(null);
    }
  };

  // Model change
  const handleModelChange = async (provider: string, model: string) => {
    try {
      await apiKeyApi.setModel(provider, model);
      await fetchApiKeySettings();
    } catch (error) {
      console.error('Failed to set model:', error);
    }
  };

  // Docker action
  const handleDockerAction = async (action: 'start' | 'stop' | 'restart') => {
    if (!apiId) return;

    const actionText = {
      start: '시작',
      stop: '중지',
      restart: '재시작',
    };

    // 전역 로딩 시작 (confirm 대화상자 제거)
    setDockerAction(action);
    setGlobalLoading({
      isLoading: true,
      action,
      target: apiInfo?.display_name || apiId,
    });

    try {
      await axios.post(ADMIN_ENDPOINTS.docker(action, apiId), {}, { timeout: 30000 });
      showToast(`✓ ${apiInfo?.display_name || apiId} ${actionText[action]} 완료`, 'success');
      setTimeout(fetchAPIInfo, 2000);
      setTimeout(fetchContainerStatus, 2000);
    } catch (error) {
      let errorMsg = '알 수 없는 오류';
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNABORTED') {
          errorMsg = '시간 초과 (30초)';
        } else if (error.response) {
          errorMsg = `HTTP ${error.response.status}: ${error.response.data?.detail || error.response.statusText}`;
        } else if (error.request) {
          errorMsg = '서버 응답 없음 - Gateway API 확인 필요';
        }
      } else if (error instanceof Error) {
        errorMsg = error.message;
      }
      showToast(`✗ ${apiInfo?.display_name || apiId} ${actionText[action]} 실패\n${errorMsg}`, 'error');
    } finally {
      setDockerAction(null);
      setGlobalLoading({ isLoading: false, action: null, target: '' });
    }
  };

  // Save configuration
  const handleSave = async () => {
    setSaving(true);
    setGlobalLoading({
      isLoading: true,
      action: 'save',
      target: apiInfo?.display_name || apiId || '설정',
    });

    try {
      // Save serviceConfigs
      const savedConfigs = localStorage.getItem('serviceConfigs');
      const configs = savedConfigs ? JSON.parse(savedConfigs) : [];

      const configIndex = configs.findIndex((c: { name: string }) =>
        c.name === `${apiId}-api` || c.name === apiId
      );
      const newConfig = {
        name: `${apiId}-api`,
        displayName: apiInfo?.display_name || apiId,
        port: apiInfo?.port,
        device: config.device,
        memory_limit: config.memory_limit,
        gpu_memory: config.gpu_memory,
        enabled: config.enabled,
      };

      if (configIndex >= 0) {
        configs[configIndex] = newConfig;
      } else {
        configs.push(newConfig);
      }

      localStorage.setItem('serviceConfigs', JSON.stringify(configs));

      // Save hyperParameters
      const savedHyperParams = localStorage.getItem('hyperParameters');
      const hyperParams = savedHyperParams ? JSON.parse(savedHyperParams) : {};

      Object.entries(config.hyperparams).forEach(([key, value]) => {
        hyperParams[`${apiId}_${key}`] = value;
      });

      localStorage.setItem('hyperParameters', JSON.stringify(hyperParams));

      // 컨테이너 설정 적용 (confirm 없이 바로 적용)
      try {
        const response = await axios.post(
          `${ADMIN_ENDPOINTS.status.replace('/status', '')}/container/configure/${apiId}`,
          {
            device: config.device,
            memory_limit: config.memory_limit,
            gpu_memory: config.gpu_memory,
          },
          { timeout: 60000 } // 컨테이너 재생성에 시간이 걸릴 수 있음
        );

        if (response.data.success) {
          showToast(
            `✓ 설정 저장 및 컨테이너 적용 완료\n\n` +
            `연산 장치: ${config.device.toUpperCase()}\n` +
            `GPU 메모리: ${config.gpu_memory || '제한 없음'}`,
            'success'
          );
          setTimeout(fetchContainerStatus, 2000);
        } else {
          showToast(
            `⚠️ 설정 저장됨, 컨테이너 적용 실패\n${response.data.message}`,
            'warning'
          );
        }
      } catch (configError) {
        let errorMsg = '알 수 없는 오류';
        if (axios.isAxiosError(configError)) {
          if (configError.code === 'ECONNABORTED') {
            errorMsg = '시간 초과 (60초)';
          } else if (configError.response) {
            errorMsg = configError.response.data?.detail || configError.response.statusText;
          } else if (configError.request) {
            errorMsg = '서버 응답 없음';
          }
        } else if (configError instanceof Error) {
          errorMsg = configError.message;
        }
        showToast(
          `⚠️ 설정 저장됨, 컨테이너 적용 실패\n${errorMsg}`,
          'warning'
        );
      }
    } catch (error) {
      console.error('Failed to save config:', error);
      const errorMsg = error instanceof Error ? error.message : '알 수 없는 오류';
      showToast(`✗ 설정 저장 실패\n${errorMsg}`, 'error');
    } finally {
      setSaving(false);
      setGlobalLoading({ isLoading: false, action: null, target: '' });
    }
  };

  // Get enhanced hyperparam definitions for VL API
  const getEnhancedHyperparamDefs = useCallback(
    (baseDefs: HyperparamDefinitionItem[], apiIdParam: string): HyperparamDefinitionItem[] => {
      if (!apiIdParam.includes('vl')) return baseDefs;
      if (!apiKeySettings) return baseDefs;

      const modelFieldIndex = baseDefs.findIndex(def => def.key === 'model' || def.label === '모델');
      if (modelFieldIndex === -1) return baseDefs;

      const modelField = baseDefs[modelFieldIndex];
      if (modelField.type !== 'select' || !modelField.options) return baseDefs;

      const enhancedOptions = [...modelField.options];

      const providers = ['openai', 'anthropic', 'google'] as const;
      providers.forEach(provider => {
        const settings = apiKeySettings[provider];
        if (settings?.has_key && settings.models) {
          settings.models.forEach(model => {
            const providerLabel = {
              openai: 'OpenAI',
              anthropic: 'Anthropic',
              google: 'Google'
            }[provider];

            if (!enhancedOptions.some(opt => opt.value === model.id)) {
              enhancedOptions.push({
                value: model.id,
                label: `${model.name} (${providerLabel})${model.recommended ? ' *' : ''}`
              });
            }
          });
        }
      });

      const newDefs = [...baseDefs];
      newDefs[modelFieldIndex] = {
        ...modelField,
        options: enhancedOptions
      };
      return newDefs;
    },
    [apiKeySettings]
  );

  // ============================================================================
  // Effects
  // ============================================================================

  useEffect(() => {
    fetchAPIInfo();
    fetchContainerStatus();
    if (apiId && API_KEY_REQUIRED_APIS.some(id => apiId.includes(id) || id.includes(apiId.replace(/-/g, '_')))) {
      fetchApiKeySettings();
    }
  }, [fetchAPIInfo, fetchContainerStatus, fetchApiKeySettings, apiId]);

  useEffect(() => {
    if (config.device === 'cuda') {
      fetchGPUInfo();
    }
  }, [config.device, fetchGPUInfo]);

  useEffect(() => {
    if (!apiId) return;

    const loadSpecParams = async () => {
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
    };

    loadSpecParams();
  }, [apiId]);

  useEffect(() => {
    if (activeTab === 'logs') {
      fetchLogs();
    }
  }, [activeTab, fetchLogs]);

  // ============================================================================
  // Computed Values
  // ============================================================================

  const normalizedApiId = apiId?.replace(/-/g, '_') || '';
  const baseHyperparamDefs = dynamicHyperparamDefs.length > 0
    ? dynamicHyperparamDefs.map(def => ({
        label: def.label,
        type: def.type,
        min: def.min,
        max: def.max,
        step: def.step,
        options: def.options,
        description: def.description,
        key: def.key,
      }))
    : (HYPERPARAM_DEFINITIONS[normalizedApiId] || HYPERPARAM_DEFINITIONS[apiId || ''] || []);

  const hyperparamDefs = getEnhancedHyperparamDefs(baseHyperparamDefs, apiId || '');

  const requiresApiKey = API_KEY_REQUIRED_APIS.some(
    id => apiId?.includes(id) || id.includes(apiId?.replace(/-/g, '_') || '')
  );

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // State
    apiInfo,
    config,
    setConfig,
    logs,
    activeTab,
    setActiveTab,
    loading,
    saving,
    dockerAction,
    gpuInfo,
    containerStatus,
    apiKeySettings,
    apiKeyInputs,
    setApiKeyInputs,
    showApiKeys,
    setShowApiKeys,
    testingProvider,
    testResults,
    savingApiKey,
    hyperparamDefs,
    requiresApiKey,

    // Toast & Loading 상태
    toast,
    globalLoading,
    hideToast,

    // Handlers
    handleSaveApiKey,
    handleDeleteApiKey,
    handleTestConnection,
    handleModelChange,
    handleDockerAction,
    handleSave,
    fetchLogs,
  };
}
