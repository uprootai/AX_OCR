/**
 * Custom hook for API Detail page state management and data fetching
 * Centralizes all state, API calls, and handlers
 *
 * Composed from:
 *  - types.ts         — shared interfaces & constants
 *  - useFetchers.ts   — data fetching callbacks
 *  - useHandlers.ts   — action handlers & UI state
 */

export type {
  ToastState,
  LoadingState,
  HyperParams,
  APIConfig,
  GPUInfo,
  ContainerStatus,
  TestResult,
} from './types';
export { API_KEY_REQUIRED_APIS } from './types';

import { useState, useEffect } from 'react';
import { API_KEY_REQUIRED_APIS } from './types';
import { useFetchers } from './useFetchers';
import { useHandlers } from './useHandlers';
import { HYPERPARAM_DEFINITIONS } from '../config/hyperparamDefinitions';

export function useAPIDetail(apiId: string | undefined) {
  const [config, setConfig] = useState({
    enabled: true,
    device: 'cpu' as 'cpu' | 'cuda',
    memory_limit: '2g',
    hyperparams: {} as Record<string, number | boolean | string>,
  });

  const [activeTab, setActiveTab] = useState<'settings' | 'logs'>('settings');

  const fetchers = useFetchers(apiId);

  const handlers = useHandlers(
    apiId,
    fetchers.apiInfo,
    config,
    fetchers.apiKeySettings,
    fetchers.fetchApiKeySettings,
    fetchers.fetchAPIInfo,
    fetchers.fetchContainerStatus,
    setConfig
  );

  // ============================================================================
  // Effects
  // ============================================================================

  useEffect(() => {
    fetchers.fetchAPIInfo(setConfig);
    fetchers.fetchContainerStatus(setConfig);
    if (apiId && API_KEY_REQUIRED_APIS.some(id => apiId.includes(id) || id.includes(apiId.replace(/-/g, '_')))) {
      fetchers.fetchApiKeySettings();
    }
  }, [fetchers.fetchAPIInfo, fetchers.fetchContainerStatus, fetchers.fetchApiKeySettings, apiId]);

  useEffect(() => {
    if (config.device === 'cuda') {
      fetchers.fetchGPUInfo();
    }
  }, [config.device, fetchers.fetchGPUInfo]);

  useEffect(() => {
    fetchers.loadSpecParams(setConfig);
  }, [fetchers.loadSpecParams]);

  useEffect(() => {
    if (activeTab === 'logs') {
      fetchers.fetchLogs();
    }
  }, [activeTab, fetchers.fetchLogs]);

  // ============================================================================
  // Computed Values
  // ============================================================================

  const normalizedApiId = apiId?.replace(/-/g, '_') || '';
  const baseHyperparamDefs = fetchers.dynamicHyperparamDefs.length > 0
    ? fetchers.dynamicHyperparamDefs.map(def => ({
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

  const hyperparamDefs = handlers.getEnhancedHyperparamDefs(baseHyperparamDefs, apiId || '');

  const requiresApiKey = API_KEY_REQUIRED_APIS.some(
    id => apiId?.includes(id) || id.includes(apiId?.replace(/-/g, '_') || '')
  );

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // State
    apiInfo: fetchers.apiInfo,
    config,
    setConfig,
    logs: fetchers.logs,
    activeTab,
    setActiveTab,
    loading: fetchers.loading,
    saving: handlers.saving,
    dockerAction: handlers.dockerAction,
    gpuInfo: fetchers.gpuInfo,
    containerStatus: fetchers.containerStatus,
    apiKeySettings: fetchers.apiKeySettings,
    apiKeyInputs: handlers.apiKeyInputs,
    setApiKeyInputs: handlers.setApiKeyInputs,
    showApiKeys: handlers.showApiKeys,
    setShowApiKeys: handlers.setShowApiKeys,
    testingProvider: handlers.testingProvider,
    testResults: handlers.testResults,
    savingApiKey: handlers.savingApiKey,
    hyperparamDefs,
    requiresApiKey,

    // Toast & Loading 상태
    toast: handlers.toast,
    globalLoading: handlers.globalLoading,
    hideToast: handlers.hideToast,

    // Handlers
    handleSaveApiKey: handlers.handleSaveApiKey,
    handleDeleteApiKey: handlers.handleDeleteApiKey,
    handleTestConnection: handlers.handleTestConnection,
    handleModelChange: handlers.handleModelChange,
    handleDockerAction: handlers.handleDockerAction,
    handleSave: handlers.handleSave,
    fetchLogs: fetchers.fetchLogs,
  };
}
