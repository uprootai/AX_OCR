/**
 * 공통 SVG 오버레이 유틸리티
 *
 * PID Composer의 SVG 오버레이 패턴을 다른 노드에도 적용하기 위한 공통 모듈
 * - YOLO Detection
 * - Line Detector
 * - OCR Results
 * - Blueprint AI BOM
 */

// ============ Types ============

export interface BBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Point {
  x: number;
  y: number;
}

export interface BBoxItem {
  id?: string;
  bbox: BBox;
  label?: string;
  confidence?: number;
  color?: string;
  category?: string;
  metadata?: Record<string, unknown>;
}

export interface LineItem {
  id?: string;
  start: Point;
  end: Point;
  label?: string;
  lineType?: 'solid' | 'dashed' | 'dotted' | 'dash-dot';
  color?: string;
  strokeWidth?: number;
  category?: string;
  metadata?: Record<string, unknown>;
}

export interface TextItem {
  id?: string;
  position: Point;
  text: string;
  bbox?: BBox;
  color?: string;
  fontSize?: number;
  category?: string;
  metadata?: Record<string, unknown>;
}

export interface OverlayOptions {
  width: number;
  height: number;
  interactive?: boolean;
  showLabels?: boolean;
  showConfidence?: boolean;
  defaultColor?: string;
  strokeWidth?: number;
  opacity?: number;
  className?: string;
}

export interface LayerConfig {
  visible: boolean;
  opacity: number;
  color?: string;
}

export interface OverlayLayers {
  bboxes?: LayerConfig;
  lines?: LayerConfig;
  texts?: LayerConfig;
}

// ============ Default Styles ============

export const DEFAULT_COLORS: Record<string, string> = {
  detection: '#3b82f6', // blue
  symbol: '#10b981', // green
  line: '#ef4444', // red
  text: '#f59e0b', // amber
  region: '#8b5cf6', // purple
  // P&ID 라인 타입별 색상
  pipe: '#FF0000',
  signal: '#0000FF',
  dashed: '#808080',
  instrument: '#00FF00',
  // OCR 텍스트 타입별 색상
  dimension: '#FFA500',
  tag: '#00CED1',
  note: '#9370DB',
};

export const LINE_STYLES: Record<string, string> = {
  solid: 'none',
  dashed: '8,4',
  dotted: '2,2',
  'dash-dot': '8,4,2,4',
};

// ============ SVG Generation ============

/**
 * SVG 오버레이 생성
 */
export function createSvgOverlay(
  items: {
    bboxes?: BBoxItem[];
    lines?: LineItem[];
    texts?: TextItem[];
  },
  options: OverlayOptions
): string {
  const {
    width,
    height,
    interactive = true,
    showLabels = true,
    showConfidence = false,
    defaultColor = '#3b82f6',
    strokeWidth = 2,
    opacity = 0.8,
    className = 'detection-overlay',
  } = options;

  const parts: string[] = [];

  // SVG 시작
  parts.push(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" class="${className}">`
  );

  // 스타일 정의
  parts.push(generateStyles(interactive, opacity));

  // 바운딩 박스 렌더링
  if (items.bboxes) {
    parts.push('<g class="layer-bboxes">');
    items.bboxes.forEach((item, index) => {
      parts.push(renderBBox(item, index, { showLabels, showConfidence, defaultColor, strokeWidth }));
    });
    parts.push('</g>');
  }

  // 라인 렌더링
  if (items.lines) {
    parts.push('<g class="layer-lines">');
    items.lines.forEach((item, index) => {
      parts.push(renderLine(item, index, { defaultColor, strokeWidth }));
    });
    parts.push('</g>');
  }

  // 텍스트 렌더링
  if (items.texts) {
    parts.push('<g class="layer-texts">');
    items.texts.forEach((item, index) => {
      parts.push(renderText(item, index, { defaultColor }));
    });
    parts.push('</g>');
  }

  parts.push('</svg>');

  return parts.join('\n');
}

/**
 * SVG 스타일 생성
 */
function generateStyles(interactive: boolean, opacity: number): string {
  const hoverStyles = interactive
    ? `
    .overlay-item:hover {
      stroke-width: 3;
      filter: brightness(1.2);
    }
    .overlay-item:hover .overlay-label {
      display: block;
    }
  `
    : '';

  return `
  <style>
    .overlay-item {
      opacity: ${opacity};
      transition: all 0.2s ease;
      cursor: ${interactive ? 'pointer' : 'default'};
    }
    .overlay-label {
      font-family: 'Pretendard', sans-serif;
      font-size: 12px;
      fill: white;
      pointer-events: none;
    }
    .overlay-label-bg {
      opacity: 0.8;
    }
    ${hoverStyles}
  </style>
  `;
}

/**
 * 바운딩 박스 렌더링
 */
function renderBBox(
  item: BBoxItem,
  index: number,
  options: {
    showLabels: boolean;
    showConfidence: boolean;
    defaultColor: string;
    strokeWidth: number;
  }
): string {
  const { bbox, label, confidence, color, category, metadata } = item;
  const itemColor = color || DEFAULT_COLORS[category || ''] || options.defaultColor;
  const id = item.id || `bbox-${index}`;

  // 메타데이터를 data-* 속성으로 변환
  const dataAttrs = metadata
    ? Object.entries(metadata)
        .map(([key, value]) => `data-${key}="${String(value)}"`)
        .join(' ')
    : '';

  let labelText = label || '';
  if (options.showConfidence && confidence !== undefined) {
    labelText += ` (${(confidence * 100).toFixed(1)}%)`;
  }

  const labelElement = options.showLabels && labelText
    ? `
    <rect class="overlay-label-bg" x="${bbox.x}" y="${bbox.y - 20}" width="${labelText.length * 8 + 8}" height="18" fill="${itemColor}" rx="2"/>
    <text class="overlay-label" x="${bbox.x + 4}" y="${bbox.y - 6}">${escapeHtml(labelText)}</text>
  `
    : '';

  return `
  <g class="overlay-item overlay-bbox" id="${id}" data-category="${category || ''}" ${dataAttrs}>
    <rect x="${bbox.x}" y="${bbox.y}" width="${bbox.width}" height="${bbox.height}"
          fill="none" stroke="${itemColor}" stroke-width="${options.strokeWidth}"/>
    ${labelElement}
  </g>
  `;
}

/**
 * 라인 렌더링
 */
function renderLine(
  item: LineItem,
  index: number,
  options: { defaultColor: string; strokeWidth: number }
): string {
  const { start, end, label, lineType = 'solid', color, strokeWidth, category, metadata } = item;
  const itemColor = color || DEFAULT_COLORS[category || ''] || options.defaultColor;
  const width = strokeWidth || options.strokeWidth;
  const dashArray = LINE_STYLES[lineType] || 'none';
  const id = item.id || `line-${index}`;

  const dataAttrs = metadata
    ? Object.entries(metadata)
        .map(([key, value]) => `data-${key}="${String(value)}"`)
        .join(' ')
    : '';

  // 라인 중간점에 라벨 표시
  const midX = (start.x + end.x) / 2;
  const midY = (start.y + end.y) / 2;

  const labelElement = label
    ? `
    <rect class="overlay-label-bg" x="${midX - label.length * 4}" y="${midY - 18}" width="${label.length * 8 + 8}" height="18" fill="${itemColor}" rx="2"/>
    <text class="overlay-label" x="${midX - label.length * 4 + 4}" y="${midY - 4}">${escapeHtml(label)}</text>
  `
    : '';

  return `
  <g class="overlay-item overlay-line" id="${id}" data-category="${category || ''}" data-line-type="${lineType}" ${dataAttrs}>
    <line x1="${start.x}" y1="${start.y}" x2="${end.x}" y2="${end.y}"
          stroke="${itemColor}" stroke-width="${width}" stroke-dasharray="${dashArray}"/>
    ${labelElement}
  </g>
  `;
}

/**
 * 텍스트 렌더링
 */
function renderText(
  item: TextItem,
  index: number,
  options: { defaultColor: string }
): string {
  const { position, text, bbox, color, fontSize = 12, category, metadata } = item;
  const itemColor = color || DEFAULT_COLORS[category || ''] || options.defaultColor;
  const id = item.id || `text-${index}`;

  const dataAttrs = metadata
    ? Object.entries(metadata)
        .map(([key, value]) => `data-${key}="${String(value)}"`)
        .join(' ')
    : '';

  // bbox가 있으면 하이라이트 박스 그리기
  const bboxElement = bbox
    ? `<rect x="${bbox.x}" y="${bbox.y}" width="${bbox.width}" height="${bbox.height}"
            fill="${itemColor}" fill-opacity="0.2" stroke="${itemColor}" stroke-width="1"/>`
    : '';

  return `
  <g class="overlay-item overlay-text" id="${id}" data-category="${category || ''}" ${dataAttrs}>
    ${bboxElement}
    <text x="${position.x}" y="${position.y}" font-size="${fontSize}" fill="${itemColor}">
      ${escapeHtml(text)}
    </text>
  </g>
  `;
}

// ============ SVG Parsing ============

/**
 * SVG 오버레이에서 바운딩 박스 데이터 파싱
 */
export function parseSvgOverlay(svg: string): BBoxItem[] {
  const items: BBoxItem[] = [];
  const parser = new DOMParser();
  const doc = parser.parseFromString(svg, 'image/svg+xml');

  // 바운딩 박스 파싱
  const bboxGroups = doc.querySelectorAll('.overlay-bbox');
  bboxGroups.forEach((group) => {
    const rect = group.querySelector('rect:not(.overlay-label-bg)');
    if (!rect) return;

    const x = parseFloat(rect.getAttribute('x') || '0');
    const y = parseFloat(rect.getAttribute('y') || '0');
    const width = parseFloat(rect.getAttribute('width') || '0');
    const height = parseFloat(rect.getAttribute('height') || '0');

    const labelText = group.querySelector('.overlay-label')?.textContent || '';
    const category = group.getAttribute('data-category') || undefined;

    // 메타데이터 추출
    const metadata: Record<string, unknown> = {};
    Array.from(group.attributes).forEach((attr) => {
      if (attr.name.startsWith('data-') && attr.name !== 'data-category') {
        const key = attr.name.replace('data-', '');
        metadata[key] = attr.value;
      }
    });

    items.push({
      id: group.id,
      bbox: { x, y, width, height },
      label: labelText,
      category,
      metadata: Object.keys(metadata).length > 0 ? metadata : undefined,
    });
  });

  return items;
}

// ============ Utilities ============

/**
 * HTML 이스케이프
 */
function escapeHtml(text: string): string {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}

/**
 * SVG를 Data URL로 변환
 */
export function svgToDataUrl(svg: string): string {
  const encoded = encodeURIComponent(svg);
  return `data:image/svg+xml,${encoded}`;
}

/**
 * 바운딩 박스 정규화 (퍼센트 → 픽셀)
 */
export function normalizeBBox(
  bbox: BBox,
  imageWidth: number,
  imageHeight: number,
  isPercent = false
): BBox {
  if (!isPercent) return bbox;

  return {
    x: bbox.x * imageWidth,
    y: bbox.y * imageHeight,
    width: bbox.width * imageWidth,
    height: bbox.height * imageHeight,
  };
}

/**
 * YOLO 검출 결과를 BBoxItem으로 변환
 */
export function yoloDetectionsToBBoxItems(
  detections: Array<{
    class_id: number;
    class_name: string;
    confidence: number;
    bbox: { x: number; y: number; width: number; height: number };
  }>
): BBoxItem[] {
  return detections.map((det, index) => ({
    id: `yolo-${index}`,
    bbox: det.bbox,
    label: det.class_name,
    confidence: det.confidence,
    category: 'detection',
    color: DEFAULT_COLORS.detection,
    metadata: { class_id: det.class_id },
  }));
}

/**
 * OCR 결과를 TextItem으로 변환
 */
export function ocrResultsToTextItems(
  results: Array<{
    text: string;
    confidence: number;
    bbox: { x: number; y: number; width: number; height: number };
    category?: string;
  }>
): TextItem[] {
  return results.map((result, index) => ({
    id: `ocr-${index}`,
    position: { x: result.bbox.x, y: result.bbox.y + result.bbox.height },
    text: result.text,
    bbox: result.bbox,
    category: result.category || 'text',
    color: DEFAULT_COLORS[result.category || 'text'],
    metadata: { confidence: result.confidence },
  }));
}

/**
 * 라인 검출 결과를 LineItem으로 변환
 */
export function lineDetectionToLineItems(
  lines: Array<{
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    line_type?: string;
    category?: string;
  }>
): LineItem[] {
  return lines.map((line, index) => ({
    id: `line-${index}`,
    start: { x: line.x1, y: line.y1 },
    end: { x: line.x2, y: line.y2 },
    lineType: (line.line_type as LineItem['lineType']) || 'solid',
    category: line.category || 'line',
    color: DEFAULT_COLORS[line.category || 'line'],
  }));
}
