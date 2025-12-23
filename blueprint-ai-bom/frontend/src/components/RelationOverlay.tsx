/**
 * RelationOverlay - 치수-객체 관계 시각화 오버레이
 * Phase 2: 치수선 기반 관계를 캔버스 위에 그립니다
 */

import { useMemo } from 'react';
import type { DimensionRelation, Detection, BoundingBox } from '../types';

interface Dimension {
  id: string;
  bbox: BoundingBox;
  value: string;
}

interface RelationOverlayProps {
  relations: DimensionRelation[];
  dimensions: Dimension[];
  detections: Detection[];
  imageSize: { width: number; height: number };
  containerSize: { width: number; height: number };
  selectedDimensionId?: string | null;
  showLabels?: boolean;
  showConfidence?: boolean;
}

// 방법별 색상
const METHOD_COLORS = {
  dimension_line: '#22c55e', // green
  extension_line: '#3b82f6', // blue
  proximity: '#eab308', // yellow
  manual: '#a855f7', // purple
};

// 신뢰도별 불투명도
function getOpacity(confidence: number): number {
  if (confidence >= 0.85) return 0.8;
  if (confidence >= 0.6) return 0.6;
  return 0.4;
}

// bbox 중심점 계산
function getCenter(bbox: BoundingBox): { x: number; y: number } {
  return {
    x: (bbox.x1 + bbox.x2) / 2,
    y: (bbox.y1 + bbox.y2) / 2,
  };
}

// 좌표 스케일링
function scalePoint(
  point: { x: number; y: number },
  imageSize: { width: number; height: number },
  containerSize: { width: number; height: number }
): { x: number; y: number } {
  const scaleX = containerSize.width / imageSize.width;
  const scaleY = containerSize.height / imageSize.height;
  return {
    x: point.x * scaleX,
    y: point.y * scaleY,
  };
}

// 베지어 커브 컨트롤 포인트 계산
function getControlPoint(
  start: { x: number; y: number },
  end: { x: number; y: number },
  offset: number = 30
): { x: number; y: number } {
  const midX = (start.x + end.x) / 2;
  const midY = (start.y + end.y) / 2;

  // 수직/수평 방향 판단
  const dx = Math.abs(end.x - start.x);
  const dy = Math.abs(end.y - start.y);

  if (dx > dy) {
    // 수평 연결 - 위로 곡선
    return { x: midX, y: midY - offset };
  } else {
    // 수직 연결 - 오른쪽으로 곡선
    return { x: midX + offset, y: midY };
  }
}

export function RelationOverlay({
  relations,
  dimensions,
  detections,
  imageSize,
  containerSize,
  selectedDimensionId,
  showLabels = true,
  showConfidence = true,
}: RelationOverlayProps) {
  // 관계 라인 데이터 계산
  const relationLines = useMemo(() => {
    return relations
      .filter((rel) => rel.target_id && rel.target_bbox)
      .map((rel) => {
        // 치수 찾기
        const dimension = dimensions.find((d) => d.id === rel.dimension_id);
        if (!dimension) return null;

        // 타겟 찾기
        const target = detections.find((d) => d.id === rel.target_id);
        const targetBbox = target?.bbox || rel.target_bbox;
        if (!targetBbox) return null;

        // 중심점 계산
        const dimCenter = getCenter(dimension.bbox);
        const targetCenter = getCenter(targetBbox);

        // 스케일링
        const scaledDim = scalePoint(dimCenter, imageSize, containerSize);
        const scaledTarget = scalePoint(targetCenter, imageSize, containerSize);
        const controlPoint = getControlPoint(scaledDim, scaledTarget);

        return {
          id: rel.id,
          dimensionId: rel.dimension_id,
          targetId: rel.target_id,
          method: rel.method,
          confidence: rel.confidence,
          relationType: rel.relation_type,
          start: scaledDim,
          end: scaledTarget,
          control: controlPoint,
          isSelected: selectedDimensionId === rel.dimension_id,
          dimensionValue: dimension.value,
          targetName: target?.class_name || 'Unknown',
        };
      })
      .filter(Boolean);
  }, [relations, dimensions, detections, imageSize, containerSize, selectedDimensionId]);

  if (relationLines.length === 0) return null;

  return (
    <svg
      className="absolute inset-0 pointer-events-none"
      width={containerSize.width}
      height={containerSize.height}
      style={{ overflow: 'visible' }}
    >
      <defs>
        {/* 화살표 마커 */}
        {Object.entries(METHOD_COLORS).map(([method, color]) => (
          <marker
            key={method}
            id={`arrow-${method}`}
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill={color} />
          </marker>
        ))}

        {/* 그라데이션 (선택된 관계용) */}
        <linearGradient id="selected-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#3b82f6" />
          <stop offset="100%" stopColor="#8b5cf6" />
        </linearGradient>
      </defs>

      {/* 관계 라인들 */}
      {relationLines.map((line) => {
        if (!line) return null;

        const color = line.isSelected ? 'url(#selected-gradient)' : METHOD_COLORS[line.method as keyof typeof METHOD_COLORS] || '#888';
        const opacity = line.isSelected ? 1 : getOpacity(line.confidence);
        const strokeWidth = line.isSelected ? 3 : 2;

        // 베지어 커브 경로
        const path = `M ${line.start.x} ${line.start.y} Q ${line.control.x} ${line.control.y} ${line.end.x} ${line.end.y}`;

        return (
          <g key={line.id}>
            {/* 연결선 */}
            <path
              d={path}
              fill="none"
              stroke={color}
              strokeWidth={strokeWidth}
              strokeOpacity={opacity}
              strokeDasharray={line.method === 'proximity' ? '4,4' : undefined}
              markerEnd={`url(#arrow-${line.method})`}
            />

            {/* 시작점 (치수) */}
            <circle
              cx={line.start.x}
              cy={line.start.y}
              r={line.isSelected ? 6 : 4}
              fill={color}
              fillOpacity={opacity}
              stroke="white"
              strokeWidth={1}
            />

            {/* 끝점 (타겟) */}
            <circle
              cx={line.end.x}
              cy={line.end.y}
              r={line.isSelected ? 6 : 4}
              fill={color}
              fillOpacity={opacity}
              stroke="white"
              strokeWidth={1}
            />

            {/* 신뢰도 레이블 */}
            {showConfidence && line.isSelected && (
              <g>
                <rect
                  x={line.control.x - 20}
                  y={line.control.y - 10}
                  width={40}
                  height={20}
                  rx={4}
                  fill="rgba(0,0,0,0.75)"
                />
                <text
                  x={line.control.x}
                  y={line.control.y + 4}
                  textAnchor="middle"
                  fill="white"
                  fontSize={11}
                  fontWeight="500"
                >
                  {(line.confidence * 100).toFixed(0)}%
                </text>
              </g>
            )}

            {/* 연결 레이블 (선택 시) */}
            {showLabels && line.isSelected && (
              <g>
                {/* 치수 값 */}
                <rect
                  x={line.start.x - 30}
                  y={line.start.y - 25}
                  width={60}
                  height={18}
                  rx={4}
                  fill="rgba(59, 130, 246, 0.9)"
                />
                <text
                  x={line.start.x}
                  y={line.start.y - 12}
                  textAnchor="middle"
                  fill="white"
                  fontSize={10}
                  fontWeight="500"
                >
                  {line.dimensionValue}
                </text>

                {/* 타겟 이름 */}
                <rect
                  x={line.end.x - 40}
                  y={line.end.y + 8}
                  width={80}
                  height={18}
                  rx={4}
                  fill="rgba(34, 197, 94, 0.9)"
                />
                <text
                  x={line.end.x}
                  y={line.end.y + 21}
                  textAnchor="middle"
                  fill="white"
                  fontSize={10}
                  fontWeight="500"
                >
                  {line.targetName}
                </text>
              </g>
            )}
          </g>
        );
      })}

      {/* 범례 (하단) */}
      <g transform={`translate(10, ${containerSize.height - 30})`}>
        <rect x={0} y={0} width={280} height={24} rx={4} fill="rgba(0,0,0,0.6)" />

        <g transform="translate(8, 16)">
          {/* 치수선 */}
          <line x1={0} y1={0} x2={20} y2={0} stroke={METHOD_COLORS.dimension_line} strokeWidth={2} />
          <text x={25} y={4} fill="white" fontSize={9}>치수선</text>

          {/* 연장선 */}
          <line x1={70} y1={0} x2={90} y2={0} stroke={METHOD_COLORS.extension_line} strokeWidth={2} />
          <text x={95} y={4} fill="white" fontSize={9}>연장선</text>

          {/* 근접성 */}
          <line x1={140} y1={0} x2={160} y2={0} stroke={METHOD_COLORS.proximity} strokeWidth={2} strokeDasharray="4,4" />
          <text x={165} y={4} fill="white" fontSize={9}>근접성</text>

          {/* 수동 */}
          <line x1={210} y1={0} x2={230} y2={0} stroke={METHOD_COLORS.manual} strokeWidth={2} />
          <text x={235} y={4} fill="white" fontSize={9}>수동</text>
        </g>
      </g>
    </svg>
  );
}
