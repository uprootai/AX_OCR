/**
 * Service Settings Card Component
 * Displays port, device, memory settings, and container status
 */

import { Card } from '../../../../components/ui/Card';
import { Server } from 'lucide-react';
import type { APIConfig, GPUInfo, ContainerStatus } from '../hooks/useAPIDetail';
import type { APIInfo } from '../../../../components/monitoring/types';

interface ServiceSettingsCardProps {
  apiInfo: APIInfo;
  config: APIConfig;
  setConfig: React.Dispatch<React.SetStateAction<APIConfig>>;
  containerStatus: ContainerStatus | null;
  gpuInfo: GPUInfo | null;
}

export function ServiceSettingsCard({
  apiInfo,
  config,
  setConfig,
  containerStatus,
  gpuInfo,
}: ServiceSettingsCardProps) {
  return (
    <Card>
      <div className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Server className="h-5 w-5" />
          서비스 설정
        </h3>

        {/* Current container status */}
        {containerStatus && (
          <div className="mb-4 p-3 bg-muted/50 rounded border">
            <div className="text-sm font-medium mb-2">현재 컨테이너 상태</div>
            <div className="flex items-center gap-4 text-sm">
              <span className={`flex items-center gap-1 ${containerStatus.running ? 'text-green-600' : 'text-red-500'}`}>
                <span className={`w-2 h-2 rounded-full ${containerStatus.running ? 'bg-green-500' : 'bg-red-500'}`} />
                {containerStatus.running ? '실행 중' : '중지됨'}
              </span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${containerStatus.gpu_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                {containerStatus.gpu_enabled ? 'GPU' : 'CPU'}
              </span>
              {containerStatus.memory_limit && (
                <span className="text-muted-foreground">
                  메모리: {containerStatus.memory_limit}
                </span>
              )}
            </div>
          </div>
        )}

        <div className="space-y-4">
          {/* Port */}
          <div>
            <label className="block text-sm font-medium mb-1">포트</label>
            <input
              type="text"
              value={apiInfo.port}
              disabled
              className="w-full px-3 py-2 border rounded bg-muted"
            />
          </div>

          {/* Device */}
          <div>
            <label className="block text-sm font-medium mb-1">연산 장치</label>
            <select
              value={config.device}
              onChange={(e) => setConfig({ ...config, device: e.target.value as 'cpu' | 'cuda' })}
              className="w-full px-3 py-2 border rounded bg-background"
            >
              <option value="cpu">CPU</option>
              <option value="cuda">CUDA (GPU)</option>
            </select>
          </div>

          {/* Memory limit */}
          <div>
            <label className="block text-sm font-medium mb-1">메모리 제한</label>
            <input
              type="text"
              value={config.memory_limit}
              onChange={(e) => setConfig({ ...config, memory_limit: e.target.value })}
              placeholder="예: 4g"
              className="w-full px-3 py-2 border rounded bg-background"
            />
          </div>

          {/* GPU Memory */}
          {config.device === 'cuda' && (
            <div>
              <label className="block text-sm font-medium mb-1">GPU 메모리 제한</label>
              <input
                type="text"
                value={config.gpu_memory || ''}
                onChange={(e) => setConfig({ ...config, gpu_memory: e.target.value })}
                placeholder="예: 6g"
                className="w-full px-3 py-2 border rounded bg-background"
              />
              {/* GPU info display */}
              {gpuInfo && (
                <div className="mt-2 p-3 bg-muted/50 rounded border text-sm">
                  <div className="font-medium text-primary mb-2">{gpuInfo.name}</div>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div>
                      <div className="text-xs text-muted-foreground">전체</div>
                      <div className="font-semibold">{(gpuInfo.total_mb / 1024).toFixed(1)}GB</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">사용 중</div>
                      <div className="font-semibold text-orange-500">{(gpuInfo.used_mb / 1024).toFixed(1)}GB</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">사용 가능</div>
                      <div className="font-semibold text-green-500">{(gpuInfo.free_mb / 1024).toFixed(1)}GB</div>
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-muted-foreground">
                    GPU 사용률: {gpuInfo.utilization}% |
                    권장: {Math.floor(gpuInfo.free_mb / 1024 * 0.8)}GB 이하
                  </div>
                  {/* Progress bar */}
                  <div className="mt-2 h-2 bg-gray-200 rounded overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500"
                      style={{ width: `${(gpuInfo.used_mb / gpuInfo.total_mb) * 100}%` }}
                    />
                  </div>
                </div>
              )}
              {!gpuInfo && (
                <p className="text-xs text-muted-foreground mt-1">
                  GPU 정보를 로드할 수 없습니다
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
