/**
 * Final Results Section
 * 최종 검증 결과 이미지 섹션 컴포넌트
 */

import { useEffect, useRef, useState } from 'react';
import type { Detection } from '../../../types';

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
}

export function FinalResultsSection({
  detections,
  imageData,
  imageSize,
  stats,
  onImageClick,
  selectedClassName: externalSelectedClassName,
  onClassSelect,
}: FinalResultsSectionProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [internalSelectedClassName, setInternalSelectedClassName] = useState<string | null>(null);

  // 외부 prop 있으면 사용, 없으면 내부 상태 사용
  const selectedClassName = externalSelectedClassName !== undefined ? externalSelectedClassName : internalSelectedClassName;
  const setSelectedClassName = onClassSelect || setInternalSelectedClassName;

  const finalDetections = detections.filter(d =>
    d.verification_status === 'approved' ||
    d.verification_status === 'modified' ||
    d.verification_status === 'manual'
  );

  const modifiedCount = detections.filter(d =>
    d.modified_class_name && d.modified_class_name !== d.class_name
  ).length;

  const manualCount = detections.filter(d => d.verification_status === 'manual').length;

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
          // 선택된 클래스가 있을 때
          if (isSelected) {
            // 선택된 항목: 파란색 반투명 채우기 + 굵은 테두리
            ctx.fillStyle = 'rgba(59, 130, 246, 0.3)';
            ctx.fillRect(sx1, sy1, w, h);
            ctx.strokeStyle = '#2563eb';
            ctx.lineWidth = 3;
            ctx.strokeRect(sx1, sy1, w, h);

            // 라벨
            const label = `${idx + 1}`;
            ctx.font = 'bold 12px sans-serif';
            const textWidth = ctx.measureText(label).width;
            ctx.fillStyle = '#2563eb';
            ctx.fillRect(sx1, sy1 - 18, textWidth + 8, 18);
            ctx.fillStyle = 'white';
            ctx.fillText(label, sx1 + 4, sy1 - 5);
          } else {
            // 선택되지 않은 항목: 회색 얇은 테두리
            ctx.strokeStyle = 'rgba(156, 163, 175, 0.4)';
            ctx.lineWidth = 1;
            ctx.strokeRect(sx1, sy1, w, h);
          }
        } else {
          // 선택 없을 때: 기존 상태별 색상
          let color = '#22c55e'; // green - approved
          if (detection.modified_class_name && detection.modified_class_name !== detection.class_name) {
            color = '#f97316'; // orange - modified
          } else if (detection.verification_status === 'manual') {
            color = '#a855f7'; // purple - manual
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
    };
    img.src = imageData;
  }, [imageData, imageSize, finalDetections, selectedClassName]);

  const handleClassClick = (className: string) => {
    setSelectedClassName(selectedClassName === className ? null : className);
  };

  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">최종 검증 결과 이미지</h2>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center border border-green-200 dark:border-green-800">
          <p className="text-2xl font-bold text-green-600">{stats.approved}</p>
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
            최종 선정된 부품: 총 {finalDetections.length}개
          </p>
        </div>

        {/* Right: BOM List */}
        <div className="lg:col-span-1">
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 h-full">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">BOM 심볼 리스트</h3>
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
          </div>
        </div>
      </div>
    </section>
  );
}
