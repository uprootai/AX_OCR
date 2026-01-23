import { useEffect, useRef, useState, useMemo } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { ZoomIn, Layers, Image as ImageIcon, Eye, EyeOff, Square, Hash, Settings } from 'lucide-react';
import { ConfidenceDistributionChart } from '../charts/ConfidenceDistributionChart';
import { useLayerToggle, type LayerConfig } from '../../hooks/useLayerToggle';

export interface SVGOverlayData {
  svg: string;
  svg_minimal?: string;
  width: number;
  height: number;
  detection_count: number;
  model_type?: string;
}

interface YOLOVisualizationProps {
  imageFile: File;
  detections: Array<{
    class?: string;           // Legacy field name
    class_name?: string;      // New API field name
    confidence: number;
    bbox: number[] | { x: number; y: number; width: number; height: number };
    value?: string | null;    // Extracted text value
    extracted_text?: string | null;  // Alternative field name for extracted text
  }>;
  /** SVG 오버레이 데이터 (API에서 include_svg=true로 받은 경우) */
  svgOverlay?: SVGOverlayData;
  /** 기본 렌더링 모드 */
  defaultMode?: 'canvas' | 'svg';
  onZoomClick?: (imageDataUrl: string) => void;
  /** 심볼 선택 콜백 */
  onSymbolSelect?: (detection: BoundingBox | null, index: number | null) => void;
  /** 외부에서 선택된 인덱스 (제어 컴포넌트) */
  selectedIndex?: number | null;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  confidence: number;
  className: string;
  color: string;
  extractedText?: string;  // Extracted text from OCR
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
  reference_dim: '#8b5cf6',    // 보라색 (파랑/초록과 명확히 구분)

  // GD&T
  flatness: '#10b981',         // 초록
  cylindricity: '#34d399',     // 밝은 초록
  position: '#6ee7b7',         // 연한 초록
  perpendicularity: '#059669', // 진한 초록
  parallelism: '#047857',      // 매우 진한 초록

  // 기타
  surface_roughness: '#f59e0b', // 주황
  text_block: '#ec4899',        // 핫핑크 (더 눈에 띄는 색상)
};

// 클래스 이름 한글 변환 (한글명 + 영문명 + 약어)
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
  text_block: '텍스트 블록',
};

// 상세 설명 (한글명 + 영문 + 약어)
const CLASS_DETAILS: Record<string, { korean: string; english: string; abbr: string }> = {
  diameter_dim: { korean: '직경 치수', english: 'Diameter', abbr: 'Ø' },
  linear_dim: { korean: '선형 치수', english: 'Linear', abbr: 'L' },
  radius_dim: { korean: '반경 치수', english: 'Radius', abbr: 'R' },
  angular_dim: { korean: '각도 치수', english: 'Angular', abbr: '°' },
  chamfer_dim: { korean: '모따기 치수', english: 'Chamfer', abbr: 'C' },
  tolerance_dim: { korean: '공차 치수', english: 'Tolerance', abbr: '±' },
  reference_dim: { korean: '참조 치수', english: 'Reference', abbr: '()' },
  flatness: { korean: '평면도', english: 'Flatness', abbr: '⏥' },
  cylindricity: { korean: '원통도', english: 'Cylindricity', abbr: '⌭' },
  position: { korean: '위치도', english: 'Position', abbr: '⊕' },
  perpendicularity: { korean: '수직도', english: 'Perpendicularity', abbr: '⊥' },
  parallelism: { korean: '평행도', english: 'Parallelism', abbr: '∥' },
  surface_roughness: { korean: '표면 조도', english: 'Surface Roughness', abbr: 'Ra' },
  text_block: { korean: '텍스트 블록', english: 'Text Block', abbr: 'TXT' },
};

// 카테고리 그룹
const CLASS_CATEGORIES = {
  dimensions: ['diameter_dim', 'linear_dim', 'radius_dim', 'angular_dim', 'chamfer_dim', 'tolerance_dim', 'reference_dim'],
  gdt: ['flatness', 'cylindricity', 'position', 'perpendicularity', 'parallelism'],
  other: ['surface_roughness', 'text_block'],
};

// 레이어 토글 설정
const YOLO_LAYER_CONFIG: Record<string, LayerConfig> = {
  dimensions: { label: '치수', color: '#3b82f6', icon: Hash, defaultVisible: true },
  gdt: { label: 'GD&T', color: '#10b981', icon: Square, defaultVisible: true },
  other: { label: '기타', color: '#f59e0b', icon: Settings, defaultVisible: true },
};

// Parse bbox from various formats to {x, y, width, height}
function parseBbox(bbox: unknown): { x: number; y: number; width: number; height: number } | null {
  if (!bbox) return null;

  // Already in array format: [x, y, width, height]
  if (Array.isArray(bbox)) {
    // Polygon format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    if (bbox.length >= 4 && Array.isArray(bbox[0])) {
      const points = bbox as number[][];
      const xs = points.map(p => p[0]);
      const ys = points.map(p => p[1]);
      const xMin = Math.min(...xs);
      const yMin = Math.min(...ys);
      const xMax = Math.max(...xs);
      const yMax = Math.max(...ys);
      return { x: xMin, y: yMin, width: xMax - xMin, height: yMax - yMin };
    }

    // Flat array format: [x, y, width, height] or [x1, y1, x2, y2]
    if (bbox.length === 4 && typeof bbox[0] === 'number') {
      const [a, b, c, d] = bbox as number[];
      // Heuristic: if c,d are much larger than a,b, it's [x1,y1,x2,y2]
      // (e.g., x1=100, y1=50, x2=200, y2=150 => x2 > x1*2 is false, but x2 > x1 and y2 > y1)
      // Better heuristic: if c > a and d > b and (c > a + 10 or d > b + 10), assume it's coordinates
      if (c > a && d > b && (c > a * 2 || d > b * 2 || (c > a + 50 && d > b + 50))) {
        return { x: a, y: b, width: c - a, height: d - b };
      }
      return { x: a, y: b, width: c, height: d };
    }
  }

  // Dict format: {x, y, width, height}
  if (typeof bbox === 'object' && bbox !== null && !Array.isArray(bbox)) {
    const b = bbox as Record<string, unknown>;
    if ('x' in b && 'y' in b) {
      return {
        x: Number(b.x) || 0,
        y: Number(b.y) || 0,
        width: Number(b.width) || 0,
        height: Number(b.height) || 0,
      };
    }
  }

  return null;
}

export default function YOLOVisualization({
  imageFile,
  detections,
  svgOverlay,
  defaultMode = 'canvas',
  onZoomClick,
  onSymbolSelect,
  selectedIndex: externalSelectedIndex,
}: YOLOVisualizationProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [boundingBoxes, setBoundingBoxes] = useState<BoundingBox[]>([]);
  const [renderMode, setRenderMode] = useState<'canvas' | 'svg'>(svgOverlay ? defaultMode : 'canvas');
  const [imageDataUrl, setImageDataUrl] = useState<string | null>(null);
  const [hoveredDetection, setHoveredDetection] = useState<number | null>(null);
  const [internalSelectedIndex, setInternalSelectedIndex] = useState<number | null>(null);

  // 선택 상태: 외부 제어 또는 내부 상태
  const selectedDetection = externalSelectedIndex !== undefined ? externalSelectedIndex : internalSelectedIndex;

  // 레이어 토글 훅
  const {
    visibility,
    toggleLayer,
    showLabels,
    toggleLabels,
    layerConfigs,
    visibleCount,
    totalCount,
  } = useLayerToggle({
    layers: YOLO_LAYER_CONFIG,
    initialShowLabels: true,
  });

  // 카테고리별 클래스 맵
  const getClassCategory = (className: string): keyof typeof YOLO_LAYER_CONFIG => {
    if (CLASS_CATEGORIES.dimensions.includes(className)) return 'dimensions';
    if (CLASS_CATEGORIES.gdt.includes(className)) return 'gdt';
    return 'other';
  };

  // 필터링된 바운딩 박스 (레이어 visibility 기반)
  const filteredBoundingBoxes = useMemo(() => {
    return boundingBoxes.filter(box => {
      const category = getClassCategory(box.className);
      return visibility[category];
    });
  }, [boundingBoxes, visibility]);

  // 심볼 클릭 핸들러
  const handleSymbolClick = (index: number) => {
    const newIndex = selectedDetection === index ? null : index;
    if (externalSelectedIndex === undefined) {
      setInternalSelectedIndex(newIndex);
    }
    if (onSymbolSelect) {
      onSymbolSelect(newIndex !== null ? filteredBoundingBoxes[newIndex] : null, newIndex);
    }
  };

  const handleCanvasClick = () => {
    if (canvasRef.current && onZoomClick) {
      const dataUrl = canvasRef.current.toDataURL('image/png');
      onZoomClick(dataUrl);
    }
  };

  useEffect(() => {
    const boxes: BoundingBox[] = [];

    detections.forEach((det) => {
      // Parse bbox from various formats (array, polygon, dict)
      const parsed = parseBbox(det.bbox);
      if (!parsed) return; // Skip if bbox is invalid

      const { x, y, width, height } = parsed;

      // Support both 'class' and 'class_name' field names
      const className = det.class_name || det.class || 'unknown';
      const color = CLASS_COLORS[className] || '#6b7280'; // 기본 회색
      const koreanName = CLASS_NAMES[className] || className;

      // Get extracted text if available
      const extractedText = det.extracted_text || det.value;

      // Build label: Korean name + confidence + extracted text (if available)
      let label = `${koreanName} (${(det.confidence * 100).toFixed(1)}%)`;
      if (extractedText && extractedText !== 'null') {
        // Trim long text values
        const displayText = extractedText.length > 20 ? extractedText.substring(0, 20) + '...' : extractedText;
        label += ` - ${displayText}`;
      } else {
        // If no extracted text, show bbox size for reference
        label += ` [${Math.round(width)}×${Math.round(height)}]`;
      }

      boxes.push({
        x,
        y,
        width,
        height,
        label,
        confidence: det.confidence,
        className,
        color,
        extractedText: extractedText || undefined,
      });
    });

    // 신뢰도 순으로 정렬 (높은 순)
    boxes.sort((a, b) => b.confidence - a.confidence);

    setBoundingBoxes(boxes);
  }, [detections]);

  // SVG 모드에서 사용할 이미지 데이터 URL 생성
  useEffect(() => {
    if (!imageFile || renderMode !== 'svg') return;

    const reader = new FileReader();
    reader.onload = (e) => {
      setImageDataUrl(e.target?.result as string);
      setImageLoaded(true);
    };
    reader.readAsDataURL(imageFile);

    return () => {
      reader.abort();
    };
  }, [imageFile, renderMode]);

  // SVG 오버레이 이벤트 핸들러
  const handleSvgMouseOver = (e: React.MouseEvent) => {
    const target = e.target as SVGElement;
    const detectionId = target.getAttribute('data-id');
    if (detectionId) {
      setHoveredDetection(parseInt(detectionId, 10));
    }
  };

  const handleSvgMouseOut = () => {
    setHoveredDetection(null);
  };

  useEffect(() => {
    if (!imageFile || !canvasRef.current || renderMode !== 'canvas') return;

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

      // Calculate scale factor based on image size for better visibility
      // Base reference: 1000px width image uses default sizes
      const scaleFactor = Math.max(1, Math.min(4, Math.max(img.width, img.height) / 1000));
      const fontSize = Math.round(11 * scaleFactor);
      const baseLineWidth = Math.round(2 * scaleFactor);
      const padding = Math.round(3 * scaleFactor);
      const labelHeight = Math.round(16 * scaleFactor);
      const gap = Math.round(2 * scaleFactor);

      // Track used label positions to prevent overlap
      const usedLabelPositions: Array<{x: number; y: number; width: number; height: number}> = [];

      const checkLabelOverlap = (x: number, y: number, width: number, height: number): boolean => {
        return usedLabelPositions.some(used =>
          !(x + width < used.x || x > used.x + used.width ||
            y + height < used.y || y > used.y + used.height)
        );
      };

      // Draw bounding boxes (filtered by visibility)
      filteredBoundingBoxes.forEach((box) => {
        const x = box.x;
        const y = box.y;
        const boxWidth = box.width;
        const boxHeight = box.height;
        const color = box.color;

        // Draw semi-transparent box (higher opacity for better visibility)
        ctx.fillStyle = color + '40';  // 40 = 25% opacity (was 30 = 18%)
        ctx.fillRect(x, y, boxWidth, boxHeight);

        // Draw border (thicker for text_block)
        ctx.strokeStyle = color;
        ctx.lineWidth = box.className === 'text_block' ? baseLineWidth * 2 : baseLineWidth;
        ctx.strokeRect(x, y, boxWidth, boxHeight);

        // Draw label background with dynamic font size
        ctx.font = `bold ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans", sans-serif`;
        const textMetrics = ctx.measureText(box.label);
        const labelWidth = textMetrics.width + padding * 2;

        // Try to position label above bbox first
        let labelX = x;
        let labelY = y - labelHeight - gap;

        // If label would go off top, try below
        if (labelY < 0) {
          labelY = y + boxHeight + gap;
        }

        // Check for overlap and adjust position
        let attempts = 0;
        while (checkLabelOverlap(labelX, labelY, labelWidth, labelHeight) && attempts < 4) {
          attempts++;
          // Try different positions: above, below, left, right
          if (attempts === 1) {
            labelY = y + boxHeight + gap; // below
          } else if (attempts === 2) {
            labelX = x - labelWidth - gap; // left
            labelY = y;
          } else if (attempts === 3) {
            labelX = x + boxWidth + gap; // right
            labelY = y;
          }
        }

        // If label would go off canvas edges, constrain it
        if (labelX < gap) labelX = gap;
        if (labelY < gap) labelY = gap;
        if (labelX + labelWidth > canvas.width) labelX = canvas.width - labelWidth - gap;
        if (labelY + labelHeight > canvas.height) labelY = canvas.height - labelHeight - gap;

        // Draw label (if showLabels is true)
        if (showLabels) {
          // Draw label background
          ctx.fillStyle = color;
          ctx.fillRect(labelX, labelY, labelWidth, labelHeight);

          // Draw label text with shadow for better readability
          ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
          ctx.shadowBlur = scaleFactor;
          ctx.fillStyle = '#ffffff';
          ctx.textBaseline = 'top';
          ctx.fillText(box.label, labelX + padding, labelY + gap);
          ctx.shadowBlur = 0;

          // Record this label position to prevent future overlaps
          usedLabelPositions.push({x: labelX, y: labelY, width: labelWidth, height: labelHeight});
        }
      });

      setImageLoaded(true);
      URL.revokeObjectURL(url);
    };

    img.onerror = () => {
      console.error('Failed to load image');
      URL.revokeObjectURL(url);
    };

    img.src = url;
  }, [imageFile, filteredBoundingBoxes, renderMode, showLabels]);

  // 필터링된 클래스별 카운트
  const filteredClassCounts = filteredBoundingBoxes.reduce((acc, box) => {
    acc[box.className] = (acc[box.className] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const totalDetections = boundingBoxes.length;
  const filteredDetections = filteredBoundingBoxes.length;

  return (
    <Card>
      <div className="p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">YOLOv11 검출 결과 시각화</h3>
          <div className="flex gap-2">
            <Badge variant="default">
              {filteredDetections === totalDetections
                ? `총 ${totalDetections}개 검출`
                : `${filteredDetections}/${totalDetections}개 표시`}
            </Badge>
            {/* 렌더링 모드 토글 (SVG 오버레이가 있는 경우만) */}
            {svgOverlay && (
              <Button
                variant={renderMode === 'svg' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setRenderMode(renderMode === 'canvas' ? 'svg' : 'canvas')}
                title={renderMode === 'canvas' ? 'SVG 오버레이 모드로 전환' : 'Canvas 모드로 전환'}
              >
                {renderMode === 'canvas' ? (
                  <>
                    <Layers className="h-4 w-4 mr-1" />
                    SVG
                  </>
                ) : (
                  <>
                    <ImageIcon className="h-4 w-4 mr-1" />
                    Canvas
                  </>
                )}
              </Button>
            )}
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

        {/* 레이어 토글 컨트롤 */}
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
                style={{
                  backgroundColor: visible ? config.color : undefined,
                  borderColor: config.color,
                }}
              >
                <Icon className="h-3.5 w-3.5" />
                {config.label}
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

        {/* SVG 오버레이 모드 */}
        {renderMode === 'svg' && svgOverlay && (
          <div className="border rounded-lg overflow-auto bg-gray-50 dark:bg-gray-900">
            <div
              ref={containerRef}
              className="relative"
              style={{ width: svgOverlay.width, height: svgOverlay.height }}
            >
              {/* 배경 이미지 */}
              {imageDataUrl && (
                <img
                  src={imageDataUrl}
                  alt="Detection result"
                  className="absolute top-0 left-0 w-full h-full"
                  style={{ pointerEvents: 'none' }}
                />
              )}
              {/* SVG 오버레이 */}
              <div
                className="absolute top-0 left-0 w-full h-full"
                dangerouslySetInnerHTML={{ __html: svgOverlay.svg }}
                onMouseOver={handleSvgMouseOver}
                onMouseOut={handleSvgMouseOut}
              />
            </div>
            {/* 호버된 검출 정보 */}
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

        {/* Canvas 모드 */}
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
            {renderMode === 'canvas' ? '이미지를 클릭하면 확대해서 볼 수 있습니다' : 'SVG 모드에서는 호버로 상세 정보를 확인할 수 있습니다'}
          </p>
        )}

        {/* Comprehensive Legend */}
        {Object.keys(filteredClassCounts).length > 0 && (
          <div className="space-y-3 p-4 bg-accent/30 rounded-lg border">
            <h4 className="font-semibold text-sm">검출 클래스 범례</h4>

            {/* Dimensions Category */}
            {CLASS_CATEGORIES.dimensions.some(cls => filteredClassCounts[cls]) && (
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">📏 치수 (Dimensions)</p>
                <div className="grid grid-cols-2 gap-2">
                  {CLASS_CATEGORIES.dimensions.map((className) => {
                    const count = filteredClassCounts[className];
                    if (!count) return null;
                    const details = CLASS_DETAILS[className];
                    return (
                      <div key={className} className="flex items-center gap-2 text-xs">
                        <div
                          className="w-4 h-4 rounded flex-shrink-0"
                          style={{ backgroundColor: CLASS_COLORS[className] }}
                        ></div>
                        <span className="flex-1">
                          <span className="font-medium">{details.korean}</span>
                          <span className="text-muted-foreground"> ({details.english}, {details.abbr})</span>
                          <span className="text-blue-600 ml-1">· {count}개</span>
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* GD&T Category */}
            {CLASS_CATEGORIES.gdt.some(cls => filteredClassCounts[cls]) && (
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">🎯 GD&T (Geometric Dimensioning & Tolerancing)</p>
                <div className="grid grid-cols-2 gap-2">
                  {CLASS_CATEGORIES.gdt.map((className) => {
                    const count = filteredClassCounts[className];
                    if (!count) return null;
                    const details = CLASS_DETAILS[className];
                    return (
                      <div key={className} className="flex items-center gap-2 text-xs">
                        <div
                          className="w-4 h-4 rounded flex-shrink-0"
                          style={{ backgroundColor: CLASS_COLORS[className] }}
                        ></div>
                        <span className="flex-1">
                          <span className="font-medium">{details.korean}</span>
                          <span className="text-muted-foreground"> ({details.english}, {details.abbr})</span>
                          <span className="text-green-600 ml-1">· {count}개</span>
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Other Category */}
            {CLASS_CATEGORIES.other.some(cls => filteredClassCounts[cls]) && (
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">🔧 기타 (Other)</p>
                <div className="grid grid-cols-2 gap-2">
                  {CLASS_CATEGORIES.other.map((className) => {
                    const count = filteredClassCounts[className];
                    if (!count) return null;
                    const details = CLASS_DETAILS[className];
                    return (
                      <div key={className} className="flex items-center gap-2 text-xs">
                        <div
                          className="w-4 h-4 rounded flex-shrink-0"
                          style={{ backgroundColor: CLASS_COLORS[className] }}
                        ></div>
                        <span className="flex-1">
                          <span className="font-medium">{details.korean}</span>
                          <span className="text-muted-foreground"> ({details.english}, {details.abbr})</span>
                          <span className="text-orange-600 ml-1">· {count}개</span>
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

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

        {/* Selected Detection Panel */}
        {selectedDetection !== null && filteredBoundingBoxes[selectedDetection] && (
          <div className="p-4 bg-primary/10 border border-primary/30 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-semibold text-primary">선택된 객체</h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleSymbolClick(selectedDetection)}
                className="h-6 px-2"
              >
                선택 해제
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">클래스:</span>
                <span className="ml-2 font-medium">
                  {CLASS_DETAILS[filteredBoundingBoxes[selectedDetection].className]?.korean ||
                    filteredBoundingBoxes[selectedDetection].className}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">신뢰도:</span>
                <span className="ml-2 font-medium">
                  {(filteredBoundingBoxes[selectedDetection].confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">위치:</span>
                <span className="ml-2 font-mono text-xs">
                  ({Math.round(filteredBoundingBoxes[selectedDetection].x)},
                  {Math.round(filteredBoundingBoxes[selectedDetection].y)})
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">크기:</span>
                <span className="ml-2 font-mono text-xs">
                  {Math.round(filteredBoundingBoxes[selectedDetection].width)}×
                  {Math.round(filteredBoundingBoxes[selectedDetection].height)}
                </span>
              </div>
              {filteredBoundingBoxes[selectedDetection].extractedText && (
                <div className="col-span-2">
                  <span className="text-muted-foreground">추출 텍스트:</span>
                  <span className="ml-2 font-mono bg-accent/50 px-2 py-0.5 rounded">
                    {filteredBoundingBoxes[selectedDetection].extractedText}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Details List */}
        <div className="space-y-2">
          <h4 className="font-medium">
            검출된 객체 상세 ({filteredDetections === totalDetections
              ? `${totalDetections}개`
              : `${filteredDetections}/${totalDetections}개`})
            {onSymbolSelect && (
              <span className="text-xs text-muted-foreground ml-2">(클릭하여 선택)</span>
            )}
          </h4>
          <div className="max-h-64 overflow-y-auto space-y-1 text-sm">
            {filteredBoundingBoxes.map((box, index) => (
              <div
                key={index}
                onClick={() => handleSymbolClick(index)}
                className={`flex items-center gap-2 p-2 rounded transition-colors cursor-pointer ${
                  selectedDetection === index
                    ? 'bg-primary/20 border-2 border-primary'
                    : 'bg-accent/50 hover:bg-accent border-2 border-transparent'
                }`}
              >
                <div
                  className="w-3 h-3 rounded flex-shrink-0"
                  style={{ backgroundColor: box.color }}
                ></div>
                <div className="flex-1">
                  <span className="font-medium">{box.label}</span>
                  {box.extractedText && (
                    <div className="text-xs text-muted-foreground mt-0.5">
                      텍스트: "{box.extractedText}"
                    </div>
                  )}
                </div>
                <span className="text-muted-foreground text-xs whitespace-nowrap">
                  위치: ({Math.round(box.x)}, {Math.round(box.y)})
                </span>
                <span className="text-muted-foreground text-xs whitespace-nowrap">
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
