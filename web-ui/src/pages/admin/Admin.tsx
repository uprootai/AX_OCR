import { useState, useEffect, useCallback } from 'react';
import { Server, Cpu, Database, RefreshCw, FileCode, Download, Upload, Archive } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import axios from 'axios';
import {
  ADMIN_ENDPOINTS,
  SYSTEM_CONFIG,
} from '../../config/api';

interface APIStatus {
  name: string;
  display_name: string;
  status: string;
  response_time: number;
  port: number;
  gpu_enabled: boolean;
}

interface GPUStatus {
  available: boolean;
  device_name?: string;
  total_memory?: number;
  used_memory?: number;
  free_memory?: number;
  utilization?: number;
}

interface SystemResources {
  cpu_percent: number;
  memory_percent: number;
  memory_used_gb: number;
  memory_total_gb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
}

interface SystemStatus {
  apis: APIStatus[];
  gpu: GPUStatus;
  system: SystemResources;
  timestamp: string;
}

interface ModelInfo {
  model_type: string;
  host_path: string;
  file_count: number;
  total_size_mb: number;
}

export default function Admin() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'models' | 'logs' | 'backup'>('overview');
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [logs, setLogs] = useState<string>('');
  const [selectedService, setSelectedService] = useState<string>('gateway');

  const fetchStatus = useCallback(async () => {
    try {
      const response = await axios.get(ADMIN_ENDPOINTS.status);
      setStatus(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch status:', error);
      setLoading(false);
    }
  }, []);

  const fetchModels = async () => {
    try {
      const response = await axios.get(ADMIN_ENDPOINTS.allModels);
      setModels(response.data || []);
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const fetchLogs = async (service: string) => {
    try {
      const response = await axios.get(ADMIN_ENDPOINTS.logs(service));
      setLogs(response.data.logs || '');
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      setLogs('로그를 불러올 수 없습니다.');
    }
  };

  const handleExport = () => {
    try {
      const exportData = {
        version: '1.0.0',
        exportDate: new Date().toISOString(),
        serviceConfigs: localStorage.getItem('serviceConfigs'),
        hyperParameters: localStorage.getItem('hyperParameters'),
        customAPIs: localStorage.getItem('api-config-store'),
      };

      const dataStr = JSON.stringify(exportData, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);

      const link = document.createElement('a');
      link.href = url;
      link.download = `ax-settings-backup-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      alert('설정이 성공적으로 백업되었습니다.');
    } catch (err) {
      console.error('백업 실패:', err);
      alert('백업에 실패했습니다.');
    }
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';

    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const importData = JSON.parse(event.target?.result as string);

          if (!importData.version) {
            throw new Error('유효하지 않은 백업 파일입니다.');
          }

          const confirmMsg = `백업 파일을 복원하시겠습니까?\n\n` +
            `백업 날짜: ${new Date(importData.exportDate).toLocaleString()}\n` +
            `버전: ${importData.version}\n\n` +
            `현재 설정은 덮어씌워집니다.`;

          if (!confirm(confirmMsg)) return;

          if (importData.serviceConfigs) {
            localStorage.setItem('serviceConfigs', importData.serviceConfigs);
          }
          if (importData.hyperParameters) {
            localStorage.setItem('hyperParameters', importData.hyperParameters);
          }
          if (importData.customAPIs) {
            localStorage.setItem('api-config-store', importData.customAPIs);
          }

          alert('설정이 복원되었습니다. 페이지를 새로고침합니다.');
          setTimeout(() => window.location.reload(), 500);
        } catch (err) {
          console.error('복원 실패:', err);
          alert('복원에 실패했습니다: ' + (err instanceof Error ? err.message : '알 수 없는 오류'));
        }
      };

      reader.readAsText(file);
    };

    input.click();
  };

  const handleReset = () => {
    if (confirm('모든 설정을 기본값으로 되돌리시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.')) {
      localStorage.removeItem('serviceConfigs');
      localStorage.removeItem('hyperParameters');
      alert('설정이 초기화되었습니다. 페이지를 새로고침합니다.');
      setTimeout(() => window.location.reload(), 500);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, SYSTEM_CONFIG.AUTO_REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  useEffect(() => {
    if (activeTab === 'models') {
      fetchModels();
    } else if (activeTab === 'logs') {
      fetchLogs(selectedService);
    }
  }, [activeTab, selectedService]);

  if (loading && !status) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg">시스템 상태를 불러오는 중...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">시스템 관리</h1>
        <p className="text-muted-foreground">
          모델 관리, Docker 제어, 로그 조회 - 모든 것을 한 곳에서
        </p>
      </div>

      <div className="border-b">
        <nav className="flex gap-4">
          {[
            { id: 'overview', label: '시스템 현황', icon: Server },
            { id: 'models', label: '모델 관리', icon: Database },
            { id: 'logs', label: '로그 조회', icon: FileCode },
            { id: 'backup', label: '백업/복원', icon: Archive },
          ].map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'overview' | 'models' | 'logs' | 'backup')}
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

      {activeTab === 'overview' && status && (
        <div className="space-y-6">
          <Card>
            <h2 className="text-xl font-semibold mb-4">API 상태</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {status.apis.map(api => {
                const isHealthy = api.status === 'healthy';
                return (
                  <div
                    key={api.name}
                    className={`p-4 rounded-lg border-2 ${
                      isHealthy
                        ? 'border-green-500 bg-green-50 dark:bg-green-950'
                        : 'border-red-500 bg-red-50 dark:bg-red-950'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-semibold">{api.display_name}</h3>
                        <p className="text-xs text-muted-foreground">Port: {api.port}</p>
                      </div>
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded ${
                          isHealthy
                            ? 'bg-green-600 text-white'
                            : 'bg-red-600 text-white'
                        }`}
                      >
                        {api.status}
                      </span>
                    </div>
                    <div className="mt-2 space-y-1 text-xs">
                      <div className="flex justify-between">
                        <span>GPU:</span>
                        <span className={api.gpu_enabled ? 'text-green-600 font-semibold' : ''}>
                          {api.gpu_enabled ? '✅ Enabled' : '❌ Disabled'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Response:</span>
                        <span className="font-mono">
                          {(api.response_time * 1000).toFixed(1)}ms
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {status.gpu.available && (
            <Card>
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Cpu className="h-5 w-5" />
                GPU 상태
              </h2>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="font-medium">{status.gpu.device_name}</span>
                    <span className="text-sm text-muted-foreground">
                      {status.gpu.used_memory} / {status.gpu.total_memory} MB
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-purple-600 h-4 rounded-full transition-all"
                      style={{
                        width: `${((status.gpu.used_memory || 0) / (status.gpu.total_memory || 1)) * 100}%`,
                      }}
                    />
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">
                    Memory: {(((status.gpu.used_memory || 0) / (status.gpu.total_memory || 1)) * 100).toFixed(1)}% |
                    Utilization: {status.gpu.utilization}%
                  </div>
                </div>
              </div>
            </Card>
          )}

          <Card>
            <h2 className="text-xl font-semibold mb-4">시스템 리소스</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { label: 'CPU', value: status.system.cpu_percent, color: 'bg-blue-500' },
                { label: 'Memory', value: status.system.memory_percent, color: 'bg-green-500', detail: `${status.system.memory_used_gb}/${status.system.memory_total_gb} GB` },
                { label: 'Disk', value: status.system.disk_percent, color: 'bg-purple-500', detail: `${status.system.disk_used_gb}/${status.system.disk_total_gb} GB` },
              ].map(({ label, value, color, detail }) => (
                <div key={label}>
                  <div className="flex justify-between mb-1">
                    <span className="font-medium">{label}</span>
                    <span className="text-sm">{value.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all ${color}`}
                      style={{ width: `${value}%` }}
                    />
                  </div>
                  {detail && <div className="text-xs text-muted-foreground mt-1">{detail}</div>}
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'models' && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">모델 경로</h2>
            <Button size="sm" variant="outline" onClick={fetchModels}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
          <div className="space-y-3">
            {models.length > 0 ? (
              models.map((model) => (
                <div
                  key={model.model_type}
                  className="flex justify-between items-center p-4 bg-accent rounded-lg"
                >
                  <div>
                    <h3 className="font-semibold capitalize">{model.model_type}</h3>
                    <code className="text-sm text-muted-foreground">{model.host_path}</code>
                  </div>
                  <div className="text-right text-sm">
                    <div className="font-medium">{model.total_size_mb.toFixed(1)} MB</div>
                    <div className="text-muted-foreground">{model.file_count}개 파일</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-muted-foreground py-8">
                모델 정보를 불러오는 중...
              </div>
            )}
          </div>
        </Card>
      )}

      {activeTab === 'logs' && status && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">서비스 로그</h2>
            <div className="flex gap-2">
              <select
                value={selectedService}
                onChange={e => setSelectedService(e.target.value)}
                className="px-3 py-2 border rounded bg-background"
              >
                {status.apis.map(api => (
                  <option key={api.name} value={api.name}>
                    {api.display_name}
                  </option>
                ))}
              </select>
              <Button onClick={() => fetchLogs(selectedService)}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <div className="bg-black text-green-400 p-4 rounded font-mono text-sm h-96 overflow-auto">
            <pre>{logs || '로그를 불러오는 중...'}</pre>
          </div>
        </Card>
      )}

      {activeTab === 'backup' && (
        <div className="space-y-6">
          <Card>
            <h2 className="text-xl font-semibold mb-4">설정 백업</h2>
            <p className="text-muted-foreground mb-4">
              API 설정, 하이퍼파라미터, 커스텀 API 정보를 JSON 파일로 내보냅니다.
            </p>
            <Button onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              설정 내보내기
            </Button>
          </Card>

          <Card>
            <h2 className="text-xl font-semibold mb-4">설정 복원</h2>
            <p className="text-muted-foreground mb-4">
              백업된 JSON 파일에서 설정을 복원합니다. 현재 설정은 덮어씌워집니다.
            </p>
            <Button variant="outline" onClick={handleImport}>
              <Upload className="h-4 w-4 mr-2" />
              설정 가져오기
            </Button>
          </Card>

          <Card>
            <h2 className="text-xl font-semibold mb-4">설정 초기화</h2>
            <p className="text-muted-foreground mb-4">
              모든 설정을 기본값으로 되돌립니다. 이 작업은 되돌릴 수 없습니다.
            </p>
            <Button variant="outline" className="text-red-600 hover:bg-red-50 border-red-200" onClick={handleReset}>
              <RefreshCw className="h-4 w-4 mr-2" />
              기본값으로 초기화
            </Button>
          </Card>
        </div>
      )}

      {status && (
        <div className="text-sm text-muted-foreground text-center">
          마지막 업데이트: {new Date(status.timestamp).toLocaleString('ko-KR')} •
          자동 갱신: {SYSTEM_CONFIG.AUTO_REFRESH_INTERVAL / 1000}초마다
        </div>
      )}
    </div>
  );
}
