/**
 * ZoomableImage — 확대/축소/전체화면 기능이 있는 이미지 컴포넌트
 * 모든 도면/크롭/OCR 오버레이 이미지에 공통으로 사용
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, Maximize2, RotateCcw, Move } from 'lucide-react';

interface ZoomableImageProps {
  src: string;
  alt: string;
  initialZoom?: number;    // 초기 줌 % (기본 100)
  minZoom?: number;        // 최소 줌 % (기본 10)
  maxZoom?: number;        // 최대 줌 % (기본 300)
  zoomStep?: number;       // 줌 단계 % (기본 20)
  className?: string;      // 컨테이너 className
  showControls?: boolean;  // 컨트롤 표시 여부 (기본 true)
  compact?: boolean;       // 컴팩트 모드 (작은 컨트롤)
  onFullscreen?: () => void; // 전체화면 콜백 (없으면 새 탭)
}

export function ZoomableImage({
  src, alt,
  initialZoom = 100,
  minZoom = 10, maxZoom = 300, zoomStep = 20,
  className = '',
  showControls = true,
  compact = false,
  onFullscreen,
}: ZoomableImageProps) {
  const [zoom, setZoom] = useState(initialZoom);
  const [dragging, setDragging] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  const zoomIn = useCallback(() => setZoom(z => Math.min(maxZoom, z + zoomStep)), [maxZoom, zoomStep]);
  const zoomOut = useCallback(() => setZoom(z => Math.max(minZoom, z - zoomStep)), [minZoom, zoomStep]);
  const resetZoom = useCallback(() => { setZoom(initialZoom); setPosition({ x: 0, y: 0 }); }, [initialZoom]);

  const handleFullscreen = useCallback(() => {
    if (onFullscreen) {
      onFullscreen();
    } else {
      window.open(src, '_blank');
    }
  }, [src, onFullscreen]);

  // 마우스 휠 줌
  const handleWheel = useCallback((e: React.WheelEvent) => {
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      if (e.deltaY < 0) zoomIn();
      else zoomOut();
    }
  }, [zoomIn, zoomOut]);

  // 드래그 이동 (줌 > 100% 시)
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (zoom > 100) {
      setDragging(true);
      setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
    }
  }, [zoom, position]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (dragging) {
      setPosition({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  }, [dragging, dragStart]);

  const handleMouseUp = useCallback(() => setDragging(false), []);

  useEffect(() => {
    if (dragging) {
      const up = () => setDragging(false);
      window.addEventListener('mouseup', up);
      return () => window.removeEventListener('mouseup', up);
    }
  }, [dragging]);

  const btnSize = compact ? 'w-6 h-6 text-xs' : 'w-7 h-7 text-sm';
  const iconSize = compact ? 'w-3 h-3' : 'w-3.5 h-3.5';
  const btnClass = `${btnSize} flex items-center justify-center rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 transition-colors`;

  return (
    <div className={`relative group ${className}`}>
      {/* 컨트롤 바 */}
      {showControls && (
        <div className={`absolute top-2 right-2 z-10 flex items-center gap-1 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-lg px-1.5 py-1 shadow-sm border border-gray-200 dark:border-gray-700 opacity-0 group-hover:opacity-100 transition-opacity ${compact ? 'scale-90' : ''}`}>
          <button onClick={zoomOut} className={btnClass} title="축소">
            <ZoomOut className={iconSize} />
          </button>
          <span className="text-xs text-gray-500 w-8 text-center font-mono">{zoom}%</span>
          <button onClick={zoomIn} className={btnClass} title="확대">
            <ZoomIn className={iconSize} />
          </button>
          <div className="w-px h-4 bg-gray-300 dark:bg-gray-600 mx-0.5" />
          <button onClick={resetZoom} className={btnClass} title="원래 크기">
            <RotateCcw className={iconSize} />
          </button>
          <button onClick={handleFullscreen} className={btnClass} title="전체화면">
            <Maximize2 className={iconSize} />
          </button>
        </div>
      )}

      {/* 이미지 컨테이너 */}
      <div
        ref={containerRef}
        className="overflow-auto rounded-lg"
        style={{ cursor: zoom > 100 ? (dragging ? 'grabbing' : 'grab') : 'zoom-in' }}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onClick={() => { if (!dragging && zoom <= 100) handleFullscreen(); }}
      >
        <img
          src={src}
          alt={alt}
          draggable={false}
          style={{
            width: `${zoom}%`,
            height: 'auto',
            transition: dragging ? 'none' : 'width 0.2s ease',
            transform: zoom > 100 ? `translate(${position.x}px, ${position.y}px)` : 'none',
          }}
          loading="lazy"
        />
      </div>

      {/* 줌 > 100% 힌트 */}
      {zoom > 100 && !dragging && (
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs text-gray-400 bg-white/80 dark:bg-gray-800/80 px-2 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
          <Move className="w-3 h-3" /> 드래그하여 이동
        </div>
      )}
    </div>
  );
}
