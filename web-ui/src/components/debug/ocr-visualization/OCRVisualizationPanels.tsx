import { Layers, Eye, EyeOff } from 'lucide-react';
import { Button } from '../../ui/Button';
import type { BoundingBox, SVGOverlayData } from './types';
import { OCR_LAYER_CONFIG } from './types';
import type { LayerConfig } from '../../../hooks/useLayerToggle';

// ── LayerControls ────────────────────────────────────────────────────────────

interface LayerControlsProps {
  layerConfigs: { key: string; config: LayerConfig; visible: boolean }[];
  visibility: Record<string, boolean>;
  showLabels: boolean;
  visibleCount: number;
  totalCount: number;
  dimensionCount: number;
  gdtCount: number;
  textCount: number;
  toggleLayer: (key: keyof typeof OCR_LAYER_CONFIG) => void;
  toggleLabels: () => void;
}

export function LayerControls({
  layerConfigs,
  visibility: _visibility,
  showLabels,
  visibleCount,
  totalCount,
  dimensionCount,
  gdtCount,
  textCount,
  toggleLayer,
  toggleLabels,
}: LayerControlsProps) {
  return (
    <div className="flex flex-wrap items-center gap-2 p-2 bg-accent/20 rounded-lg">
      <span className="text-sm font-medium text-muted-foreground">레이어:</span>
      {layerConfigs.map(({ key, config, visible }) => {
        const Icon = config.icon || Layers;
        const count =
          key === 'dimension' ? dimensionCount : key === 'gdt' ? gdtCount : textCount;
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
  );
}

// ── Legend ───────────────────────────────────────────────────────────────────

interface LegendProps {
  visibility: Record<string, boolean>;
  filteredDimensionCount: number;
  filteredGdtCount: number;
  filteredTextCount: number;
}

export function Legend({
  visibility,
  filteredDimensionCount,
  filteredGdtCount,
  filteredTextCount,
}: LegendProps) {
  return (
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
  );
}

// ── SVGOverlayView ────────────────────────────────────────────────────────────

interface SVGOverlayViewProps {
  svgOverlay: SVGOverlayData;
  imageUrl: string | null;
  containerRef: React.RefObject<HTMLDivElement | null>;
}

export function SVGOverlayView({ svgOverlay, imageUrl, containerRef }: SVGOverlayViewProps) {
  return (
    <div
      ref={containerRef}
      className="border rounded-lg overflow-auto bg-gray-50 dark:bg-gray-900"
    >
      <div
        className="relative"
        style={{ width: svgOverlay.width, height: svgOverlay.height }}
      >
        {imageUrl && (
          <img
            src={imageUrl}
            alt="OCR visualization"
            className="absolute top-0 left-0 w-full h-full"
            style={{ width: svgOverlay.width, height: svgOverlay.height }}
          />
        )}
        <div
          className="absolute top-0 left-0 w-full h-full pointer-events-auto"
          style={{ width: svgOverlay.width, height: svgOverlay.height }}
          dangerouslySetInnerHTML={{ __html: svgOverlay.svg }}
        />
      </div>
    </div>
  );
}

// ── CanvasView ────────────────────────────────────────────────────────────────

interface CanvasViewProps {
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  imageLoaded: boolean;
  onZoomClick?: (imageDataUrl: string) => void;
  handleCanvasClick: () => void;
}

export function CanvasView({
  canvasRef,
  imageLoaded,
  onZoomClick,
  handleCanvasClick,
}: CanvasViewProps) {
  return (
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
  );
}

// ── DetectionList ─────────────────────────────────────────────────────────────

interface DetectionListProps {
  filteredBoundingBoxes: BoundingBox[];
  totalDetections: number;
}

export function DetectionList({ filteredBoundingBoxes, totalDetections }: DetectionListProps) {
  const filteredDetections = filteredBoundingBoxes.length;
  return (
    <div className="space-y-2">
      <h4 className="font-medium">
        인식된 항목 상세 (
        {filteredDetections === totalDetections
          ? `${totalDetections}개`
          : `${filteredDetections}/${totalDetections}개`}
        )
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
  );
}
