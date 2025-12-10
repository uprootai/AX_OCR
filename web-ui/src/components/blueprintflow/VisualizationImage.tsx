import { useState, useCallback } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Download, ZoomIn, ZoomOut, Maximize2, X } from 'lucide-react';

interface VisualizationImageProps {
  base64: string;
  title?: string;
  downloadable?: boolean;
  className?: string;
  maxHeight?: string;
}

export default function VisualizationImage({
  base64,
  title,
  downloadable = true,
  className = '',
  maxHeight = '300px',
}: VisualizationImageProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [zoom, setZoom] = useState(1);

  // base64 데이터 URL 변환
  const imgSrc = base64.startsWith('data:')
    ? base64
    : `data:image/png;base64,${base64}`;

  // 이미지 다운로드
  const handleDownload = useCallback(() => {
    const link = document.createElement('a');
    link.href = imgSrc;
    link.download = `${title || 'visualization'}_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [imgSrc, title]);

  // 줌 핸들러
  const handleZoomIn = () => setZoom(z => Math.min(3, z + 0.25));
  const handleZoomOut = () => setZoom(z => Math.max(0.5, z - 0.25));
  const handleResetZoom = () => setZoom(1);

  // 전체화면 모달
  if (isFullscreen) {
    return (
      <div
        className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
        onClick={() => setIsFullscreen(false)}
      >
        <div className="absolute top-4 right-4 flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={(e) => { e.stopPropagation(); handleZoomOut(); }}
            className="bg-white/10 hover:bg-white/20 text-white border-white/20"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={(e) => { e.stopPropagation(); handleResetZoom(); }}
            className="bg-white/10 hover:bg-white/20 text-white border-white/20"
          >
            {Math.round(zoom * 100)}%
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={(e) => { e.stopPropagation(); handleZoomIn(); }}
            className="bg-white/10 hover:bg-white/20 text-white border-white/20"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
          {downloadable && (
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => { e.stopPropagation(); handleDownload(); }}
              className="bg-white/10 hover:bg-white/20 text-white border-white/20"
            >
              <Download className="w-4 h-4" />
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsFullscreen(false)}
            className="bg-white/10 hover:bg-white/20 text-white border-white/20"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div
          className="overflow-auto max-w-[95vw] max-h-[95vh]"
          onClick={(e) => e.stopPropagation()}
        >
          <img
            src={imgSrc}
            alt={title || 'Visualization'}
            style={{ transform: `scale(${zoom})`, transformOrigin: 'center' }}
            className="transition-transform duration-200"
          />
        </div>

        {title && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-white text-sm bg-black/50 px-4 py-2 rounded">
            {title}
          </div>
        )}
      </div>
    );
  }

  return (
    <Card className={`p-2 ${className}`}>
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-2">
        {title && (
          <span className="text-xs font-medium text-muted-foreground">
            {title}
          </span>
        )}
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsFullscreen(true)}
            className="h-6 w-6 p-0"
            title="전체화면"
          >
            <Maximize2 className="w-3 h-3" />
          </Button>
          {downloadable && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDownload}
              className="h-6 w-6 p-0"
              title="다운로드"
            >
              <Download className="w-3 h-3" />
            </Button>
          )}
        </div>
      </div>

      {/* 이미지 */}
      <div
        className="overflow-hidden rounded border bg-muted/20 cursor-pointer"
        style={{ maxHeight }}
        onClick={() => setIsFullscreen(true)}
      >
        <img
          src={imgSrc}
          alt={title || 'Visualization'}
          className="w-full h-auto object-contain"
        />
      </div>
    </Card>
  );
}

// 시각화 필드 자동 감지
export function extractVisualizationImages(output: Record<string, unknown>): {
  field: string;
  base64: string;
  title: string;
}[] {
  const visualizationFields: Record<string, string> = {
    'visualization': '결과 시각화',
    'visualized_image': '시각화 이미지',
    'annotated_image': '어노테이션 이미지',
    'result_image': '결과 이미지',
    'output_image': '출력 이미지',
    'image': '이미지',
    'segmentation_mask': '세그멘테이션 마스크',
    'upscaled_image': '업스케일 이미지',
    'enhanced_image': '향상된 이미지',
  };

  const results: { field: string; base64: string; title: string }[] = [];

  for (const [field, title] of Object.entries(visualizationFields)) {
    const value = output[field];
    if (typeof value === 'string' && value.length > 100) {
      // base64 이미지로 추정
      results.push({ field, base64: value, title });
    }
  }

  return results;
}
