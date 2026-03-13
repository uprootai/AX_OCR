/**
 * PIDOverlayViewer - 타입 정의
 */

export interface BBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface PIDSymbol {
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: BBox;
}

export interface PIDLine {
  id: number;
  start_point: [number, number];
  end_point: [number, number];
  line_type: string;
  line_style?: string;
  waypoints?: [number, number][];
}

export interface TextItem {
  text: string;
  confidence: number;
  position: BBox;
  bbox?: number[][];
}

export interface Region {
  id: number;
  bbox: [number, number, number, number];
  region_type: string;
  region_type_korean?: string;
}

export interface OverlayData {
  symbols: PIDSymbol[];
  lines: PIDLine[];
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

// PID Layer 타입 (useLayerToggle에서 사용)
export type PIDLayerKey = 'symbols' | 'lines' | 'texts' | 'regions';

export const LINE_TYPE_COLORS: Record<string, string> = {
  pipe: '#ff0000',
  signal: '#0000ff',
  unknown: '#00ff00',
};

export interface PIDOverlayViewerProps {
  initialImage?: string;
  /** Design Checker API URL (default: http://localhost:5019) */
  apiUrl?: string;
  onOverlayGenerated?: (data: OverlayData) => void;
}
