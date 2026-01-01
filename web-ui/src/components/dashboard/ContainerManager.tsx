import { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import Toast from '../ui/Toast';
import { Play, Square, RefreshCw, Server, Cpu, HardDrive } from 'lucide-react';

// Toast 알림 타입
interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

interface ContainerInfo {
  id: string;
  name: string;
  status: string;
  image: string;
  ports: Record<string, string>;
  created: string;
  memory_usage: string | null;
  cpu_percent: number | null;
}

interface ContainerListResponse {
  success: boolean;
  containers: ContainerInfo[];
  error?: string;
}

export default function ContainerManager() {
  const [containers, setContainers] = useState<ContainerInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Toast 알림 상태
  const [toast, setToast] = useState<ToastState>({ show: false, message: '', type: 'info' });

  // Toast 표시 헬퍼 함수
  const showToast = useCallback((message: string, type: ToastState['type'] = 'info') => {
    setToast({ show: true, message, type });
  }, []);

  const fetchContainers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/v1/containers');
      const data: ContainerListResponse = await response.json();
      if (data.success) {
        setContainers(data.containers);
      } else {
        setError(data.error || 'Failed to fetch containers');
      }
    } catch (_err) {
      setError('Failed to connect to Gateway API');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchContainers();
    // 30초마다 자동 새로고침
    const interval = setInterval(fetchContainers, 30000);
    return () => clearInterval(interval);
  }, [fetchContainers]);

  const handleAction = async (containerName: string, action: 'start' | 'stop' | 'restart') => {
    setActionLoading(containerName);
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/containers/${containerName}/${action}`,
        { method: 'POST' }
      );
      const data = await response.json();
      if (data.success) {
        // 성공 시 목록 새로고침
        await fetchContainers();
        const actionLabel = action === 'start' ? '시작' : action === 'stop' ? '중지' : '재시작';
        showToast(`✓ ${containerName} ${actionLabel} 완료`, 'success');
      } else {
        const errorMsg = data.error || data.message || '알 수 없는 오류';
        showToast(`✗ ${containerName} 작업 실패\n${errorMsg}`, 'error');
      }
    } catch (err) {
      const errorMsg = (err as Error).message || '알 수 없는 오류';
      showToast(`✗ ${containerName} 작업 실패\n${errorMsg}`, 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-500';
      case 'exited':
        return 'bg-red-500';
      case 'paused':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  const runningCount = containers.filter(c => c.status === 'running').length;
  const stoppedCount = containers.filter(c => c.status !== 'running').length;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5" />
            Container Management ({runningCount}/{containers.length})
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchContainers}
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Summary */}
        <div className="flex gap-4 mb-4">
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span>Running: {runningCount}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span>Stopped: {stoppedCount}</span>
          </div>
        </div>

        {/* Container List */}
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {containers.map((container) => (
            <div
              key={container.id}
              className={`flex items-center justify-between p-3 border rounded-lg transition-colors ${
                container.status === 'running'
                  ? 'bg-background'
                  : 'bg-muted/50 opacity-70'
              }`}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                {/* Status indicator */}
                <div
                  className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${getStatusColor(container.status)}`}
                  title={container.status}
                />

                {/* Container info */}
                <div className="min-w-0 flex-1">
                  <div className="font-medium truncate">{container.name}</div>
                  <div className="text-xs text-muted-foreground flex items-center gap-3 flex-wrap">
                    <span className="truncate">{container.image.split(':')[0]}</span>
                    {Object.entries(container.ports).length > 0 && (
                      <span className="text-blue-600 dark:text-blue-400">
                        :{Object.values(container.ports)[0]}
                      </span>
                    )}
                  </div>
                </div>

                {/* Resource usage */}
                {container.status === 'running' && (
                  <div className="hidden sm:flex items-center gap-4 text-xs text-muted-foreground">
                    {container.memory_usage && (
                      <div className="flex items-center gap-1" title="Memory">
                        <HardDrive className="w-3 h-3" />
                        {container.memory_usage}
                      </div>
                    )}
                    {container.cpu_percent !== null && (
                      <div className="flex items-center gap-1" title="CPU">
                        <Cpu className="w-3 h-3" />
                        {container.cpu_percent}%
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1 ml-2">
                {container.status === 'running' ? (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleAction(container.name, 'stop')}
                    disabled={actionLoading === container.name}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    title="Stop"
                  >
                    {actionLoading === container.name ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Square className="w-4 h-4" />
                    )}
                  </Button>
                ) : (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleAction(container.name, 'start')}
                    disabled={actionLoading === container.name}
                    className="text-green-600 hover:text-green-700 hover:bg-green-50"
                    title="Start"
                  >
                    {actionLoading === container.name ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                  </Button>
                )}
              </div>
            </div>
          ))}

          {containers.length === 0 && !loading && (
            <div className="text-center text-muted-foreground py-8">
              No containers found
            </div>
          )}

          {loading && containers.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
              Loading containers...
            </div>
          )}
        </div>

        {/* Toast 알림 */}
        {toast.show && (
          <Toast
            message={toast.message}
            type={toast.type}
            duration={toast.type === 'error' ? 15000 : 10000}
            onClose={() => setToast(prev => ({ ...prev, show: false }))}
          />
        )}
      </CardContent>
    </Card>
  );
}
