/**
 * GeometryDebugOverlay — 기하학 디버그 정보를 도면 위에 SVG 오버레이로 시각화
 *
 * 레이어:
 * - Circles: 검출된 원 (cyan 점선)
 * - Dim Lines: 치수선 (녹색 + 끝점 마커)
 * - ROIs: OCR 영역 (노란 점선)
 * - Endpoints: 중심/원주점 (빨강/파랑)
 * - Symbols: R/Ø 심볼 위치 (마젠타)
 * - Rays: 레이캐스트 경로 (주황 화살표)
 */
import { useState } from 'react';
import type { GeometryDebugInfo } from './types';

interface Props {
  debug: GeometryDebugInfo;
  imageWidth: number;
  imageHeight: number;
  scaledHeight: number;
}

const LAYERS = [
  { key: 'circles', label: 'Circles', color: '#06b6d4' },
  { key: 'dimLines', label: 'Dim Lines', color: '#22c55e' },
  { key: 'rois', label: 'ROIs', color: '#eab308' },
  { key: 'endpoints', label: 'Endpoints', color: '#ef4444' },
  { key: 'symbols', label: 'Symbols', color: '#d946ef' },
  { key: 'rays', label: 'Rays', color: '#f97316' },
] as const;

type LayerKey = (typeof LAYERS)[number]['key'];

export function GeometryDebugOverlay({ debug, imageWidth, imageHeight, scaledHeight }: Props) {
  const [visible, setVisible] = useState<Record<LayerKey, boolean>>({
    circles: true, dimLines: true, rois: true,
    endpoints: true, symbols: true, rays: true,
  });
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  const toggle = (key: LayerKey) =>
    setVisible((prev) => ({ ...prev, [key]: !prev[key] }));

  const hasData = debug.circles.length > 0 || debug.dim_lines.length > 0 ||
    debug.rois.length > 0 || debug.rays.length > 0 || debug.symbols_found.length > 0;

  if (!hasData) return null;

  return (
    <div className="mt-3">
      {/* 레이어 토글 */}
      <div className="flex flex-wrap items-center gap-3 mb-2 px-1">
        <span className="text-xs font-semibold text-gray-500 dark:text-gray-400">Debug Layers:</span>
        {LAYERS.map((layer) => (
          <label key={layer.key} className="flex items-center gap-1.5 text-xs cursor-pointer select-none">
            <input
              type="checkbox"
              checked={visible[layer.key]}
              onChange={() => toggle(layer.key)}
              className="rounded"
            />
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: layer.color }} />
            <span className="text-gray-600 dark:text-gray-300">{layer.label}</span>
            <span className="text-gray-400">
              ({layer.key === 'circles' ? debug.circles.length
                : layer.key === 'dimLines' ? debug.dim_lines.length
                : layer.key === 'rois' ? debug.rois.length
                : layer.key === 'rays' ? debug.rays.length
                : layer.key === 'symbols' ? debug.symbols_found.length
                : debug.dim_lines.length})
            </span>
          </label>
        ))}
      </div>

      {/* SVG 오버레이 */}
      <svg
        className="absolute top-0 left-0 w-full pointer-events-none"
        style={{ height: scaledHeight }}
        viewBox={`0 0 ${imageWidth} ${imageHeight}`}
        preserveAspectRatio="xMinYMin meet"
      >
        {/* Circles (cyan 점선) */}
        {visible.circles && debug.circles.map((c, idx) => (
          <g key={`circle-${idx}`}>
            <circle
              cx={c.cx} cy={c.cy} r={c.radius}
              fill="none" stroke="#06b6d4" strokeWidth={2}
              strokeDasharray="8,4" opacity={0.7}
            />
            <circle cx={c.cx} cy={c.cy} r={4} fill="#06b6d4" opacity={0.8} />
            <text x={c.cx + 8} y={c.cy - 8} fill="#06b6d4" fontSize={12} fontWeight="bold" opacity={0.8}>
              r={Math.round(c.radius)}
            </text>
          </g>
        ))}

        {/* Dim Lines (녹색 + 끝점) */}
        {visible.dimLines && debug.dim_lines.map((dl, idx) => (
          <g key={`dimline-${idx}`}>
            <line
              x1={dl.x1} y1={dl.y1} x2={dl.x2} y2={dl.y2}
              stroke="#22c55e" strokeWidth={2} opacity={0.7}
            />
            {/* Endpoints */}
            {visible.endpoints && (
              <>
                <circle
                  cx={dl.x1} cy={dl.y1} r={5}
                  fill={dl.endpoint_type === 'center' ? '#ef4444' : dl.endpoint_type === 'circumference' ? '#3b82f6' : '#9ca3af'}
                  opacity={0.9}
                  style={{ pointerEvents: 'auto' }}
                  onMouseEnter={() => setHoveredItem(`ep1-${idx}`)}
                  onMouseLeave={() => setHoveredItem(null)}
                />
                <circle
                  cx={dl.x2} cy={dl.y2} r={5}
                  fill={dl.near_center ? '#ef4444' : '#3b82f6'}
                  opacity={0.9}
                />
              </>
            )}
          </g>
        ))}

        {/* ROIs (노란 점선) */}
        {visible.rois && debug.rois.map((roi, idx) => (
          <g key={`roi-${idx}`}>
            <rect
              x={roi.x} y={roi.y} width={roi.w} height={roi.h}
              fill="none" stroke="#eab308" strokeWidth={1.5}
              strokeDasharray="6,3" opacity={0.6}
            />
            {roi.ocr_text && (
              <text x={roi.x + 2} y={roi.y - 3} fill="#eab308" fontSize={10} opacity={0.8}>
                {roi.ocr_text}
              </text>
            )}
          </g>
        ))}

        {/* Symbols (마젠타 마커) */}
        {visible.symbols && debug.symbols_found.map((sym, idx) => (
          <g key={`sym-${idx}`}>
            <rect
              x={sym.x - 12} y={sym.y - 12} width={24} height={24}
              fill="none" stroke="#d946ef" strokeWidth={2} rx={4} opacity={0.8}
            />
            <text x={sym.x - 10} y={sym.y - 16} fill="#d946ef" fontSize={11} fontWeight="bold" opacity={0.9}>
              {sym.type === 'RADIUS' ? 'R' : 'Ø'} {sym.text}
            </text>
          </g>
        ))}

        {/* Rays (주황 화살표) */}
        {visible.rays && debug.rays.map((ray, idx) => (
          <g key={`ray-${idx}`}>
            <line
              x1={ray.origin_cx} y1={ray.origin_cy}
              x2={ray.hit_x} y2={ray.hit_y}
              stroke="#f97316" strokeWidth={1.5} opacity={0.5}
              strokeDasharray="4,4"
              markerEnd="url(#arrowhead)"
            />
            <circle cx={ray.hit_x} cy={ray.hit_y} r={4} fill="#f97316" opacity={0.7} />
            <text x={ray.hit_x + 6} y={ray.hit_y - 4} fill="#f97316" fontSize={10} opacity={0.7}>
              d={Math.round(ray.distance)}
            </text>
          </g>
        ))}

        {/* Arrow marker definition */}
        <defs>
          <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#f97316" opacity="0.6" />
          </marker>
        </defs>
      </svg>

      {/* 호버 툴팁 */}
      {hoveredItem && (
        <div className="absolute top-2 right-2 bg-gray-900/90 text-white text-xs px-3 py-2 rounded-lg shadow-lg z-50">
          {hoveredItem}
        </div>
      )}

      {/* 범례 */}
      <div className="flex flex-wrap items-center gap-3 mt-2 text-[10px] text-gray-400 px-1">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#ef4444' }} /> Center
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#3b82f6' }} /> Circumference
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#9ca3af' }} /> Unknown
        </span>
      </div>
    </div>
  );
}
