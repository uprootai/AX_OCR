import { Hash, Square, Settings } from 'lucide-react';
import { type LayerConfig } from '../../../hooks/useLayerToggle';

// ─── Public Interfaces ───────────────────────────────────────────────────────

export interface SVGOverlayData {
  svg: string;
  svg_minimal?: string;
  width: number;
  height: number;
  detection_count: number;
  model_type?: string;
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
  extractedText?: string;
}

export interface YOLOVisualizationProps {
  imageFile: File;
  detections: Array<{
    class?: string;
    class_name?: string;
    confidence: number;
    bbox: number[] | { x: number; y: number; width: number; height: number };
    value?: string | null;
    extracted_text?: string | null;
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

// ─── Color / Name / Detail Constants ─────────────────────────────────────────

export const CLASS_COLORS: Record<string, string> = {
  // 치수
  diameter_dim: '#3b82f6',
  linear_dim: '#60a5fa',
  radius_dim: '#93c5fd',
  angular_dim: '#2563eb',
  chamfer_dim: '#1d4ed8',
  tolerance_dim: '#1e40af',
  reference_dim: '#8b5cf6',

  // GD&T
  flatness: '#10b981',
  cylindricity: '#34d399',
  position: '#6ee7b7',
  perpendicularity: '#059669',
  parallelism: '#047857',

  // 기타
  surface_roughness: '#f59e0b',
  text_block: '#ec4899',
};

export const CLASS_NAMES: Record<string, string> = {
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

export const CLASS_DETAILS: Record<string, { korean: string; english: string; abbr: string }> = {
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

export const CLASS_CATEGORIES = {
  dimensions: ['diameter_dim', 'linear_dim', 'radius_dim', 'angular_dim', 'chamfer_dim', 'tolerance_dim', 'reference_dim'],
  gdt: ['flatness', 'cylindricity', 'position', 'perpendicularity', 'parallelism'],
  other: ['surface_roughness', 'text_block'],
};

export const YOLO_LAYER_CONFIG: Record<string, LayerConfig> = {
  dimensions: { label: '치수', color: '#3b82f6', icon: Hash, defaultVisible: true },
  gdt: { label: 'GD&T', color: '#10b981', icon: Square, defaultVisible: true },
  other: { label: '기타', color: '#f59e0b', icon: Settings, defaultVisible: true },
};

// ─── Utility: parseBbox ───────────────────────────────────────────────────────

export function parseBbox(bbox: unknown): { x: number; y: number; width: number; height: number } | null {
  if (!bbox) return null;

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
