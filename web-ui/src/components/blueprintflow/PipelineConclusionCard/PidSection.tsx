import { Boxes } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { ConclusionData } from './types';

interface PidSectionProps {
  pidSymbols: ConclusionData['pidSymbols'];
  pidConnections: number;
  bomItems: ConclusionData['bomItems'];
}

export function PidSection({ pidSymbols, pidConnections, bomItems }: PidSectionProps) {
  const { t } = useTranslation();

  if (pidSymbols.length === 0 && bomItems.length === 0) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-semibold flex items-center gap-2 text-gray-700 dark:text-gray-300">
        <Boxes className="w-4 h-4" />
        {t('blueprintflow.pidAnalysis', 'P&ID 분석 결과')}
      </h4>

      {pidSymbols.length > 0 && (
        <div className="p-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
          <div className="text-xs font-medium text-orange-600 dark:text-orange-400 mb-1">
            {t('blueprintflow.detectedSymbols', '검출된 심볼')}
          </div>
          <div className="flex flex-wrap gap-1">
            {pidSymbols.slice(0, 20).map((sym, idx) => (
              <span
                key={idx}
                className="text-xs px-1.5 py-0.5 bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300 rounded"
              >
                {sym.name} ({(sym.confidence * 100).toFixed(0)}%)
              </span>
            ))}
            {pidSymbols.length > 20 && (
              <span className="text-xs text-gray-500">+{pidSymbols.length - 20} more</span>
            )}
          </div>
        </div>
      )}

      {bomItems.length > 0 && (
        <div className="p-2 bg-teal-50 dark:bg-teal-900/20 rounded-lg">
          <div className="text-xs font-medium text-teal-600 dark:text-teal-400 mb-1">
            {t('blueprintflow.bomItems', 'BOM 항목')}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-1">
            {bomItems.slice(0, 12).map((item, idx) => (
              <div
                key={idx}
                className="text-xs flex justify-between px-2 py-1 bg-teal-100 dark:bg-teal-900 rounded"
              >
                <span>{item.item}</span>
                <span className="font-bold">x{item.quantity}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {pidConnections > 0 && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {t('blueprintflow.connectionsFound', '연결 감지')}: {pidConnections}
        </div>
      )}
    </div>
  );
}
