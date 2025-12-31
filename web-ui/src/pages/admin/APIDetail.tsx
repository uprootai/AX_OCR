/**
 * API Detail Page
 * Displays and manages configuration for individual API services
 *
 * Refactored from 1,197 lines to ~250 lines
 * Modularized components:
 * - api-detail/hooks/useAPIDetail.ts - State management and data fetching
 * - api-detail/components/ServiceSettingsCard.tsx - Service configuration UI
 * - api-detail/components/DockerControlCard.tsx - Docker controls
 * - api-detail/components/APIKeySettingsPanel.tsx - External API key management
 * - api-detail/components/HyperparamEditor.tsx - Hyperparameter editing
 * - api-detail/config/hyperparamDefinitions.ts - Parameter definitions
 * - api-detail/config/defaultHyperparams.ts - Default values
 */

import { useParams, useNavigate } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import {
  ArrowLeft,
  Save,
  RefreshCw,
  Settings,
  FileText,
  ExternalLink,
  AlertCircle,
} from 'lucide-react';
import { YOLOModelManager } from '../../components/admin/YOLOModelManager';

// Import modularized components and hooks
import {
  useAPIDetail,
  ServiceSettingsCard,
  DockerControlCard,
  APIKeySettingsPanel,
  HyperparamEditor,
} from './api-detail';

export default function APIDetail() {
  const { apiId } = useParams<{ apiId: string }>();
  const navigate = useNavigate();

  // Use custom hook for all state and handlers
  const {
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

    // Handlers
    handleSaveApiKey,
    handleDeleteApiKey,
    handleTestConnection,
    handleModelChange,
    handleDockerAction,
    handleSave,
    fetchLogs,
  } = useAPIDetail(apiId);

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Not found state
  if (!apiInfo) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => navigate('/dashboard')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          대시보드로 돌아가기
        </Button>
        <Card>
          <div className="p-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">API를 찾을 수 없습니다</h2>
            <p className="text-muted-foreground">ID: {apiId}</p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-3">
            <span
              className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
              style={{ backgroundColor: apiInfo.color + '20' }}
            >
              {apiInfo.icon}
            </span>
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                {apiInfo.display_name}
                <Badge variant={apiInfo.status === 'healthy' ? 'success' : 'error'}>
                  {apiInfo.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
                </Badge>
              </h1>
              <p className="text-muted-foreground">{apiInfo.description}</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <a
            href={`http://localhost:${apiInfo.port}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
          >
            <ExternalLink className="h-4 w-4" />
            Swagger
          </a>
          <Button onClick={handleSave} disabled={saving}>
            <Save className="h-4 w-4 mr-2" />
            {saving ? '저장 중...' : '저장'}
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b">
        <nav className="flex gap-4">
          {[
            { id: 'settings', label: '설정', icon: Settings },
            { id: 'logs', label: '로그', icon: FileText },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'settings' | 'logs')}
                className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary text-primary font-semibold'
                    : 'border-transparent hover:border-gray-300'
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="grid md:grid-cols-2 gap-6">
          {/* Service Settings */}
          <ServiceSettingsCard
            apiInfo={apiInfo}
            config={config}
            setConfig={setConfig}
            containerStatus={containerStatus}
            gpuInfo={gpuInfo}
          />

          {/* Docker Control */}
          <DockerControlCard
            apiId={apiId || ''}
            dockerAction={dockerAction}
            onDockerAction={handleDockerAction}
          />

          {/* API Key Settings */}
          {apiKeySettings && requiresApiKey && (
            <APIKeySettingsPanel
              apiKeySettings={apiKeySettings}
              apiKeyInputs={apiKeyInputs}
              setApiKeyInputs={setApiKeyInputs}
              showApiKeys={showApiKeys}
              setShowApiKeys={setShowApiKeys}
              testingProvider={testingProvider}
              testResults={testResults}
              savingApiKey={savingApiKey}
              onSaveApiKey={handleSaveApiKey}
              onDeleteApiKey={handleDeleteApiKey}
              onTestConnection={handleTestConnection}
              onModelChange={handleModelChange}
            />
          )}

          {/* Hyperparameter Editor */}
          <HyperparamEditor
            hyperparamDefs={hyperparamDefs}
            config={config}
            setConfig={setConfig}
          />
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">서비스 로그</h3>
              <Button variant="outline" size="sm" onClick={fetchLogs}>
                <RefreshCw className="h-4 w-4 mr-2" />
                새로고침
              </Button>
            </div>
            <div className="bg-black text-green-400 p-4 rounded font-mono text-sm h-96 overflow-auto">
              <pre>{logs || '로그를 불러오는 중...'}</pre>
            </div>
          </div>
        </Card>
      )}

      {/* YOLO Model Manager (yolo API only) */}
      {activeTab === 'settings' && apiInfo?.id === 'yolo' && (
        <div className="mt-6">
          <YOLOModelManager apiBaseUrl={apiInfo.base_url} />
        </div>
      )}
    </div>
  );
}
