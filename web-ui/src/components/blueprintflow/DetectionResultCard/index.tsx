/**
 * DetectionResultCard - 검출 결과 + GT 비교 통합 표시 컴포넌트
 *
 * 기능:
 * 1. 검출 결과 요약 (개수, 평균 신뢰도)
 * 2. GT 자동 매칭 및 로드
 * 3. GT 비교 결과 표시 (F1/Precision/Recall)
 * 4. TP/FP/FN 통합 캔버스
 * 5. 필터 토글
 */

import { CheckCircle2, XCircle, AlertTriangle, Eye, EyeOff, Loader2 } from 'lucide-react';
import type { DetectionResultCardProps } from './types';
import { MetricCard } from './MetricCard';
import { FilterCheckbox } from './FilterCheckbox';
import { useDetectionData } from './useDetectionData';

export default function DetectionResultCard({
  nodeStatus,
  uploadedImage,
  uploadedFileName,
}: DetectionResultCardProps) {
  const {
    detections,
    avgConfidence,
    gtLoading,
    compareResult,
    filters,
    setFilters,
    showCanvas,
    setShowCanvas,
    canvasRef,
    containerRef,
  } = useDetectionData(nodeStatus, uploadedImage, uploadedFileName);

  // 검출 결과 없으면 표시하지 않음
  if (detections.length === 0 && !nodeStatus.output) {
    return null;
  }

  return (
    <div className="space-y-3">
      {/* 검출 결과 요약 */}
      <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-lg">🎯</span>
            <span className="font-medium text-blue-700 dark:text-blue-300">
              AI 검출 결과
            </span>
          </div>
          {nodeStatus.elapsedSeconds && (
            <span className="text-xs text-gray-500">
              {nodeStatus.elapsedSeconds.toFixed(1)}s
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-gray-600 dark:text-gray-400">검출:</span>
            <span className="font-bold text-blue-600 dark:text-blue-400">
              {detections.length}개
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-600 dark:text-gray-400">신뢰도:</span>
            <span className="font-bold text-blue-600 dark:text-blue-400">
              {(avgConfidence * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* GT 비교 섹션 (GT가 있는 경우만) */}
      {gtLoading && (
        <div className="flex items-center gap-2 text-xs text-gray-500 p-2">
          <Loader2 className="w-3 h-3 animate-spin" />
          GT 파일 검색 중...
        </div>
      )}

      {compareResult && (
        <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="text-lg">📊</span>
              <span className="font-medium text-purple-700 dark:text-purple-300">
                GT 비교
              </span>
            </div>
            <span className="text-xs text-gray-500">
              {compareResult.gt_count}개 라벨
            </span>
          </div>

          {/* 메트릭 카드 */}
          <div className="grid grid-cols-3 gap-2 mb-3">
            <MetricCard
              label="Precision"
              value={compareResult.metrics.precision}
              color="text-green-600 dark:text-green-400"
            />
            <MetricCard
              label="Recall"
              value={compareResult.metrics.recall}
              color="text-blue-600 dark:text-blue-400"
            />
            <MetricCard
              label="F1"
              value={compareResult.metrics.f1_score}
              color="text-purple-600 dark:text-purple-400"
            />
          </div>

          {/* TP/FP/FN 요약 */}
          <div className="flex items-center justify-center gap-4 text-xs">
            <div className="flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-green-500" />
              <span className="text-green-600 dark:text-green-400 font-medium">
                TP: {compareResult.metrics.tp}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <XCircle className="w-3 h-3 text-red-500" />
              <span className="text-red-600 dark:text-red-400 font-medium">
                FP: {compareResult.metrics.fp}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-yellow-500" />
              <span className="text-yellow-600 dark:text-yellow-400 font-medium">
                FN: {compareResult.metrics.fn}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 필터 & 캔버스 토글 */}
      {(detections.length > 0 || compareResult) && uploadedImage && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              {compareResult && (
                <>
                  <FilterCheckbox
                    label="TP"
                    icon="✅"
                    count={compareResult.metrics.tp}
                    checked={filters.showTP}
                    onChange={(checked) => setFilters((f) => ({ ...f, showTP: checked }))}
                    color="text-green-600 dark:text-green-400"
                  />
                  <FilterCheckbox
                    label="FP"
                    icon="❌"
                    count={compareResult.metrics.fp}
                    checked={filters.showFP}
                    onChange={(checked) => setFilters((f) => ({ ...f, showFP: checked }))}
                    color="text-red-600 dark:text-red-400"
                  />
                  <FilterCheckbox
                    label="FN"
                    icon="⚠️"
                    count={compareResult.metrics.fn}
                    checked={filters.showFN}
                    onChange={(checked) => setFilters((f) => ({ ...f, showFN: checked }))}
                    color="text-yellow-600 dark:text-yellow-400"
                  />
                </>
              )}
            </div>
            <button
              onClick={() => setShowCanvas(!showCanvas)}
              className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              {showCanvas ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
              {showCanvas ? '숨기기' : '보기'}
            </button>
          </div>

          {/* 캔버스 */}
          {showCanvas && (
            <div
              ref={containerRef}
              className="rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-800"
            >
              <canvas
                ref={canvasRef}
                className="w-full h-auto"
                style={{ maxHeight: '300px' }}
              />
            </div>
          )}
        </div>
      )}

      {/* JSON 미리보기 (접기/펼치기) */}
      {nodeStatus.output && (
        <details className="text-xs">
          <summary className="cursor-pointer text-blue-600 dark:text-blue-400 hover:underline">
            JSON 데이터 보기
          </summary>
          <pre className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs overflow-auto max-h-40 border border-gray-200 dark:border-gray-700">
            {JSON.stringify(nodeStatus.output, null, 2).slice(0, 2000)}
            {JSON.stringify(nodeStatus.output).length > 2000 && '...'}
          </pre>
        </details>
      )}
    </div>
  );
}

export type { DetectionResultCardProps };
export { MetricCard, FilterCheckbox, useDetectionData };
export type { MetricCardProps, FilterCheckboxProps } from './types';
