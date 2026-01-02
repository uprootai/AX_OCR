/**
 * PIDOverlayViewer - P&ID 도면 오버레이 뷰어
 *
 * Gateway PID Overlay API와 연동하여 심볼, 라인, 텍스트, 영역을 시각화합니다.
 *
 * Features:
 * - 레이어별 토글 (심볼/라인/텍스트/영역)
 * - SVG 오버레이 또는 이미지 출력
 * - 확대/축소 지원
 * - 호버 시 상세 정보 표시
 */

import { useState, useCallback, useMemo, useRef } from 'react';
import {
  Eye, EyeOff, Upload, Loader2, Download,
  Layers, GitBranch, Type, Square, ZoomIn, ZoomOut, RotateCcw
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

// Types
interface BBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface Symbol {
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: BBox;
}

interface Line {
  id: number;
  start_point: [number, number];
  end_point: [number, number];
  line_type: string;
  line_style?: string;
  waypoints?: [number, number][];
}

interface TextItem {
  text: string;
  confidence: number;
  position: BBox;
  bbox?: number[][];
}

interface Region {
  id: number;
  bbox: [number, number, number, number];
  region_type: string;
  region_type_korean?: string;
}

interface OverlayData {
  symbols: Symbol[];
  lines: Line[];
  texts: TextItem[];
  regions: Region[];
  statistics: {
    image_size: { width: number; height: number };
    symbols_count: number;
    lines_count: number;
    texts_count: number;
    regions_count: number;
  };
}

interface LayerVisibility {
  symbols: boolean;
  lines: boolean;
  texts: boolean;
  regions: boolean;
}

// Constants
const LAYER_CONFIG = {
  symbols: { label: '심볼', color: '#ff7800', icon: Layers },
  lines: { label: '라인', color: '#3b82f6', icon: GitBranch },
  texts: { label: '텍스트', color: '#ffa500', icon: Type },
  regions: { label: '영역', color: '#00ffff', icon: Square },
} as const;

const LINE_TYPE_COLORS: Record<string, string> = {
  pipe: '#ff0000',
  signal: '#0000ff',
  unknown: '#00ff00',
};

interface PIDOverlayViewerProps {
  initialImage?: string;
  gatewayUrl?: string;
  onOverlayGenerated?: (data: OverlayData) => void;
}

export function PIDOverlayViewer({
  initialImage,
  gatewayUrl = 'http://localhost:8000',
  onOverlayGenerated,
}: PIDOverlayViewerProps) {
  // State
  const [image, setImage] = useState<string | null>(initialImage || null);
  const [overlayData, setOverlayData] = useState<OverlayData | null>(null);
  const [_svgOverlay, setSvgOverlay] = useState<string | null>(null);
  const [annotatedImage, setAnnotatedImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [visibility, setVisibility] = useState<LayerVisibility>({
    symbols: true,
    lines: true,
    texts: true,
    regions: true,
  });
  const [showLabels, setShowLabels] = useState(true);
  const [viewMode, setViewMode] = useState<'svg' | 'image'>('svg');
  const [zoom, setZoom] = useState(1);
  const [hoveredItem, setHoveredItem] = useState<{ type: string; data: unknown } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Image size from overlay data
  const imageSize = useMemo(() => {
    if (overlayData?.statistics.image_size) {
      return overlayData.statistics.image_size;
    }
    return { width: 1000, height: 800 };
  }, [overlayData]);

  // Handle file upload
  const handleFileChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Show preview
    const reader = new FileReader();
    reader.onload = (evt) => {
      if (evt.target?.result) {
        setImage(evt.target.result as string);
      }
    };
    reader.readAsDataURL(file);

    // Call API
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('layers', 'all');
      formData.append('output_format', 'both');
      formData.append('show_labels', showLabels ? 'true' : 'false');
      formData.append('symbol_model', 'pid_symbol');
      formData.append('symbol_confidence', '0.3');

      const response = await fetch(`${gatewayUrl}/api/v1/pid-overlay/generate`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        const data: OverlayData = {
          symbols: result.symbols || [],
          lines: result.lines || [],
          texts: result.texts || [],
          regions: result.regions || [],
          statistics: result.statistics || {
            image_size: { width: 1000, height: 800 },
            symbols_count: 0,
            lines_count: 0,
            texts_count: 0,
            regions_count: 0,
          },
        };

        setOverlayData(data);
        setSvgOverlay(result.svg_overlay || null);
        setAnnotatedImage(result.annotated_image || null);
        onOverlayGenerated?.(data);
      } else {
        throw new Error(result.error || 'Unknown error');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate overlay');
    } finally {
      setIsLoading(false);
    }
  }, [gatewayUrl, showLabels, onOverlayGenerated]);

  // Toggle layer visibility
  const toggleLayer = useCallback((layer: keyof LayerVisibility) => {
    setVisibility(prev => ({ ...prev, [layer]: !prev[layer] }));
  }, []);

  // Zoom controls
  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.5));
  const handleZoomReset = () => setZoom(1);

  // Download annotated image
  const handleDownload = useCallback(() => {
    if (annotatedImage) {
      const link = document.createElement('a');
      link.href = `data:image/png;base64,${annotatedImage}`;
      link.download = 'pid_annotated.png';
      link.click();
    }
  }, [annotatedImage]);

  // Render SVG overlay manually (when we have overlay data but not SVG string)
  const renderSvgOverlay = useMemo(() => {
    if (!overlayData) return null;

    return (
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
        style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
      >
        {/* Regions layer (bottom) */}
        {visibility.regions && overlayData.regions.map((region, i) => {
          const [x1, y1, x2, y2] = region.bbox;
          return (
            <g key={`region-${i}`}>
              <rect
                x={x1}
                y={y1}
                width={x2 - x1}
                height={y2 - y1}
                fill="rgba(0, 255, 255, 0.1)"
                stroke="#00ffff"
                strokeWidth={2}
                strokeDasharray="5,5"
                className="pointer-events-auto cursor-pointer"
                onMouseEnter={() => setHoveredItem({ type: 'region', data: region })}
                onMouseLeave={() => setHoveredItem(null)}
              />
              {showLabels && (
                <text x={x1 + 5} y={y1 + 15} fill="#00ffff" fontSize={12}>
                  {region.region_type_korean || region.region_type}
                </text>
              )}
            </g>
          );
        })}

        {/* Lines layer */}
        {visibility.lines && overlayData.lines.map((line, i) => {
          const color = LINE_TYPE_COLORS[line.line_type] || LINE_TYPE_COLORS.unknown;

          if (line.waypoints && line.waypoints.length >= 2) {
            const points = line.waypoints.map(p => `${p[0]},${p[1]}`).join(' ');
            return (
              <polyline
                key={`line-${i}`}
                points={points}
                fill="none"
                stroke={color}
                strokeWidth={2}
                className="pointer-events-auto cursor-pointer"
                onMouseEnter={() => setHoveredItem({ type: 'line', data: line })}
                onMouseLeave={() => setHoveredItem(null)}
              />
            );
          }

          return (
            <line
              key={`line-${i}`}
              x1={line.start_point[0]}
              y1={line.start_point[1]}
              x2={line.end_point[0]}
              y2={line.end_point[1]}
              stroke={color}
              strokeWidth={2}
              className="pointer-events-auto cursor-pointer"
              onMouseEnter={() => setHoveredItem({ type: 'line', data: line })}
              onMouseLeave={() => setHoveredItem(null)}
            />
          );
        })}

        {/* Symbols layer */}
        {visibility.symbols && overlayData.symbols.map((symbol, i) => (
          <g key={`symbol-${i}`}>
            <rect
              x={symbol.bbox.x}
              y={symbol.bbox.y}
              width={symbol.bbox.width}
              height={symbol.bbox.height}
              fill="rgba(255, 120, 0, 0.1)"
              stroke="#ff7800"
              strokeWidth={2}
              className="pointer-events-auto cursor-pointer"
              onMouseEnter={() => setHoveredItem({ type: 'symbol', data: symbol })}
              onMouseLeave={() => setHoveredItem(null)}
            />
            {showLabels && (
              <text
                x={symbol.bbox.x}
                y={symbol.bbox.y - 5}
                fill="#ff7800"
                fontSize={12}
                fontWeight="bold"
              >
                {symbol.class_name} ({(symbol.confidence * 100).toFixed(0)}%)
              </text>
            )}
          </g>
        ))}

        {/* Texts layer */}
        {visibility.texts && overlayData.texts.map((text, i) => (
          <g key={`text-${i}`}>
            <rect
              x={text.position.x}
              y={text.position.y}
              width={text.position.width}
              height={text.position.height}
              fill="none"
              stroke="#ffa500"
              strokeWidth={1}
              className="pointer-events-auto cursor-pointer"
              onMouseEnter={() => setHoveredItem({ type: 'text', data: text })}
              onMouseLeave={() => setHoveredItem(null)}
            />
          </g>
        ))}
      </svg>
    );
  }, [overlayData, imageSize, visibility, showLabels, zoom]);

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

        {/* Layer toggles */}
        {overlayData && (
          <div className="flex flex-wrap gap-2 mt-3">
            {(Object.entries(LAYER_CONFIG) as [keyof LayerVisibility, typeof LAYER_CONFIG.symbols][]).map(
              ([key, config]) => {
                const Icon = config.icon;
                const countKey = `${key}_count` as 'symbols_count' | 'lines_count' | 'texts_count' | 'regions_count';
                const count = overlayData.statistics[countKey] || 0;
                return (
                  <button
                    key={key}
                    onClick={() => toggleLayer(key)}
                    className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors ${
                      visibility[key]
                        ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                        : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
                    }`}
                    style={{ borderLeft: visibility[key] ? `3px solid ${config.color}` : '3px solid transparent' }}
                  >
                    <Icon className="w-3 h-3" />
                    <span>{config.label}</span>
                    <span className="text-gray-500">({count})</span>
                    {visibility[key] ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                  </button>
                );
              }
            )}

            {/* Labels toggle */}
            <button
              onClick={() => setShowLabels(!showLabels)}
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
                {overlayData && renderSvgOverlay}
              </>
            )}
          </div>
        )}

        {/* Hover tooltip */}
        {hoveredItem && (
          <div className="absolute bottom-4 left-4 bg-black/80 text-white text-xs p-2 rounded shadow-lg z-50 max-w-xs">
            {hoveredItem.type === 'symbol' && (
              <div>
                <div className="font-semibold">{(hoveredItem.data as Symbol).class_name}</div>
                <div>신뢰도: {((hoveredItem.data as Symbol).confidence * 100).toFixed(1)}%</div>
              </div>
            )}
            {hoveredItem.type === 'line' && (
              <div>
                <div className="font-semibold">라인 #{(hoveredItem.data as Line).id}</div>
                <div>유형: {(hoveredItem.data as Line).line_type}</div>
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
