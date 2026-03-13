import { Target, Ruler, Layers, Boxes } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { ConclusionData } from './types';

interface SummaryStatsProps {
  conclusion: ConclusionData;
}

export function SummaryStats({ conclusion }: SummaryStatsProps) {
  const { t } = useTranslation();

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {conclusion.totalDetections > 0 && (
        <div className="flex items-center gap-2 p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
          <Target className="w-4 h-4 text-purple-600 dark:text-purple-400" />
          <div>
            <div className="text-xs text-purple-600 dark:text-purple-400">
              {t('blueprintflow.detectedObjects', '검출 객체')}
            </div>
            <div className="text-lg font-bold text-purple-700 dark:text-purple-300">
              {conclusion.totalDetections}
            </div>
          </div>
        </div>
      )}
      {conclusion.totalDimensions > 0 && (
        <div className="flex items-center gap-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <Ruler className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <div>
            <div className="text-xs text-blue-600 dark:text-blue-400">
              {t('blueprintflow.dimensions', '치수')}
            </div>
            <div className="text-lg font-bold text-blue-700 dark:text-blue-300">
              {conclusion.totalDimensions}
            </div>
          </div>
        </div>
      )}
      {conclusion.totalGDT > 0 && (
        <div className="flex items-center gap-2 p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <Layers className="w-4 h-4 text-green-600 dark:text-green-400" />
          <div>
            <div className="text-xs text-green-600 dark:text-green-400">GD&amp;T</div>
            <div className="text-lg font-bold text-green-700 dark:text-green-300">
              {conclusion.totalGDT}
            </div>
          </div>
        </div>
      )}
      {conclusion.pidSymbols.length > 0 && (
        <div className="flex items-center gap-2 p-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
          <Boxes className="w-4 h-4 text-orange-600 dark:text-orange-400" />
          <div>
            <div className="text-xs text-orange-600 dark:text-orange-400">
              {t('blueprintflow.pidSymbols', 'P&ID 심볼')}
            </div>
            <div className="text-lg font-bold text-orange-700 dark:text-orange-300">
              {conclusion.pidSymbols.length}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
