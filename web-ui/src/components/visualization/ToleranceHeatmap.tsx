/**
 * ToleranceHeatmap - 공차 히트맵 시각화 컴포넌트
 *
 * 도면의 치수별 공차 엄격도를 색상으로 표시합니다.
 * 빨강(엄격) → 노랑(중간) → 초록(관대)
 *
 * Features:
 * - 공차 등급별 색상 매핑
 * - 클릭 시 상세 정보 표시
 * - 범례 및 통계
 * - 확대/축소 지원
 */

import { useState, useMemo, useCallback } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Eye, EyeOff, Info } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

// ============ Types ============

export interface ToleranceDimension {
  id: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  value: string;
  tolerance: string | null;
  toleranceGrade: ToleranceGrade;
  dimension_type: string;
}

export type ToleranceGrade = 'IT5' | 'IT6' | 'IT7' | 'IT8' | 'IT9' | 'IT10' | 'IT11' | 'IT12' | 'none';

export interface ToleranceHeatmapProps {
  imageUrl: string;
  dimensions: ToleranceDimension[];
  title?: string;
  onDimensionSelect?: (dimension: ToleranceDimension | null) => void;
  selectedDimensionId?: string | null;
  className?: string;
}

// ============ Constants ============

const TOLERANCE_COLORS: Record<ToleranceGrade, { bg: string; border: string; label: string; severity: number }> = {
  IT5: { bg: '#dc262620', border: '#dc2626', label: 'IT5 (정밀)', severity: 5 },
  IT6: { bg: '#ea580c20', border: '#ea580c', label: 'IT6 (고정밀)', severity: 4 },
  IT7: { bg: '#f9731620', border: '#f97316', label: 'IT7 (표준)', severity: 3 },
  IT8: { bg: '#eab30820', border: '#eab308', label: 'IT8 (일반)', severity: 2 },
  IT9: { bg: '#84cc1620', border: '#84cc16', label: 'IT9 (거친)', severity: 1 },
  IT10: { bg: '#22c55e20', border: '#22c55e', label: 'IT10 (조립)', severity: 0 },
  IT11: { bg: '#10b98120', border: '#10b981', label: 'IT11 (자유)', severity: 0 },
  IT12: { bg: '#06b6d420', border: '#06b6d4', label: 'IT12 (매우 관대)', severity: 0 },
  none: { bg: '#6b728020', border: '#6b7280', label: '공차 없음', severity: -1 },
};

const DIMENSION_TYPE_LABELS: Record<string, string> = {
  linear: '선형',
  diameter: '직경',
  radius: '반경',
  angular: '각도',
  chamfer: '모따기',
  thread: '나사',
  unknown: '기타',
};

// ============ Helper Functions ============

/**
 * 공차 문자열에서 IT 등급 추출
 */
export function parseToleranceGrade(tolerance: string | null): ToleranceGrade {
  if (!tolerance) return 'none';

  const normalized = tolerance.toUpperCase().replace(/\s/g, '');

  // IT 등급 직접 매칭
  const itMatch = normalized.match(/IT(\d+)/);
  if (itMatch) {
    const grade = parseInt(itMatch[1], 10);
    if (grade >= 5 && grade <= 12) return `IT${grade}` as ToleranceGrade;
  }

  // H7, h6 같은 끼워맞춤 공차에서 등급 추론
  const fitMatch = normalized.match(/[A-Z](\d+)/i);
  if (fitMatch) {
    const grade = parseInt(fitMatch[1], 10);
    if (grade >= 5 && grade <= 12) return `IT${grade}` as ToleranceGrade;
  }

  // ±0.01 같은 숫자 공차에서 등급 추정
  const numMatch = tolerance.match(/[±+\-]?\s*(\d+\.?\d*)/);
  if (numMatch) {
    const val = parseFloat(numMatch[1]);
    if (val <= 0.01) return 'IT6';
    if (val <= 0.02) return 'IT7';
    if (val <= 0.05) return 'IT8';
    if (val <= 0.1) return 'IT9';
    if (val <= 0.2) return 'IT10';
    return 'IT11';
  }

  return 'none';
}

// ============ Component ============

export function ToleranceHeatmap({
  imageUrl,
  dimensions,
  title = '공차 히트맵',
  onDimensionSelect,
  selectedDimensionId,
  className = '',
}: ToleranceHeatmapProps) {
  // State
  const [imageSize, setImageSize] = useState<{ width: number; height: number } | null>(null);
  const [zoom, setZoom] = useState(1);
  const [showOverlay, setShowOverlay] = useState(true);
  const [showLegend, setShowLegend] = useState(true);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  // Handle image load
  const handleImageLoad = useCallback((e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setImageSize({ width: img.naturalWidth, height: img.naturalHeight });
  }, []);

  // Zoom controls
  const handleZoomIn = useCallback(() => setZoom(prev => Math.min(prev + 0.25, 3)), []);
  const handleZoomOut = useCallback(() => setZoom(prev => Math.max(prev - 0.25, 0.5)), []);
  const handleZoomReset = useCallback(() => setZoom(1), []);

  // Handle dimension click
  const handleDimensionClick = useCallback((dim: ToleranceDimension) => {
    onDimensionSelect?.(selectedDimensionId === dim.id ? null : dim);
  }, [selectedDimensionId, onDimensionSelect]);

  // Statistics
  const stats = useMemo(() => {
    const gradeCounts: Record<ToleranceGrade, number> = {
      IT5: 0, IT6: 0, IT7: 0, IT8: 0, IT9: 0, IT10: 0, IT11: 0, IT12: 0, none: 0,
    };
    dimensions.forEach(d => gradeCounts[d.toleranceGrade]++);

    const withTolerance = dimensions.filter(d => d.toleranceGrade !== 'none').length;
    const avgSeverity = withTolerance > 0
      ? dimensions.reduce((sum, d) => sum + (TOLERANCE_COLORS[d.toleranceGrade]?.severity || 0), 0) / withTolerance
      : 0;

    return { gradeCounts, withTolerance, avgSeverity };
  }, [dimensions]);

  // Render SVG overlay
  const renderOverlay = useMemo(() => {
    if (!imageSize || !showOverlay) return null;

    return (
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
        style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
      >
        {dimensions.map((dim) => {
          const isSelected = dim.id === selectedDimensionId;
          const isHovered = dim.id === hoveredId;
          const colorConfig = TOLERANCE_COLORS[dim.toleranceGrade] || TOLERANCE_COLORS.none;
          const { x1, y1, x2, y2 } = dim.bbox;
          const width = x2 - x1;
          const height = y2 - y1;

          return (
            <g key={dim.id}>
              {/* Heat rect */}
              <rect
                x={x1}
                y={y1}
                width={width}
                height={height}
                fill={isSelected || isHovered ? colorConfig.bg.replace('20', '60') : colorConfig.bg}
                stroke={colorConfig.border}
                strokeWidth={isSelected ? 3 : isHovered ? 2.5 : 1.5}
                className="pointer-events-auto cursor-pointer"
                onMouseEnter={() => setHoveredId(dim.id)}
                onMouseLeave={() => setHoveredId(null)}
                onClick={() => handleDimensionClick(dim)}
              />
              {/* Value label */}
              {(isHovered || isSelected) && (
                <text
                  x={x1}
                  y={y1 - 4}
                  fill={colorConfig.border}
                  fontSize={Math.max(10, 14 / zoom)}
                  fontWeight="bold"
                  className="pointer-events-none"
                >
                  {dim.value} {dim.tolerance || ''}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    );
  }, [imageSize, dimensions, selectedDimensionId, hoveredId, showOverlay, zoom, handleDimensionClick]);

  // Selected dimension detail
  const selectedDimension = useMemo(() => {
    if (!selectedDimensionId) return null;
    return dimensions.find(d => d.id === selectedDimensionId);
  }, [selectedDimensionId, dimensions]);

  return (
    <Card className={`w-full ${className}`}>
      {/* Header */}
      <div className="p-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold">{title}</h3>
            <Badge variant="outline" className="text-xs">
              {dimensions.length}개 치수
            </Badge>
            {stats.withTolerance > 0 && (
              <Badge variant="secondary" className="text-xs">
                평균 엄격도: {stats.avgSeverity.toFixed(1)}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" onClick={handleZoomOut}>
              <ZoomOut className="w-4 h-4" />
            </Button>
            <span className="text-xs text-gray-500 w-10 text-center">{(zoom * 100).toFixed(0)}%</span>
            <Button variant="ghost" size="sm" onClick={handleZoomIn}>
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={handleZoomReset}>
              <RotateCcw className="w-4 h-4" />
            </Button>
            <Button
              variant={showOverlay ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setShowOverlay(!showOverlay)}
            >
              {showOverlay ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            </Button>
            <Button
              variant={showLegend ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setShowLegend(!showLegend)}
            >
              <Info className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Legend */}
        {showLegend && (
          <div className="flex flex-wrap gap-2 mt-2">
            {(Object.entries(stats.gradeCounts) as [ToleranceGrade, number][])
              .filter(([, count]) => count > 0)
              .sort((a, b) => (TOLERANCE_COLORS[b[0]]?.severity || 0) - (TOLERANCE_COLORS[a[0]]?.severity || 0))
              .map(([grade, count]) => (
                <div
                  key={grade}
                  className="flex items-center gap-1 text-xs px-2 py-0.5 rounded"
                  style={{
                    backgroundColor: TOLERANCE_COLORS[grade].bg,
                    borderLeft: `3px solid ${TOLERANCE_COLORS[grade].border}`,
                  }}
                >
                  <span>{TOLERANCE_COLORS[grade].label}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
          </div>
        )}
      </div>

      {/* Image with overlay */}
      <div className="relative overflow-auto bg-gray-100 dark:bg-gray-900" style={{ maxHeight: 500 }}>
        <div
          className="relative inline-block"
          style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
        >
          <img
            src={imageUrl}
            alt="도면"
            className="max-w-none"
            onLoad={handleImageLoad}
            draggable={false}
          />
          {renderOverlay}
        </div>
      </div>

      {/* Selected dimension detail */}
      {selectedDimension && (
        <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-500">값:</span>
              <span className="ml-1 font-medium">{selectedDimension.value}</span>
            </div>
            <div>
              <span className="text-gray-500">유형:</span>
              <span className="ml-1">{DIMENSION_TYPE_LABELS[selectedDimension.dimension_type] || selectedDimension.dimension_type}</span>
            </div>
            <div>
              <span className="text-gray-500">공차:</span>
              <span className="ml-1">{selectedDimension.tolerance || '없음'}</span>
            </div>
            <div>
              <span className="text-gray-500">등급:</span>
              <span
                className="ml-1 font-medium"
                style={{ color: TOLERANCE_COLORS[selectedDimension.toleranceGrade]?.border }}
              >
                {TOLERANCE_COLORS[selectedDimension.toleranceGrade]?.label}
              </span>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

export default ToleranceHeatmap;
