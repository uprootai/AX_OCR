import type { MetricCardProps } from './types';

export const MetricCard = ({ label, value, color }: MetricCardProps) => (
  <div className="text-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
    <div className={`text-lg font-bold ${color}`}>
      {(value * 100).toFixed(1)}%
    </div>
    <div className="text-[10px] text-gray-500 dark:text-gray-400">{label}</div>
  </div>
);
