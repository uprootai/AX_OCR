/**
 * APICard — 개별 API 상태 카드
 */

import {
  ExternalLink,
  Settings,
  Trash2,
  Cpu,
  MemoryStick,
  Loader2,
  StopCircle,
  PlayCircle,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import type { APIInfo, ContainerStats, APIResourceSpec } from '../types';

interface APICardProps {
  api: APIInfo;
  containerStats?: ContainerStats;
  resourceSpec?: APIResourceSpec;
  onDelete: () => void;
  onAction: (api: APIInfo, action: 'stop' | 'start') => void;
  isActionLoading: boolean;
  isGlobalLoading: boolean;
}

export function APICard({
  api,
  containerStats,
  resourceSpec,
  onDelete,
  onAction,
  isActionLoading,
  isGlobalLoading,
}: APICardProps) {
  return (
    <div className={`p-3 rounded-lg border-2 transition-all ${
      api.status === 'healthy'
        ? 'border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-950/50'
        : 'border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-950/50'
    }`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="w-7 h-7 rounded flex items-center justify-center text-sm" style={{ backgroundColor: api.color + '25' }}>
            {api.icon}
          </span>
          <div>
            <h4 className="font-medium text-sm leading-tight">{api.display_name}</h4>
            <code className="text-[10px] text-muted-foreground">{api.id}</code>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {/* Stop/Start 버튼 */}
          {api.status === 'healthy' ? (
            <button
              onClick={(e) => { e.stopPropagation(); onAction(api, 'stop'); }}
              disabled={isActionLoading || isGlobalLoading}
              className={`p-1 rounded transition-colors ${
                isActionLoading
                  ? 'bg-red-100 text-red-400 cursor-wait'
                  : 'hover:bg-red-100 text-red-500 hover:text-red-700'
              }`}
              title="API 중지"
            >
              {isActionLoading ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <StopCircle className="h-3.5 w-3.5" />
              )}
            </button>
          ) : (
            <button
              onClick={(e) => { e.stopPropagation(); onAction(api, 'start'); }}
              disabled={isActionLoading || isGlobalLoading}
              className={`p-1 rounded transition-colors ${
                isActionLoading
                  ? 'bg-green-100 text-green-400 cursor-wait'
                  : 'hover:bg-green-100 text-green-500 hover:text-green-700'
              }`}
              title="API 시작"
            >
              {isActionLoading ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <PlayCircle className="h-3.5 w-3.5" />
              )}
            </button>
          )}
          <span className={`px-1.5 py-0.5 text-[10px] font-semibold rounded ${
            api.status === 'healthy' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
          }`}>
            {api.status === 'healthy' ? 'OK' : 'ERR'}
          </span>
        </div>
      </div>

      <p className="text-xs text-muted-foreground mb-2 line-clamp-1">{api.description}</p>

      {/* Resource Usage */}
      <div className="mb-2 space-y-1">
        {api.status === 'healthy' && containerStats && (
          <div className="flex items-center gap-2 text-[10px] text-blue-600 dark:text-blue-400">
            {containerStats.memory_usage && (
              <span className="flex items-center gap-0.5">
                <MemoryStick className="h-2.5 w-2.5" />
                {containerStats.memory_usage}
              </span>
            )}
            {containerStats.cpu_percent !== null && (
              <span className="flex items-center gap-0.5">
                <Cpu className="h-2.5 w-2.5" />
                {containerStats.cpu_percent?.toFixed(1)}%
              </span>
            )}
          </div>
        )}

        {resourceSpec && (
          <div className="space-y-1">
            <div className="flex flex-wrap gap-1 text-[9px]">
              {resourceSpec.gpu && (
                <span className={`px-1.5 py-0.5 rounded cursor-help ${
                  resourceSpec.gpu.vram === 'N/A'
                    ? 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
                    : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                }`} title={resourceSpec.gpu.recommended || ''}>
                  🎮 {resourceSpec.gpu.vram || '-'}
                </span>
              )}
              {resourceSpec.cpu && (
                <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 rounded cursor-help"
                  title={resourceSpec.cpu.note || ''}>
                  💻 {resourceSpec.cpu.ram || '?'}/{resourceSpec.cpu.cores || '?'}c
                </span>
              )}
            </div>
            {resourceSpec.parameterImpact && resourceSpec.parameterImpact.length > 0 && (
              <div className="text-[8px] text-amber-600 dark:text-amber-400 truncate"
                title={resourceSpec.parameterImpact.map(p => `${p.parameter}: ${p.impact}`).join('\n')}>
                ⚠️ {resourceSpec.parameterImpact[0].impact}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between text-[10px]">
        <span className="text-muted-foreground">:{api.port}</span>
        <div className="flex items-center gap-2">
          <a href={`http://localhost:${api.port}/docs`} target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-0.5 text-primary hover:underline" onClick={(e) => e.stopPropagation()}>
            <ExternalLink className="h-2.5 w-2.5" />
            Swagger
          </a>
          <Link to={`/admin/api/${api.id}`} className="flex items-center gap-0.5 text-muted-foreground hover:text-primary"
            onClick={(e) => e.stopPropagation()}>
            <Settings className="h-2.5 w-2.5" />
            설정
          </Link>
          <button onClick={(e) => { e.stopPropagation(); onDelete(); }}
            className="flex items-center gap-0.5 text-muted-foreground hover:text-destructive" title="목록에서 삭제">
            <Trash2 className="h-2.5 w-2.5" />
            삭제
          </button>
        </div>
      </div>
    </div>
  );
}
