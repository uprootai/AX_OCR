/**
 * ConnectivityDiagram - P&ID 심볼 연결 다이어그램 컴포넌트
 * Phase 6: 심볼 간 연결 관계를 시각화
 *
 * - 노드: 검출된 심볼
 * - 엣지: 심볼 간 연결
 * - 연결 타입별 색상 구분
 * - 경로 찾기 및 하이라이트
 */

import { useMemo, useState, useCallback } from 'react';
import type { Detection, BoundingBox } from '../types';

// 연결 타입
interface SymbolNode {
  id: string;
  class_name: string;
  center: { x: number; y: number };
  bbox: BoundingBox;
  connections: string[];
  connected_lines: string[];
  tag?: string | null;
}

interface Connection {
  id: string;
  source_id: string;
  target_id: string;
  line_ids: string[];
  connection_type: string;
  confidence: number;
  path_length: number;
}

interface ConnectivityResult {
  nodes: Record<string, SymbolNode>;
  connections: Connection[];
  orphan_symbols: string[];
  statistics: {
    total_symbols: number;
    total_connections: number;
    orphan_count: number;
    connectivity_ratio: number;
    avg_connections_per_symbol: number;
    connection_distribution: Record<string, number>;
    class_statistics: Record<string, { count: number; connected: number }>;
    connection_type_distribution: Record<string, number>;
  };
}

interface ConnectivityDiagramProps {
  data: ConnectivityResult | null;
  detections: Detection[];
  imageSize: { width: number; height: number };
  containerSize: { width: number; height: number };
  selectedSymbolId?: string | null;
  highlightPath?: string[] | null;
  onSymbolClick?: (symbolId: string) => void;
  onSymbolHover?: (symbolId: string | null) => void;
  showLabels?: boolean;
  showOrphans?: boolean;
}

// 연결 타입별 색상
const CONNECTION_TYPE_COLORS: Record<string, string> = {
  through_lines: '#3b82f6',        // blue - 선을 통한 연결
  through_intersection: '#8b5cf6', // purple - 교차점을 통한 연결
  proximity: '#f59e0b',            // amber - 근접성 기반 연결
  direct: '#22c55e',               // green - 직접 연결
  inferred: '#6b7280',             // gray - 추론된 연결
};

// 클래스별 색상
const CLASS_COLORS: Record<string, string> = {
  valve: '#ef4444',         // red
  pump: '#3b82f6',          // blue
  tank: '#22c55e',          // green
  heat_exchanger: '#f97316', // orange
  compressor: '#8b5cf6',    // purple
  reactor: '#ec4899',       // pink
  column: '#14b8a6',        // teal
  separator: '#eab308',     // yellow
  default: '#6b7280',       // gray
};

function getClassColor(className: string): string {
  // 클래스명에 포함된 키워드로 색상 결정
  const lowerName = className.toLowerCase();
  for (const [key, color] of Object.entries(CLASS_COLORS)) {
    if (lowerName.includes(key)) {
      return color;
    }
  }
  return CLASS_COLORS.default;
}

// 좌표 스케일링
function scalePoint(
  point: { x: number; y: number },
  imageSize: { width: number; height: number },
  containerSize: { width: number; height: number }
): { x: number; y: number } {
  const scaleX = containerSize.width / imageSize.width;
  const scaleY = containerSize.height / imageSize.height;
  const scale = Math.min(scaleX, scaleY);

  const offsetX = (containerSize.width - imageSize.width * scale) / 2;
  const offsetY = (containerSize.height - imageSize.height * scale) / 2;

  return {
    x: point.x * scale + offsetX,
    y: point.y * scale + offsetY,
  };
}

// 베지어 커브 컨트롤 포인트
function getControlPoint(
  start: { x: number; y: number },
  end: { x: number; y: number },
  offset: number = 20
): { x: number; y: number } {
  const midX = (start.x + end.x) / 2;
  const midY = (start.y + end.y) / 2;

  const dx = Math.abs(end.x - start.x);
  const dy = Math.abs(end.y - start.y);

  if (dx > dy) {
    return { x: midX, y: midY - offset };
  } else {
    return { x: midX + offset, y: midY };
  }
}

export function ConnectivityDiagram({
  data,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  detections: _detections,  // Reserved for future use (e.g., detection-based filtering)
  imageSize,
  containerSize,
  selectedSymbolId,
  highlightPath,
  onSymbolClick,
  onSymbolHover,
  showLabels = true,
  showOrphans = true,
}: ConnectivityDiagramProps) {
  const [hoveredSymbolId, setHoveredSymbolId] = useState<string | null>(null);

  // 노드 위치 계산
  // eslint-disable-next-line react-hooks/preserve-manual-memoization -- 옵셔널 체이닝 사용으로 인한 의존성 차이
  const scaledNodes = useMemo(() => {
    if (!data?.nodes) return {};

    const result: Record<string, { node: SymbolNode; scaledCenter: { x: number; y: number }; color: string }> = {};

    for (const [id, node] of Object.entries(data.nodes)) {
      const scaledCenter = scalePoint(node.center, imageSize, containerSize);
      const color = getClassColor(node.class_name);

      result[id] = { node, scaledCenter, color };
    }

    return result;
  }, [data?.nodes, imageSize, containerSize]);

  // 연결 라인 계산
  // eslint-disable-next-line react-hooks/preserve-manual-memoization -- 옵셔널 체이닝 사용으로 인한 의존성 차이
  const connectionLines = useMemo(() => {
    if (!data?.connections) return [];

    return data.connections.map((conn) => {
      const sourceNode = scaledNodes[conn.source_id];
      const targetNode = scaledNodes[conn.target_id];

      if (!sourceNode || !targetNode) return null;

      const control = getControlPoint(sourceNode.scaledCenter, targetNode.scaledCenter);

      const isHighlighted =
        highlightPath?.includes(conn.source_id) &&
        highlightPath?.includes(conn.target_id) &&
        Math.abs(highlightPath.indexOf(conn.source_id) - highlightPath.indexOf(conn.target_id)) === 1;

      const isConnectedToSelected =
        selectedSymbolId === conn.source_id || selectedSymbolId === conn.target_id;

      const isConnectedToHovered =
        hoveredSymbolId === conn.source_id || hoveredSymbolId === conn.target_id;

      return {
        ...conn,
        start: sourceNode.scaledCenter,
        end: targetNode.scaledCenter,
        control,
        isHighlighted,
        isConnectedToSelected,
        isConnectedToHovered,
      };
    }).filter(Boolean);
  }, [data?.connections, scaledNodes, highlightPath, selectedSymbolId, hoveredSymbolId]);

  // 이벤트 핸들러
  const handleSymbolClick = useCallback((symbolId: string) => {
    onSymbolClick?.(symbolId);
  }, [onSymbolClick]);

  const handleSymbolHover = useCallback((symbolId: string | null) => {
    setHoveredSymbolId(symbolId);
    onSymbolHover?.(symbolId);
  }, [onSymbolHover]);

  if (!data || Object.keys(data.nodes).length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <div className="text-center">
          <svg className="w-12 h-12 mx-auto mb-2 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <p>연결 분석 데이터 없음</p>
          <p className="text-sm mt-1">먼저 선 검출을 실행하세요</p>
        </div>
      </div>
    );
  }

  const stats = data.statistics;

  return (
    <div className="relative" style={{ width: containerSize.width, height: containerSize.height }}>
      <svg
        width={containerSize.width}
        height={containerSize.height}
        className="absolute top-0 left-0"
        style={{ overflow: 'visible' }}
      >
        <defs>
          {/* 화살표 마커 */}
          {Object.entries(CONNECTION_TYPE_COLORS).map(([type, color]) => (
            <marker
              key={type}
              id={`conn-arrow-${type}`}
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="5"
              markerHeight="5"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill={color} />
            </marker>
          ))}

          {/* 하이라이트용 글로우 필터 */}
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* 경로 하이라이트 그라데이션 */}
          <linearGradient id="path-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22c55e" />
            <stop offset="100%" stopColor="#3b82f6" />
          </linearGradient>
        </defs>

        {/* 연결선 그리기 */}
        <g className="connections">
          {connectionLines.map((line) => {
            if (!line) return null;

            const color = line.isHighlighted
              ? 'url(#path-gradient)'
              : CONNECTION_TYPE_COLORS[line.connection_type] || CONNECTION_TYPE_COLORS.inferred;

            const opacity = line.isHighlighted
              ? 1
              : line.isConnectedToSelected || line.isConnectedToHovered
              ? 0.9
              : 0.5;

            const strokeWidth = line.isHighlighted ? 4 : line.isConnectedToSelected ? 3 : 2;

            const path = `M ${line.start.x} ${line.start.y} Q ${line.control.x} ${line.control.y} ${line.end.x} ${line.end.y}`;

            return (
              <g key={line.id}>
                <path
                  d={path}
                  fill="none"
                  stroke={color}
                  strokeWidth={strokeWidth}
                  strokeOpacity={opacity}
                  strokeDasharray={line.connection_type === 'proximity' ? '6,3' : undefined}
                  markerEnd={`url(#conn-arrow-${line.connection_type})`}
                  style={line.isHighlighted ? { filter: 'url(#glow)' } : undefined}
                />

                {/* 신뢰도 표시 (선택 시) */}
                {(line.isConnectedToSelected || line.isHighlighted) && (
                  <g>
                    <rect
                      x={line.control.x - 18}
                      y={line.control.y - 10}
                      width={36}
                      height={20}
                      rx={4}
                      fill="rgba(0,0,0,0.75)"
                    />
                    <text
                      x={line.control.x}
                      y={line.control.y + 4}
                      textAnchor="middle"
                      fill="white"
                      fontSize={10}
                      fontWeight="500"
                    >
                      {(line.confidence * 100).toFixed(0)}%
                    </text>
                  </g>
                )}
              </g>
            );
          })}
        </g>

        {/* 노드 그리기 */}
        <g className="nodes">
          {Object.entries(scaledNodes).map(([id, { node, scaledCenter, color }]) => {
            const isSelected = selectedSymbolId === id;
            const isHovered = hoveredSymbolId === id;
            const isInPath = highlightPath?.includes(id);
            const isOrphan = data.orphan_symbols.includes(id);

            // 고립 노드 숨기기 옵션
            if (isOrphan && !showOrphans) return null;

            const radius = isSelected || isHovered ? 14 : isInPath ? 12 : 10;
            const strokeWidth = isSelected ? 3 : isInPath ? 2.5 : 2;

            return (
              <g
                key={id}
                className="cursor-pointer"
                onClick={() => handleSymbolClick(id)}
                onMouseEnter={() => handleSymbolHover(id)}
                onMouseLeave={() => handleSymbolHover(null)}
              >
                {/* 노드 배경 (하이라이트) */}
                {(isSelected || isInPath) && (
                  <circle
                    cx={scaledCenter.x}
                    cy={scaledCenter.y}
                    r={radius + 4}
                    fill="none"
                    stroke={isInPath ? '#22c55e' : '#3b82f6'}
                    strokeWidth={2}
                    strokeDasharray="4,2"
                    opacity={0.6}
                  />
                )}

                {/* 노드 */}
                <circle
                  cx={scaledCenter.x}
                  cy={scaledCenter.y}
                  r={radius}
                  fill={isOrphan ? '#6b7280' : color}
                  stroke="white"
                  strokeWidth={strokeWidth}
                  opacity={isOrphan ? 0.5 : 1}
                  style={isSelected || isHovered ? { filter: 'url(#glow)' } : undefined}
                />

                {/* 연결 수 표시 */}
                {node.connections.length > 0 && (
                  <>
                    <circle
                      cx={scaledCenter.x + radius - 2}
                      cy={scaledCenter.y - radius + 2}
                      r={7}
                      fill="#1f2937"
                      stroke="white"
                      strokeWidth={1}
                    />
                    <text
                      x={scaledCenter.x + radius - 2}
                      y={scaledCenter.y - radius + 6}
                      textAnchor="middle"
                      fill="white"
                      fontSize={9}
                      fontWeight="bold"
                    >
                      {node.connections.length}
                    </text>
                  </>
                )}

                {/* 레이블 */}
                {showLabels && (isSelected || isHovered) && (
                  <g>
                    <rect
                      x={scaledCenter.x - 50}
                      y={scaledCenter.y + radius + 4}
                      width={100}
                      height={22}
                      rx={4}
                      fill="rgba(0,0,0,0.85)"
                    />
                    <text
                      x={scaledCenter.x}
                      y={scaledCenter.y + radius + 18}
                      textAnchor="middle"
                      fill="white"
                      fontSize={10}
                      fontWeight="500"
                    >
                      {node.class_name}
                      {node.tag && ` (${node.tag})`}
                    </text>
                  </g>
                )}
              </g>
            );
          })}
        </g>
      </svg>

      {/* 통계 패널 */}
      <div className="absolute top-2 right-2 bg-black/70 text-white text-xs px-3 py-2 rounded-lg">
        <div className="font-semibold mb-1">연결 통계</div>
        <div className="space-y-0.5">
          <div className="flex justify-between gap-4">
            <span>심볼:</span>
            <span className="font-medium">{stats.total_symbols}개</span>
          </div>
          <div className="flex justify-between gap-4">
            <span>연결:</span>
            <span className="font-medium">{stats.total_connections}개</span>
          </div>
          <div className="flex justify-between gap-4">
            <span>연결률:</span>
            <span className="font-medium">{(stats.connectivity_ratio * 100).toFixed(0)}%</span>
          </div>
          {stats.orphan_count > 0 && (
            <div className="flex justify-between gap-4 text-amber-400">
              <span>고립:</span>
              <span className="font-medium">{stats.orphan_count}개</span>
            </div>
          )}
        </div>
      </div>

      {/* 범례 */}
      <div className="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-3 py-2 rounded-lg">
        <div className="font-semibold mb-1">연결 유형</div>
        <div className="flex flex-wrap gap-x-3 gap-y-1">
          {Object.entries(CONNECTION_TYPE_COLORS).slice(0, 3).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1">
              <div className="w-3 h-0.5" style={{ backgroundColor: color }} />
              <span className="text-gray-300">
                {type === 'through_lines' && '선'}
                {type === 'through_intersection' && '교차'}
                {type === 'proximity' && '근접'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 선택된 심볼 정보 */}
      {selectedSymbolId && scaledNodes[selectedSymbolId] && (
        <div className="absolute top-2 left-2 bg-black/80 text-white text-xs px-3 py-2 rounded-lg max-w-[200px]">
          <div className="font-semibold text-blue-400 mb-1">
            {scaledNodes[selectedSymbolId].node.class_name}
          </div>
          <div className="space-y-0.5 text-gray-300">
            <div>연결: {scaledNodes[selectedSymbolId].node.connections.length}개</div>
            {scaledNodes[selectedSymbolId].node.connected_lines.length > 0 && (
              <div>선: {scaledNodes[selectedSymbolId].node.connected_lines.length}개</div>
            )}
            {scaledNodes[selectedSymbolId].node.tag && (
              <div>태그: {scaledNodes[selectedSymbolId].node.tag}</div>
            )}
          </div>
        </div>
      )}

      {/* 경로 하이라이트 정보 */}
      {highlightPath && highlightPath.length > 1 && (
        <div className="absolute bottom-2 right-2 bg-green-900/80 text-white text-xs px-3 py-2 rounded-lg">
          <div className="font-semibold text-green-400 mb-1">경로</div>
          <div className="flex items-center gap-1 flex-wrap">
            {highlightPath.map((id, index) => (
              <span key={id} className="flex items-center">
                <span className="bg-green-600 px-1.5 py-0.5 rounded">
                  {scaledNodes[id]?.node.class_name || id}
                </span>
                {index < highlightPath.length - 1 && (
                  <span className="mx-1 text-green-400">→</span>
                )}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ConnectivityDiagram;
