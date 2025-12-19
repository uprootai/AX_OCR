/**
 * ResourcePanel Component
 * GPU 및 컨테이너 리소스 표시 패널
 */

import { useState } from 'react';
import { ChevronDown, ChevronUp, Cpu, MemoryStick, Thermometer } from 'lucide-react';
import type { ContainerStats, GPUStats, APIInfo } from '../types';

interface ResourcePanelProps {
  gpuAvailable: boolean;
  gpuStats: GPUStats[];
  containerStats: Record<string, ContainerStats>;
  apis: APIInfo[];
}

export function ResourcePanel({
  gpuAvailable,
  gpuStats,
  containerStats,
  apis,
}: ResourcePanelProps) {
  const [showResourcePanel, setShowResourcePanel] = useState(true);

  return (
    <div className="border rounded-lg overflow-hidden">
      <button
        onClick={() => setShowResourcePanel(!showResourcePanel)}
        className="w-full flex items-center justify-between p-3 bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-950 dark:to-indigo-950 hover:opacity-90"
      >
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-purple-600" />
          <span className="font-semibold text-purple-700 dark:text-purple-300">시스템 리소스</span>
          {gpuAvailable && (
            <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 rounded-full">
              GPU 활성
            </span>
          )}
        </div>
        {showResourcePanel ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {showResourcePanel && (
        <div className="p-3 space-y-3">
          {/* GPU Stats */}
          {gpuAvailable && gpuStats.length > 0 && (
            <div className="space-y-2">
              {gpuStats.map((gpu) => (
                <GPUCard key={gpu.index} gpu={gpu} />
              ))}
            </div>
          )}

          {!gpuAvailable && (
            <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-center">
              <span className="text-sm text-muted-foreground">GPU 없음 (CPU 모드)</span>
            </div>
          )}

          {/* Container Resource Summary */}
          {Object.keys(containerStats).length > 0 && (
            <ContainerResourceGrid containerStats={containerStats} apis={apis} />
          )}
        </div>
      )}
    </div>
  );
}

// GPU Card component
function GPUCard({ gpu }: { gpu: GPUStats }) {
  return (
    <div className="p-3 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">🎮</span>
          <span className="font-medium text-sm">{gpu.name}</span>
        </div>
        {gpu.temperature && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Thermometer className="h-3 w-3" />
            <span className={gpu.temperature > 80 ? 'text-red-500' : gpu.temperature > 60 ? 'text-yellow-500' : 'text-green-500'}>
              {gpu.temperature}°C
            </span>
          </div>
        )}
      </div>
      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">VRAM</span>
          <span className="font-mono">{gpu.memory_used}MB / {gpu.memory_total}MB ({gpu.memory_percent}%)</span>
        </div>
        <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all ${
              gpu.memory_percent > 90 ? 'bg-red-500' :
              gpu.memory_percent > 70 ? 'bg-yellow-500' : 'bg-green-500'
            }`}
            style={{ width: `${gpu.memory_percent}%` }}
          />
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">GPU 사용률</span>
          <span className="font-mono">{gpu.utilization}%</span>
        </div>
        <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all ${
              gpu.utilization > 90 ? 'bg-red-500' :
              gpu.utilization > 70 ? 'bg-yellow-500' : 'bg-blue-500'
            }`}
            style={{ width: `${gpu.utilization}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// Container resource grid
function ContainerResourceGrid({
  containerStats,
  apis,
}: {
  containerStats: Record<string, ContainerStats>;
  apis: APIInfo[];
}) {
  return (
    <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
      <div className="flex items-center gap-2 mb-2">
        <MemoryStick className="h-4 w-4 text-blue-500" />
        <span className="text-sm font-medium">실행 중인 컨테이너 리소스</span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
        {Object.entries(containerStats)
          .filter(([, stats]) => stats.memory_usage || stats.cpu_percent)
          .map(([apiId, stats]) => {
            const api = apis.find(a => a.id === apiId);
            return (
              <div key={apiId} className="p-2 bg-white dark:bg-gray-800 rounded border text-xs">
                <div className="font-medium truncate">{api?.display_name || apiId}</div>
                <div className="flex items-center gap-2 mt-1 text-muted-foreground">
                  {stats.memory_usage && (
                    <span className="flex items-center gap-1">
                      <MemoryStick className="h-3 w-3" />
                      {stats.memory_usage}
                    </span>
                  )}
                  {stats.cpu_percent !== null && (
                    <span className="flex items-center gap-1">
                      <Cpu className="h-3 w-3" />
                      {stats.cpu_percent.toFixed(1)}%
                    </span>
                  )}
                </div>
              </div>
            );
          })}
      </div>
    </div>
  );
}
