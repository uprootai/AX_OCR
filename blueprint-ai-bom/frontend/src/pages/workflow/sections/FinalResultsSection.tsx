/**
 * Final Results Section
 * 최종 검증 결과 이미지 섹션 컴포넌트
 */

import { useEffect, useRef, useState } from 'react';
import type { Detection } from '../../../types';

interface Dimension {
  id: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  value: string;
  unit: string | null;
  dimension_type: string;
  confidence: number;
  verification_status: string;
  modified_value: string | null;
}

interface DimensionStats {
  pending: number;
  approved: number;
  rejected: number;
  modified: number;
  manual: number;
}

interface FinalResultsSectionProps {
  detections: Detection[];
  imageData: string;
  imageSize: { width: number; height: number };
  stats: {
    approved: number;
    manual: number;
  };
  onImageClick: () => void;
  // BOM ↔ 도면 하이라이트 연동
  selectedClassName?: string | null;
  onClassSelect?: (className: string | null) => void;
  // 치수 전용 워크플로우 지원
  dimensions?: Dimension[];
  dimensionStats?: DimensionStats | null;
}

export function FinalResultsSection({
  detections,
  imageData,
  imageSize,
  stats,
  onImageClick,
  selectedClassName: externalSelectedClassName,
  onClassSelect,
  dimensions = [],
  dimensionStats,
}: FinalResultsSectionProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [internalSelectedClassName, setInternalSelectedClassName] = useState<string | null>(null);

  // 외부 prop 있으면 사용, 없으면 내부 상태 사용
  const selectedClassName = externalSelectedClassName !== undefined ? externalSelectedClassName : internalSelectedClassName;
  const setSelectedClassName = onClassSelect || setInternalSelectedClassName;

  // 치수 전용 모드: 심볼이 없고 치수가 있는 경우
  const isDimensionOnly = detections.length === 0 && dimensions.length > 0;

  const finalDetections = detections.filter(d =>
    d.verification_status === 'approved' ||
    d.verification_status === 'modified' ||
    d.verification_status === 'manual'
  );

  const finalDimensions = dimensions.filter(d =>
    d.verification_status === 'approved' ||
    d.verification_status === 'modified' ||
    d.verification_status === 'manual'
  );

  const modifiedCount = isDimensionOnly
    ? (dimensionStats?.modified || 0)
    : detections.filter(d => d.modified_class_name && d.modified_class_name !== d.class_name).length;

  const manualCount = isDimensionOnly
    ? (dimensionStats?.manual || 0)
    : detections.filter(d => d.verification_status === 'manual').length;

  const approvedCount = isDimensionOnly
    ? (dimensionStats?.approved || 0)
    : stats.approved;

  // Group by class name
  const grouped = finalDetections.reduce((acc, d) => {
    const className = d.modified_class_name || d.class_name;
    if (!acc[className]) {
      acc[className] = { count: 0, items: [] as Detection[] };
    }
    acc[className].count++;
    acc[className].items.push(d);
    return acc;
  }, {} as Record<string, { count: number; items: Detection[] }>);

  const sortedClasses = Object.entries(grouped).sort((a, b) => b[1].count - a[1].count);

  // Draw canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !imageData || !imageSize) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      const maxWidth = 600;
      const scale = Math.min(1, maxWidth / imageSize.width);
      canvas.width = imageSize.width * scale;
      canvas.height = imageSize.height * scale;
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      // 치수 전용 모드: 치수 bbox 그리기
      if (isDimensionOnly) {
        finalDimensions.forEach((dim) => {
          const { x1, y1, x2, y2 } = dim.bbox;
          const sx1 = x1 * scale, sy1 = y1 * scale;
          const w = (x2 - x1) * scale, h = (y2 - y1) * scale;

          let color = '#22c55e';
          if (dim.verification_status === 'modified') color = '#f97316';
          else if (dim.verification_status === 'manual') color = '#a855f7';

          ctx.strokeStyle = color;
          ctx.lineWidth = 2;
          ctx.strokeRect(sx1, sy1, w, h);

          const label = dim.modified_value || dim.value;
          ctx.font = 'bold 10px sans-serif';
          const textWidth = ctx.measureText(label).width;
          ctx.fillStyle = color;
          ctx.fillRect(sx1, sy1 - 14, textWidth + 6, 14);
          ctx.fillStyle = 'white';
          ctx.fillText(label, sx1 + 3, sy1 - 3);
        });
      } else {
        finalDetections.forEach((detection, idx) => {
          const { x1, y1, x2, y2 } = detection.bbox;
          const sx1 = x1 * scale;
          const sy1 = y1 * scale;
          const sx2 = x2 * scale;
          const sy2 = y2 * scale;
          const w = sx2 - sx1;
          const h = sy2 - sy1;

          const detClassName = detection.modified_class_name || detection.class_name;
          const isSelected = selectedClassName === detClassName;

          if (selectedClassName) {
            if (isSelected) {
              ctx.fillStyle = 'rgba(59, 130, 246, 0.3)';
              ctx.fillRect(sx1, sy1, w, h);
              ctx.strokeStyle = '#2563eb';
              ctx.lineWidth = 3;
              ctx.strokeRect(sx1, sy1, w, h);

              const label = `${idx + 1}`;
              ctx.font = 'bold 12px sans-serif';
              const textWidth = ctx.measureText(label).width;
              ctx.fillStyle = '#2563eb';
              ctx.fillRect(sx1, sy1 - 18, textWidth + 8, 18);
              ctx.fillStyle = 'white';
              ctx.fillText(label, sx1 + 4, sy1 - 5);
            } else {
              ctx.strokeStyle = 'rgba(156, 163, 175, 0.4)';
              ctx.lineWidth = 1;
              ctx.strokeRect(sx1, sy1, w, h);
            }
          } else {
            let color = '#22c55e';
            if (detection.modified_class_name && detection.modified_class_name !== detection.class_name) {
              color = '#f97316';
            } else if (detection.verification_status === 'manual') {
              color = '#a855f7';
            }

            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.strokeRect(sx1, sy1, w, h);

            const label = `${idx + 1}`;
            ctx.font = 'bold 12px sans-serif';
            const textWidth = ctx.measureText(label).width;
            ctx.fillStyle = color;
            ctx.fillRect(sx1, sy1 - 18, textWidth + 8, 18);
            ctx.fillStyle = 'white';
            ctx.fillText(label, sx1 + 4, sy1 - 5);
          }
        });
      }
    };
    img.src = imageData;
  }, [imageData, imageSize, finalDetections, finalDimensions, isDimensionOnly, selectedClassName]);

  const handleClassClick = (className: string) => {
    setSelectedClassName(selectedClassName === className ? null : className);
  };

  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">최종 검증 결과 이미지</h2>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center border border-green-200 dark:border-green-800">
          <p className="text-2xl font-bold text-green-600">{approvedCount}</p>
          <p className="text-sm text-gray-500">✅ 승인됨</p>
        </div>
        <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 text-center border border-orange-200 dark:border-orange-800">
          <p className="text-2xl font-bold text-orange-600">{modifiedCount}</p>
          <p className="text-sm text-gray-500">✏️ 수정됨</p>
        </div>
        <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 text-center border border-purple-200 dark:border-purple-800">
          <p className="text-2xl font-bold text-purple-600">{manualCount}</p>
          <p className="text-sm text-gray-500">수작업</p>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mb-4 text-sm">
        {selectedClassName ? (
          <>
            <span className="flex items-center gap-1">
              <span className="w-4 h-4 bg-blue-600 rounded"></span> {selectedClassName}
            </span>
            <button
              onClick={() => setSelectedClassName(null)}
              className="text-xs text-gray-500 hover:text-gray-700 underline"
            >
              선택 해제
            </button>
          </>
        ) : (
          <>
            <span className="flex items-center gap-1">
              <span className="w-4 h-4 bg-green-500 rounded"></span> 승인
            </span>
            <span className="flex items-center gap-1">
              <span className="w-4 h-4 bg-orange-500 rounded"></span> 수정
            </span>
            <span className="flex items-center gap-1">
              <span className="w-4 h-4 bg-purple-500 rounded"></span> 수작업
            </span>
          </>
        )}
      </div>

      {/* 2-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Final Image with Bounding Boxes */}
        <div className="lg:col-span-2">
          <div
            className="relative border rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700 cursor-pointer hover:ring-2 hover:ring-primary-500 transition-all"
            onClick={onImageClick}
            title="클릭하여 확대"
          >
            <canvas ref={canvasRef} className="max-w-full" />
            <div className="absolute bottom-2 right-2 bg-black/50 text-white text-xs px-2 py-1 rounded">
              🔍 클릭하여 확대
            </div>
          </div>
          <p className="text-center text-sm text-gray-500 mt-2">
            {isDimensionOnly
              ? `검증 완료 치수: 총 ${finalDimensions.length}개`
              : `최종 선정된 부품: 총 ${finalDetections.length}개`
            }
          </p>
        </div>

        {/* Right: BOM List */}
        <div className="lg:col-span-1">
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 h-full">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
              {isDimensionOnly ? '치수 유형별 요약' : 'BOM 심볼 리스트'}
            </h3>
            {isDimensionOnly ? (
              <DimensionTypeSummary dimensions={finalDimensions} />
            ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {sortedClasses.map(([className, data], idx) => {
                const isActive = selectedClassName === className;
                return (
                  <div
                    key={className}
                    onClick={() => handleClassClick(className)}
                    className={`flex items-center justify-between p-2 rounded border cursor-pointer transition-all ${
                      isActive
                        ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-400 ring-2 ring-blue-300'
                        : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600 hover:border-blue-300 hover:bg-blue-50/50'
                    }`}
                  >
                    <div className="flex items-center space-x-2 min-w-0">
                      <span className={`w-6 h-6 flex items-center justify-center text-white text-xs rounded-full font-bold shrink-0 ${
                        isActive ? 'bg-blue-600' : 'bg-primary-500'
                      }`}>
                        {idx + 1}
                      </span>
                      <span className={`font-medium text-sm truncate ${
                        isActive ? 'text-blue-700 dark:text-blue-300' : 'text-gray-900 dark:text-white'
                      }`}>{className}</span>
                    </div>
                    <div className="flex items-center space-x-2 shrink-0">
                      <span className={`text-lg font-bold ${isActive ? 'text-blue-600' : 'text-primary-600'}`}>{data.count}</span>
                      <span className="text-xs text-gray-500">개</span>
                    </div>
                  </div>
                );
              })}
            </div>
            )}
            {!isDimensionOnly && (
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-gray-700 dark:text-gray-300">총 품목 수</span>
                <span className="text-xl font-bold text-primary-600">
                  {new Set(finalDetections.map(d => d.modified_class_name || d.class_name)).size}종
                </span>
              </div>
              <div className="flex justify-between items-center mt-1">
                <span className="font-semibold text-gray-700 dark:text-gray-300">총 수량</span>
                <span className="text-xl font-bold text-green-600">
                  {finalDetections.length}개
                </span>
              </div>
            </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

const DIMENSION_TYPE_LABELS: Record<string, string> = {
  length: '길이', diameter: '직경', radius: '반경', angle: '각도',
  tolerance: '공차', surface_finish: '표면', unknown: '기타',
};

function DimensionTypeSummary({ dimensions }: { dimensions: Dimension[] }) {
  const grouped = dimensions.reduce((acc, d) => {
    const type = d.dimension_type || 'unknown';
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const sorted = Object.entries(grouped).sort((a, b) => b[1] - a[1]);

  return (
    <>
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {sorted.map(([type, count]) => (
          <div key={type} className="flex items-center justify-between p-2 rounded border bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-600">
            <span className="font-medium text-sm text-gray-900 dark:text-white">
              {DIMENSION_TYPE_LABELS[type] || type}
            </span>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-bold text-primary-600">{count}</span>
              <span className="text-xs text-gray-500">개</span>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
        <div className="flex justify-between items-center">
          <span className="font-semibold text-gray-700 dark:text-gray-300">총 치수</span>
          <span className="text-xl font-bold text-green-600">{dimensions.length}개</span>
        </div>
      </div>
    </>
  );
}
