/**
 * Line Detection Section
 * 선 검출 결과 섹션 컴포넌트
 */

import { Loader2, Ruler, Check } from 'lucide-react';
import { InfoTooltip } from '../../../components/Tooltip';
import { FEATURE_TOOLTIPS } from '../../../components/tooltipContent';
import { IntegratedOverlay } from '../../../components/IntegratedOverlay';
import type { Detection } from '../../../types';
import type { Dimension, LineData, IntersectionData } from '../types/workflow';

interface Link {
  dimension_id: string;
  symbol_id: string;
  distance?: number;
  confidence?: number;
}

interface LineDetectionSectionProps {
  imageData: string;
  imageSize: { width: number; height: number };
  lines: LineData[];
  intersections: IntersectionData[];
  detections: Detection[];
  dimensions: Dimension[];
  links: Link[];
  showLines: boolean;
  setShowLines: (show: boolean) => void;
  isRunningLineDetection: boolean;
  onRunLineDetection: () => void;
  onLinkDimensionsToSymbols: () => void;
}

export function LineDetectionSection({
  imageData,
  imageSize,
  lines,
  intersections,
  detections,
  dimensions,
  links,
  showLines,
  setShowLines,
  isRunningLineDetection,
  onRunLineDetection,
  onLinkDimensionsToSymbols,
}: LineDetectionSectionProps) {
  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-1">
          📐 선 검출
          <InfoTooltip content={FEATURE_TOOLTIPS.lineDetection.description} position="right" />
          {lines.length > 0 && (
            <span className="text-base font-normal text-gray-500 ml-2">
              ({lines.length}개 선, {intersections.length}개 교차점)
            </span>
          )}
        </h2>
        <div className="flex items-center gap-2">
          {lines.length > 0 && (
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={showLines}
                onChange={(e) => setShowLines(e.target.checked)}
                className="rounded text-primary-600"
              />
              선 표시
            </label>
          )}
          <button
            onClick={onRunLineDetection}
            disabled={isRunningLineDetection}
            className="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 transition-colors"
          >
            {isRunningLineDetection ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>검출 중...</span>
              </>
            ) : (
              <>
                <Ruler className="w-4 h-4" />
                <span>선 검출</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* 선 검출 결과 표시 */}
      {lines.length > 0 ? (
        <div className="space-y-4">
          {/* 이미지 + 선 오버레이 */}
          <div className="relative border rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700" style={{ height: 400 }}>
            <img
              src={imageData}
              alt="Blueprint with lines"
              className="w-full h-full object-contain"
            />
            {showLines && (
              <div className="absolute top-0 left-0 w-full h-full">
                <IntegratedOverlay
                  imageData={imageData}
                  imageSize={imageSize}
                  detections={detections}
                  lines={lines}
                  dimensions={dimensions}
                  intersections={intersections}
                  links={links}
                  maxWidth="100%"
                  maxHeight={400}
                />
              </div>
            )}
          </div>

          {/* 선 유형별 통계 */}
          <div className="grid grid-cols-4 gap-2 text-sm">
            {Object.entries(
              lines.reduce((acc, line) => {
                acc[line.line_type] = (acc[line.line_type] || 0) + 1;
                return acc;
              }, {} as Record<string, number>)
            ).slice(0, 4).map(([type, count]) => (
              <div key={type} className="bg-gray-50 dark:bg-gray-700 rounded p-2 text-center">
                <p className="text-lg font-bold text-gray-900 dark:text-white">{count}</p>
                <p className="text-xs text-gray-500">{type}</p>
              </div>
            ))}
          </div>

          {/* 치수-심볼 연결 버튼 */}
          {dimensions.length > 0 && detections.length > 0 && (
            <button
              onClick={onLinkDimensionsToSymbols}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Check className="w-4 h-4" />
              <span>치수 → 심볼 자동 연결</span>
            </button>
          )}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <Ruler className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p>선 검출을 실행하여 도면의 선을 분석하세요</p>
          <p className="text-sm text-gray-400 mt-1">치수선, 배관, 신호선 등을 자동으로 분류합니다</p>
        </div>
      )}
    </section>
  );
}
