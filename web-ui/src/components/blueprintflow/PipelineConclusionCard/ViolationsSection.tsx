import { AlertCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { ConclusionData } from './types';

interface ViolationsSectionProps {
  pidViolations: ConclusionData['pidViolations'];
}

export function ViolationsSection({ pidViolations }: ViolationsSectionProps) {
  const { t } = useTranslation();

  if (pidViolations.length === 0) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-semibold flex items-center gap-2 text-red-600 dark:text-red-400">
        <AlertCircle className="w-4 h-4" />
        {t('blueprintflow.violations', '설계 규칙 위반')} ({pidViolations.length})
      </h4>
      <div className="space-y-1">
        {pidViolations.slice(0, 5).map((v, idx) => (
          <div
            key={idx}
            className="text-xs p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded"
          >
            <span className="font-medium text-red-700 dark:text-red-300">{v.rule}:</span>{' '}
            <span className="text-red-600 dark:text-red-400">{v.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
