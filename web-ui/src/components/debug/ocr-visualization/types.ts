import type { LayerConfig } from '../../../hooks/useLayerToggle';
import { Hash, Square, Type } from 'lucide-react';
import type { OCRResult } from '../../../types/api';

// OCR 레이어 설정
export const OCR_LAYER_CONFIG: Record<string, LayerConfig> = {
  dimension: { label: '치수', color: '#3b82f6', icon: Hash, defaultVisible: true },
  gdt: { label: 'GD&T', color: '#10b981', icon: Square, defaultVisible: true },
  text: { label: '텍스트', color: '#f59e0b', icon: Type, defaultVisible: true },
};

export interface SVGOverlayData {
  svg: string;
  svg_minimal?: string;
  width: number;
  height: number;
  dimension_count?: number;
  gdt_count?: number;
  text_count?: number;
  detection_count?: number;
}

export interface OCRVisualizationProps {
  imageFile?: File;
  imageBase64?: string;
  ocrResult: OCRResult;
  /** SVG 오버레이 데이터 (API에서 include_svg=true로 받은 경우) */
  svgOverlay?: SVGOverlayData;
  /** 기본 렌더링 모드 */
  defaultMode?: 'canvas' | 'svg';
  onZoomClick?: (imageDataUrl: string) => void;
  compact?: boolean;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  type: 'dimension' | 'gdt' | 'text';
}
