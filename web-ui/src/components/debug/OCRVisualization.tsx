import { useEffect, useRef, useState } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import type { OCRResult } from '../../types/api';

interface OCRVisualizationProps {
  imageFile: File;
  ocrResult: OCRResult;
}

interface BoundingBox {
  x: number;
  y: number;
  label: string;
  type: 'dimension' | 'gdt' | 'text';
}

export default function OCRVisualization({ imageFile, ocrResult }: OCRVisualizationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [boundingBoxes, setBoundingBoxes] = useState<BoundingBox[]>([]);

  useEffect(() => {
    const boxes: BoundingBox[] = [];

    // Dimensions
    if (ocrResult.dimensions) {
      ocrResult.dimensions.forEach((dim) => {
        if (dim.location) {
          boxes.push({
            x: dim.location.x,
            y: dim.location.y,
            label: `${dim.type}: ${dim.value}${dim.unit || ''} ${dim.tolerance || ''}`,
            type: 'dimension',
          });
        }
      });
    }

    // GD&T
    if (ocrResult.gdt) {
      ocrResult.gdt.forEach((gdt) => {
        if (gdt.location) {
          boxes.push({
            x: gdt.location.x,
            y: gdt.location.y,
            label: `${gdt.type}: ${gdt.value}${gdt.datum ? ` (${gdt.datum})` : ''}`,
            type: 'gdt',
          });
        }
      });
    }

    setBoundingBoxes(boxes);
  }, [ocrResult]);

  useEffect(() => {
    if (!imageFile || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    const url = URL.createObjectURL(imageFile);

    img.onload = () => {
      // Set canvas size to image size
      canvas.width = img.width;
      canvas.height = img.height;

      // Draw image
      ctx.drawImage(img, 0, 0);

      // Draw bounding boxes
      boundingBoxes.forEach((box) => {
        const boxSize = 80;
        const x = box.x - boxSize / 2;
        const y = box.y - boxSize / 2;

        // Set color based on type
        let color = '#3b82f6'; // blue for dimensions
        if (box.type === 'gdt') color = '#10b981'; // green for GD&T
        if (box.type === 'text') color = '#f59e0b'; // orange for text

        // Draw semi-transparent box
        ctx.fillStyle = color + '40';
        ctx.fillRect(x, y, boxSize, boxSize);

        // Draw border
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.strokeRect(x, y, boxSize, boxSize);

        // Draw center point
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(box.x, box.y, 5, 0, 2 * Math.PI);
        ctx.fill();

        // Draw label background
        ctx.font = '14px Arial';
        const textMetrics = ctx.measureText(box.label);
        const labelX = box.x - textMetrics.width / 2;
        const labelY = y - 10;

        ctx.fillStyle = color;
        ctx.fillRect(
          labelX - 4,
          labelY - 16,
          textMetrics.width + 8,
          20
        );

        // Draw label text
        ctx.fillStyle = '#ffffff';
        ctx.fillText(box.label, labelX, labelY);
      });

      setImageLoaded(true);
      URL.revokeObjectURL(url);
    };

    img.onerror = () => {
      console.error('Failed to load image');
      URL.revokeObjectURL(url);
    };

    img.src = url;
  }, [imageFile, boundingBoxes]);

  const dimensionCount = ocrResult.dimensions?.length || 0;
  const gdtCount = ocrResult.gdt?.length || 0;
  const totalDetections = dimensionCount + gdtCount;

  return (
    <Card>
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">OCR 인식 위치 시각화</h3>
          <div className="flex gap-2">
            <Badge variant="default">
              총 {totalDetections}개 인식
            </Badge>
          </div>
        </div>

        {/* Legend */}
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span>치수 ({dimensionCount}개)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span>GD&T ({gdtCount}개)</span>
          </div>
        </div>

        {/* Canvas */}
        <div className="border rounded-lg overflow-auto bg-gray-50 dark:bg-gray-900">
          <canvas
            ref={canvasRef}
            className="max-w-full h-auto"
            style={{ display: imageLoaded ? 'block' : 'none' }}
          />
          {!imageLoaded && (
            <div className="flex items-center justify-center h-64">
              <div className="text-muted-foreground">이미지 로딩 중...</div>
            </div>
          )}
        </div>

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
