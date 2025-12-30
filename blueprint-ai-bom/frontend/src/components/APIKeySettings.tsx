/**
 * API Key Settings Component
 * Dashboard에서 VLM/LLM API 키를 관리하는 UI
 *
 * 지원 프로바이더:
 * - OpenAI (GPT-4o-mini, GPT-4o, GPT-4-Turbo)
 * - Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
 * - Google (Gemini Pro Vision)
 * - Local VL API (API 키 불필요)
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Key,
  Eye,
  EyeOff,
  Save,
  Trash2,
  CheckCircle,
  XCircle,
  Loader2,
  Settings,
  AlertTriangle,
  Zap,
  X,
} from 'lucide-react';
import { settingsApi } from '../lib/api';
import type { AllAPIKeySettings, APIKeyModel, TestConnectionResult } from '../lib/api';

interface APIKeySettingsProps {
  isOpen: boolean;
  onClose: () => void;
}

// 프로바이더별 아이콘/색상 설정
const PROVIDER_STYLES: Record<
  string,
  { icon: string; color: string; bgColor: string }
> = {
  openai: { icon: '🤖', color: 'text-green-600', bgColor: 'bg-green-50' },
  anthropic: { icon: '🧠', color: 'text-orange-600', bgColor: 'bg-orange-50' },
  google: { icon: '🔮', color: 'text-blue-600', bgColor: 'bg-blue-50' },
  local: { icon: '💻', color: 'text-gray-600', bgColor: 'bg-gray-50' },
};

export function APIKeySettings({ isOpen, onClose }: APIKeySettingsProps) {
  const [settings, setSettings] = useState<AllAPIKeySettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 프로바이더별 상태
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [selectedModels, setSelectedModels] = useState<Record<string, string>>({});
  const [savingStates, setSavingStates] = useState<Record<string, boolean>>({});
  const [testingStates, setTestingStates] = useState<Record<string, boolean>>({});
  const [testResults, setTestResults] = useState<
    Record<string, TestConnectionResult | null>
  >({});

  // 설정 로드
  const loadSettings = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await settingsApi.getAllAPIKeySettings();
      setSettings(data);

      // 초기 선택 모델 설정
      const initialModels: Record<string, string> = {};
      Object.entries(data.providers).forEach(([provider, config]) => {
        if (config.selected_model) {
          initialModels[provider] = config.selected_model;
        } else if (config.available_models?.length > 0) {
          const recommended = config.available_models.find((m) => m.recommended);
          initialModels[provider] = recommended?.id || config.available_models[0].id;
        }
      });
      setSelectedModels(initialModels);
    } catch (err) {
      setError('설정을 불러올 수 없습니다.');
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen, loadSettings]);

  // API 키 저장
  const handleSaveKey = async (provider: string) => {
    const key = apiKeys[provider];
    if (!key?.trim()) return;

    try {
      setSavingStates((prev) => ({ ...prev, [provider]: true }));
      await settingsApi.setAPIKey({
        provider,
        api_key: key,
        selected_model: selectedModels[provider],
      });
      await loadSettings();
      setApiKeys((prev) => ({ ...prev, [provider]: '' }));
      setTestResults((prev) => ({ ...prev, [provider]: null }));
    } catch (err) {
      console.error('Failed to save API key:', err);
      setError('API 키 저장에 실패했습니다.');
    } finally {
      setSavingStates((prev) => ({ ...prev, [provider]: false }));
    }
  };

  // API 키 삭제
  const handleDeleteKey = async (provider: string) => {
    if (!window.confirm('API 키를 삭제하시겠습니까?')) return;

    try {
      setSavingStates((prev) => ({ ...prev, [provider]: true }));
      await settingsApi.deleteAPIKey(provider);
      await loadSettings();
      setTestResults((prev) => ({ ...prev, [provider]: null }));
    } catch (err) {
      console.error('Failed to delete API key:', err);
    } finally {
      setSavingStates((prev) => ({ ...prev, [provider]: false }));
    }
  };

  // 연결 테스트
  const handleTestConnection = async (provider: string) => {
    try {
      setTestingStates((prev) => ({ ...prev, [provider]: true }));
      const result = await settingsApi.testConnection(
        provider,
        apiKeys[provider] || undefined
      );
      setTestResults((prev) => ({ ...prev, [provider]: result }));
    } catch {
      setTestResults((prev) => ({
        ...prev,
        [provider]: {
          success: false,
          provider,
          model: null,
          message: '연결 테스트 실패',
          latency_ms: null,
        },
      }));
    } finally {
      setTestingStates((prev) => ({ ...prev, [provider]: false }));
    }
  };

  // 모델 변경
  const handleModelChange = async (provider: string, modelId: string) => {
    setSelectedModels((prev) => ({ ...prev, [provider]: modelId }));

    // 이미 키가 있으면 모델만 변경
    if (settings?.providers[provider]?.has_key) {
      try {
        await settingsApi.setSelectedModel(provider, modelId);
      } catch (err) {
        console.error('Failed to update model:', err);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden">
        {/* 헤더 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <Settings className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                AI API 설정
              </h2>
              <p className="text-sm text-gray-500">
                VLM 분류 및 노트 추출에 사용할 API 키를 설정합니다
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* 컨텐츠 */}
        <div className="p-6 overflow-y-auto max-h-[calc(85vh-8rem)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
              <span className="ml-3 text-gray-500">설정 로딩 중...</span>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12">
              <AlertTriangle className="w-12 h-12 text-red-500 mb-4" />
              <p className="text-red-600">{error}</p>
              <button
                onClick={loadSettings}
                className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                다시 시도
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {/* 기본 프로바이더 표시 */}
              {settings?.default_provider && (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg px-4 py-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="text-sm text-green-800 dark:text-green-200">
                      기본 프로바이더:{' '}
                      <strong>
                        {settings.providers[settings.default_provider]?.display_name}
                      </strong>
                    </span>
                  </div>
                </div>
              )}

              {/* 프로바이더별 설정 */}
              {settings?.providers &&
                Object.entries(settings.providers).map(([provider, config]) => {
                  const style = PROVIDER_STYLES[provider] || PROVIDER_STYLES.local;
                  const testResult = testResults[provider];

                  return (
                    <div
                      key={provider}
                      className={`rounded-xl border ${
                        config.has_key
                          ? 'border-green-200 dark:border-green-800'
                          : 'border-gray-200 dark:border-gray-700'
                      } overflow-hidden`}
                    >
                      {/* 프로바이더 헤더 */}
                      <div
                        className={`px-4 py-3 ${style.bgColor} dark:bg-opacity-20 flex items-center justify-between`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{style.icon}</span>
                          <div>
                            <h3 className={`font-bold ${style.color}`}>
                              {config.display_name}
                            </h3>
                            {config.has_key && config.masked_key && (
                              <p className="text-xs text-gray-500">
                                키: {config.masked_key}
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {config.has_key ? (
                            <span className="flex items-center gap-1 px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">
                              <CheckCircle className="w-3 h-3" />
                              설정됨
                            </span>
                          ) : provider !== 'local' ? (
                            <span className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">
                              <Key className="w-3 h-3" />
                              미설정
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full">
                              <Zap className="w-3 h-3" />
                              키 불필요
                            </span>
                          )}
                        </div>
                      </div>

                      {/* 프로바이더 본문 */}
                      <div className="p-4 space-y-4">
                        {/* 모델 선택 */}
                        {config.available_models && config.available_models.length > 0 && (
                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                              모델 선택
                            </label>
                            <select
                              value={selectedModels[provider] || ''}
                              onChange={(e) =>
                                handleModelChange(provider, e.target.value)
                              }
                              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
                            >
                              {config.available_models.map((model: APIKeyModel) => (
                                <option key={model.id} value={model.id}>
                                  {model.name}
                                  {model.recommended && ' (권장)'}
                                  {model.cost && ` - ${model.cost}`}
                                </option>
                              ))}
                            </select>
                          </div>
                        )}

                        {/* API 키 입력 (local 제외) */}
                        {provider !== 'local' && (
                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                              API 키
                            </label>
                            <div className="flex gap-2">
                              <div className="relative flex-1">
                                <input
                                  type={showKeys[provider] ? 'text' : 'password'}
                                  value={apiKeys[provider] || ''}
                                  onChange={(e) =>
                                    setApiKeys((prev) => ({
                                      ...prev,
                                      [provider]: e.target.value,
                                    }))
                                  }
                                  placeholder={
                                    config.has_key
                                      ? '새 키로 변경...'
                                      : 'API 키 입력...'
                                  }
                                  className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-sm"
                                />
                                <button
                                  type="button"
                                  onClick={() =>
                                    setShowKeys((prev) => ({
                                      ...prev,
                                      [provider]: !prev[provider],
                                    }))
                                  }
                                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600"
                                >
                                  {showKeys[provider] ? (
                                    <EyeOff className="w-4 h-4" />
                                  ) : (
                                    <Eye className="w-4 h-4" />
                                  )}
                                </button>
                              </div>
                              <button
                                onClick={() => handleSaveKey(provider)}
                                disabled={
                                  !apiKeys[provider]?.trim() ||
                                  savingStates[provider]
                                }
                                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                              >
                                {savingStates[provider] ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <Save className="w-4 h-4" />
                                )}
                                저장
                              </button>
                              {config.has_key && (
                                <button
                                  onClick={() => handleDeleteKey(provider)}
                                  disabled={savingStates[provider]}
                                  className="px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 disabled:opacity-50"
                                  title="키 삭제"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              )}
                            </div>
                          </div>
                        )}

                        {/* 연결 테스트 */}
                        <div className="flex items-center justify-between">
                          <button
                            onClick={() => handleTestConnection(provider)}
                            disabled={
                              testingStates[provider] ||
                              (!config.has_key &&
                                !apiKeys[provider]?.trim() &&
                                provider !== 'local')
                            }
                            className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                          >
                            {testingStates[provider] ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Zap className="w-4 h-4" />
                            )}
                            연결 테스트
                          </button>

                          {testResult && (
                            <div
                              className={`flex items-center gap-2 text-sm ${
                                testResult.success
                                  ? 'text-green-600'
                                  : 'text-red-600'
                              }`}
                            >
                              {testResult.success ? (
                                <CheckCircle className="w-4 h-4" />
                              ) : (
                                <XCircle className="w-4 h-4" />
                              )}
                              <span>{testResult.message}</span>
                              {testResult.latency_ms && (
                                <span className="text-gray-400">
                                  ({testResult.latency_ms.toFixed(0)}ms)
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}

              {/* 도움말 */}
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg px-4 py-3">
                <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">
                  API 키 발급 안내
                </h4>
                <ul className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
                  <li>
                    • OpenAI:{' '}
                    <a
                      href="https://platform.openai.com/api-keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline hover:text-blue-900"
                    >
                      platform.openai.com/api-keys
                    </a>
                  </li>
                  <li>
                    • Anthropic:{' '}
                    <a
                      href="https://console.anthropic.com/settings/keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline hover:text-blue-900"
                    >
                      console.anthropic.com/settings/keys
                    </a>
                  </li>
                  <li>
                    • Google AI:{' '}
                    <a
                      href="https://aistudio.google.com/app/apikey"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline hover:text-blue-900"
                    >
                      aistudio.google.com/app/apikey
                    </a>
                  </li>
                  <li>• 로컬 VL API: API 키 없이 로컬 모델 사용 (VL API 서버 필요)</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default APIKeySettings;
