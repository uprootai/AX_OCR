/**
 * DimensionOverlay
 * 원본 도면 위에 치수 bbox를 오버레이하는 읽기 전용 컴포넌트
 * DrawingCanvas 패턴(img + svg overlay) 재사용, 그리기 기능 없음
 */

import { useRef, useEffect } from 'react';

interface Dimension {
  id: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  value: string;
  modified_value: string | null;
  verification_status: 'pending' | 'approved' | 'rejected' | 'modified' | 'manual';
}

interface DimensionOverlayProps {
  imageData: string;
  imageSize: { width: number; height: number };
  dimensions: Dimension[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
}

const STATUS_COLORS: Record<string, string> = {
  pending: '#eab308',
  approved: '#22c55e',
  rejected: '#ef4444',
  modified: '#3b82f6',
  manual: '#a855f7',
};

export function DimensionOverlay({
  imageData,
  imageSize,
  dimensions,
  selectedId,
  onSelect,
}: DimensionOverlayProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const selectedRef = useRef<SVGRectElement>(null);

  // 선택된 bbox로 스크롤
  useEffect(() => {
    if (selectedId && selectedRef.current && containerRef.current) {
      const container = containerRef.current;
      const rect = selectedRef.current.getBoundingClientRect();
      const containerRect = container.getBoundingClientRect();
      if (rect.top < containerRect.top || rect.bottom > containerRect.bottom) {
        selectedRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [selectedId]);

  return (
    <div className="mb-4 flex justify-center">
      <div
        ref={containerRef}
        className="relative border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
        style={{ width: '75%' }}
      >
          <img
            src={imageData}
            alt="도면"
            className="w-full"
            draggable={false}
          />

          <svg
            className="absolute top-0 left-0 w-full h-full"
            viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
            preserveAspectRatio="none"
            style={{ pointerEvents: 'none' }}
          >
            {dimensions.map((dim) => {
              const isSelected = dim.id === selectedId;
              const color = STATUS_COLORS[dim.verification_status] || STATUS_COLORS.pending;
              const { x1, y1, x2, y2 } = dim.bbox;
              const w = x2 - x1;
              const h = y2 - y1;
              const label = dim.modified_value || dim.value;

              return (
                <g key={dim.id} style={{ pointerEvents: 'auto', cursor: 'pointer' }}>
                  <rect
                    ref={isSelected ? selectedRef : undefined}
                    x={x1}
                    y={y1}
                    width={w}
                    height={h}
                    fill={color}
                    fillOpacity={isSelected ? 0.25 : 0.1}
                    stroke={color}
                    strokeWidth={isSelected ? 3 : 1.5}
                    strokeOpacity={isSelected ? 1 : 0.7}
                    rx={2}
                    onClick={() => onSelect(isSelected ? null : dim.id)}
                  />
                  <text
                    x={x1 + w / 2}
                    y={y1 - 4}
                    textAnchor="middle"
                    fill={color}
                    fontSize={Math.min(14, Math.max(9, h * 0.4))}
                    fontWeight={isSelected ? 'bold' : 'normal'}
                    style={{ pointerEvents: 'none' }}
                  >
                    {label}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
    </div>
  );
}
