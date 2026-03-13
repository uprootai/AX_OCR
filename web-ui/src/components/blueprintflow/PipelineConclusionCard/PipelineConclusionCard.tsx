import { CheckCircle2, ClipboardList } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { useConclusion, useGroupedResults } from './hooks';
import { SummaryStats } from './SummaryStats';
import { DetectionSection } from './DetectionSection';
import { DimensionsSection } from './DimensionsSection';
import { GdtSection } from './GdtSection';
import { PidSection } from './PidSection';
import { ViolationsSection } from './ViolationsSection';
import type { PipelineConclusionCardProps } from './types';

export default function PipelineConclusionCard({
  executionResult,
  nodes,
}: PipelineConclusionCardProps) {
  const { t } = useTranslation();
  const conclusion = useConclusion(executionResult, nodes);
  const { groupedDetections, groupedDimensions } = useGroupedResults(conclusion);

  const hasData =
    conclusion.totalDetections > 0 ||
    conclusion.totalDimensions > 0 ||
    conclusion.totalGDT > 0 ||
    conclusion.pidSymbols.length > 0 ||
    conclusion.bomItems.length > 0;

  if (!hasData) return null;

  return (
    <Card className="mt-4 border-2 border-blue-200 dark:border-blue-800">
      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b pb-3">
          <div className="flex items-center gap-2">
            <ClipboardList className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {t('blueprintflow.conclusion', '분석 결론')}
            </h3>
          </div>
          <Badge variant="default" className="bg-blue-600">
            {t('blueprintflow.analysisComplete', '분석 완료')}
          </Badge>
        </div>

        <SummaryStats conclusion={conclusion} />
        <DetectionSection groupedDetections={groupedDetections} />
        <DimensionsSection groupedDimensions={groupedDimensions} />
        <GdtSection gdtSymbols={conclusion.gdtSymbols} />
        <PidSection
          pidSymbols={conclusion.pidSymbols}
          pidConnections={conclusion.pidConnections}
          bomItems={conclusion.bomItems}
        />
        <ViolationsSection pidViolations={conclusion.pidViolations} />

        {/* Overall Status */}
        <div className="pt-3 border-t flex items-center justify-between">
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-medium">
              {t('blueprintflow.analysisSuccessful', '분석이 성공적으로 완료되었습니다')}
            </span>
          </div>
          <div className="text-sm text-gray-500">
            {executionResult.execution_time_ms && (
              <span>
                {t('blueprintflow.totalTime', '총 소요 시간')}:{' '}
                {(executionResult.execution_time_ms / 1000).toFixed(2)}s
              </span>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
