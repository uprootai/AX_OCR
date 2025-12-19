/**
 * QuickStats Component
 * API 상태 요약 통계 표시
 */

import { Server, CheckCircle, AlertCircle } from 'lucide-react';

interface QuickStatsProps {
  totalCount: number;
  healthyCount: number;
  unhealthyCount: number;
  categoryCount: number;
}

export function QuickStats({
  totalCount,
  healthyCount,
  unhealthyCount,
  categoryCount,
}: QuickStatsProps) {
  const uptime = totalCount > 0 ? Math.round((healthyCount / totalCount) * 100) : 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div className="p-3 bg-muted/50 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">전체</span>
          <Server className="h-4 w-4 text-muted-foreground" />
        </div>
        <p className="text-2xl font-bold">{totalCount}</p>
      </div>
      <div className="p-3 bg-green-50 dark:bg-green-950 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm text-green-600 dark:text-green-400">정상</span>
          <CheckCircle className="h-4 w-4 text-green-500" />
        </div>
        <p className="text-2xl font-bold text-green-600 dark:text-green-400">{healthyCount}</p>
      </div>
      <div className="p-3 bg-red-50 dark:bg-red-950 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm text-red-600 dark:text-red-400">오류</span>
          <AlertCircle className="h-4 w-4 text-red-500" />
        </div>
        <p className="text-2xl font-bold text-red-600 dark:text-red-400">{unhealthyCount}</p>
      </div>
      <div className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm text-blue-600 dark:text-blue-400">가동률</span>
          <span className="text-xs text-blue-500">{categoryCount} 카테고리</span>
        </div>
        <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{uptime}%</p>
      </div>
    </div>
  );
}
