import { useEffect, useRef, useState } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import type { SegmentationResult } from '../../types/api';

interface SegmentationVisualizationProps {
  imageFile?: File;
  imageBase64?: string;  // Support base64 image string
  segmentationResult: SegmentationResult;
  compact?: boolean;  // Compact mode for BlueprintFlow
}

export default function SegmentationVisualization({
  imageFile,
  imageBase64,
  segmentationResult,
  compact = false,
}: SegmentationVisualizationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [imageLoaded, setImageLoaded] = useState(false);

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

      // Draw classification overlay
      // Note: In a real implementation, you would draw actual segmentation masks
      // For now, we just display the image with a legend

      setImageLoaded(true);
      if (url) URL.revokeObjectURL(url);
    };

    img.onerror = () => {
      console.error('Failed to load image');
      if (url) URL.revokeObjectURL(url);
    };
  }, [imageFile, imageBase64]);

  const contourCount = segmentationResult.classifications?.contour || 0;
  const textCount = segmentationResult.classifications?.text || 0;
  const dimensionCount = segmentationResult.classifications?.dimension || 0;
  const totalComponents = segmentationResult.num_components || 0;

  if (compact) {
    return (
      <div className="space-y-3">
        {/* Summary Stats */}
        <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-green-900 dark:text-green-100">
              Segmentation Results
            </span>
            <span className="text-xs font-bold bg-green-200 dark:bg-green-800 text-green-900 dark:text-green-100 px-2 py-0.5 rounded">
              {totalComponents} components
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-purple-500 rounded"></div>
              <span className="text-green-700 dark:text-green-300">Contours:</span>
              <span className="font-semibold text-green-900 dark:text-green-100">{contourCount}</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-orange-500 rounded"></div>
              <span className="text-green-700 dark:text-green-300">Text:</span>
              <span className="font-semibold text-green-900 dark:text-green-100">{textCount}</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-blue-500 rounded"></div>
              <span className="text-green-700 dark:text-green-300">Dims:</span>
              <span className="font-semibold text-green-900 dark:text-green-100">{dimensionCount}</span>
            </div>
          </div>
        </div>

        {/* Graph Info (if available) */}
        {segmentationResult.graph && (
          <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
            <div className="text-xs font-semibold text-purple-900 dark:text-purple-100 mb-2">
              Graph Structure
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-purple-700 dark:text-purple-300">Nodes:</span>
                <span className="font-semibold text-purple-900 dark:text-purple-100">{segmentationResult.graph.nodes}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-purple-700 dark:text-purple-300">Edges:</span>
                <span className="font-semibold text-purple-900 dark:text-purple-100">{segmentationResult.graph.edges}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-purple-700 dark:text-purple-300">Deg:</span>
                <span className="font-semibold text-purple-900 dark:text-purple-100">{segmentationResult.graph.avg_degree.toFixed(1)}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <Card>
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">세그멘테이션 시각화</h3>
          <div className="flex gap-2">
            <Badge variant="default">
              총 {totalComponents}개 컴포넌트
            </Badge>
          </div>
        </div>

        {/* Legend */}
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-purple-500 rounded"></div>
            <span>윤곽선 ({contourCount}개)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-orange-500 rounded"></div>
            <span>텍스트 ({textCount}개)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span>치수 ({dimensionCount}개)</span>
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

        {/* Component Stats */}
        <div className="space-y-2">
          <h4 className="font-medium">컴포넌트 분류 상세</h4>
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-3 h-3 bg-purple-500 rounded"></div>
                <span className="text-sm font-medium">윤곽선</span>
              </div>
              <p className="text-2xl font-bold">{contourCount}</p>
              <p className="text-xs text-muted-foreground">Contours</p>
            </div>
            <div className="p-3 bg-orange-500/10 border border-orange-500/20 rounded">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-3 h-3 bg-orange-500 rounded"></div>
                <span className="text-sm font-medium">텍스트</span>
              </div>
              <p className="text-2xl font-bold">{textCount}</p>
              <p className="text-xs text-muted-foreground">Text</p>
            </div>
            <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-3 h-3 bg-blue-500 rounded"></div>
                <span className="text-sm font-medium">치수</span>
              </div>
              <p className="text-2xl font-bold">{dimensionCount}</p>
              <p className="text-xs text-muted-foreground">Dimensions</p>
            </div>
          </div>
        </div>

        {/* Graph Info */}
        {segmentationResult.graph && (
          <div className="space-y-2">
            <h4 className="font-medium">그래프 구조</h4>
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-background border rounded text-center">
                <p className="text-xl font-bold">{segmentationResult.graph.nodes}</p>
                <p className="text-xs text-muted-foreground">노드</p>
              </div>
              <div className="p-3 bg-background border rounded text-center">
                <p className="text-xl font-bold">{segmentationResult.graph.edges}</p>
                <p className="text-xs text-muted-foreground">엣지</p>
              </div>
              <div className="p-3 bg-background border rounded text-center">
                <p className="text-xl font-bold">{segmentationResult.graph.avg_degree.toFixed(2)}</p>
                <p className="text-xs text-muted-foreground">평균 차수</p>
              </div>
            </div>
          </div>
        )}

        {/* Vectorization Info */}
        {segmentationResult.vectorization && (
          <div className="space-y-2">
            <h4 className="font-medium">벡터화 정보</h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-background border rounded">
                <p className="text-sm text-muted-foreground mb-1">베지어 곡선 수</p>
                <p className="text-xl font-bold">{segmentationResult.vectorization.num_bezier_curves}</p>
              </div>
              <div className="p-3 bg-background border rounded">
                <p className="text-sm text-muted-foreground mb-1">총 길이</p>
                <p className="text-xl font-bold">{segmentationResult.vectorization.total_length.toFixed(1)}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
