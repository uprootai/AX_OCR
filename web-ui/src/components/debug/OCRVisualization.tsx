import { useEffect, useRef, useState, useMemo } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { ZoomIn, Layers, Image as ImageIcon, Eye, EyeOff, Hash, Square, Type } from 'lucide-react';
import type { OCRResult } from '../../types/api';
import { useLayerToggle, type LayerConfig } from '../../hooks/useLayerToggle';

// OCR 레이어 설정
const OCR_LAYER_CONFIG: Record<string, LayerConfig> = {
  dimension: { label: '치수', color: '#3b82f6', icon: Hash, defaultVisible: true },
  gdt: { label: 'GD&T', color: '#10b981', icon: Square, defaultVisible: true },
  text: { label: '텍스트', color: '#f59e0b', icon: Type, defaultVisible: true },
};

export interface SVGOverlayData {
  svg: string;
  svg_minimal?: string;
  width: number;
  height: number;
  dimension_count?: number;
  gdt_count?: number;
  text_count?: number;
  detection_count?: number;
}

interface OCRVisualizationProps {
  imageFile?: File;
  imageBase64?: string;  // Support base64 image string
  ocrResult: OCRResult;
  /** SVG 오버레이 데이터 (API에서 include_svg=true로 받은 경우) */
  svgOverlay?: SVGOverlayData;
  /** 기본 렌더링 모드 */
  defaultMode?: 'canvas' | 'svg';
  onZoomClick?: (imageDataUrl: string) => void;
  compact?: boolean;  // Compact mode for BlueprintFlow
}

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  type: 'dimension' | 'gdt' | 'text';
}

// Parse location from various formats to {x, y, width, height}
function parseLocation(location: unknown): { x: number; y: number; width: number; height: number } | null {
  if (!location) return null;

  // Already in dict format: {x, y, width, height}
  if (typeof location === 'object' && !Array.isArray(location) && location !== null) {
    const loc = location as Record<string, unknown>;
    if ('x' in loc && 'y' in loc) {
      return {
        x: Number(loc.x) || 0,
        y: Number(loc.y) || 0,
        width: Number(loc.width) || 0,
        height: Number(loc.height) || 0,
      };
    }
  }

  // Array format
  if (Array.isArray(location)) {
    // Polygon format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    if (location.length >= 4 && Array.isArray(location[0])) {
      const points = location as number[][];
      const xs = points.map(p => p[0]);
      const ys = points.map(p => p[1]);
      const xMin = Math.min(...xs);
      const yMin = Math.min(...ys);
      const xMax = Math.max(...xs);
      const yMax = Math.max(...ys);
      return {
        x: xMin,
        y: yMin,
        width: xMax - xMin,
        height: yMax - yMin,
      };
    }

    // Flat array format: [x, y, width, height] or [x1, y1, x2, y2]
    if (location.length === 4 && typeof location[0] === 'number') {
      const [a, b, c, d] = location as number[];
      // Heuristic: if c,d are much larger than a,b, it's [x1,y1,x2,y2]
      if (c > a * 2 || d > b * 2) {
        return { x: a, y: b, width: c - a, height: d - b };
      }
      return { x: a, y: b, width: c, height: d };
    }
  }

  return null;
}

export default function OCRVisualization({
  imageFile,
  imageBase64,
  ocrResult,
  svgOverlay,
  defaultMode = 'canvas',
  onZoomClick,
  compact: _compact = false
}: OCRVisualizationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [boundingBoxes, setBoundingBoxes] = useState<BoundingBox[]>([]);
  const [renderMode, setRenderMode] = useState<'canvas' | 'svg'>(svgOverlay ? defaultMode : 'canvas');
  const [imageUrl, setImageUrl] = useState<string | null>(null);

  // 레이어 토글 훅
  const {
    visibility,
    toggleLayer,
    showLabels,
    toggleLabels,
    layerConfigs,
    visibleCount,
    totalCount,
  } = useLayerToggle({
    layers: OCR_LAYER_CONFIG,
    initialShowLabels: true,
  });

  // 필터링된 바운딩 박스 (레이어 visibility 기반)
  const filteredBoundingBoxes = useMemo(() => {
    return boundingBoxes.filter(box => visibility[box.type]);
  }, [boundingBoxes, visibility]);

  const handleCanvasClick = () => {
    if (canvasRef.current && onZoomClick) {
      const dataUrl = canvasRef.current.toDataURL('image/png');
      onZoomClick(dataUrl);
    }
  };

  useEffect(() => {
    const boxes: BoundingBox[] = [];

    // Dimensions
    if (ocrResult.dimensions) {
      ocrResult.dimensions.forEach((dim) => {
        // Support both 'bbox' and 'location' in various formats
        const bbox = parseLocation(dim.bbox) || parseLocation(dim.location);
        if (bbox) {
          boxes.push({
            x: bbox.x,
            y: bbox.y,
            width: bbox.width,
            height: bbox.height,
            label: `${dim.type || 'dim'}: ${dim.value}${dim.unit || ''} ${dim.tolerance || ''}`.trim(),
            type: 'dimension',
          });
        }
      });
    }

    // GD&T
    if (ocrResult.gdt) {
      ocrResult.gdt.forEach((gdt) => {
        // Support both 'bbox' and 'location' in various formats
        const bbox = parseLocation(gdt.bbox) || parseLocation(gdt.location);
        if (bbox) {
          boxes.push({
            x: bbox.x,
            y: bbox.y,
            width: bbox.width,
            height: bbox.height,
            label: `${gdt.type || 'GD&T'}: ${gdt.value}${gdt.datum ? ` (${gdt.datum})` : ''}`,
            type: 'gdt',
          });
        }
      });
    }

    // Possible text (from eDOCr2)
    if (ocrResult.possible_text) {
      ocrResult.possible_text.forEach((textItem: { text?: string; location?: unknown }) => {
        const bbox = parseLocation(textItem.location);
        if (bbox) {
          boxes.push({
            x: bbox.x,
            y: bbox.y,
            width: bbox.width,
            height: bbox.height,
            label: textItem.text || 'text',
            type: 'text',
          });
        }
      });
    }

    setBoundingBoxes(boxes);
  }, [ocrResult]);

  // Create image URL for SVG mode
  useEffect(() => {
    if (!imageFile && !imageBase64) return;
    if (renderMode !== 'svg') return;

    let url: string | null = null;
    if (imageFile) {
      url = URL.createObjectURL(imageFile);
    } else if (imageBase64) {
      url = imageBase64.startsWith('data:')
        ? imageBase64
        : `data:image/jpeg;base64,${imageBase64}`;
    }
    setImageUrl(url);
    setImageLoaded(true);

    return () => {
      if (url && imageFile) {
        URL.revokeObjectURL(url);
      }
    };
  }, [imageFile, imageBase64, renderMode]);

  useEffect(() => {
    // Support both File and base64 (Canvas mode)
    if ((!imageFile && !imageBase64) || !canvasRef.current || renderMode !== 'canvas') return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    let url: string | null = null;

    if (imageFile) {
      url = URL.createObjectURL(imageFile);
      img.src = url;
    } else if (imageBase64) {
      // Handle base64: add data URL prefix if needed
      img.src = imageBase64.startsWith('data:')
        ? imageBase64
        : `data:image/jpeg;base64,${imageBase64}`;
    }

    img.onload = () => {
      // Set canvas size to image size
      canvas.width = img.width;
      canvas.height = img.height;

      // Draw image
      ctx.drawImage(img, 0, 0);

      // Calculate scale factor based on image size for better visibility
      // Base reference: 1000px width image uses default sizes
      const scaleFactor = Math.max(1, Math.min(4, Math.max(img.width, img.height) / 1000));
      const fontSize = Math.round(14 * scaleFactor);
      const lineWidth = Math.round(3 * scaleFactor);
      const pointRadius = Math.round(5 * scaleFactor);
      const labelPadding = Math.round(4 * scaleFactor);
      const labelHeight = Math.round(20 * scaleFactor);

      // Draw bounding boxes (filtered by visibility)
      filteredBoundingBoxes.forEach((box) => {
        // Use actual bbox dimensions if available, otherwise use default size
        const defaultBoxSize = 80 * scaleFactor;
        const boxWidth = box.width > 0 ? box.width : defaultBoxSize;
        const boxHeight = box.height > 0 ? box.height : defaultBoxSize;
        const x = box.x;
        const y = box.y;

        // Set color based on type
        let color = '#3b82f6'; // blue for dimensions
        if (box.type === 'gdt') color = '#10b981'; // green for GD&T
        if (box.type === 'text') color = '#f59e0b'; // orange for text

        // Draw semi-transparent box
        ctx.fillStyle = color + '40';
        ctx.fillRect(x, y, boxWidth, boxHeight);

        // Draw border
        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;
        ctx.strokeRect(x, y, boxWidth, boxHeight);

        // Draw center point
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x + boxWidth / 2, y + boxHeight / 2, pointRadius, 0, 2 * Math.PI);
        ctx.fill();

        // Draw label with dynamic font size (if showLabels is true)
        if (showLabels) {
          ctx.font = `bold ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans", sans-serif`;
          const textMetrics = ctx.measureText(box.label);
          const labelX = Math.max(labelPadding, x + boxWidth / 2 - textMetrics.width / 2);

          // Ensure label stays within canvas bounds
          const labelOffset = Math.round(10 * scaleFactor);
          let labelY = y - labelOffset;

          // If label would go above canvas, place it below the box instead
          if (labelY - labelHeight < 0) {
            labelY = y + boxHeight + labelOffset + labelHeight;
          }

          // Draw label background with rounded corners effect
          ctx.fillStyle = color;
          ctx.fillRect(
            labelX - labelPadding,
            labelY - labelHeight + labelPadding,
            textMetrics.width + labelPadding * 2,
            labelHeight
          );

          // Draw label text with shadow for better readability
          ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
          ctx.shadowBlur = 2 * scaleFactor;
          ctx.fillStyle = '#ffffff';
          ctx.fillText(box.label, labelX, labelY);
          ctx.shadowBlur = 0;
        }
      });

      setImageLoaded(true);
      if (url) URL.revokeObjectURL(url);
    };

    img.onerror = () => {
      console.error('Failed to load image');
      if (url) URL.revokeObjectURL(url);
    };
  }, [imageFile, imageBase64, filteredBoundingBoxes, showLabels]);

  const dimensionCount = ocrResult.dimensions?.length || 0;
  const gdtCount = ocrResult.gdt?.length || 0;
  const textCount = (ocrResult.possible_text as unknown[])?.length || 0;
  const totalDetections = dimensionCount + gdtCount + textCount;
  const filteredDetections = filteredBoundingBoxes.length;

  // 필터링된 타입별 카운트
  const filteredDimensionCount = visibility.dimension ? (boundingBoxes.filter(b => b.type === 'dimension').length) : 0;
  const filteredGdtCount = visibility.gdt ? (boundingBoxes.filter(b => b.type === 'gdt').length) : 0;
  const filteredTextCount = visibility.text ? (boundingBoxes.filter(b => b.type === 'text').length) : 0;

  return (
    <Card>
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">OCR 인식 위치 시각화</h3>
          <div className="flex gap-2">
            <Badge variant="default">
              {filteredDetections === totalDetections
                ? `총 ${totalDetections}개 인식`
                : `${filteredDetections}/${totalDetections}개 표시`}
            </Badge>
            {/* SVG/Canvas 모드 토글 버튼 */}
            {svgOverlay && (
              <Button
                variant={renderMode === 'svg' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setRenderMode(renderMode === 'canvas' ? 'svg' : 'canvas')}
              >
                {renderMode === 'svg' ? (
                  <>
                    <Layers className="h-4 w-4 mr-2" />
                    SVG 모드
                  </>
                ) : (
                  <>
                    <ImageIcon className="h-4 w-4 mr-2" />
                    Canvas 모드
                  </>
                )}
              </Button>
            )}
            {onZoomClick && imageLoaded && renderMode === 'canvas' && (
              <Button
                variant="default"
                size="sm"
                onClick={handleCanvasClick}
              >
                <ZoomIn className="h-4 w-4 mr-2" />
                확대 보기
              </Button>
            )}
          </div>
        </div>

        {/* 레이어 토글 컨트롤 */}
        <div className="flex flex-wrap items-center gap-2 p-2 bg-accent/20 rounded-lg">
          <span className="text-sm font-medium text-muted-foreground">레이어:</span>
          {layerConfigs.map(({ key, config, visible }) => {
            const Icon = config.icon || Layers;
            const count = key === 'dimension' ? dimensionCount : key === 'gdt' ? gdtCount : textCount;
            if (count === 0) return null;
            return (
              <Button
                key={key}
                variant={visible ? 'default' : 'outline'}
                size="sm"
                onClick={() => toggleLayer(key as keyof typeof OCR_LAYER_CONFIG)}
                className="gap-1.5"
                style={{
                  backgroundColor: visible ? config.color : undefined,
                  borderColor: config.color,
                }}
              >
                <Icon className="h-3.5 w-3.5" />
                {config.label} ({count})
                {visible ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
              </Button>
            );
          })}
          <div className="h-4 border-l border-border mx-1" />
          <Button
            variant={showLabels ? 'default' : 'outline'}
            size="sm"
            onClick={toggleLabels}
            className="gap-1.5"
          >
            라벨
            {showLabels ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
          </Button>
          <span className="text-xs text-muted-foreground ml-auto">
            {visibleCount}/{totalCount} 레이어
          </span>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-4 text-sm">
          {visibility.dimension && filteredDimensionCount > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-blue-500 rounded"></div>
              <span>치수 ({filteredDimensionCount}개)</span>
            </div>
          )}
          {visibility.gdt && filteredGdtCount > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-500 rounded"></div>
              <span>GD&T ({filteredGdtCount}개)</span>
            </div>
          )}
          {visibility.text && filteredTextCount > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-orange-500 rounded"></div>
              <span>텍스트 ({filteredTextCount}개)</span>
            </div>
          )}
        </div>

        {/* SVG Mode */}
        {renderMode === 'svg' && svgOverlay && (
          <div
            ref={containerRef}
            className="border rounded-lg overflow-auto bg-gray-50 dark:bg-gray-900"
          >
            <div
              className="relative"
              style={{ width: svgOverlay.width, height: svgOverlay.height }}
            >
              {/* Background Image */}
              {imageUrl && (
                <img
                  src={imageUrl}
                  alt="OCR visualization"
                  className="absolute top-0 left-0 w-full h-full"
                  style={{ width: svgOverlay.width, height: svgOverlay.height }}
                />
              )}
              {/* SVG Overlay */}
              <div
                className="absolute top-0 left-0 w-full h-full pointer-events-auto"
                style={{ width: svgOverlay.width, height: svgOverlay.height }}
                dangerouslySetInnerHTML={{ __html: svgOverlay.svg }}
              />
            </div>
          </div>
        )}

        {/* Canvas Mode */}
        {renderMode === 'canvas' && (
          <div className="border rounded-lg overflow-auto bg-gray-50 dark:bg-gray-900">
            <canvas
              ref={canvasRef}
              className={`max-w-full h-auto ${onZoomClick ? 'cursor-pointer hover:opacity-90 transition-opacity' : ''}`}
              style={{ display: imageLoaded ? 'block' : 'none' }}
              onClick={onZoomClick ? handleCanvasClick : undefined}
            />
            {!imageLoaded && (
              <div className="flex items-center justify-center h-64">
                <div className="text-muted-foreground">이미지 로딩 중...</div>
              </div>
            )}
          </div>
        )}

        {onZoomClick && imageLoaded && renderMode === 'canvas' && (
          <p className="text-xs text-muted-foreground text-center">
            이미지를 클릭하면 확대해서 볼 수 있습니다
          </p>
        )}
        {renderMode === 'svg' && (
          <p className="text-xs text-muted-foreground text-center">
            SVG 모드: 마우스를 올리면 상세 정보를 확인할 수 있습니다
          </p>
        )}

        {/* Details List */}
        <div className="space-y-2">
          <h4 className="font-medium">
            인식된 항목 상세 ({filteredDetections === totalDetections
              ? `${totalDetections}개`
              : `${filteredDetections}/${totalDetections}개`})
          </h4>
          <div className="space-y-1 text-sm">
            {filteredBoundingBoxes.map((box, index) => (
              <div
                key={index}
                className="flex items-center gap-2 p-2 rounded bg-accent/50"
              >
                <div
                  className={`w-3 h-3 rounded ${
                    box.type === 'dimension'
                      ? 'bg-blue-500'
                      : box.type === 'gdt'
                      ? 'bg-green-500'
                      : 'bg-orange-500'
                  }`}
                ></div>
                <span className="flex-1">{box.label}</span>
                <span className="text-muted-foreground text-xs">
                  위치: ({box.x}, {box.y})
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
}
