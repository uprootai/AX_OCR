/**
 * svgOverlay.ts 단위 테스트
 */
import { describe, it, expect } from 'vitest';
import {
  createSvgOverlay,
  parseSvgOverlay,
  svgToDataUrl,
  normalizeBBox,
  yoloDetectionsToBBoxItems,
  ocrResultsToTextItems,
  lineDetectionToLineItems,
  DEFAULT_COLORS,
  LINE_STYLES,
  type BBoxItem,
  type LineItem,
  type TextItem,
  type OverlayOptions,
} from './svgOverlay';

describe('svgOverlay', () => {
  const defaultOptions: OverlayOptions = {
    width: 1000,
    height: 800,
    interactive: true,
    showLabels: true,
  };

  describe('createSvgOverlay', () => {
    it('빈 아이템으로 기본 SVG 생성', () => {
      const svg = createSvgOverlay({}, defaultOptions);

      expect(svg).toContain('<svg');
      expect(svg).toContain('viewBox="0 0 1000 800"');
      expect(svg).toContain('</svg>');
    });

    it('바운딩 박스가 포함된 SVG 생성', () => {
      const bboxes: BBoxItem[] = [
        {
          id: 'test-1',
          bbox: { x: 100, y: 100, width: 200, height: 150 },
          label: 'Test Label',
          confidence: 0.95,
          category: 'detection',
        },
      ];

      const svg = createSvgOverlay({ bboxes }, defaultOptions);

      expect(svg).toContain('class="layer-bboxes"');
      expect(svg).toContain('id="test-1"');
      expect(svg).toContain('x="100"');
      expect(svg).toContain('y="100"');
      expect(svg).toContain('width="200"');
      expect(svg).toContain('height="150"');
      expect(svg).toContain('Test Label');
    });

    it('라인이 포함된 SVG 생성', () => {
      const lines: LineItem[] = [
        {
          id: 'line-1',
          start: { x: 0, y: 0 },
          end: { x: 100, y: 100 },
          lineType: 'dashed',
          category: 'pipe',
        },
      ];

      const svg = createSvgOverlay({ lines }, defaultOptions);

      expect(svg).toContain('class="layer-lines"');
      expect(svg).toContain('x1="0"');
      expect(svg).toContain('y1="0"');
      expect(svg).toContain('x2="100"');
      expect(svg).toContain('y2="100"');
      expect(svg).toContain('stroke-dasharray="8,4"');
    });

    it('텍스트가 포함된 SVG 생성', () => {
      const texts: TextItem[] = [
        {
          id: 'text-1',
          position: { x: 50, y: 50 },
          text: 'Sample Text',
          category: 'dimension',
        },
      ];

      const svg = createSvgOverlay({ texts }, defaultOptions);

      expect(svg).toContain('class="layer-texts"');
      expect(svg).toContain('Sample Text');
      expect(svg).toContain('x="50"');
      expect(svg).toContain('y="50"');
    });

    it('신뢰도 표시 옵션이 작동함', () => {
      const bboxes: BBoxItem[] = [
        {
          bbox: { x: 100, y: 100, width: 200, height: 150 },
          label: 'Test',
          confidence: 0.85,
        },
      ];

      const svg = createSvgOverlay(
        { bboxes },
        { ...defaultOptions, showConfidence: true }
      );

      expect(svg).toContain('85.0%');
    });

    it('HTML 특수문자가 이스케이프됨', () => {
      const bboxes: BBoxItem[] = [
        {
          bbox: { x: 0, y: 0, width: 100, height: 100 },
          label: '<script>alert("xss")</script>',
        },
      ];

      const svg = createSvgOverlay({ bboxes }, defaultOptions);

      expect(svg).not.toContain('<script>');
      expect(svg).toContain('&lt;script&gt;');
    });
  });

  describe('parseSvgOverlay', () => {
    it('바운딩 박스를 파싱함', () => {
      const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 800">
          <g class="overlay-item overlay-bbox" id="bbox-0" data-category="detection">
            <rect x="100" y="200" width="300" height="400" fill="none" stroke="#3b82f6"/>
            <text class="overlay-label">Test Label</text>
          </g>
        </svg>
      `;

      const items = parseSvgOverlay(svg);

      expect(items).toHaveLength(1);
      expect(items[0].id).toBe('bbox-0');
      expect(items[0].bbox.x).toBe(100);
      expect(items[0].bbox.y).toBe(200);
      expect(items[0].bbox.width).toBe(300);
      expect(items[0].bbox.height).toBe(400);
      expect(items[0].category).toBe('detection');
    });
  });

  describe('svgToDataUrl', () => {
    it('SVG를 Data URL로 변환', () => {
      const svg = '<svg><rect/></svg>';
      const dataUrl = svgToDataUrl(svg);

      expect(dataUrl.startsWith('data:image/svg+xml,')).toBe(true);
      expect(dataUrl).toContain(encodeURIComponent('<svg>'));
    });
  });

  describe('normalizeBBox', () => {
    it('픽셀 값은 그대로 반환', () => {
      const bbox = { x: 100, y: 200, width: 300, height: 400 };
      const result = normalizeBBox(bbox, 1000, 800, false);

      expect(result).toEqual(bbox);
    });

    it('퍼센트를 픽셀로 변환', () => {
      const bbox = { x: 0.1, y: 0.2, width: 0.3, height: 0.4 };
      const result = normalizeBBox(bbox, 1000, 800, true);

      expect(result.x).toBe(100);
      expect(result.y).toBe(160);
      expect(result.width).toBe(300);
      expect(result.height).toBe(320);
    });
  });

  describe('yoloDetectionsToBBoxItems', () => {
    it('YOLO 검출 결과를 BBoxItem으로 변환', () => {
      const detections = [
        {
          class_id: 0,
          class_name: 'valve',
          confidence: 0.95,
          bbox: { x: 100, y: 100, width: 50, height: 50 },
        },
        {
          class_id: 1,
          class_name: 'pump',
          confidence: 0.87,
          bbox: { x: 200, y: 200, width: 80, height: 60 },
        },
      ];

      const items = yoloDetectionsToBBoxItems(detections);

      expect(items).toHaveLength(2);
      expect(items[0].id).toBe('yolo-0');
      expect(items[0].label).toBe('valve');
      expect(items[0].confidence).toBe(0.95);
      expect(items[0].category).toBe('detection');
      expect(items[0].metadata?.class_id).toBe(0);
    });
  });

  describe('ocrResultsToTextItems', () => {
    it('OCR 결과를 TextItem으로 변환', () => {
      const results = [
        {
          text: '100mm',
          confidence: 0.99,
          bbox: { x: 50, y: 50, width: 100, height: 20 },
          category: 'dimension',
        },
      ];

      const items = ocrResultsToTextItems(results);

      expect(items).toHaveLength(1);
      expect(items[0].id).toBe('ocr-0');
      expect(items[0].text).toBe('100mm');
      expect(items[0].category).toBe('dimension');
      expect(items[0].color).toBe(DEFAULT_COLORS.dimension);
    });
  });

  describe('lineDetectionToLineItems', () => {
    it('라인 검출 결과를 LineItem으로 변환', () => {
      const lines = [
        { x1: 0, y1: 0, x2: 100, y2: 100, line_type: 'dashed', category: 'pipe' },
      ];

      const items = lineDetectionToLineItems(lines);

      expect(items).toHaveLength(1);
      expect(items[0].id).toBe('line-0');
      expect(items[0].start).toEqual({ x: 0, y: 0 });
      expect(items[0].end).toEqual({ x: 100, y: 100 });
      expect(items[0].lineType).toBe('dashed');
      expect(items[0].color).toBe(DEFAULT_COLORS.pipe);
    });
  });

  describe('DEFAULT_COLORS', () => {
    it('주요 카테고리 색상이 정의됨', () => {
      expect(DEFAULT_COLORS.detection).toBeDefined();
      expect(DEFAULT_COLORS.symbol).toBeDefined();
      expect(DEFAULT_COLORS.line).toBeDefined();
      expect(DEFAULT_COLORS.text).toBeDefined();
      expect(DEFAULT_COLORS.pipe).toBeDefined();
    });
  });

  describe('LINE_STYLES', () => {
    it('라인 스타일이 정의됨', () => {
      expect(LINE_STYLES.solid).toBe('none');
      expect(LINE_STYLES.dashed).toBe('8,4');
      expect(LINE_STYLES.dotted).toBe('2,2');
      expect(LINE_STYLES['dash-dot']).toBe('8,4,2,4');
    });
  });
});
