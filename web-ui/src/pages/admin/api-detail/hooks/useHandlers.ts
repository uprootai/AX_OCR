/**
 * Handler functions for useAPIDetail hook
 */

import { useState, useCallback } from 'react';
import axios from 'axios';
import { ADMIN_ENDPOINTS } from '../../../../config/api';
import { apiKeyApi } from '../../../../lib/api';
import type { AllAPIKeySettings } from '../../../../lib/api';
import type { APIInfo } from '../../../../components/monitoring/types';
import type { HyperparamDefinitionItem } from '../config/hyperparamDefinitions';
import type { APIConfig, ToastState, LoadingState, TestResult } from './types';

export function useHandlers(
  apiId: string | undefined,
  apiInfo: APIInfo | null,
  config: APIConfig,
  apiKeySettings: AllAPIKeySettings | null,
  fetchApiKeySettings: () => Promise<void>,
  fetchAPIInfo: (setConfig: React.Dispatch<React.SetStateAction<APIConfig>>) => Promise<void>,
  fetchContainerStatus: (setConfig: React.Dispatch<React.SetStateAction<APIConfig>>) => Promise<void>,
  setConfig: React.Dispatch<React.SetStateAction<APIConfig>>
) {
  // API Key state
  const [apiKeyInputs, setApiKeyInputs] = useState<Record<string, string>>({});
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({});
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});
  const [savingApiKey, setSavingApiKey] = useState<string | null>(null);

  // UI state
  const [saving, setSaving] = useState(false);
  const [dockerAction, setDockerAction] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastState>({ show: false, message: '', type: 'info' });
  const [globalLoading, setGlobalLoading] = useState<LoadingState>({
    isLoading: false,
    action: null,
    target: '',
  });

  const showToast = useCallback((message: string, type: ToastState['type'] = 'info') => {
    setToast({ show: true, message, type });
  }, []);

  const hideToast = useCallback(() => {
    setToast(prev => ({ ...prev, show: false }));
  }, []);

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

  const handleModelChange = async (provider: string, model: string) => {
    try {
      await apiKeyApi.setModel(provider, model);
      await fetchApiKeySettings();
    } catch (error) {
      console.error('Failed to set model:', error);
    }
  };

  const handleDockerAction = async (action: 'start' | 'stop' | 'restart') => {
    if (!apiId) return;

    const actionText = {
      start: '시작',
      stop: '중지',
      restart: '재시작',
    };

    setDockerAction(action);
    setGlobalLoading({
      isLoading: true,
      action,
      target: apiInfo?.display_name || apiId,
    });

    try {
      await axios.post(ADMIN_ENDPOINTS.docker(action, apiId), {}, { timeout: 30000 });
      showToast(`✓ ${apiInfo?.display_name || apiId} ${actionText[action]} 완료`, 'success');
      setTimeout(() => fetchAPIInfo(setConfig), 2000);
      setTimeout(() => fetchContainerStatus(setConfig), 2000);
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

      // 컨테이너 설정 적용
      try {
        const response = await axios.post(
          `${ADMIN_ENDPOINTS.status.replace('/status', '')}/container/configure/${apiId}`,
          {
            device: config.device,
            memory_limit: config.memory_limit,
            gpu_memory: config.gpu_memory,
          },
          { timeout: 60000 }
        );

        if (response.data.success) {
          showToast(
            `✓ 설정 저장 및 컨테이너 적용 완료\n\n` +
            `연산 장치: ${config.device.toUpperCase()}\n` +
            `GPU 메모리: ${config.gpu_memory || '제한 없음'}`,
            'success'
          );
          setTimeout(() => fetchContainerStatus(setConfig), 2000);
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

  return {
    // API Key state
    apiKeyInputs,
    setApiKeyInputs,
    showApiKeys,
    setShowApiKeys,
    testingProvider,
    testResults,
    savingApiKey,
    // UI state
    saving,
    dockerAction,
    toast,
    globalLoading,
    hideToast,
    // Handlers
    showToast,
    handleSaveApiKey,
    handleDeleteApiKey,
    handleTestConnection,
    handleModelChange,
    handleDockerAction,
    handleSave,
    getEnhancedHyperparamDefs,
  };
}
