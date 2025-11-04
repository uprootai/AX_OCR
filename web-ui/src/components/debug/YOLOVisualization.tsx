import { useEffect, useRef, useState } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { ZoomIn } from 'lucide-react';

interface YOLOVisualizationProps {
  imageFile: File;
  detections: Array<{
    class: string;
    confidence: number;
    bbox: number[] | { x: number; y: number; width: number; height: number };
  }>;
  onZoomClick?: (imageDataUrl: string) => void;
}

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  confidence: number;
  className: string;
  color: string;
}

// 클래스별 색상 매핑
const CLASS_COLORS: Record<string, string> = {
  // 치수
  diameter_dim: '#3b82f6',    // 파랑
  linear_dim: '#60a5fa',       // 밝은 파랑
  radius_dim: '#93c5fd',       // 연한 파랑
  angular_dim: '#2563eb',      // 진한 파랑
  chamfer_dim: '#1d4ed8',      // 매우 진한 파랑
  tolerance_dim: '#1e40af',    // 가장 진한 파랑
  reference_dim: '#3730a3',    // 남색

  // GD&T
  flatness: '#10b981',         // 초록
  cylindricity: '#34d399',     // 밝은 초록
  position: '#6ee7b7',         // 연한 초록
  perpendicularity: '#059669', // 진한 초록
  parallelism: '#047857',      // 매우 진한 초록

  // 기타
  surface_roughness: '#f59e0b', // 주황
  text_block: '#ef4444',        // 빨강
};

// 클래스 이름 한글 변환
const CLASS_NAMES: Record<string, string> = {
  diameter_dim: '직경',
  linear_dim: '선형',
  radius_dim: '반경',
  angular_dim: '각도',
  chamfer_dim: '모따기',
  tolerance_dim: '공차',
  reference_dim: '참조',
  flatness: '평면도',
  cylindricity: '원통도',
  position: '위치도',
  perpendicularity: '수직도',
  parallelism: '평행도',
  surface_roughness: '표면거칠기',
  text_block: '텍스트',
};

export default function YOLOVisualization({ imageFile, detections, onZoomClick }: YOLOVisualizationProps) {
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

    detections.forEach((det) => {
      let x, y, width, height;

      // bbox가 배열 형식인 경우 [x, y, width, height]
      if (Array.isArray(det.bbox)) {
        [x, y, width, height] = det.bbox;
      } else {
        // bbox가 객체 형식인 경우 {x, y, width, height}
        x = det.bbox.x;
        y = det.bbox.y;
        width = det.bbox.width;
        height = det.bbox.height;
      }

      const className = det.class;
      const color = CLASS_COLORS[className] || '#6b7280'; // 기본 회색
      const koreanName = CLASS_NAMES[className] || className;

      boxes.push({
        x,
        y,
        width,
        height,
        label: `${koreanName} (${(det.confidence * 100).toFixed(1)}%)`,
        confidence: det.confidence,
        className,
        color,
      });
    });

    // 신뢰도 순으로 정렬 (높은 순)
    boxes.sort((a, b) => b.confidence - a.confidence);

    setBoundingBoxes(boxes);
  }, [detections]);

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
        const x = box.x;
        const y = box.y;
        const boxWidth = box.width;
        const boxHeight = box.height;
        const color = box.color;

        // Draw semi-transparent box
        ctx.fillStyle = color + '30';
        ctx.fillRect(x, y, boxWidth, boxHeight);

        // Draw border
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, boxWidth, boxHeight);

        // Draw label background
        ctx.font = 'bold 12px Arial';
        const textMetrics = ctx.measureText(box.label);
        const padding = 4;
        const labelWidth = textMetrics.width + padding * 2;
        const labelHeight = 18;

        // Position label above bbox, or below if not enough space
        let labelX = x;
        let labelY = y - labelHeight - 2;

        // If label would go off top of canvas, put it below
        if (labelY < 0) {
          labelY = y + boxHeight + 2;
        }

        // If label would go off right of canvas, align to right
        if (labelX + labelWidth > canvas.width) {
          labelX = canvas.width - labelWidth;
        }

        // Draw label background
        ctx.fillStyle = color;
        ctx.fillRect(labelX, labelY, labelWidth, labelHeight);

        // Draw label text
        ctx.fillStyle = '#ffffff';
        ctx.textBaseline = 'top';
        ctx.fillText(box.label, labelX + padding, labelY + 2);
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

  // 클래스별 카운트
  const classCounts = boundingBoxes.reduce((acc, box) => {
    acc[box.className] = (acc[box.className] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const totalDetections = boundingBoxes.length;

  return (
    <Card>
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">YOLOv11 검출 결과 시각화</h3>
          <div className="flex gap-2">
            <Badge variant="default">
              총 {totalDetections}개 검출
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

        {/* Legend - 클래스별 카운트 */}
        {Object.keys(classCounts).length > 0 && (
          <div className="flex flex-wrap gap-3 text-xs">
            {Object.entries(classCounts).map(([className, count]) => (
              <div key={className} className="flex items-center gap-1.5">
                <div
                  className="w-3 h-3 rounded"
                  style={{ backgroundColor: CLASS_COLORS[className] || '#6b7280' }}
                ></div>
                <span>
                  {CLASS_NAMES[className] || className} ({count}개)
                </span>
              </div>
            ))}
          </div>
        )}

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
          <h4 className="font-medium">검출된 객체 상세 ({totalDetections}개)</h4>
          <div className="max-h-64 overflow-y-auto space-y-1 text-sm">
            {boundingBoxes.map((box, index) => (
              <div
                key={index}
                className="flex items-center gap-2 p-2 rounded bg-accent/50 hover:bg-accent transition-colors"
              >
                <div
                  className="w-3 h-3 rounded flex-shrink-0"
                  style={{ backgroundColor: box.color }}
                ></div>
                <span className="flex-1 font-medium">{box.label}</span>
                <span className="text-muted-foreground text-xs">
                  위치: ({Math.round(box.x)}, {Math.round(box.y)})
                </span>
                <span className="text-muted-foreground text-xs">
                  크기: {Math.round(box.width)}×{Math.round(box.height)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
}
