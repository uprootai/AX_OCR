/**
 * BOMConnectionLines - BOM 항목과 도면 요소 연결선 시각화
 *
 * BOM 테이블의 항목과 도면 내 해당 요소 사이의 연결 관계를 시각화합니다.
 * 매칭된 항목은 선으로 연결되고, 미매칭은 별도 표시됩니다.
 *
 * Features:
 * - BOM 항목 → 도면 위치 연결선
 * - 매칭 상태별 색상 (완료/부분/미매칭)
 * - 호버 시 연결 강조
 * - 레이아웃: 좌측 BOM 테이블 + 우측 도면
 */

import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Link2, Unlink } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

// ============ Types ============

export interface BOMConnectionItem {
  /** BOM 항목 ID */
  id: string;
  /** 품번 */
  itemNo: string;
  /** 품명/설명 */
  description: string;
  /** 도면번호 */
  drawingNumber?: string;
  /** 수량 */
  quantity: number;
  /** 도면 내 위치 (백분율) - null이면 미매칭 */
  drawingPosition?: { x: number; y: number } | null;
  /** 매칭 상태 */
  matchStatus: 'matched' | 'partial' | 'unmatched';
}

export interface BOMConnectionLinesProps {
  /** 도면 이미지 URL */
  imageUrl: string;
  /** BOM 항목 목록 */
  items: BOMConnectionItem[];
  /** 제목 */
  title?: string;
  /** 항목 선택 콜백 */
  onItemSelect?: (item: BOMConnectionItem | null) => void;
  /** 선택된 항목 ID */
  selectedItemId?: string | null;
  /** 클래스명 */
  className?: string;
}

// ============ Constants ============

const MATCH_STATUS_COLORS = {
  matched: { line: '#22c55e', bg: '#22c55e20', label: '매칭 완료' },
  partial: { line: '#eab308', bg: '#eab30820', label: '부분 매칭' },
  unmatched: { line: '#ef4444', bg: '#ef444420', label: '미매칭' },
};

// ============ Component ============

export function BOMConnectionLines({
  imageUrl,
  items,
  title = 'BOM 연결 뷰',
  onItemSelect,
  selectedItemId,
  className = '',
}: BOMConnectionLinesProps) {
  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const bomListRef = useRef<HTMLDivElement>(null);
  const imageContainerRef = useRef<HTMLDivElement>(null);

  // State
  const [imageSize, setImageSize] = useState<{ width: number; height: number } | null>(null);
  const [containerSize, setContainerSize] = useState<{ width: number; height: number } | null>(null);
  const [zoom, setZoom] = useState(1);
  const [showLines, setShowLines] = useState(true);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [bomItemPositions, setBomItemPositions] = useState<Record<string, { x: number; y: number }>>({});

  // Handle image load
  const handleImageLoad = useCallback((e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setImageSize({ width: img.naturalWidth, height: img.naturalHeight });
  }, []);

  // Measure container
  useEffect(() => {
    if (!containerRef.current) return;

    const updateSize = () => {
      if (containerRef.current) {
        setContainerSize({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight,
        });
      }
    };

    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(containerRef.current);

    return () => observer.disconnect();
  }, []);

  // Update BOM item positions for connection lines
  useEffect(() => {
    if (!bomListRef.current) return;

    const positions: Record<string, { x: number; y: number }> = {};
    const containerRect = containerRef.current?.getBoundingClientRect();

    if (!containerRect) return;

    items.forEach(item => {
      const el = bomListRef.current?.querySelector(`[data-item-id="${item.id}"]`);
      if (el) {
        const rect = el.getBoundingClientRect();
        positions[item.id] = {
          x: rect.right - containerRect.left,
          y: rect.top + rect.height / 2 - containerRect.top,
        };
      }
    });

    setBomItemPositions(positions);
  }, [items, containerSize]);

  // Zoom controls
  const handleZoomIn = useCallback(() => setZoom(prev => Math.min(prev + 0.25, 3)), []);
  const handleZoomOut = useCallback(() => setZoom(prev => Math.max(prev - 0.25, 0.5)), []);
  const handleZoomReset = useCallback(() => setZoom(1), []);

  // Handle item click
  const handleItemClick = useCallback((item: BOMConnectionItem) => {
    onItemSelect?.(selectedItemId === item.id ? null : item);
  }, [selectedItemId, onItemSelect]);

  // Statistics
  const stats = useMemo(() => ({
    total: items.length,
    matched: items.filter(i => i.matchStatus === 'matched').length,
    partial: items.filter(i => i.matchStatus === 'partial').length,
    unmatched: items.filter(i => i.matchStatus === 'unmatched').length,
  }), [items]);

  // Calculate drawing position in pixels
  const getDrawingPixelPosition = useCallback((pos: { x: number; y: number } | null | undefined): { x: number; y: number } | null => {
    if (!pos || !imageSize || !imageContainerRef.current) return null;

    const containerRect = imageContainerRef.current.getBoundingClientRect();
    const parentRect = containerRef.current?.getBoundingClientRect();
    if (!parentRect) return null;

    const offsetX = containerRect.left - parentRect.left;
    const offsetY = containerRect.top - parentRect.top;

    // Calculate scaled dimensions
    const displayWidth = imageSize.width * zoom;
    const displayHeight = imageSize.height * zoom;

    return {
      x: offsetX + pos.x * displayWidth,
      y: offsetY + pos.y * displayHeight,
    };
  }, [imageSize, zoom]);

  // Render connection lines
  const renderConnectionLines = useMemo(() => {
    if (!showLines || !containerSize) return null;

    return (
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none z-10"
        style={{ width: containerSize.width, height: containerSize.height }}
      >
        <defs>
          <marker
            id="arrowhead-matched"
            markerWidth="6"
            markerHeight="4"
            refX="5"
            refY="2"
            orient="auto"
          >
            <polygon points="0 0, 6 2, 0 4" fill="#22c55e" />
          </marker>
          <marker
            id="arrowhead-partial"
            markerWidth="6"
            markerHeight="4"
            refX="5"
            refY="2"
            orient="auto"
          >
            <polygon points="0 0, 6 2, 0 4" fill="#eab308" />
          </marker>
        </defs>

        {items.map(item => {
          if (item.matchStatus === 'unmatched') return null;

          const bomPos = bomItemPositions[item.id];
          const drawingPos = getDrawingPixelPosition(item.drawingPosition);

          if (!bomPos || !drawingPos) return null;

          const isHighlighted = item.id === selectedItemId || item.id === hoveredId;
          const color = MATCH_STATUS_COLORS[item.matchStatus].line;
          const markerId = `arrowhead-${item.matchStatus}`;

          // Calculate bezier control points for smooth curve
          const midX = (bomPos.x + drawingPos.x) / 2;

          return (
            <g key={item.id}>
              <path
                d={`M ${bomPos.x} ${bomPos.y} C ${midX} ${bomPos.y}, ${midX} ${drawingPos.y}, ${drawingPos.x} ${drawingPos.y}`}
                stroke={color}
                strokeWidth={isHighlighted ? 3 : 1.5}
                strokeOpacity={isHighlighted ? 1 : 0.6}
                fill="none"
                markerEnd={`url(#${markerId})`}
                className="transition-all duration-200"
              />
              {/* Drawing position marker */}
              <circle
                cx={drawingPos.x}
                cy={drawingPos.y}
                r={isHighlighted ? 8 : 5}
                fill={color}
                fillOpacity={0.3}
                stroke={color}
                strokeWidth={2}
              />
            </g>
          );
        })}
      </svg>
    );
  }, [items, bomItemPositions, getDrawingPixelPosition, showLines, containerSize, selectedItemId, hoveredId]);

  return (
    <Card className={`w-full ${className}`}>
      {/* Header */}
      <div className="p-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold">{title}</h3>
            <Badge variant="outline" className="text-xs">
              {stats.total}개 항목
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
              variant={showLines ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setShowLines(!showLines)}
            >
              {showLines ? <Link2 className="w-4 h-4" /> : <Unlink className="w-4 h-4" />}
            </Button>
          </div>
        </div>

        {/* Statistics */}
        <div className="flex gap-2 mt-2">
          {Object.entries(MATCH_STATUS_COLORS).map(([status, config]) => {
            const count = stats[status as keyof typeof stats];
            if (count === 0) return null;
            return (
              <div
                key={status}
                className="flex items-center gap-1 text-xs px-2 py-0.5 rounded"
                style={{
                  backgroundColor: config.bg,
                  borderLeft: `3px solid ${config.line}`,
                }}
              >
                <span>{config.label}</span>
                <span className="font-medium">{count}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main content - split view */}
      <div
        ref={containerRef}
        className="relative flex"
        style={{ height: 500 }}
      >
        {/* BOM List (left side) */}
        <div
          ref={bomListRef}
          className="w-1/3 overflow-auto border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800"
        >
          {items.map(item => {
            const isSelected = item.id === selectedItemId;
            const isHovered = item.id === hoveredId;
            const statusColor = MATCH_STATUS_COLORS[item.matchStatus];

            return (
              <div
                key={item.id}
                data-item-id={item.id}
                className={`p-2 border-b border-gray-200 dark:border-gray-700 cursor-pointer transition-colors ${
                  isSelected ? 'bg-blue-100 dark:bg-blue-900' : isHovered ? 'bg-gray-100 dark:bg-gray-700' : ''
                }`}
                style={{ borderLeftWidth: 3, borderLeftColor: statusColor.line }}
                onClick={() => handleItemClick(item)}
                onMouseEnter={() => setHoveredId(item.id)}
                onMouseLeave={() => setHoveredId(null)}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium">{item.itemNo}</span>
                  <span className="text-xs text-gray-500">x{item.quantity}</span>
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400 truncate">
                  {item.description}
                </div>
                {item.drawingNumber && (
                  <div className="text-xs text-gray-400 truncate">
                    {item.drawingNumber}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Drawing (right side) */}
        <div
          ref={imageContainerRef}
          className="flex-1 overflow-auto bg-gray-100 dark:bg-gray-900"
        >
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
          </div>
        </div>

        {/* Connection lines overlay */}
        {renderConnectionLines}
      </div>

      {/* Selected item detail */}
      {selectedItemId && (
        <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          {(() => {
            const item = items.find(i => i.id === selectedItemId);
            if (!item) return null;

            return (
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <span className="text-gray-500">품번:</span>
                  <span className="ml-1 font-medium">{item.itemNo}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-gray-500">품명:</span>
                  <span className="ml-1">{item.description}</span>
                </div>
                {item.drawingNumber && (
                  <div>
                    <span className="text-gray-500">도면번호:</span>
                    <span className="ml-1">{item.drawingNumber}</span>
                  </div>
                )}
                <div>
                  <span className="text-gray-500">수량:</span>
                  <span className="ml-1">{item.quantity}</span>
                </div>
                <div>
                  <span className="text-gray-500">상태:</span>
                  <span
                    className="ml-1 font-medium"
                    style={{ color: MATCH_STATUS_COLORS[item.matchStatus].line }}
                  >
                    {MATCH_STATUS_COLORS[item.matchStatus].label}
                  </span>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </Card>
  );
}

export default BOMConnectionLines;
