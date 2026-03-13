/**
 * QuotationDashboard - 공유 타입 및 상수
 */

export type FilterType = 'all' | 'completed' | 'pending' | 'no_session';

export interface BatchStatus {
  status: string;
  total: number;
  completed: number;
  failed: number;
  skipped: number;
  current_drawing: string | null;
}

export const STATUS_BADGE: Record<string, string> = {
  completed: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
  detecting: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
  detected: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
  verifying: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400',
  error: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
};

export const COST_SOURCE_STYLES: Record<string, { label: string; className: string }> = {
  calculated: { label: '계산', className: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' },
  estimated: { label: '추정', className: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' },
  standard_catalog: { label: '카탈로그', className: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' },
  none: { label: '-', className: 'bg-gray-50 dark:bg-gray-700 text-gray-400 dark:text-gray-500' },
};
