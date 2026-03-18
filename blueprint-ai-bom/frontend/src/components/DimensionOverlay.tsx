/**
 * DimensionOverlay
 * 원본 도면 위에 치수 bbox를 오버레이하는 읽기 전용 컴포넌트
 * DrawingCanvas 패턴(img + svg overlay) 재사용, 그리기 기능 없음
 */

import { useRef, useEffect, useState, useCallback } from 'react';

type MaterialRole = 'outer_diameter' | 'inner_diameter' | 'length' | 'other' | null;

interface Dimension {
  id: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  value: string;
  modified_value: string | null;
  verification_status: 'pending' | 'approved' | 'rejected' | 'modified' | 'manual';
  material_role?: MaterialRole;
}

interface DimensionOverlayProps {
  imageData: string;
  imageSize: { width: number; height: number };
  dimensions: Dimension[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onImagePopup?: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  pending: '#eab308',
  approved: '#22c55e',
  rejected: '#ef4444',
  modified: '#3b82f6',
  manual: '#a855f7',
};

const ROLE_COLORS: Record<string, { color: string; label: string }> = {
  outer_diameter: { color: '#ef4444', label: 'OD' },
  inner_diameter: { color: '#3b82f6', label: 'ID' },
  length: { color: '#22c55e', label: 'W' },
};

export function DimensionOverlay({
  imageData,
  imageSize,
  dimensions,
  selectedId,
  onSelect,
  onImagePopup,
}: DimensionOverlayProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const selectedRef = useRef<SVGRectElement>(null);
  const [scale, setScale] = useState(1);

  // viewBox → 실제 픽셀 스케일 계산 (strokeWidth, fontSize 보정)
  const measureScale = useCallback(() => {
    if (containerRef.current && imageSize.width > 0) {
      const rendered = containerRef.current.getBoundingClientRect().width;
      setScale(imageSize.width / (rendered || 1));
    }
  }, [imageSize.width]);

  useEffect(() => {
    measureScale();
    window.addEventListener('resize', measureScale);
    return () => window.removeEventListener('resize', measureScale);
  }, [measureScale]);

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

  // 화면 픽셀 단위를 SVG viewBox 단위로 변환
  const px = (pixels: number) => pixels * scale;

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
            style={onImagePopup ? { cursor: 'zoom-in' } : undefined}
            draggable={false}
            onLoad={measureScale}
            onClick={onImagePopup}
            title={onImagePopup ? '클릭하여 새 창에서 확대' : undefined}
          />

          <svg
            className="absolute top-0 left-0 w-full h-full"
            viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
            preserveAspectRatio="none"
            style={{ pointerEvents: 'none' }}
          >
            {dimensions.map((dim) => {
              const isSelected = dim.id === selectedId;
              const roleConfig = dim.material_role ? ROLE_COLORS[dim.material_role] : null;
              const color = roleConfig?.color || STATUS_COLORS[dim.verification_status] || STATUS_COLORS.pending;
              const { x1, y1, x2, y2 } = dim.bbox;
              const w = x2 - x1;
              const h = y2 - y1;
              const label = dim.modified_value || dim.value;
              const roleLabel = roleConfig ? `[${roleConfig.label}] ` : '';

              return (
                <g key={dim.id} style={{ pointerEvents: 'auto', cursor: 'pointer' }}>
                  <rect
                    ref={isSelected ? selectedRef : undefined}
                    x={x1}
                    y={y1}
                    width={w}
                    height={h}
                    fill={color}
                    fillOpacity={isSelected ? 0.35 : roleConfig ? 0.25 : 0.15}
                    stroke={color}
                    strokeWidth={isSelected ? px(3) : roleConfig ? px(2.5) : px(2)}
                    strokeOpacity={isSelected ? 1 : 0.8}
                    strokeDasharray={roleConfig ? undefined : 'none'}
                    rx={px(2)}
                    onClick={() => onSelect(isSelected ? null : dim.id)}
                  />
                  <text
                    x={x1 + w / 2}
                    y={y1 - px(3)}
                    textAnchor="middle"
                    fill={color}
                    fontSize={px(roleConfig ? 13 : 11)}
                    fontWeight={roleConfig ? 'bold' : isSelected ? 'bold' : '600'}
                    stroke="white"
                    strokeWidth={px(0.5)}
                    paintOrder="stroke"
                    style={{ pointerEvents: 'none' }}
                  >
                    {roleLabel}{label}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
    </div>
  );
}
