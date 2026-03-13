import { Ruler } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface DimensionsSectionProps {
  groupedDimensions: Record<string, string[]>;
}

export function DimensionsSection({ groupedDimensions }: DimensionsSectionProps) {
  const { t } = useTranslation();

  if (Object.keys(groupedDimensions).length === 0) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-semibold flex items-center gap-2 text-gray-700 dark:text-gray-300">
        <Ruler className="w-4 h-4" />
        {t('blueprintflow.recognizedDimensions', '인식된 치수')}
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {Object.entries(groupedDimensions).map(([type, values]) => (
          <div key={type} className="p-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1 capitalize">
              {type} ({values.length})
            </div>
            <div className="flex flex-wrap gap-1">
              {values.slice(0, 10).map((val, idx) => (
                <span
                  key={idx}
                  className="text-xs px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded"
                >
                  {val}
                </span>
              ))}
              {values.length > 10 && (
                <span className="text-xs text-gray-500">+{values.length - 10} more</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
