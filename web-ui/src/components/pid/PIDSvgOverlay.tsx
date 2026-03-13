/**
 * PIDSvgOverlay - P&ID 도면 SVG 오버레이 레이어 렌더러
 */

import type { OverlayData, PIDLayerKey } from './types';
import { LINE_TYPE_COLORS } from './types';

interface PIDSvgOverlayProps {
  overlayData: OverlayData;
  imageSize: { width: number; height: number };
  visibility: Record<PIDLayerKey, boolean>;
  showLabels: boolean;
  zoom: number;
  onHover: (item: { type: string; data: unknown } | null) => void;
}

export function PIDSvgOverlay({
  overlayData,
  imageSize,
  visibility,
  showLabels,
  zoom,
  onHover,
}: PIDSvgOverlayProps) {
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
              onMouseEnter={() => onHover({ type: 'region', data: region })}
              onMouseLeave={() => onHover(null)}
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
              onMouseEnter={() => onHover({ type: 'line', data: line })}
              onMouseLeave={() => onHover(null)}
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
            onMouseEnter={() => onHover({ type: 'line', data: line })}
            onMouseLeave={() => onHover(null)}
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
            onMouseEnter={() => onHover({ type: 'symbol', data: symbol })}
            onMouseLeave={() => onHover(null)}
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
            onMouseEnter={() => onHover({ type: 'text', data: text })}
            onMouseLeave={() => onHover(null)}
          />
        </g>
      ))}
    </svg>
  );
}
