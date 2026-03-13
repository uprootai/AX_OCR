import { Layers } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Badge } from '../../ui/Badge';
import type { ConclusionData } from './types';

interface GdtSectionProps {
  gdtSymbols: ConclusionData['gdtSymbols'];
}

export function GdtSection({ gdtSymbols }: GdtSectionProps) {
  const { t } = useTranslation();

  if (gdtSymbols.length === 0) return null;

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-semibold flex items-center gap-2 text-gray-700 dark:text-gray-300">
        <Layers className="w-4 h-4" />
        {t('blueprintflow.gdtSymbols', 'GD&T 기호')}
      </h4>
      <div className="flex flex-wrap gap-2">
        {gdtSymbols.slice(0, 15).map((gdt, idx) => (
          <Badge key={idx} variant="outline" className="px-2 py-1">
            <span className="font-mono">{gdt.symbol}</span>
            {gdt.value && <span className="ml-1">{gdt.value}</span>}
            {gdt.datum && <span className="ml-1 text-gray-500">({gdt.datum})</span>}
          </Badge>
        ))}
        {gdtSymbols.length > 15 && (
          <span className="text-xs text-gray-500 self-center">
            +{gdtSymbols.length - 15} more
          </span>
        )}
      </div>
    </div>
  );
}
