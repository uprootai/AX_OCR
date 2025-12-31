/**
 * API Key Settings Panel Component
 * Manages external AI API keys (OpenAI, Anthropic, Google, Local)
 */

import { Card } from '../../../../components/ui/Card';
import { Button } from '../../../../components/ui/Button';
import { Badge } from '../../../../components/ui/Badge';
import {
  Key,
  Eye,
  EyeOff,
  Check,
  X,
  Loader2,
} from 'lucide-react';
import type { AllAPIKeySettings, ProviderSettings } from '../../../../lib/api';
import type { TestResult } from '../hooks/useAPIDetail';

interface APIKeySettingsPanelProps {
  apiKeySettings: AllAPIKeySettings;
  apiKeyInputs: Record<string, string>;
  setApiKeyInputs: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  showApiKeys: Record<string, boolean>;
  setShowApiKeys: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
  testingProvider: string | null;
  testResults: Record<string, TestResult>;
  savingApiKey: string | null;
  onSaveApiKey: (provider: string) => Promise<void>;
  onDeleteApiKey: (provider: string) => Promise<void>;
  onTestConnection: (provider: string) => Promise<void>;
  onModelChange: (provider: string, model: string) => Promise<void>;
}

const PROVIDER_LABELS: Record<string, { name: string; color: string; icon: string }> = {
  openai: { name: 'OpenAI', color: 'bg-green-500', icon: '' },
  anthropic: { name: 'Anthropic', color: 'bg-orange-500', icon: '' },
  google: { name: 'Google AI', color: 'bg-blue-500', icon: '' },
  local: { name: 'Local VL', color: 'bg-purple-500', icon: '' },
};

export function APIKeySettingsPanel({
  apiKeySettings,
  apiKeyInputs,
  setApiKeyInputs,
  showApiKeys,
  setShowApiKeys,
  testingProvider,
  testResults,
  savingApiKey,
  onSaveApiKey,
  onDeleteApiKey,
  onTestConnection,
  onModelChange,
}: APIKeySettingsPanelProps) {
  return (
    <Card className="md:col-span-2">
      <div className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Key className="h-5 w-5" />
          외부 AI API 설정
        </h3>
        <p className="text-sm text-muted-foreground mb-4">
          이 서비스는 외부 AI API를 사용합니다. API Key를 설정하면 해당 서비스를 이용할 수 있습니다.
        </p>

        <div className="grid md:grid-cols-2 gap-4">
          {(['openai', 'anthropic', 'google', 'local'] as const).map((provider) => {
            const settings = apiKeySettings[provider] as ProviderSettings;
            const label = PROVIDER_LABELS[provider];
            const testResult = testResults[provider];

            return (
              <div key={provider} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{label.icon}</span>
                    <span className="font-medium">{label.name}</span>
                  </div>
                  {settings.has_key && (
                    <Badge variant="success" className="text-xs">
                      {settings.source === 'environment' ? '환경변수' : '설정됨'}
                    </Badge>
                  )}
                </div>

                {/* Current key display */}
                {settings.has_key && settings.masked_key && (
                  <div className="mb-3 p-2 bg-muted/50 rounded text-sm flex items-center justify-between">
                    <span className="font-mono">{settings.masked_key}</span>
                    {settings.source === 'dashboard' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDeleteApiKey(provider)}
                        className="h-6 px-2 text-red-500 hover:text-red-600"
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                )}

                {/* API Key input */}
                {provider !== 'local' && (
                  <div className="mb-3">
                    <div className="relative">
                      <input
                        type={showApiKeys[provider] ? 'text' : 'password'}
                        value={apiKeyInputs[provider] || ''}
                        onChange={(e) => setApiKeyInputs(prev => ({ ...prev, [provider]: e.target.value }))}
                        placeholder={settings.has_key ? '새 키로 덮어쓰기' : 'API Key 입력'}
                        className="w-full px-3 py-2 pr-10 border rounded bg-background text-sm font-mono"
                      />
                      <button
                        type="button"
                        onClick={() => setShowApiKeys(prev => ({ ...prev, [provider]: !prev[provider] }))}
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showApiKeys[provider] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                )}

                {/* Model selection */}
                {settings.models && settings.models.length > 0 && (
                  <div className="mb-3">
                    <label className="block text-xs text-muted-foreground mb-1">모델</label>
                    <select
                      value={settings.model || ''}
                      onChange={(e) => onModelChange(provider, e.target.value)}
                      className="w-full px-3 py-2 border rounded bg-background text-sm"
                    >
                      {settings.models.map((model) => (
                        <option key={model.id} value={model.id}>
                          {model.name} ({model.cost}){model.recommended ? ' *' : ''}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Test result */}
                {testResult && (
                  <div className={`mb-3 p-2 rounded text-sm flex items-center gap-2 ${testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                    {testResult.success ? <Check className="h-4 w-4" /> : <X className="h-4 w-4" />}
                    {testResult.message}
                  </div>
                )}

                {/* Action buttons */}
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onTestConnection(provider)}
                    disabled={testingProvider === provider}
                    className="flex-1"
                  >
                    {testingProvider === provider ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      '테스트'
                    )}
                  </Button>
                  {provider !== 'local' && apiKeyInputs[provider] && (
                    <Button
                      size="sm"
                      onClick={() => onSaveApiKey(provider)}
                      disabled={savingApiKey === provider}
                      className="flex-1"
                    >
                      {savingApiKey === provider ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        '저장'
                      )}
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
}
