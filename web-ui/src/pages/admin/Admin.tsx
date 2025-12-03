import { useState, useEffect } from 'react';
import { Server, Cpu, HardDrive, Database, Play, Square, RefreshCw, FileCode } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import axios from 'axios';
import {
  ADMIN_ENDPOINTS,
  TRAINABLE_MODELS,
  DOCKER_SERVICES,
  SYSTEM_CONFIG,
  getAllAPIs,
} from '../../config/api';

interface SystemStatus {
  apis: any[];
  gpu: any;
  system: any;
  timestamp: string;
}

export default function Admin() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'models' | 'training' | 'docker' | 'logs'>('overview');
  const [models, setModels] = useState<any>({});
  const [logs, setLogs] = useState<string>('');
  const [selectedService, setSelectedService] = useState<string>('edocr2');
  const [trainingJobs, setTrainingJobs] = useState<any[]>([]);

  const fetchStatus = async () => {
    try {
      const response = await axios.get(ADMIN_ENDPOINTS.status);
      setStatus(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch status:', error);
      setLoading(false);
    }
  };

  const fetchModels = async (modelType: string) => {
    try {
      const response = await axios.get(ADMIN_ENDPOINTS.models(modelType));
      setModels((prev) => ({ ...prev, [modelType]: response.data.files || [] }));
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
    }
  };

  const fetchTrainingJobs = async () => {
    try {
      const response = await axios.get(ADMIN_ENDPOINTS.trainingList);
      setTrainingJobs(response.data.jobs || []);
    } catch (error) {
      console.error('Failed to fetch training jobs:', error);
    }
  };

  const trainModel = async (modelType: string) => {
    if (!window.confirm(`${modelType} 모델을 재학습하시겠습니까?`)) return;
    try {
      const response = await axios.post(ADMIN_ENDPOINTS.trainingStart, null, {
        params: { model_type: modelType }
      });
      alert(`학습이 백그라운드에서 시작되었습니다!\nJob ID: ${response.data.job_id}`);
      await fetchTrainingJobs();
    } catch (error) {
      const err = error as { response?: { data?: { message?: string } }; message?: string };
      alert(`학습 시작 실패: ${err.response?.data?.message || err.message}`);
    }
  };

  const dockerControl = async (action: string, service: string) => {
    if (!window.confirm(`${service} 서비스를 ${action}하시겠습니까?`)) return;
    try {
      const response = await axios.post(ADMIN_ENDPOINTS.docker(action, service));
      alert(`Docker ${action} ${service}: ${response.data.message}`);
      await fetchStatus();
    } catch (error) {
      const err = error as { response?: { data?: { message?: string } }; message?: string };
      alert(`Docker ${action} failed: ${err.response?.data?.message || err.message}`);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, SYSTEM_CONFIG.AUTO_REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeTab === 'models') {
      ['skinmodel', 'edgnet', 'yolo', 'edocr2'].forEach(fetchModels);
    } else if (activeTab === 'logs') {
      fetchLogs(selectedService);
    } else if (activeTab === 'training') {
      fetchTrainingJobs();
      const interval = setInterval(fetchTrainingJobs, 5000); // 5초마다 새로고침
      return () => clearInterval(interval);
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
          모델 관리, 학습 실행, Docker 제어 - 모든 것을 한 곳에서
        </p>
      </div>

      <div className="border-b">
        <nav className="flex gap-4">
          {[
            { id: 'overview', label: '시스템 현황', icon: Server },
            { id: 'models', label: '모델 관리', icon: Database },
            { id: 'training', label: '학습 실행', icon: Play },
            { id: 'docker', label: 'Docker 제어', icon: HardDrive },
            { id: 'logs', label: '로그 조회', icon: FileCode },
          ].map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
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
              {getAllAPIs().map(api => {
                const apiStatus = status.apis.find((a) => a.name === api.name);
                const isHealthy = apiStatus?.status === 'healthy';
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
                        <h3 className="font-semibold">{api.displayName}</h3>
                        <p className="text-xs text-muted-foreground">{api.description}</p>
                      </div>
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded ${
                          isHealthy
                            ? 'bg-green-600 text-white'
                            : 'bg-red-600 text-white'
                        }`}
                      >
                        {apiStatus?.status || 'unknown'}
                      </span>
                    </div>
                    <div className="mt-2 space-y-1 text-xs">
                      <div className="flex justify-between">
                        <span>Port:</span>
                        <span className="font-mono">{api.port}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>GPU:</span>
                        <span className={api.gpuEnabled ? 'text-green-600 font-semibold' : ''}>
                          {api.gpuEnabled ? '✅ Enabled' : '❌ Disabled'}
                        </span>
                      </div>
                      {apiStatus && (
                        <div className="flex justify-between">
                          <span>Response:</span>
                          <span className="font-mono">
                            {(apiStatus.response_time * 1000).toFixed(1)}ms
                          </span>
                        </div>
                      )}
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
                        width: `${(status.gpu.used_memory / status.gpu.total_memory) * 100}%`,
                      }}
                    />
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">
                    Memory: {((status.gpu.used_memory / status.gpu.total_memory) * 100).toFixed(1)}% |
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
                { label: 'CPU', value: status.system.cpu_percent, color: 'blue' },
                { label: 'Memory', value: status.system.memory_percent, color: 'green' },
                { label: 'Disk', value: status.system.disk_percent, color: 'purple' },
              ].map(({ label, value, color }) => (
                <div key={label}>
                  <div className="flex justify-between mb-1">
                    <span className="font-medium">{label}</span>
                    <span className="text-sm">{value.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full transition-all bg-${color}-500`}
                      style={{ width: `${value}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'models' && (
        <div className="space-y-6">
          {['skinmodel', 'edgnet', 'yolo', 'edocr2'].map(modelType => (
            <Card key={modelType}>
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-xl font-semibold capitalize">{modelType} 모델</h2>
                <Button size="sm" variant="outline" onClick={() => fetchModels(modelType)}>
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
              <div className="space-y-2">
                {models[modelType]?.length > 0 ? (
                  models[modelType].map((file) => (
                    <div
                      key={file.name}
                      className="flex justify-between items-center p-3 bg-accent rounded"
                    >
                      <span className="font-mono text-sm">{file.name}</span>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                        {file.modified && (
                          <span>{new Date(file.modified).toLocaleDateString('ko-KR')}</span>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-muted-foreground py-8">
                    모델 파일이 없습니다
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {activeTab === 'training' && (
        <div className="space-y-6">
          <Card>
            <h2 className="text-xl font-semibold mb-4">모델 학습 실행</h2>
            <p className="text-muted-foreground mb-6">
              웹에서 클릭 한 번으로 모델을 재학습할 수 있습니다.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {TRAINABLE_MODELS.map(model => (
                <div key={model.type} className="p-4 border rounded-lg">
                  <h3 className="font-semibold">{model.displayName}</h3>
                  <p className="text-sm text-muted-foreground mt-1">{model.description}</p>
                  <div className="mt-2 space-y-1 text-xs">
                    <p>예상 소요 시간: {model.estimatedTime}</p>
                    <p>GPU 필요: {model.gpuRequired ? '✅ Yes' : '❌ No'}</p>
                  </div>
                  <Button onClick={() => trainModel(model.type)} className="w-full mt-4">
                    <Play className="h-4 w-4 mr-2" />
                    학습 시작
                  </Button>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <h2 className="text-xl font-semibold mb-4">학습 작업 목록</h2>
            <p className="text-muted-foreground mb-6">
              현재 진행 중이거나 완료된 학습 작업을 실시간으로 확인할 수 있습니다.
            </p>
            {trainingJobs.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                학습 작업이 없습니다
              </div>
            ) : (
              <div className="space-y-4">
                {trainingJobs.map(job => (
                  <div key={job.job_id} className="p-4 border rounded-lg">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-semibold text-lg">{job.model_type}</h3>
                        <p className="text-xs text-muted-foreground font-mono">{job.job_id}</p>
                      </div>
                      <span
                        className={`px-3 py-1 text-xs font-semibold rounded ${
                          job.status === 'completed'
                            ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'
                            : job.status === 'failed'
                            ? 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300'
                            : job.status === 'running'
                            ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                            : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                        }`}
                      >
                        {job.status}
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-3">
                      <div className="flex justify-between text-sm mb-1">
                        <span>진행률</span>
                        <span className="font-semibold">{job.progress.toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                        <div
                          className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                          style={{ width: `${job.progress}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Epoch Counter */}
                    <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                      <div>
                        <span className="text-muted-foreground">현재 에포크:</span>
                        <span className="ml-2 font-semibold">{job.current_epoch} / {job.total_epochs}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">시작 시간:</span>
                        <span className="ml-2 font-mono text-xs">
                          {job.started_at ? new Date(job.started_at).toLocaleString('ko-KR') : 'N/A'}
                        </span>
                      </div>
                    </div>

                    {/* Logs */}
                    {job.logs && job.logs.length > 0 && (
                      <div className="mt-3">
                        <div className="text-sm font-semibold mb-2">최근 로그</div>
                        <div className="bg-gray-100 dark:bg-gray-800 rounded p-3 max-h-48 overflow-y-auto">
                          <pre className="text-xs font-mono whitespace-pre-wrap">
                            {job.logs.slice(-10).join('\n')}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

      {activeTab === 'docker' && (
        <Card>
          <h2 className="text-xl font-semibold mb-4">Docker 컨테이너 제어</h2>
          <p className="text-muted-foreground mb-6">
            각 서비스의 Docker 컨테이너를 시작, 중지, 재시작할 수 있습니다.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {DOCKER_SERVICES.map(service => (
              <div key={service.name} className="p-4 border rounded-lg">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-semibold">{service.displayName}</h3>
                  {service.gpuEnabled && (
                    <span className="px-2 py-1 text-xs bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded">
                      GPU
                    </span>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => dockerControl('start', service.name)}
                    className="flex-1"
                    title="시작"
                  >
                    <Play className="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => dockerControl('stop', service.name)}
                    className="flex-1"
                    title="중지"
                  >
                    <Square className="h-3 w-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => dockerControl('restart', service.name)}
                    className="flex-1"
                    title="재시작"
                  >
                    <RefreshCw className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {activeTab === 'logs' && (
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">서비스 로그</h2>
            <div className="flex gap-2">
              <select
                value={selectedService}
                onChange={e => setSelectedService(e.target.value)}
                className="px-3 py-2 border rounded bg-background"
              >
                {DOCKER_SERVICES.map(service => (
                  <option key={service.name} value={service.name}>
                    {service.displayName}
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

      {status && (
        <div className="text-sm text-muted-foreground text-center">
          마지막 업데이트: {new Date(status.timestamp).toLocaleString('ko-KR')} •
          자동 갱신: {SYSTEM_CONFIG.AUTO_REFRESH_INTERVAL / 1000}초마다
        </div>
      )}
    </div>
  );
}
