/**
 * LineOverlay - 선 검출 결과 오버레이 컴포넌트
 *
 * 이미지 위에 검출된 선을 시각화
 * - 선 유형별 색상 구분
 * - 교차점 표시
 * - 치수선 강조
 */

import { useMemo } from 'react';

interface Point {
  x: number;
  y: number;
}

interface Line {
  id: string;
  start: Point;
  end: Point;
  length: number;
  angle: number;
  line_type: string;
  line_style: string;
  color?: string;
  confidence: number;
  thickness?: number;
}

interface Intersection {
  id: string;
  point: Point;
  line_ids: string[];
  intersection_type?: string;
}

interface LineOverlayProps {
  lines: Line[];
  intersections?: Intersection[];
  imageWidth: number;
  imageHeight: number;
  containerWidth: number;
  containerHeight: number;
  showIntersections?: boolean;
  showLabels?: boolean;
  highlightedLineId?: string | null;
  onLineHover?: (lineId: string | null) => void;
  onLineClick?: (lineId: string) => void;
}

// 선 유형별 색상
const LINE_TYPE_COLORS: Record<string, string> = {
  process: '#3b82f6',      // blue - 공정 배관
  cooling: '#06b6d4',      // cyan - 냉각
  steam: '#f97316',        // orange - 증기
  signal: '#8b5cf6',       // purple - 신호선
  electrical: '#f59e0b',   // amber - 전기
  dimension: '#22c55e',    // green - 치수선
  extension: '#84cc16',    // lime - 연장선
  leader: '#14b8a6',       // teal - 지시선
  unknown: '#6b7280',      // gray - 미분류
};

// 선 스타일
const LINE_STYLE_PATTERNS: Record<string, string> = {
  solid: '',
  dashed: '8,4',
  dotted: '2,4',
  chain: '12,4,2,4',
  double_chain: '12,4,2,4,2,4',
  unknown: '',
};

export function LineOverlay({
  lines,
  intersections = [],
  imageWidth,
  imageHeight,
  containerWidth,
  containerHeight,
  showIntersections = true,
  showLabels = false,
  highlightedLineId,
  onLineHover,
  onLineClick,
}: LineOverlayProps) {
  // 스케일 계산
  const scale = useMemo(() => {
    const scaleX = containerWidth / imageWidth;
    const scaleY = containerHeight / imageHeight;
    return Math.min(scaleX, scaleY);
  }, [containerWidth, containerHeight, imageWidth, imageHeight]);

  // 오프셋 계산 (중앙 정렬)
  const offset = useMemo(() => {
    const scaledWidth = imageWidth * scale;
    const scaledHeight = imageHeight * scale;
    return {
      x: (containerWidth - scaledWidth) / 2,
      y: (containerHeight - scaledHeight) / 2,
    };
  }, [containerWidth, containerHeight, imageWidth, imageHeight, scale]);

  // 좌표 변환 함수
  const transformPoint = (point: Point) => ({
    x: point.x * scale + offset.x,
    y: point.y * scale + offset.y,
  });

  // 통계
  const stats = useMemo(() => {
    const byType: Record<string, number> = {};
    lines.forEach((line) => {
      const type = line.line_type || 'unknown';
      byType[type] = (byType[type] || 0) + 1;
    });
    return byType;
  }, [lines]);

  if (lines.length === 0) {
    return null;
  }

  return (
    <div className="relative" style={{ width: containerWidth, height: containerHeight }}>
      {/* SVG 오버레이 */}
      <svg
        width={containerWidth}
        height={containerHeight}
        className="absolute top-0 left-0 pointer-events-none"
        style={{ zIndex: 10 }}
      >
        {/* 선 그리기 */}
        {lines.map((line) => {
          const start = transformPoint(line.start);
          const end = transformPoint(line.end);
          const color = LINE_TYPE_COLORS[line.line_type] || LINE_TYPE_COLORS.unknown;
          const dashArray = LINE_STYLE_PATTERNS[line.line_style] || '';
          const isHighlighted = highlightedLineId === line.id;
          const strokeWidth = isHighlighted ? 3 : (line.thickness ? line.thickness * scale : 1.5);

          return (
            <g key={line.id}>
              <line
                x1={start.x}
                y1={start.y}
                x2={end.x}
                y2={end.y}
                stroke={line.color || color}
                strokeWidth={strokeWidth}
                strokeDasharray={dashArray}
                strokeLinecap="round"
                opacity={isHighlighted ? 1 : 0.7}
                className="pointer-events-auto cursor-pointer transition-all duration-150"
                style={{ filter: isHighlighted ? 'drop-shadow(0 0 4px rgba(255,255,255,0.8))' : 'none' }}
                onMouseEnter={() => onLineHover?.(line.id)}
                onMouseLeave={() => onLineHover?.(null)}
                onClick={() => onLineClick?.(line.id)}
              />
              {/* 라벨 (선택적) */}
              {showLabels && (
                <text
                  x={(start.x + end.x) / 2}
                  y={(start.y + end.y) / 2 - 4}
                  fill={color}
                  fontSize={10}
                  textAnchor="middle"
                  className="pointer-events-none"
                >
                  {line.line_type}
                </text>
              )}
            </g>
          );
        })}

        {/* 교차점 그리기 */}
        {showIntersections && intersections.map((intersection) => {
          const point = transformPoint(intersection.point);

          return (
            <g key={intersection.id}>
              <circle
                cx={point.x}
                cy={point.y}
                r={4}
                fill="#ef4444"
                stroke="#fff"
                strokeWidth={1.5}
                opacity={0.8}
              />
              {intersection.intersection_type && (
                <text
                  x={point.x + 6}
                  y={point.y + 3}
                  fill="#ef4444"
                  fontSize={8}
                  fontWeight="bold"
                >
                  {intersection.intersection_type}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      {/* 범례 */}
      <div className="absolute bottom-2 left-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
        <div className="flex items-center gap-3">
          {Object.entries(stats).slice(0, 4).map(([type, count]) => (
            <div key={type} className="flex items-center gap-1">
              <span
                className="w-3 h-0.5 inline-block"
                style={{ backgroundColor: LINE_TYPE_COLORS[type] || LINE_TYPE_COLORS.unknown }}
              />
              <span>{type}: {count}</span>
            </div>
          ))}
          <span className="text-gray-300">총 {lines.length}개</span>
        </div>
      </div>
    </div>
  );
}

export default LineOverlay;
