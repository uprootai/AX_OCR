/**
 * GenericOverlayViewer - 제네릭 이미지 오버레이 뷰어
 *
 * PIDOverlayViewer, DetectionViewer 등에서 공통으로 사용할 수 있는 기반 컴포넌트
 *
 * Features:
 * - 이미지 업로드 및 표시
 * - SVG 오버레이 렌더링
 * - 확대/축소/패닝 지원
 * - 호버 툴팁
 * - 레이어 토글 (useLayerToggle 연동)
 * - 다운로드 지원
 */

import { useState, useCallback, useRef, useMemo } from 'react';
import type { ReactNode } from 'react';
import {
  Upload, Loader2, Download,
  ZoomIn, ZoomOut, RotateCcw, Move
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

// ============ Types ============

export interface BBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface OverlayItem {
  id: string | number;
  bbox: BBox;
  label?: string;
  color?: string;
  confidence?: number;
  metadata?: Record<string, unknown>;
}

export interface ImageSize {
  width: number;
  height: number;
}

export interface TooltipData {
  type: string;
  data: unknown;
  position?: { x: number; y: number };
}

export interface GenericOverlayViewerProps {
  /** 제목 */
  title?: string;
  /** 초기 이미지 (base64 또는 URL) */
  initialImage?: string;
  /** 이미지 크기 (SVG viewBox용) */
  imageSize?: ImageSize;
  /** 로딩 상태 */
  isLoading?: boolean;
  /** 에러 메시지 */
  error?: string | null;
  /** 파일 업로드 핸들러 */
  onFileUpload?: (file: File) => void;
  /** 허용되는 파일 형식 (default: "image/*") */
  acceptedFileTypes?: string;
  /** SVG 오버레이 렌더링 함수 */
  renderOverlay?: (props: RenderOverlayProps) => ReactNode;
  /** 툴팁 렌더링 함수 */
  renderTooltip?: (data: TooltipData) => ReactNode;
  /** 다운로드용 이미지 (base64) */
  downloadImage?: string;
  /** 다운로드 파일명 */
  downloadFilename?: string;
  /** 추가 헤더 액션 */
  headerActions?: ReactNode;
  /** 푸터 콘텐츠 */
  footer?: ReactNode;
  /** 최소 높이 (default: 400) */
  minHeight?: number;
  /** 최대 높이 (default: 600) */
  maxHeight?: number;
  /** 업로드 안내 텍스트 */
  uploadPlaceholder?: string;
  /** 업로드 설명 텍스트 */
  uploadDescription?: string;
  /** 클래스명 */
  className?: string;
}

export interface RenderOverlayProps {
  imageSize: ImageSize;
  zoom: number;
  onItemHover: (data: TooltipData | null) => void;
}

// ============ Component ============

export function GenericOverlayViewer({
  title = '이미지 뷰어',
  initialImage,
  imageSize: propImageSize,
  isLoading = false,
  error = null,
  onFileUpload,
  acceptedFileTypes = 'image/*',
  renderOverlay,
  renderTooltip,
  downloadImage,
  downloadFilename = 'image.png',
  headerActions,
  footer,
  minHeight = 400,
  maxHeight = 600,
  uploadPlaceholder = '이미지를 업로드하세요',
  uploadDescription = 'PNG, JPG 지원',
  className = '',
}: GenericOverlayViewerProps) {
  // State
  const [image, setImage] = useState<string | null>(initialImage || null);
  const [zoom, setZoom] = useState(1);
  const [isPanning, setIsPanning] = useState(false);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [hoveredItem, setHoveredItem] = useState<TooltipData | null>(null);

  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const dragStartRef = useRef<{ x: number; y: number; offsetX: number; offsetY: number } | null>(null);

  // Image size
  const imageSize = useMemo<ImageSize>(() => {
    if (propImageSize) return propImageSize;
    return { width: 1000, height: 800 };
  }, [propImageSize]);

  // File upload handler
  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Show preview
    const reader = new FileReader();
    reader.onload = (evt) => {
      if (evt.target?.result) {
        setImage(evt.target.result as string);
      }
    };
    reader.readAsDataURL(file);

    // Callback
    onFileUpload?.(file);
  }, [onFileUpload]);

  // Zoom controls
  const handleZoomIn = useCallback(() => setZoom(prev => Math.min(prev + 0.25, 3)), []);
  const handleZoomOut = useCallback(() => setZoom(prev => Math.max(prev - 0.25, 0.5)), []);
  const handleZoomReset = useCallback(() => {
    setZoom(1);
    setPanOffset({ x: 0, y: 0 });
  }, []);

  // Pan handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (!isPanning) return;
    dragStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      offsetX: panOffset.x,
      offsetY: panOffset.y,
    };
  }, [isPanning, panOffset]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragStartRef.current || !isPanning) return;
    const dx = e.clientX - dragStartRef.current.x;
    const dy = e.clientY - dragStartRef.current.y;
    setPanOffset({
      x: dragStartRef.current.offsetX + dx,
      y: dragStartRef.current.offsetY + dy,
    });
  }, [isPanning]);

  const handleMouseUp = useCallback(() => {
    dragStartRef.current = null;
  }, []);

  // Download handler
  const handleDownload = useCallback(() => {
    if (downloadImage) {
      const link = document.createElement('a');
      link.href = downloadImage.startsWith('data:') ? downloadImage : `data:image/png;base64,${downloadImage}`;
      link.download = downloadFilename;
      link.click();
    }
  }, [downloadImage, downloadFilename]);

  // Hover handler for overlay items
  const handleItemHover = useCallback((data: TooltipData | null) => {
    setHoveredItem(data);
  }, []);

  return (
    <Card className={`w-full ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">{title}</h3>
          <div className="flex items-center gap-2">
            {/* Upload button */}
            {onFileUpload && (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Upload className="w-4 h-4" />
                  )}
                  <span className="ml-1">업로드</span>
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={acceptedFileTypes}
                  className="hidden"
                  onChange={handleFileChange}
                />
              </>
            )}

            {/* Download */}
            {downloadImage && (
              <Button variant="outline" size="sm" onClick={handleDownload}>
                <Download className="w-4 h-4" />
              </Button>
            )}

            {/* Additional header actions */}
            {headerActions}
          </div>
        </div>

        {/* Zoom/Pan controls */}
        {image && (
          <div className="flex items-center gap-1 mt-2">
            <Button variant="ghost" size="sm" onClick={handleZoomOut}>
              <ZoomOut className="w-4 h-4" />
            </Button>
            <span className="text-xs text-gray-500 w-12 text-center">{(zoom * 100).toFixed(0)}%</span>
            <Button variant="ghost" size="sm" onClick={handleZoomIn}>
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={handleZoomReset}>
              <RotateCcw className="w-4 h-4" />
            </Button>
            <Button
              variant={isPanning ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setIsPanning(!isPanning)}
            >
              <Move className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Main content */}
      <div
        ref={containerRef}
        className={`relative overflow-auto bg-gray-100 dark:bg-gray-900 ${isPanning ? 'cursor-grab active:cursor-grabbing' : ''}`}
        style={{ minHeight, maxHeight }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Error display */}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-red-50 dark:bg-red-900/20 z-40">
            <p className="text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* Loading overlay */}
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-gray-900/80 z-50">
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <span className="text-sm text-gray-500">처리 중...</span>
            </div>
          </div>
        )}

        {/* Upload placeholder */}
        {!image && !isLoading && onFileUpload && (
          <div
            className="flex flex-col items-center justify-center cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors"
            style={{ height: minHeight }}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="w-12 h-12 text-gray-400 mb-2" />
            <p className="text-gray-500">{uploadPlaceholder}</p>
            <p className="text-xs text-gray-400 mt-1">{uploadDescription}</p>
          </div>
        )}

        {/* Image with overlay */}
        {image && (
          <div
            className="relative inline-block"
            style={{
              transform: `scale(${zoom}) translate(${panOffset.x / zoom}px, ${panOffset.y / zoom}px)`,
              transformOrigin: 'top left',
            }}
          >
            <img
              src={image}
              alt="Viewer"
              className="max-w-none"
              draggable={false}
            />

            {/* SVG Overlay */}
            {renderOverlay && (
              <svg
                className="absolute inset-0 w-full h-full pointer-events-none"
                viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
              >
                {renderOverlay({ imageSize, zoom, onItemHover: handleItemHover })}
              </svg>
            )}
          </div>
        )}

        {/* Hover tooltip */}
        {hoveredItem && renderTooltip && (
          <div className="absolute bottom-4 left-4 bg-black/80 text-white text-xs p-2 rounded shadow-lg z-50 max-w-xs">
            {renderTooltip(hoveredItem)}
          </div>
        )}
      </div>

      {/* Footer */}
      {footer && (
        <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          {footer}
        </div>
      )}
    </Card>
  );
}

// ============ Helper Components ============

/**
 * 오버레이 아이템을 렌더링하는 헬퍼 컴포넌트
 */
export interface OverlayRectProps {
  item: OverlayItem;
  color?: string;
  fillOpacity?: number;
  strokeWidth?: number;
  showLabel?: boolean;
  labelOffset?: { x: number; y: number };
  onHover?: (data: TooltipData | null) => void;
  hoverType?: string;
}

export function OverlayRect({
  item,
  color = '#3b82f6',
  fillOpacity = 0.1,
  strokeWidth = 2,
  showLabel = false,
  labelOffset = { x: 0, y: -5 },
  onHover,
  hoverType = 'item',
}: OverlayRectProps) {
  return (
    <g>
      <rect
        x={item.bbox.x}
        y={item.bbox.y}
        width={item.bbox.width}
        height={item.bbox.height}
        fill={item.color || color}
        fillOpacity={fillOpacity}
        stroke={item.color || color}
        strokeWidth={strokeWidth}
        className="pointer-events-auto cursor-pointer"
        onMouseEnter={() => onHover?.({ type: hoverType, data: item })}
        onMouseLeave={() => onHover?.(null)}
      />
      {showLabel && item.label && (
        <text
          x={item.bbox.x + labelOffset.x}
          y={item.bbox.y + labelOffset.y}
          fill={item.color || color}
          fontSize={12}
          fontWeight="bold"
        >
          {item.label}
          {item.confidence !== undefined && ` (${(item.confidence * 100).toFixed(0)}%)`}
        </text>
      )}
    </g>
  );
}

export default GenericOverlayViewer;
