/**
 * PIDOverlayViewer - P&ID 도면 오버레이 뷰어
 *
 * Design Checker API와 연동하여 심볼 검출 결과를 시각화합니다.
 *
 * Note: 현재 심볼 검출만 지원합니다. 라인/텍스트/영역은 BlueprintFlow에서
 * 전체 파이프라인을 통해 사용할 수 있습니다.
 *
 * Features:
 * - YOLO 기반 심볼 검출 시각화
 * - SVG 오버레이 또는 이미지 출력
 * - 확대/축소 지원
 * - 호버 시 상세 정보 표시
 */

import {
  Eye, EyeOff, Upload, Loader2, Download,
  ZoomIn, ZoomOut, RotateCcw, Type
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { useLayerToggle, PID_LAYER_CONFIG } from '../../hooks/useLayerToggle';
import type { PIDOverlayViewerProps, PIDSymbol, PIDLine, TextItem, Region } from './types';
import { usePIDOverlay } from './usePIDOverlay';
import { PIDSvgOverlay } from './PIDSvgOverlay';

export function PIDOverlayViewer({
  initialImage,
  apiUrl = 'http://localhost:5019',
  onOverlayGenerated,
}: PIDOverlayViewerProps) {
  const {
    image,
    overlayData,
    annotatedImage,
    isLoading,
    error,
    viewMode,
    zoom,
    hoveredItem,
    imageSize,
    fileInputRef,
    containerRef,
    setViewMode,
    setHoveredItem,
    handleFileChange,
    handleZoomIn,
    handleZoomOut,
    handleZoomReset,
    handleDownload,
  } = usePIDOverlay({ initialImage, apiUrl, onOverlayGenerated });

  // useLayerToggle 훅으로 레이어 가시성 관리
  const {
    visibility,
    toggleLayer,
    showLabels,
    toggleLabels,
    layerConfigs,
  } = useLayerToggle({
    layers: PID_LAYER_CONFIG,
  });

  return (
    <Card className="w-full">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">P&ID 오버레이 뷰어</h3>
          <div className="flex items-center gap-2">
            {/* Upload button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              <span className="ml-1">업로드</span>
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleFileChange}
            />

            {/* View mode toggle */}
            {annotatedImage && (
              <Button
                variant={viewMode === 'svg' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode(viewMode === 'svg' ? 'image' : 'svg')}
              >
                {viewMode === 'svg' ? 'SVG' : '이미지'}
              </Button>
            )}

            {/* Download */}
            {annotatedImage && (
              <Button variant="outline" size="sm" onClick={handleDownload}>
                <Download className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Layer toggles - useLayerToggle 훅 사용 */}
        {overlayData && (
          <div className="flex flex-wrap gap-2 mt-3">
            {layerConfigs.map(({ key, config, visible }) => {
              const Icon = config.icon || Eye;
              const countKey = `${key}_count` as 'symbols_count' | 'lines_count' | 'texts_count' | 'regions_count';
              const count = overlayData.statistics[countKey] || 0;
              return (
                <button
                  key={key}
                  onClick={() => toggleLayer(key)}
                  className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors ${
                    visible
                      ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                      : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
                  }`}
                  style={{ borderLeft: visible ? `3px solid ${config.color}` : '3px solid transparent' }}
                >
                  <Icon className="w-3 h-3" />
                  <span>{config.label}</span>
                  <span className="text-gray-500">({count})</span>
                  {visible ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                </button>
              );
            })}

            {/* Labels toggle */}
            <button
              onClick={toggleLabels}
              className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs ${
                showLabels ? 'bg-gray-100 dark:bg-gray-700' : 'text-gray-400'
              }`}
            >
              <Type className="w-3 h-3" />
              <span>라벨</span>
            </button>
          </div>
        )}

        {/* Zoom controls */}
        {overlayData && (
          <div className="flex items-center gap-1 mt-2">
            <Button variant="ghost" size="sm" onClick={handleZoomOut}>
              <ZoomOut className="w-4 h-4" />
            </Button>
            <span className="text-xs text-gray-500 w-12 text-center">{(zoom * 100).toFixed(0)}%</span>
            <Button variant="ghost" size="sm" onClick={handleZoomIn}>
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={handleZoomReset}>
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Main content */}
      <div
        ref={containerRef}
        className="relative overflow-auto bg-gray-100 dark:bg-gray-900"
        style={{ minHeight: 400, maxHeight: 600 }}
      >
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-red-50 dark:bg-red-900/20">
            <p className="text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-gray-900/80 z-50">
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <span className="text-sm text-gray-500">분석 중...</span>
            </div>
          </div>
        )}

        {!image && !isLoading && (
          <div
            className="flex flex-col items-center justify-center h-96 cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="w-12 h-12 text-gray-400 mb-2" />
            <p className="text-gray-500">P&ID 도면을 업로드하세요</p>
            <p className="text-xs text-gray-400 mt-1">PNG, JPG 지원</p>
          </div>
        )}

        {image && (
          <div className="relative inline-block" style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}>
            {viewMode === 'image' && annotatedImage ? (
              <img
                src={`data:image/png;base64,${annotatedImage}`}
                alt="Annotated P&ID"
                className="max-w-none"
              />
            ) : (
              <>
                <img
                  src={image}
                  alt="P&ID"
                  className="max-w-none"
                />
                {overlayData && (
                  <PIDSvgOverlay
                    overlayData={overlayData}
                    imageSize={imageSize}
                    visibility={visibility}
                    showLabels={showLabels}
                    zoom={zoom}
                    onHover={setHoveredItem}
                  />
                )}
              </>
            )}
          </div>
        )}

        {/* Hover tooltip */}
        {hoveredItem && (
          <div className="absolute bottom-4 left-4 bg-black/80 text-white text-xs p-2 rounded shadow-lg z-50 max-w-xs">
            {hoveredItem.type === 'symbol' && (
              <div>
                <div className="font-semibold">{(hoveredItem.data as PIDSymbol).class_name}</div>
                <div>신뢰도: {((hoveredItem.data as PIDSymbol).confidence * 100).toFixed(1)}%</div>
              </div>
            )}
            {hoveredItem.type === 'line' && (
              <div>
                <div className="font-semibold">라인 #{(hoveredItem.data as PIDLine).id}</div>
                <div>유형: {(hoveredItem.data as PIDLine).line_type}</div>
              </div>
            )}
            {hoveredItem.type === 'text' && (
              <div>
                <div className="font-semibold">{(hoveredItem.data as TextItem).text}</div>
                <div>신뢰도: {((hoveredItem.data as TextItem).confidence * 100).toFixed(1)}%</div>
              </div>
            )}
            {hoveredItem.type === 'region' && (
              <div>
                <div className="font-semibold">
                  {(hoveredItem.data as Region).region_type_korean || (hoveredItem.data as Region).region_type}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Statistics footer */}
      {overlayData && (
        <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>
              이미지: {imageSize.width} x {imageSize.height}px
            </span>
            <span>
              심볼: {overlayData.statistics.symbols_count} |
              라인: {overlayData.statistics.lines_count} |
              텍스트: {overlayData.statistics.texts_count} |
              영역: {overlayData.statistics.regions_count}
            </span>
          </div>
        </div>
      )}
    </Card>
  );
}

export default PIDOverlayViewer;
