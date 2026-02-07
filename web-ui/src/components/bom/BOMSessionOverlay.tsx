/**
 * BOMSessionOverlay - BOM 세션 치수 오버레이 컴포넌트
 *
 * Blueprint AI BOM 세션의 치수를 도면 이미지 위에 표시합니다.
 * 검증 상태에 따라 색상이 다르게 표시됩니다.
 *
 * Features:
 * - 검증 상태별 색상 (pending/approved/rejected/modified/manual)
 * - 치수 선택 및 상세 정보 표시
 * - 확대/축소 지원
 * - 레이어 토글
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { projectApi } from '../../lib/blueprintBomApi';
import type { SessionDimension, VerificationStatus } from '../../lib/blueprintBomApi';

// ============ Constants ============

const STATUS_COLORS: Record<VerificationStatus, { bg: string; border: string; label: string }> = {
  pending: { bg: '#eab30820', border: '#eab308', label: '대기' },
  approved: { bg: '#22c55e20', border: '#22c55e', label: '승인' },
  rejected: { bg: '#ef444420', border: '#ef4444', label: '거부' },
  modified: { bg: '#3b82f620', border: '#3b82f6', label: '수정' },
  manual: { bg: '#a855f720', border: '#a855f7', label: '수동' },
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

// ============ Types ============

interface BOMSessionOverlayProps {
  sessionId: string;
  title?: string;
  onDimensionSelect?: (dimension: SessionDimension | null) => void;
  selectedDimensionId?: string | null;
  className?: string;
}

// ============ Component ============

export function BOMSessionOverlay({
  sessionId,
  title,
  onDimensionSelect,
  selectedDimensionId,
  className = '',
}: BOMSessionOverlayProps) {
  // State
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageSize, setImageSize] = useState<{ width: number; height: number } | null>(null);
  const [dimensions, setDimensions] = useState<SessionDimension[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [showOverlay, setShowOverlay] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Fetch session details and dimensions in parallel
        const [dims] = await Promise.all([
          projectApi.getSessionDimensions(sessionId),
        ]);

        setDimensions(dims);
        setImageUrl(projectApi.getSessionImageUrl(sessionId));
      } catch (err) {
        setError(err instanceof Error ? err.message : '데이터 로드 실패');
      } finally {
        setIsLoading(false);
      }
    };

    if (sessionId) {
      fetchData();
    }
  }, [sessionId]);

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
  const handleDimensionClick = useCallback((dim: SessionDimension) => {
    onDimensionSelect?.(selectedDimensionId === dim.id ? null : dim);
  }, [selectedDimensionId, onDimensionSelect]);

  // Status summary
  const statusSummary = useMemo(() => {
    const summary: Record<VerificationStatus, number> = {
      pending: 0,
      approved: 0,
      rejected: 0,
      modified: 0,
      manual: 0,
    };
    dimensions.forEach(d => {
      if (d.verification_status in summary) {
        summary[d.verification_status]++;
      }
    });
    return summary;
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
          const statusConfig = STATUS_COLORS[dim.verification_status] || STATUS_COLORS.pending;
          const bbox = dim.modified_bbox || dim.bbox;
          const displayValue = dim.modified_value || dim.value;

          const x = bbox.x1;
          const y = bbox.y1;
          const width = bbox.x2 - bbox.x1;
          const height = bbox.y2 - bbox.y1;

          return (
            <g key={dim.id}>
              {/* Bounding box */}
              <rect
                x={x}
                y={y}
                width={width}
                height={height}
                fill={isSelected || isHovered ? statusConfig.bg : 'transparent'}
                stroke={statusConfig.border}
                strokeWidth={isSelected ? 3 : isHovered ? 2.5 : 2}
                strokeDasharray={dim.verification_status === 'pending' ? '4,2' : undefined}
                className="pointer-events-auto cursor-pointer"
                onMouseEnter={() => setHoveredId(dim.id)}
                onMouseLeave={() => setHoveredId(null)}
                onClick={() => handleDimensionClick(dim)}
              />

              {/* Label */}
              {showLabels && (
                <text
                  x={x}
                  y={y - 4}
                  fill={statusConfig.border}
                  fontSize={Math.max(10, 14 / zoom)}
                  fontWeight="bold"
                  className="pointer-events-none"
                >
                  {displayValue}
                  {dim.tolerance && ` ${dim.tolerance}`}
                </text>
              )}

              {/* Confidence indicator (small dot) */}
              {dim.confidence < 0.7 && (
                <circle
                  cx={x + width - 4}
                  cy={y + 4}
                  r={3}
                  fill="#ef4444"
                  className="pointer-events-none"
                />
              )}
            </g>
          );
        })}
      </svg>
    );
  }, [imageSize, dimensions, selectedDimensionId, hoveredId, showOverlay, showLabels, zoom, handleDimensionClick]);

  // Selected dimension detail
  const selectedDimension = useMemo(() => {
    if (!selectedDimensionId) return null;
    return dimensions.find(d => d.id === selectedDimensionId);
  }, [selectedDimensionId, dimensions]);

  if (isLoading) {
    return (
      <Card className={`w-full ${className}`}>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          <span className="ml-2 text-gray-500">로딩 중...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`w-full ${className}`}>
        <div className="flex items-center justify-center h-64 text-red-500">
          <AlertCircle className="w-6 h-6 mr-2" />
          {error}
        </div>
      </Card>
    );
  }

  return (
    <Card className={`w-full ${className}`}>
      {/* Header */}
      <div className="p-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold">{title || `세션: ${sessionId.slice(0, 8)}...`}</h3>
            <Badge variant="outline" className="text-xs">
              {dimensions.length}개 치수
            </Badge>
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
          </div>
        </div>

        {/* Status summary */}
        <div className="flex flex-wrap gap-2 mt-2">
          {(Object.entries(statusSummary) as [VerificationStatus, number][]).map(([status, count]) => (
            count > 0 && (
              <div
                key={status}
                className="flex items-center gap-1 text-xs px-2 py-0.5 rounded"
                style={{
                  backgroundColor: STATUS_COLORS[status].bg,
                  borderLeft: `3px solid ${STATUS_COLORS[status].border}`,
                }}
              >
                <span>{STATUS_COLORS[status].label}</span>
                <span className="font-medium">{count}</span>
              </div>
            )
          ))}
          <button
            onClick={() => setShowLabels(!showLabels)}
            className={`text-xs px-2 py-0.5 rounded ${showLabels ? 'bg-gray-200 dark:bg-gray-700' : 'text-gray-400'}`}
          >
            라벨 {showLabels ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Image with overlay */}
      <div className="relative overflow-auto bg-gray-100 dark:bg-gray-900" style={{ maxHeight: 500 }}>
        {imageUrl && (
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
        )}
      </div>

      {/* Selected dimension detail */}
      {selectedDimension && (
        <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-500">값:</span>
              <span className="ml-1 font-medium">{selectedDimension.value}</span>
              {selectedDimension.modified_value && (
                <span className="ml-1 text-blue-500">→ {selectedDimension.modified_value}</span>
              )}
            </div>
            <div>
              <span className="text-gray-500">유형:</span>
              <span className="ml-1">{DIMENSION_TYPE_LABELS[selectedDimension.dimension_type] || selectedDimension.dimension_type}</span>
            </div>
            <div>
              <span className="text-gray-500">신뢰도:</span>
              <span className={`ml-1 ${selectedDimension.confidence < 0.7 ? 'text-red-500' : ''}`}>
                {(selectedDimension.confidence * 100).toFixed(1)}%
              </span>
            </div>
            <div>
              <span className="text-gray-500">상태:</span>
              <span
                className="ml-1 font-medium"
                style={{ color: STATUS_COLORS[selectedDimension.verification_status]?.border }}
              >
                {STATUS_COLORS[selectedDimension.verification_status]?.label}
              </span>
            </div>
            {selectedDimension.tolerance && (
              <div className="col-span-2">
                <span className="text-gray-500">공차:</span>
                <span className="ml-1">{selectedDimension.tolerance}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}

export default BOMSessionOverlay;
