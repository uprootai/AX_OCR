import { Card } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { Button } from '../../ui/Button';
import { ZoomIn, Layers, Image as ImageIcon, Eye, EyeOff } from 'lucide-react';
import { ConfidenceDistributionChart } from '../../charts/ConfidenceDistributionChart';
import { useYOLOVisualization } from './useYOLOVisualization';
import { DetectionLegend } from './DetectionLegend';
import { DetectionList } from './DetectionList';
import { YOLO_LAYER_CONFIG, type YOLOVisualizationProps } from './types';

export default function YOLOVisualization(props: YOLOVisualizationProps) {
  const {
    canvasRef,
    containerRef,
    imageLoaded,
    filteredBoundingBoxes,
    renderMode,
    setRenderMode,
    imageDataUrl,
    hoveredDetection,
    setHoveredDetection,
    selectedDetection,
    handleSymbolClick,
    handleCanvasClick,
    toggleLayer,
    showLabels,
    toggleLabels,
    layerConfigs,
    visibleCount,
    totalCount,
    filteredClassCounts,
    totalDetections,
    filteredDetections,
  } = useYOLOVisualization(props);

  const { svgOverlay, onZoomClick, onSymbolSelect } = props;

  const handleSvgMouseOver = (e: React.MouseEvent) => {
    const target = e.target as SVGElement;
    const detectionId = target.getAttribute('data-id');
    if (detectionId) setHoveredDetection(parseInt(detectionId, 10));
  };

  return (
    <Card>
      <div className="p-6 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">YOLOv11 검출 결과 시각화</h3>
          <div className="flex gap-2">
            <Badge variant="default">
              {filteredDetections === totalDetections
                ? `총 ${totalDetections}개 검출`
                : `${filteredDetections}/${totalDetections}개 표시`}
            </Badge>
            {svgOverlay && (
              <Button
                variant={renderMode === 'svg' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setRenderMode(renderMode === 'canvas' ? 'svg' : 'canvas')}
                title={renderMode === 'canvas' ? 'SVG 오버레이 모드로 전환' : 'Canvas 모드로 전환'}
              >
                {renderMode === 'canvas' ? (
                  <><Layers className="h-4 w-4 mr-1" />SVG</>
                ) : (
                  <><ImageIcon className="h-4 w-4 mr-1" />Canvas</>
                )}
              </Button>
            )}
            {onZoomClick && imageLoaded && (
              <Button variant="default" size="sm" onClick={handleCanvasClick}>
                <ZoomIn className="h-4 w-4 mr-2" />
                확대 보기
              </Button>
            )}
          </div>
        </div>

        {/* Layer Toggle Controls */}
        <div className="flex flex-wrap items-center gap-2 p-2 bg-accent/20 rounded-lg">
          <span className="text-sm font-medium text-muted-foreground">레이어:</span>
          {layerConfigs.map(({ key, config, visible }) => {
            const Icon = config.icon || Layers;
            return (
              <Button
                key={key}
                variant={visible ? 'default' : 'outline'}
                size="sm"
                onClick={() => toggleLayer(key as keyof typeof YOLO_LAYER_CONFIG)}
                className="gap-1.5"
                style={{ backgroundColor: visible ? config.color : undefined, borderColor: config.color }}
              >
                <Icon className="h-3.5 w-3.5" />
                {config.label}
                {visible ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
              </Button>
            );
          })}
          <div className="h-4 border-l border-border mx-1" />
          <Button variant={showLabels ? 'default' : 'outline'} size="sm" onClick={toggleLabels} className="gap-1.5">
            라벨
            {showLabels ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
          </Button>
          <span className="text-xs text-muted-foreground ml-auto">{visibleCount}/{totalCount} 레이어</span>
        </div>

        {/* SVG Overlay Mode */}
        {renderMode === 'svg' && svgOverlay && (
          <div className="border rounded-lg overflow-auto bg-gray-50 dark:bg-gray-900">
            <div
              ref={containerRef}
              className="relative"
              style={{ width: svgOverlay.width, height: svgOverlay.height }}
            >
              {imageDataUrl && (
                <img
                  src={imageDataUrl}
                  alt="Detection result"
                  className="absolute top-0 left-0 w-full h-full"
                  style={{ pointerEvents: 'none' }}
                />
              )}
              <div
                className="absolute top-0 left-0 w-full h-full"
                dangerouslySetInnerHTML={{ __html: svgOverlay.svg }}
                onMouseOver={handleSvgMouseOver}
                onMouseOut={() => setHoveredDetection(null)}
              />
            </div>
            {hoveredDetection !== null && filteredBoundingBoxes[hoveredDetection] && (
              <div className="p-2 bg-accent/90 text-sm border-t">
                <span className="font-medium">{filteredBoundingBoxes[hoveredDetection].label}</span>
                {filteredBoundingBoxes[hoveredDetection].extractedText && (
                  <span className="ml-2 text-muted-foreground">
                    텍스트: "{filteredBoundingBoxes[hoveredDetection].extractedText}"
                  </span>
                )}
              </div>
            )}
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
        {onZoomClick && imageLoaded && (
          <p className="text-xs text-muted-foreground text-center">
            {renderMode === 'canvas'
              ? '이미지를 클릭하면 확대해서 볼 수 있습니다'
              : 'SVG 모드에서는 호버로 상세 정보를 확인할 수 있습니다'}
          </p>
        )}

        {/* Detection Legend */}
        <DetectionLegend filteredClassCounts={filteredClassCounts} />

        {/* Confidence Distribution Chart */}
        {filteredBoundingBoxes.length > 0 && (
          <div className="mt-4">
            <ConfidenceDistributionChart
              detections={filteredBoundingBoxes.map(box => ({
                confidence: box.confidence,
                class_name: box.className,
              }))}
              title="신뢰도 분포"
              compact={true}
              showStatistics={true}
            />
          </div>
        )}

        {/* Detection List + Selected Panel */}
        <DetectionList
          filteredBoundingBoxes={filteredBoundingBoxes}
          totalDetections={totalDetections}
          filteredDetections={filteredDetections}
          selectedDetection={selectedDetection}
          onSymbolSelect={onSymbolSelect}
          onSymbolClick={handleSymbolClick}
        />
      </div>
    </Card>
  );
}
