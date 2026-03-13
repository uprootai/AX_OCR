import { useEffect, useRef, useState, useMemo } from 'react';
import { useLayerToggle } from '../../../hooks/useLayerToggle';
import {
  CLASS_COLORS,
  CLASS_NAMES,
  CLASS_CATEGORIES,
  YOLO_LAYER_CONFIG,
  parseBbox,
} from './types';
import type { BoundingBox, YOLOVisualizationProps } from './types';

export interface UseYOLOVisualizationReturn {
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  containerRef: React.RefObject<HTMLDivElement | null>;
  imageLoaded: boolean;
  boundingBoxes: BoundingBox[];
  filteredBoundingBoxes: BoundingBox[];
  renderMode: 'canvas' | 'svg';
  setRenderMode: (mode: 'canvas' | 'svg') => void;
  imageDataUrl: string | null;
  hoveredDetection: number | null;
  setHoveredDetection: (index: number | null) => void;
  selectedDetection: number | null;
  handleSymbolClick: (index: number) => void;
  handleCanvasClick: () => void;
  visibility: Record<string, boolean>;
  toggleLayer: (key: string) => void;
  showLabels: boolean;
  toggleLabels: () => void;
  layerConfigs: ReturnType<typeof useLayerToggle>['layerConfigs'];
  visibleCount: number;
  totalCount: number;
  filteredClassCounts: Record<string, number>;
  totalDetections: number;
  filteredDetections: number;
}

export function useYOLOVisualization({
  imageFile,
  detections,
  svgOverlay,
  defaultMode = 'canvas',
  onZoomClick,
  onSymbolSelect,
  selectedIndex: externalSelectedIndex,
}: YOLOVisualizationProps): UseYOLOVisualizationReturn {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [boundingBoxes, setBoundingBoxes] = useState<BoundingBox[]>([]);
  const [renderMode, setRenderMode] = useState<'canvas' | 'svg'>(svgOverlay ? defaultMode : 'canvas');
  const [imageDataUrl, setImageDataUrl] = useState<string | null>(null);
  const [hoveredDetection, setHoveredDetection] = useState<number | null>(null);
  const [internalSelectedIndex, setInternalSelectedIndex] = useState<number | null>(null);

  const selectedDetection = externalSelectedIndex !== undefined ? externalSelectedIndex : internalSelectedIndex;

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

  const getClassCategory = (className: string): keyof typeof YOLO_LAYER_CONFIG => {
    if (CLASS_CATEGORIES.dimensions.includes(className)) return 'dimensions';
    if (CLASS_CATEGORIES.gdt.includes(className)) return 'gdt';
    return 'other';
  };

  const filteredBoundingBoxes = useMemo(() => {
    return boundingBoxes.filter(box => {
      const category = getClassCategory(box.className);
      return visibility[category];
    });
  }, [boundingBoxes, visibility]);

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

  // Parse detections into BoundingBox list
  useEffect(() => {
    const boxes: BoundingBox[] = [];

    detections.forEach((det) => {
      const parsed = parseBbox(det.bbox);
      if (!parsed) return;

      const { x, y, width, height } = parsed;
      const className = det.class_name || det.class || 'unknown';
      const color = CLASS_COLORS[className] || '#6b7280';
      const koreanName = CLASS_NAMES[className] || className;
      const extractedText = det.extracted_text || det.value;

      let label = `${koreanName} (${(det.confidence * 100).toFixed(1)}%)`;
      if (extractedText && extractedText !== 'null') {
        const displayText = extractedText.length > 20 ? extractedText.substring(0, 20) + '...' : extractedText;
        label += ` - ${displayText}`;
      } else {
        label += ` [${Math.round(width)}×${Math.round(height)}]`;
      }

      boxes.push({ x, y, width, height, label, confidence: det.confidence, className, color, extractedText: extractedText || undefined });
    });

    boxes.sort((a, b) => b.confidence - a.confidence);
    setBoundingBoxes(boxes);
  }, [detections]);

  // SVG mode: load image as data URL
  useEffect(() => {
    if (!imageFile || renderMode !== 'svg') return;

    const reader = new FileReader();
    reader.onload = (e) => {
      setImageDataUrl(e.target?.result as string);
      setImageLoaded(true);
    };
    reader.readAsDataURL(imageFile);

    return () => { reader.abort(); };
  }, [imageFile, renderMode]);

  // Canvas mode: draw image + bounding boxes
  useEffect(() => {
    if (!imageFile || !canvasRef.current || renderMode !== 'canvas') return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    const url = URL.createObjectURL(imageFile);

    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);

      const scaleFactor = Math.max(1, Math.min(4, Math.max(img.width, img.height) / 1000));
      const fontSize = Math.round(11 * scaleFactor);
      const baseLineWidth = Math.round(2 * scaleFactor);
      const padding = Math.round(3 * scaleFactor);
      const labelHeight = Math.round(16 * scaleFactor);
      const gap = Math.round(2 * scaleFactor);

      const usedLabelPositions: Array<{ x: number; y: number; width: number; height: number }> = [];

      const checkLabelOverlap = (x: number, y: number, width: number, height: number): boolean =>
        usedLabelPositions.some(used =>
          !(x + width < used.x || x > used.x + used.width ||
            y + height < used.y || y > used.y + used.height)
        );

      filteredBoundingBoxes.forEach((box) => {
        const { x, y, width: boxWidth, height: boxHeight, color } = box;

        ctx.fillStyle = color + '40';
        ctx.fillRect(x, y, boxWidth, boxHeight);

        ctx.strokeStyle = color;
        ctx.lineWidth = box.className === 'text_block' ? baseLineWidth * 2 : baseLineWidth;
        ctx.strokeRect(x, y, boxWidth, boxHeight);

        ctx.font = `bold ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans", sans-serif`;
        const textMetrics = ctx.measureText(box.label);
        const labelWidth = textMetrics.width + padding * 2;

        let labelX = x;
        let labelY = y - labelHeight - gap;
        if (labelY < 0) labelY = y + boxHeight + gap;

        let attempts = 0;
        while (checkLabelOverlap(labelX, labelY, labelWidth, labelHeight) && attempts < 4) {
          attempts++;
          if (attempts === 1) { labelY = y + boxHeight + gap; }
          else if (attempts === 2) { labelX = x - labelWidth - gap; labelY = y; }
          else if (attempts === 3) { labelX = x + boxWidth + gap; labelY = y; }
        }

        if (labelX < gap) labelX = gap;
        if (labelY < gap) labelY = gap;
        if (labelX + labelWidth > canvas.width) labelX = canvas.width - labelWidth - gap;
        if (labelY + labelHeight > canvas.height) labelY = canvas.height - labelHeight - gap;

        if (showLabels) {
          ctx.fillStyle = color;
          ctx.fillRect(labelX, labelY, labelWidth, labelHeight);

          ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
          ctx.shadowBlur = scaleFactor;
          ctx.fillStyle = '#ffffff';
          ctx.textBaseline = 'top';
          ctx.fillText(box.label, labelX + padding, labelY + gap);
          ctx.shadowBlur = 0;

          usedLabelPositions.push({ x: labelX, y: labelY, width: labelWidth, height: labelHeight });
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

  const filteredClassCounts = filteredBoundingBoxes.reduce((acc, box) => {
    acc[box.className] = (acc[box.className] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return {
    canvasRef,
    containerRef,
    imageLoaded,
    boundingBoxes,
    filteredBoundingBoxes,
    renderMode,
    setRenderMode,
    imageDataUrl,
    hoveredDetection,
    setHoveredDetection,
    selectedDetection,
    handleSymbolClick,
    handleCanvasClick,
    visibility,
    toggleLayer,
    showLabels,
    toggleLabels,
    layerConfigs,
    visibleCount,
    totalCount,
    filteredClassCounts,
    totalDetections: boundingBoxes.length,
    filteredDetections: filteredBoundingBoxes.length,
  };
}
