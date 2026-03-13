/**
 * QuotationDashboard - 견적 현황 대시보드
 * Phase 3: BOM 항목 + 견적 집계 통합 표시
 *
 * web-ui 네이티브 구현 (다크모드 지원)
 */

import {
  BarChart3,
  Download,
  FileSpreadsheet,
  FileText,
  Loader2,
  Play,
  RefreshCw,
  Square,
} from 'lucide-react';
import {
  projectApi,
  type BOMItem,
  type ProjectDetail,
} from '../../../lib/blueprintBomApi';
import { MaterialBreakdown } from './MaterialBreakdown';
import { AssemblyBreakdown } from './AssemblyBreakdown';
import { useQuotationData } from './QuotationDashboard.hooks';
import { StatCard, formatCurrency } from './QuotationDashboard.helpers';
import { QuotationTable } from './QuotationDashboard.table';

interface QuotationDashboardProps {
  projectId: string;
  project: ProjectDetail;
  bomItems: BOMItem[];
}

export function QuotationDashboard({
  projectId,
  project,
  bomItems,
}: QuotationDashboardProps) {
  const {
    quotation,
    isAggregating,
    batchStatus,
    itemsWithSession,
    stats,
    loadQuotation,
    startBatch,
    cancelBatch,
  } = useQuotationData(projectId, project, bomItems);

  return (
    <div className="space-y-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {/* 헤더 */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-gray-400 dark:text-gray-500" />
            <h3 className="font-semibold text-gray-900 dark:text-white">견적 현황</h3>
          </div>
          <div className="flex items-center gap-2">
            {batchStatus?.status === 'running' ? (
              <button
                onClick={cancelBatch}
                className="flex items-center gap-1 px-3 py-1.5 text-xs bg-red-500 dark:bg-red-600 text-white rounded-lg hover:bg-red-600 dark:hover:bg-red-700 transition-colors"
              >
                <Square className="w-3.5 h-3.5" />
                분석 중단 ({batchStatus.completed + batchStatus.skipped + batchStatus.failed}/{batchStatus.total})
              </button>
            ) : (
              <button
                onClick={() => startBatch()}
                className="flex items-center gap-1 px-3 py-1.5 text-xs bg-green-500 dark:bg-green-600 text-white rounded-lg hover:bg-green-600 dark:hover:bg-green-700 transition-colors"
              >
                <Play className="w-3.5 h-3.5" />
                전체 분석
              </button>
            )}
            <button
              onClick={() => loadQuotation(true)}
              disabled={isAggregating}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-blue-500 dark:bg-blue-600 text-white rounded-lg hover:bg-blue-600 dark:hover:bg-blue-700 transition-colors disabled:opacity-50"
              title="견적 집계"
            >
              {isAggregating ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <RefreshCw className="w-3.5 h-3.5" />
              )}
              견적 집계
            </button>
            {quotation && (
              <>
                <a
                  href={projectApi.getQuotationDownloadUrl(projectId, 'pdf')}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  download
                >
                  <Download className="w-3.5 h-3.5" />
                  PDF
                </a>
                <a
                  href={projectApi.getQuotationDownloadUrl(projectId, 'excel')}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  download
                >
                  <FileSpreadsheet className="w-3.5 h-3.5" />
                  Excel
                </a>
              </>
            )}
          </div>
        </div>

        {/* 통계 카드 */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-3 gap-3 mb-3">
            <StatCard label="견적대상" value={`${stats.total}개`} color="text-gray-900 dark:text-white" />
            <StatCard label="분석완료" value={`${stats.completed}개`} color="text-green-600 dark:text-green-400" />
            <StatCard
              label="합계 (VAT포함)"
              value={formatCurrency(stats.grandTotal)}
              color="text-purple-600 dark:text-purple-400"
            />
          </div>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <StatCard
              label="총 재료비"
              value={formatCurrency(stats.totalMaterialCost)}
              color="text-blue-600 dark:text-blue-400"
            />
            <StatCard
              label="총 가공비"
              value={formatCurrency(stats.totalMachiningCost)}
              color="text-orange-600 dark:text-orange-400"
            />
            <StatCard
              label="소계"
              value={formatCurrency(stats.subtotal)}
              color="text-gray-700 dark:text-gray-300"
            />
          </div>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 dark:bg-green-400 transition-all"
                style={{ width: `${stats.progress}%` }}
              />
            </div>
            <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
              {stats.progress}%
            </span>
          </div>
          {batchStatus?.status === 'running' && (
            <div className="mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex items-center justify-between text-xs text-blue-700 dark:text-blue-300 mb-1">
                <span className="flex items-center gap-1">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  AI 분석 중: {batchStatus.current_drawing || '...'}
                </span>
                <span>{batchStatus.completed + batchStatus.skipped + batchStatus.failed}/{batchStatus.total}</span>
              </div>
              <div className="h-1.5 bg-blue-100 dark:bg-blue-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 dark:bg-blue-400 transition-all"
                  style={{ width: `${batchStatus.total > 0 ? ((batchStatus.completed + batchStatus.skipped + batchStatus.failed) / batchStatus.total * 100) : 0}%` }}
                />
              </div>
              {batchStatus.failed > 0 && (
                <p className="text-xs text-red-500 dark:text-red-400 mt-1">실패: {batchStatus.failed}개</p>
              )}
            </div>
          )}
          {batchStatus?.status === 'completed' && batchStatus.completed > 0 && (
            <p className="mt-2 text-xs text-green-600 dark:text-green-400">
              배치 분석 완료: {batchStatus.completed}개 성공, {batchStatus.skipped}개 스킵, {batchStatus.failed}개 실패
            </p>
          )}
        </div>

        {/* 견적 데이터가 없을 때 안내, 있을 때 테이블 */}
        {stats.grandTotal === 0 && stats.completed === 0 ? (
          <div className="px-4 py-8 text-center border-t border-gray-200 dark:border-gray-700">
            <FileText className="w-10 h-10 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
            <p className="text-gray-500 dark:text-gray-400 font-medium mb-1">
              아직 분석된 견적 항목이 없습니다.
            </p>
            <p className="text-sm text-gray-400 dark:text-gray-500">
              위의 "전체 분석" 버튼을 클릭하면 {stats.total}개 항목의 견적을 자동 산출합니다.
            </p>
          </div>
        ) : (
          <QuotationTable itemsWithSession={itemsWithSession} />
        )}
      </div>

      {/* 어셈블리별 견적 */}
      {quotation && quotation.assembly_groups?.length > 0 && (
        <AssemblyBreakdown
          groups={quotation.assembly_groups}
          onStartBatch={(dwg) => startBatch(dwg)}
          isBatchRunning={batchStatus?.status === 'running'}
        />
      )}

      {/* 재질별 분류 */}
      {quotation && quotation.material_groups.length > 0 && (
        <MaterialBreakdown groups={quotation.material_groups} />
      )}
    </div>
  );
}
