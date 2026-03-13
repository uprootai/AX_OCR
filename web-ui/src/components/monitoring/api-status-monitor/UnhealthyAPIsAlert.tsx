/**
 * UnhealthyAPIsAlert — 연결 실패 API 목록 알림
 */

import { AlertCircle } from 'lucide-react';
import type { APIInfo } from '../types';

export function UnhealthyAPIsAlert({ unhealthyAPIs }: { unhealthyAPIs: APIInfo[] }) {
  return (
    <div className="p-4 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg">
      <div className="flex items-center gap-2 mb-3">
        <AlertCircle className="h-5 w-5 text-red-500" />
        <span className="font-semibold text-red-700 dark:text-red-300">
          연결 실패 API ({unhealthyAPIs.length}개)
        </span>
      </div>
      <div className="grid md:grid-cols-2 gap-2">
        {unhealthyAPIs.map(api => (
          <div
            key={api.id}
            className="flex items-center justify-between p-2 bg-white dark:bg-gray-900 rounded border border-red-200 dark:border-red-800"
          >
            <div className="flex items-center gap-2">
              <span>{api.icon}</span>
              <span className="font-medium text-sm">{api.display_name}</span>
            </div>
            <span className="text-xs text-red-600">:{api.port}</span>
          </div>
        ))}
      </div>
      <p className="mt-3 text-xs text-muted-foreground">
        Docker 컨테이너 확인: <code className="bg-muted px-1 rounded">docker-compose ps</code>
      </p>
    </div>
  );
}
