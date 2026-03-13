import { Target } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge } from '../../ui/Badge';

interface DetectionSectionProps {
  groupedDetections: Record<string, { count: number; avgConfidence: number }>;
}

export function DetectionSection({ groupedDetections }: DetectionSectionProps) {
  const { t } = useTranslation();

  if (Object.keys(groupedDetections).length === 0) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-semibold flex items-center gap-2 text-gray-700 dark:text-gray-300">
        <Target className="w-4 h-4" />
        {t('blueprintflow.detectedObjectsList', '검출된 객체 목록')}
      </h4>
      <div className="flex flex-wrap gap-2">
        {Object.entries(groupedDetections).map(([name, data]) => (
          <Badge key={name} variant="outline" className="flex items-center gap-1 px-2 py-1">
            <span className="font-medium">{name}</span>
            <span className="text-xs bg-gray-200 dark:bg-gray-700 px-1.5 rounded">
              {data.count}
            </span>
            <span className="text-xs text-gray-500">
              ({(data.avgConfidence * 100).toFixed(0)}%)
            </span>
          </Badge>
        ))}
      </div>
    </div>
  );
}
