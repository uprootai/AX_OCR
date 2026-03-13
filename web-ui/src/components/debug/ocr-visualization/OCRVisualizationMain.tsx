import { useEffect, useRef, useState, useMemo } from 'react';
import { Card } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { Button } from '../../ui/Button';
import { ZoomIn, Layers, Image as ImageIcon } from 'lucide-react';
import { useLayerToggle } from '../../../hooks/useLayerToggle';
import type { OCRVisualizationProps, BoundingBox } from './types';
import { OCR_LAYER_CONFIG } from './types';
import { parseLocation } from './utils';
import {
  LayerControls,
  Legend,
  SVGOverlayView,
  CanvasView,
  DetectionList,
} from './OCRVisualizationPanels';

export default function OCRVisualization({
  imageFile,
  imageBase64,
  ocrResult,
  svgOverlay,
  defaultMode = 'canvas',
  onZoomClick,
  compact: _compact = false,
}: OCRVisualizationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [boundingBoxes, setBoundingBoxes] = useState<BoundingBox[]>([]);
  const [renderMode, setRenderMode] = useState<'canvas' | 'svg'>(
    svgOverlay ? defaultMode : 'canvas'
  );
  const [imageUrl, setImageUrl] = useState<string | null>(null);

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

  const filteredBoundingBoxes = useMemo(() => {
    return boundingBoxes.filter(box => visibility[box.type]);
  }, [boundingBoxes, visibility]);

  const handleCanvasClick = () => {
    if (canvasRef.current && onZoomClick) {
      const dataUrl = canvasRef.current.toDataURL('image/png');
      onZoomClick(dataUrl);
    }
  };

  // Parse bounding boxes from OCR result
  useEffect(() => {
    const boxes: BoundingBox[] = [];

    if (ocrResult.dimensions) {
      ocrResult.dimensions.forEach((dim) => {
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

    if (ocrResult.gdt) {
      ocrResult.gdt.forEach((gdt) => {
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

  // Canvas rendering
  useEffect(() => {
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
      img.src = imageBase64.startsWith('data:')
        ? imageBase64
        : `data:image/jpeg;base64,${imageBase64}`;
    }

    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);

      const scaleFactor = Math.max(1, Math.min(4, Math.max(img.width, img.height) / 1000));
      const fontSize = Math.round(14 * scaleFactor);
      const lineWidth = Math.round(3 * scaleFactor);
      const pointRadius = Math.round(5 * scaleFactor);
      const labelPadding = Math.round(4 * scaleFactor);
      const labelHeight = Math.round(20 * scaleFactor);

      filteredBoundingBoxes.forEach((box) => {
        const defaultBoxSize = 80 * scaleFactor;
        const boxWidth = box.width > 0 ? box.width : defaultBoxSize;
        const boxHeight = box.height > 0 ? box.height : defaultBoxSize;
        const x = box.x;
        const y = box.y;

        let color = '#3b82f6';
        if (box.type === 'gdt') color = '#10b981';
        if (box.type === 'text') color = '#f59e0b';

        ctx.fillStyle = color + '40';
        ctx.fillRect(x, y, boxWidth, boxHeight);

        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;
        ctx.strokeRect(x, y, boxWidth, boxHeight);

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x + boxWidth / 2, y + boxHeight / 2, pointRadius, 0, 2 * Math.PI);
        ctx.fill();

        if (showLabels) {
          ctx.font = `bold ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans", sans-serif`;
          const textMetrics = ctx.measureText(box.label);
          const labelX = Math.max(labelPadding, x + boxWidth / 2 - textMetrics.width / 2);
          const labelOffset = Math.round(10 * scaleFactor);
          let labelY = y - labelOffset;

          if (labelY - labelHeight < 0) {
            labelY = y + boxHeight + labelOffset + labelHeight;
          }

          ctx.fillStyle = color;
          ctx.fillRect(
            labelX - labelPadding,
            labelY - labelHeight + labelPadding,
            textMetrics.width + labelPadding * 2,
            labelHeight
          );

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

  // Counts
  const dimensionCount = ocrResult.dimensions?.length || 0;
  const gdtCount = ocrResult.gdt?.length || 0;
  const textCount = (ocrResult.possible_text as unknown[])?.length || 0;
  const totalDetections = dimensionCount + gdtCount + textCount;
  const filteredDetections = filteredBoundingBoxes.length;

  const filteredDimensionCount = visibility.dimension
    ? boundingBoxes.filter(b => b.type === 'dimension').length
    : 0;
  const filteredGdtCount = visibility.gdt
    ? boundingBoxes.filter(b => b.type === 'gdt').length
    : 0;
  const filteredTextCount = visibility.text
    ? boundingBoxes.filter(b => b.type === 'text').length
    : 0;

  return (
    <Card>
      <div className="p-6 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">OCR 인식 위치 시각화</h3>
          <div className="flex gap-2">
            <Badge variant="default">
              {filteredDetections === totalDetections
                ? `총 ${totalDetections}개 인식`
                : `${filteredDetections}/${totalDetections}개 표시`}
            </Badge>
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
              <Button variant="default" size="sm" onClick={handleCanvasClick}>
                <ZoomIn className="h-4 w-4 mr-2" />
                확대 보기
              </Button>
            )}
          </div>
        </div>

        {/* Layer controls */}
        <LayerControls
          layerConfigs={layerConfigs}
          visibility={visibility}
          showLabels={showLabels}
          visibleCount={visibleCount}
          totalCount={totalCount}
          dimensionCount={dimensionCount}
          gdtCount={gdtCount}
          textCount={textCount}
          toggleLayer={toggleLayer}
          toggleLabels={toggleLabels}
        />

        {/* Legend */}
        <Legend
          visibility={visibility}
          filteredDimensionCount={filteredDimensionCount}
          filteredGdtCount={filteredGdtCount}
          filteredTextCount={filteredTextCount}
        />

        {/* SVG Mode */}
        {renderMode === 'svg' && svgOverlay && (
          <SVGOverlayView
            svgOverlay={svgOverlay}
            imageUrl={imageUrl}
            containerRef={containerRef}
          />
        )}

        {/* Canvas Mode */}
        {renderMode === 'canvas' && (
          <CanvasView
            canvasRef={canvasRef}
            imageLoaded={imageLoaded}
            onZoomClick={onZoomClick}
            handleCanvasClick={handleCanvasClick}
          />
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

        {/* Detection list */}
        <DetectionList
          filteredBoundingBoxes={filteredBoundingBoxes}
          totalDetections={totalDetections}
        />
      </div>
    </Card>
  );
}
