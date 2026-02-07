/**
 * CropRegionPreview - 크롭 영역 미리보기 컴포넌트
 *
 * 이미지 위에 crop_regions 파라미터로 정의된 영역을 시각화합니다.
 * Table Detector, OCR 등 영역 기반 처리 노드에서 사용합니다.
 *
 * Features:
 * - 백분율 기반 좌표 → 픽셀 좌표 변환
 * - 선택된 영역 강조 표시
 * - 영역별 색상 및 라벨
 * - 확대/축소 지원
 */

import { useState, useMemo, useCallback } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Eye, EyeOff } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

// ============ Types ============

export interface CropRegion {
  /** 영역 ID */
  id: string;
  /** 표시 라벨 */
  label: string;
  /** 백분율 좌표 [x1, y1, x2, y2] (0.0 ~ 1.0) */
  bounds: [number, number, number, number];
  /** 영역 색상 */
  color?: string;
  /** 아이콘 (이모지) */
  icon?: string;
  /** 그룹 */
  group?: string;
  /** 설명 */
  description?: string;
}

export interface CropRegionPreviewProps {
  /** 미리보기 이미지 (File, base64, 또는 URL) */
  image: File | string | null;
  /** 사용 가능한 모든 영역 */
  regions: CropRegion[];
  /** 선택된 영역 ID 목록 */
  selectedRegions?: string[];
  /** 영역 선택 변경 콜백 */
  onSelectionChange?: (selectedIds: string[]) => void;
  /** 제목 */
  title?: string;
  /** 최소 높이 */
  minHeight?: number;
  /** 최대 높이 */
  maxHeight?: number;
  /** 클래스명 */
  className?: string;
}

// ============ Predefined Regions ============

/**
 * Table Detector 크롭 영역 (gateway 정의와 동기화)
 */
export const TABLE_DETECTOR_CROP_REGIONS: CropRegion[] = [
  // 도면 영역
  { id: 'title_block', label: '타이틀 블록', bounds: [0.55, 0.65, 1.0, 1.0], color: '#3b82f6', icon: '📋', group: '도면 영역', description: '우하단 타이틀 블록 (55-100% × 65-100%)' },
  { id: 'revision_table', label: '리비전 테이블', bounds: [0.55, 0.0, 1.0, 0.20], color: '#10b981', icon: '📝', group: '도면 영역', description: '우상단 리비전 테이블 (55-100% × 0-20%)' },
  { id: 'parts_list_right', label: 'Parts List (우측)', bounds: [0.60, 0.20, 1.0, 0.65], color: '#f59e0b', icon: '📊', group: '도면 영역', description: '우측 부품표 (60-100% × 20-65%)' },
  // 일반 영역
  { id: 'right_upper', label: '우측 상단', bounds: [0.6, 0.0, 1.0, 0.5], color: '#8b5cf6', icon: '↗', group: '일반 영역', description: '우측 상단 40% × 50%' },
  { id: 'right_lower', label: '우측 하단', bounds: [0.6, 0.5, 1.0, 1.0], color: '#ec4899', icon: '↘', group: '일반 영역', description: '우측 하단 40% × 50%' },
  { id: 'right_full', label: '우측 전체', bounds: [0.6, 0.0, 1.0, 1.0], color: '#06b6d4', icon: '▶', group: '일반 영역', description: '우측 전체 40%' },
  { id: 'left_upper', label: '좌측 상단', bounds: [0.0, 0.0, 0.4, 0.5], color: '#84cc16', icon: '↖', group: '일반 영역', description: '좌측 상단 40% × 50%' },
  { id: 'left_lower', label: '좌측 하단', bounds: [0.0, 0.5, 0.4, 1.0], color: '#f97316', icon: '↙', group: '일반 영역', description: '좌측 하단 40% × 50%' },
  { id: 'upper_half', label: '상단 절반', bounds: [0.0, 0.0, 1.0, 0.5], color: '#14b8a6', icon: '⬆', group: '일반 영역', description: '상단 50%' },
  { id: 'full', label: '전체 페이지', bounds: [0.0, 0.0, 1.0, 1.0], color: '#6b7280', icon: '📄', group: '일반 영역', description: '전체 이미지 (크롭 안함)' },
];

// ============ Component ============

export function CropRegionPreview({
  image,
  regions = TABLE_DETECTOR_CROP_REGIONS,
  selectedRegions = [],
  onSelectionChange,
  title = '크롭 영역 미리보기',
  minHeight = 300,
  maxHeight = 500,
  className = '',
}: CropRegionPreviewProps) {
  // State
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageSize, setImageSize] = useState<{ width: number; height: number } | null>(null);
  const [zoom, setZoom] = useState(1);
  const [showAllRegions, setShowAllRegions] = useState(true);
  const [hoveredRegion, setHoveredRegion] = useState<string | null>(null);

  // Convert image to URL
  useMemo(() => {
    if (!image) {
      setImageUrl(null);
      return;
    }

    if (typeof image === 'string') {
      setImageUrl(image.startsWith('data:') || image.startsWith('http') ? image : `data:image/png;base64,${image}`);
    } else {
      const url = URL.createObjectURL(image);
      setImageUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [image]);

  // Load image size
  const handleImageLoad = useCallback((e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setImageSize({ width: img.naturalWidth, height: img.naturalHeight });
  }, []);

  // Toggle region selection
  const toggleRegion = useCallback((regionId: string) => {
    if (!onSelectionChange) return;

    const newSelection = selectedRegions.includes(regionId)
      ? selectedRegions.filter(id => id !== regionId)
      : [...selectedRegions, regionId];

    onSelectionChange(newSelection);
  }, [selectedRegions, onSelectionChange]);

  // Zoom controls
  const handleZoomIn = useCallback(() => setZoom(prev => Math.min(prev + 0.25, 3)), []);
  const handleZoomOut = useCallback(() => setZoom(prev => Math.max(prev - 0.25, 0.5)), []);
  const handleZoomReset = useCallback(() => setZoom(1), []);

  // Group regions
  const groupedRegions = useMemo(() => {
    const groups: Record<string, CropRegion[]> = {};
    regions.forEach(r => {
      const group = r.group || '기타';
      if (!groups[group]) groups[group] = [];
      groups[group].push(r);
    });
    return groups;
  }, [regions]);

  // Render SVG overlay
  const renderOverlay = useMemo(() => {
    if (!imageSize) return null;

    const displayRegions = showAllRegions ? regions : regions.filter(r => selectedRegions.includes(r.id));

    return (
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
        style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
      >
        {displayRegions.map(region => {
          const [x1, y1, x2, y2] = region.bounds;
          const x = x1 * imageSize.width;
          const y = y1 * imageSize.height;
          const width = (x2 - x1) * imageSize.width;
          const height = (y2 - y1) * imageSize.height;
          const isSelected = selectedRegions.includes(region.id);
          const isHovered = hoveredRegion === region.id;
          const color = region.color || '#3b82f6';

          return (
            <g key={region.id}>
              {/* 영역 사각형 */}
              <rect
                x={x}
                y={y}
                width={width}
                height={height}
                fill={isSelected ? color + '40' : color + '20'}
                stroke={color}
                strokeWidth={isSelected || isHovered ? 3 : 1.5}
                strokeDasharray={isSelected ? 'none' : '5,5'}
                className="pointer-events-auto cursor-pointer"
                onMouseEnter={() => setHoveredRegion(region.id)}
                onMouseLeave={() => setHoveredRegion(null)}
                onClick={() => toggleRegion(region.id)}
              />
              {/* 라벨 */}
              <text
                x={x + 5}
                y={y + 16}
                fill={color}
                fontSize={Math.max(12, 16 / zoom)}
                fontWeight="bold"
                className="pointer-events-none"
              >
                {region.icon} {region.label}
              </text>
              {/* 좌표 표시 (호버 시) */}
              {isHovered && (
                <text
                  x={x + 5}
                  y={y + 32}
                  fill={color}
                  fontSize={Math.max(10, 12 / zoom)}
                  className="pointer-events-none"
                >
                  {`${(x1 * 100).toFixed(0)}%-${(x2 * 100).toFixed(0)}% × ${(y1 * 100).toFixed(0)}%-${(y2 * 100).toFixed(0)}%`}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    );
  }, [imageSize, regions, selectedRegions, showAllRegions, hoveredRegion, zoom, toggleRegion]);

  return (
    <Card className={`w-full ${className}`}>
      {/* Header */}
      <div className="p-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">{title}</h3>
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
              variant={showAllRegions ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setShowAllRegions(!showAllRegions)}
            >
              {showAllRegions ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            </Button>
          </div>
        </div>

        {/* Region selection chips */}
        {onSelectionChange && (
          <div className="flex flex-wrap gap-1 mt-2">
            {Object.entries(groupedRegions).map(([group, groupRegions]) => (
              <div key={group} className="flex items-center gap-1">
                <span className="text-xs text-gray-400">{group}:</span>
                {groupRegions.map(region => (
                  <button
                    key={region.id}
                    onClick={() => toggleRegion(region.id)}
                    className={`text-xs px-2 py-0.5 rounded transition-colors ${
                      selectedRegions.includes(region.id)
                        ? 'text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                    }`}
                    style={{
                      backgroundColor: selectedRegions.includes(region.id) ? region.color : undefined,
                    }}
                    title={region.description}
                  >
                    {region.icon} {region.label}
                  </button>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Image preview */}
      <div
        className="relative overflow-auto bg-gray-100 dark:bg-gray-900"
        style={{ minHeight, maxHeight }}
      >
        {!imageUrl ? (
          <div className="flex items-center justify-center h-full text-gray-400" style={{ height: minHeight }}>
            이미지를 선택하면 크롭 영역이 표시됩니다
          </div>
        ) : (
          <div className="relative inline-block" style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}>
            <img
              src={imageUrl}
              alt="Preview"
              className="max-w-none"
              onLoad={handleImageLoad}
              draggable={false}
            />
            {renderOverlay}
          </div>
        )}
      </div>

      {/* Footer - Selected regions summary */}
      {selectedRegions.length > 0 && (
        <div className="p-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <div className="text-xs text-gray-500">
            선택된 영역: {selectedRegions.map(id => {
              const region = regions.find(r => r.id === id);
              return region ? `${region.icon} ${region.label}` : id;
            }).join(', ')}
          </div>
        </div>
      )}
    </Card>
  );
}

export default CropRegionPreview;
