/**
 * QuotationDashboard - 헬퍼 함수 및 소형 컴포넌트
 */

import { COST_SOURCE_STYLES } from './QuotationDashboard.types';

export function formatCurrency(v: number): string {
  return v > 0 ? `₩${v.toLocaleString()}` : '-';
}

export function formatDims(dims: Record<string, number>): string {
  const parts: string[] = [];
  if (dims.od) parts.push(`\u00D8${dims.od}`);
  if (dims.id) parts.push(`\u00F8${dims.id}`);
  if (dims.length) parts.push(`L${dims.length}`);
  return parts.join(' \u00D7 ') || '-';
}

export function CostSourceBadge({ source }: { source: string }) {
  const style = COST_SOURCE_STYLES[source] || COST_SOURCE_STYLES.none;
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${style.className}`}>
      {style.label}
    </span>
  );
}

export function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{label}</p>
      <p className={`text-lg font-bold ${color} truncate`}>{value}</p>
    </div>
  );
}
