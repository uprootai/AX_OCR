import { useState, useEffect } from 'react';
import { Activity, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import axios from 'axios';

interface SystemStatus {
  apis: APIStatus[];
  gpu: GPUStatus;
  system: SystemStats;
  timestamp: string;
}

interface APIStatus {
  name: string;
  url: string;
  status: string;
  response_time: number;
  details?: any;
}

interface GPUStatus {
  available: boolean;
  device_name: string;
  total_memory: number;
  used_memory: number;
  free_memory: number;
  utilization: number;
}

interface SystemStats {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
}

export default function Monitor() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const response = await axios.get('http://localhost:9000/api/status');
      setStatus(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch status:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Every 5 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg">시스템 상태를 불러오는 중...</div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-red-500">시스템 상태를 불러올 수 없습니다</div>
      </div>
    );
  }

  const healthyAPIs = status.apis.filter(api => api.status === 'healthy').length;
  const totalAPIs = status.apis.length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
          <Activity className="h-8 w-8" />
          실시간 모니터링
        </h1>
        <p className="text-muted-foreground">
          API 성능, GPU 상태, 시스템 리소스를 실시간으로 모니터링합니다. (5초 자동 갱신)
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">API 상태</p>
              <p className="text-2xl font-bold">
                {healthyAPIs}/{totalAPIs}
              </p>
            </div>
            {healthyAPIs === totalAPIs ? (
              <CheckCircle className="h-8 w-8 text-green-500" />
            ) : (
              <AlertCircle className="h-8 w-8 text-red-500" />
            )}
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">CPU 사용률</p>
              <p className="text-2xl font-bold">{status.system.cpu_percent.toFixed(1)}%</p>
            </div>
            <TrendingUp className="h-8 w-8 text-blue-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">메모리 사용률</p>
              <p className="text-2xl font-bold">{status.system.memory_percent.toFixed(1)}%</p>
            </div>
            <TrendingUp className="h-8 w-8 text-green-500" />
          </div>
        </Card>

        {status.gpu.available && (
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">GPU 메모리</p>
                <p className="text-2xl font-bold">
                  {((status.gpu.used_memory / status.gpu.total_memory) * 100).toFixed(1)}%
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-500" />
            </div>
          </Card>
        )}
      </div>

      {/* API Status Details */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">API 상태 상세</h2>
        <div className="space-y-3">
          {status.apis.map(api => (
            <div
              key={api.name}
              className={`p-4 rounded-lg border-2 ${
                api.status === 'healthy'
                  ? 'border-green-500 bg-green-50 dark:bg-green-950'
                  : 'border-red-500 bg-red-50 dark:bg-red-950'
              }`}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold uppercase flex items-center gap-2">
                    {api.status === 'healthy' ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-red-600" />
                    )}
                    {api.name}
                  </h3>
                  <p className="text-sm text-muted-foreground mt-1">{api.url}</p>
                  {api.details && (
                    <div className="mt-2 text-xs space-y-1">
                      {api.details.service && <p>Service: {api.details.service}</p>}
                      {api.details.version && <p>Version: {api.details.version}</p>}
                      {api.details.gpu_available !== undefined && (
                        <p>GPU: {api.details.gpu_available ? '✅ Available' : '❌ Not Available'}</p>
                      )}
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <span
                    className={`px-2 py-1 text-xs font-semibold rounded ${
                      api.status === 'healthy'
                        ? 'bg-green-600 text-white'
                        : 'bg-red-600 text-white'
                    }`}
                  >
                    {api.status}
                  </span>
                  <p className="text-sm mt-2">
                    {(api.response_time * 1000).toFixed(1)}ms
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* GPU Status */}
      {status.gpu.available && (
        <Card>
          <h2 className="text-xl font-semibold mb-4">GPU 상태</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="font-medium text-lg">{status.gpu.device_name}</span>
                <span className="text-sm text-muted-foreground">
                  {status.gpu.used_memory} MB / {status.gpu.total_memory} MB
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-6">
                <div
                  className="bg-gradient-to-r from-blue-500 to-purple-600 h-6 rounded-full transition-all flex items-center justify-center text-white text-xs font-semibold"
                  style={{
                    width: `${(status.gpu.used_memory / status.gpu.total_memory) * 100}%`,
                  }}
                >
                  {((status.gpu.used_memory / status.gpu.total_memory) * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
              <div>
                <p className="text-sm text-muted-foreground">사용 중</p>
                <p className="text-xl font-bold">{status.gpu.used_memory} MB</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">여유</p>
                <p className="text-xl font-bold text-green-500">{status.gpu.free_memory} MB</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">활용률</p>
                <p className="text-xl font-bold">{status.gpu.utilization}%</p>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* System Resources */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">시스템 리소스</h2>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between mb-1">
              <span className="font-medium">CPU</span>
              <span className="text-sm">{status.system.cpu_percent.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
              <div
                className={`h-4 rounded-full transition-all ${
                  status.system.cpu_percent > 80
                    ? 'bg-red-500'
                    : status.system.cpu_percent > 50
                    ? 'bg-yellow-500'
                    : 'bg-blue-500'
                }`}
                style={{ width: `${status.system.cpu_percent}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between mb-1">
              <span className="font-medium">Memory</span>
              <span className="text-sm">{status.system.memory_percent.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
              <div
                className={`h-4 rounded-full transition-all ${
                  status.system.memory_percent > 80
                    ? 'bg-red-500'
                    : status.system.memory_percent > 50
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
                }`}
                style={{ width: `${status.system.memory_percent}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between mb-1">
              <span className="font-medium">Disk</span>
              <span className="text-sm">{status.system.disk_percent.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
              <div
                className={`h-4 rounded-full transition-all ${
                  status.system.disk_percent > 80
                    ? 'bg-red-500'
                    : status.system.disk_percent > 50
                    ? 'bg-yellow-500'
                    : 'bg-purple-500'
                }`}
                style={{ width: `${status.system.disk_percent}%` }}
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Last Updated */}
      <div className="text-sm text-muted-foreground text-center">
        마지막 업데이트: {new Date(status.timestamp).toLocaleString('ko-KR')}
      </div>
    </div>
  );
}
