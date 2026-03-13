/**
 * usePIDOverlay - P&ID 오버레이 상태 및 API 호출 훅
 */

import { useState, useCallback, useMemo, useRef } from 'react';
import type { OverlayData, PIDSymbol, PIDOverlayViewerProps } from './types';

export interface UsePIDOverlayReturn {
  image: string | null;
  overlayData: OverlayData | null;
  annotatedImage: string | null;
  isLoading: boolean;
  error: string | null;
  viewMode: 'svg' | 'image';
  zoom: number;
  hoveredItem: { type: string; data: unknown } | null;
  imageSize: { width: number; height: number };
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  containerRef: React.RefObject<HTMLDivElement | null>;
  setViewMode: (mode: 'svg' | 'image') => void;
  setHoveredItem: (item: { type: string; data: unknown } | null) => void;
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => Promise<void>;
  handleZoomIn: () => void;
  handleZoomOut: () => void;
  handleZoomReset: () => void;
  handleDownload: () => void;
}

type UsePIDOverlayOptions = Pick<PIDOverlayViewerProps, 'initialImage' | 'apiUrl' | 'onOverlayGenerated'>;

export function usePIDOverlay({
  initialImage,
  apiUrl = 'http://localhost:5019',
  onOverlayGenerated,
}: UsePIDOverlayOptions): UsePIDOverlayReturn {
  const [image, setImage] = useState<string | null>(initialImage || null);
  const [overlayData, setOverlayData] = useState<OverlayData | null>(null);
  const [_svgOverlay, setSvgOverlay] = useState<string | null>(null);
  const [annotatedImage, setAnnotatedImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'svg' | 'image'>('svg');
  const [zoom, setZoom] = useState(1);
  const [hoveredItem, setHoveredItem] = useState<{ type: string; data: unknown } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const imageSize = useMemo(() => {
    if (overlayData?.statistics.image_size) {
      return overlayData.statistics.image_size;
    }
    return { width: 1000, height: 800 };
  }, [overlayData]);

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

    // Call Design Checker API for symbol detection
    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('model_type', 'pid_class_aware');
      formData.append('confidence', '0.3');
      formData.append('use_sahi', 'true');
      formData.append('visualize', 'true');

      const response = await fetch(`${apiUrl}/api/v1/pipeline/detect`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const result = await response.json();

      if (result.success) {
        const detections = result.data?.detections || [];
        const symbols: PIDSymbol[] = detections.map((d: {
          class_name: string;
          class_id: number;
          confidence: number;
          bbox: import('./types').BBox;
        }) => ({
          class_id: d.class_id,
          class_name: d.class_name,
          confidence: d.confidence,
          bbox: d.bbox,
        }));

        const data: OverlayData = {
          symbols,
          lines: [],
          texts: [],
          regions: [],
          statistics: {
            image_size: { width: 1000, height: 800 },
            symbols_count: symbols.length,
            lines_count: 0,
            texts_count: 0,
            regions_count: 0,
          },
        };

        setOverlayData(data);
        setSvgOverlay(null);
        setAnnotatedImage(result.data?.visualized_image || null);
        onOverlayGenerated?.(data);
      } else {
        throw new Error(result.error || 'Unknown error');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to detect symbols');
    } finally {
      setIsLoading(false);
    }
  }, [apiUrl, onOverlayGenerated]);

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.5));
  const handleZoomReset = () => setZoom(1);

  const handleDownload = useCallback(() => {
    if (annotatedImage) {
      const link = document.createElement('a');
      link.href = `data:image/png;base64,${annotatedImage}`;
      link.download = 'pid_annotated.png';
      link.click();
    }
  }, [annotatedImage]);

  return {
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
  };
}
