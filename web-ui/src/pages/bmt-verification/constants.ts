import type { VerdictType, SeverityLevel } from './types';

export const VERDICT_CONFIG: Record<VerdictType, { label: string; color: string; bgColor: string; icon: string }> = {
  exact: { label: '정확 일치', color: 'text-green-700', bgColor: 'bg-green-100', icon: 'CheckCircle' },
  fuzzy: { label: '유사 일치', color: 'text-yellow-700', bgColor: 'bg-yellow-100', icon: 'AlertTriangle' },
  qty_mismatch: { label: '수량 불일치', color: 'text-orange-700', bgColor: 'bg-orange-100', icon: 'Hash' },
  prefix: { label: '접두어 일치', color: 'text-blue-700', bgColor: 'bg-blue-100', icon: 'Link' },
  synonym: { label: '동의어 일치', color: 'text-purple-700', bgColor: 'bg-purple-100', icon: 'RefreshCw' },
  drawing_only: { label: 'BOM 누락', color: 'text-red-700', bgColor: 'bg-red-100', icon: 'XCircle' },
  bom_only: { label: '도면 누락', color: 'text-red-700', bgColor: 'bg-red-100', icon: 'MinusCircle' },
  manual: { label: '수작업 입력', color: 'text-gray-700', bgColor: 'bg-gray-100', icon: 'Edit3' },
};

export const SEVERITY_CONFIG: Record<SeverityLevel, { label: string; color: string; bgColor: string; border: string }> = {
  OK: { label: '정상', color: 'text-green-700 dark:text-green-400', bgColor: 'bg-green-50 dark:bg-green-900/20', border: 'border-green-200 dark:border-green-800' },
  WARN: { label: '주의', color: 'text-yellow-700 dark:text-yellow-400', bgColor: 'bg-yellow-50 dark:bg-yellow-900/20', border: 'border-yellow-200 dark:border-yellow-800' },
  REVIEW: { label: '검토 필요', color: 'text-orange-700 dark:text-orange-400', bgColor: 'bg-orange-50 dark:bg-orange-900/20', border: 'border-orange-200 dark:border-orange-800' },
  CRITICAL: { label: '심각', color: 'text-red-700 dark:text-red-400', bgColor: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-200 dark:border-red-800' },
};

export const VIEW_NAMES = ['FRONT VIEW', 'TOP VIEW', 'RIGHT VIEW', 'BOTTOM VIEW', 'A VIEW', '3D VIEW'] as const;
