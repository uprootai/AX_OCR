import { useEffect, useRef, useState } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { ZoomIn } from 'lucide-react';
import type { OCRResult } from '../../types/api';

interface OCRVisualizationProps {
  imageFile?: File;
  imageBase64?: string;  // Support base64 image string
  ocrResult: OCRResult;
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

export default function OCRVisualization({ imageFile, imageBase64, ocrResult, onZoomClick, compact: _compact = false }: OCRVisualizationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [boundingBoxes, setBoundingBoxes] = useState<BoundingBox[]>([]);

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

  useEffect(() => {
    // Support both File and base64
    if ((!imageFile && !imageBase64) || !canvasRef.current) return;

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

      // Draw bounding boxes
      boundingBoxes.forEach((box) => {
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

        // Draw label with dynamic font size
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
      });

      setImageLoaded(true);
      if (url) URL.revokeObjectURL(url);
    };

    img.onerror = () => {
      console.error('Failed to load image');
      if (url) URL.revokeObjectURL(url);
    };
  }, [imageFile, imageBase64, boundingBoxes]);

  const dimensionCount = ocrResult.dimensions?.length || 0;
  const gdtCount = ocrResult.gdt?.length || 0;
  const textCount = (ocrResult.possible_text as unknown[])?.length || 0;
  const totalDetections = dimensionCount + gdtCount + textCount;

  return (
    <Card>
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">OCR 인식 위치 시각화</h3>
          <div className="flex gap-2">
            <Badge variant="default">
              총 {totalDetections}개 인식
            </Badge>
            {onZoomClick && imageLoaded && (
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

        {/* Legend */}
        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span>치수 ({dimensionCount}개)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span>GD&T ({gdtCount}개)</span>
          </div>
          {textCount > 0 && (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-orange-500 rounded"></div>
              <span>텍스트 ({textCount}개)</span>
            </div>
          )}
        </div>

        {/* Canvas */}
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
        {onZoomClick && imageLoaded && (
          <p className="text-xs text-muted-foreground text-center">
            이미지를 클릭하면 확대해서 볼 수 있습니다
          </p>
        )}

        {/* Details List */}
        <div className="space-y-2">
          <h4 className="font-medium">인식된 항목 상세</h4>
          <div className="space-y-1 text-sm">
            {boundingBoxes.map((box, index) => (
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
