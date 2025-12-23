/**
 * RegionEditor - 도면 영역 분할 편집 컴포넌트
 * Phase 5: 도면을 영역별로 분할하고 각 영역에 맞는 처리 전략 적용
 *
 * - 영역 타입: 표제란, 메인 뷰, BOM 테이블, 범례, 노트 등
 * - 처리 전략: YOLO+OCR, OCR 전용, 테이블 파싱, 메타데이터 추출
 * - 수동 영역 추가/편집/삭제 지원
 */

import { useState, useCallback, useMemo } from 'react';
import type { BoundingBox, VerificationStatus } from '../types';

// 영역 타입
export type RegionType =
  | 'title_block'
  | 'main_view'
  | 'bom_table'
  | 'notes'
  | 'detail_view'
  | 'section_view'
  | 'dimension_area'
  | 'legend'
  | 'revision_block'
  | 'parts_list'
  | 'unknown';

// 처리 전략
export type ProcessingStrategy =
  | 'yolo_ocr'
  | 'ocr_only'
  | 'table_parse'
  | 'metadata_extract'
  | 'symbol_match'
  | 'skip';

// 영역 인터페이스
export interface Region {
  id: string;
  region_type: RegionType;
  bbox: BoundingBox;
  confidence: number;
  bbox_normalized?: number[];
  processing_strategy: ProcessingStrategy;
  verification_status: VerificationStatus;
  label?: string;
  description?: string;
  processed: boolean;
  processing_result?: Record<string, unknown>;
}

export interface RegionSegmentationResult {
  session_id: string;
  regions: Region[];
  image_width: number;
  image_height: number;
  total_regions: number;
  processing_time_ms: number;
  region_stats: Record<string, number>;
}

interface RegionEditorProps {
  sessionId: string;
  regions: Region[];
  imageSize: { width: number; height: number };
  containerSize: { width: number; height: number };
  selectedRegionId?: string | null;
  onRegionSelect?: (regionId: string | null) => void;
  onRegionUpdate?: (regionId: string, updates: Partial<Region>) => void;
  onRegionDelete?: (regionId: string) => void;
  onRegionAdd?: (region: Partial<Region>) => void;
  onSegment?: () => void;
  onProcessRegion?: (regionId: string) => void;
  onProcessAll?: () => void;
  isProcessing?: boolean;
  showLabels?: boolean;
}

// 영역 타입별 색상
const REGION_TYPE_COLORS: Record<RegionType, string> = {
  title_block: '#3b82f6',     // blue
  main_view: '#22c55e',       // green
  bom_table: '#f97316',       // orange
  notes: '#8b5cf6',           // purple
  detail_view: '#14b8a6',     // teal
  section_view: '#ec4899',    // pink
  dimension_area: '#eab308',  // yellow
  legend: '#ef4444',          // red
  revision_block: '#6366f1',  // indigo
  parts_list: '#f59e0b',      // amber
  unknown: '#6b7280',         // gray
};

// 영역 타입 한글명
const REGION_TYPE_LABELS: Record<RegionType, string> = {
  title_block: '표제란',
  main_view: '메인 뷰',
  bom_table: 'BOM 테이블',
  notes: '노트/주석',
  detail_view: '상세도',
  section_view: '단면도',
  dimension_area: '치수 영역',
  legend: '범례',
  revision_block: '개정 이력',
  parts_list: '부품 목록',
  unknown: '미분류',
};

// 처리 전략 한글명
const STRATEGY_LABELS: Record<ProcessingStrategy, string> = {
  yolo_ocr: 'YOLO + OCR',
  ocr_only: 'OCR 전용',
  table_parse: '테이블 파싱',
  metadata_extract: '메타데이터 추출',
  symbol_match: '심볼 매칭',
  skip: '건너뛰기',
};

// 처리 전략 아이콘
const STRATEGY_ICONS: Record<ProcessingStrategy, string> = {
  yolo_ocr: '🎯',
  ocr_only: '📝',
  table_parse: '📊',
  metadata_extract: '📋',
  symbol_match: '🔗',
  skip: '⏭️',
};

// 좌표 스케일링
function scaleCoord(
  value: number,
  imageSize: number,
  containerSize: number
): number {
  return (value / imageSize) * containerSize;
}

function scaleBbox(
  bbox: BoundingBox,
  imageSize: { width: number; height: number },
  containerSize: { width: number; height: number }
): { x: number; y: number; width: number; height: number } {
  const x = scaleCoord(bbox.x1, imageSize.width, containerSize.width);
  const y = scaleCoord(bbox.y1, imageSize.height, containerSize.height);
  const width = scaleCoord(bbox.x2 - bbox.x1, imageSize.width, containerSize.width);
  const height = scaleCoord(bbox.y2 - bbox.y1, imageSize.height, containerSize.height);
  return { x, y, width, height };
}

export default function RegionEditor({
  regions,
  imageSize,
  containerSize,
  selectedRegionId,
  onRegionSelect,
  onRegionUpdate,
  onRegionDelete,
  onSegment,
  onProcessRegion,
  onProcessAll,
  isProcessing = false,
  showLabels = true,
}: RegionEditorProps) {
  const [hoveredRegionId, setHoveredRegionId] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_editingRegionId, _setEditingRegionId] = useState<string | null>(null);  // Reserved for future inline editing

  // 통계 계산
  const statistics = useMemo(() => {
    const stats = {
      total: regions.length,
      byType: {} as Record<string, number>,
      byStatus: {} as Record<string, number>,
      processed: 0,
      pending: 0,
    };

    regions.forEach((region) => {
      // 타입별 카운트
      const type = region.region_type;
      stats.byType[type] = (stats.byType[type] || 0) + 1;

      // 상태별 카운트
      const status = region.verification_status;
      stats.byStatus[status] = (stats.byStatus[status] || 0) + 1;

      // 처리 상태
      if (region.processed) {
        stats.processed++;
      } else {
        stats.pending++;
      }
    });

    return stats;
  }, [regions]);

  // 영역 클릭 핸들러
  const handleRegionClick = useCallback((regionId: string) => {
    if (selectedRegionId === regionId) {
      onRegionSelect?.(null);
    } else {
      onRegionSelect?.(regionId);
    }
  }, [selectedRegionId, onRegionSelect]);

  // 영역 타입 변경 핸들러
  const handleTypeChange = useCallback((regionId: string, newType: RegionType) => {
    onRegionUpdate?.(regionId, { region_type: newType });
  }, [onRegionUpdate]);

  // 처리 전략 변경 핸들러
  const handleStrategyChange = useCallback((regionId: string, newStrategy: ProcessingStrategy) => {
    onRegionUpdate?.(regionId, { processing_strategy: newStrategy });
  }, [onRegionUpdate]);

  // 선택된 영역
  const selectedRegion = useMemo(() => {
    return regions.find(r => r.id === selectedRegionId);
  }, [regions, selectedRegionId]);

  return (
    <div className="relative w-full h-full">
      {/* SVG 오버레이 */}
      <svg
        className="absolute inset-0 pointer-events-none"
        width={containerSize.width}
        height={containerSize.height}
        viewBox={`0 0 ${containerSize.width} ${containerSize.height}`}
      >
        {/* 영역 렌더링 */}
        {regions.map((region) => {
          const scaled = scaleBbox(region.bbox, imageSize, containerSize);
          const color = REGION_TYPE_COLORS[region.region_type];
          const isSelected = selectedRegionId === region.id;
          const isHovered = hoveredRegionId === region.id;

          return (
            <g
              key={region.id}
              className="pointer-events-auto cursor-pointer"
              onClick={() => handleRegionClick(region.id)}
              onMouseEnter={() => setHoveredRegionId(region.id)}
              onMouseLeave={() => setHoveredRegionId(null)}
            >
              {/* 영역 박스 */}
              <rect
                x={scaled.x}
                y={scaled.y}
                width={scaled.width}
                height={scaled.height}
                fill={color}
                fillOpacity={isSelected ? 0.3 : isHovered ? 0.2 : 0.1}
                stroke={color}
                strokeWidth={isSelected ? 3 : isHovered ? 2 : 1}
                strokeDasharray={region.processed ? 'none' : '5,5'}
              />

              {/* 레이블 */}
              {showLabels && (
                <g>
                  {/* 배경 */}
                  <rect
                    x={scaled.x}
                    y={scaled.y - 22}
                    width={REGION_TYPE_LABELS[region.region_type].length * 12 + 20}
                    height={20}
                    fill={color}
                    rx={4}
                  />
                  {/* 텍스트 */}
                  <text
                    x={scaled.x + 6}
                    y={scaled.y - 7}
                    fill="white"
                    fontSize={12}
                    fontWeight="bold"
                  >
                    {STRATEGY_ICONS[region.processing_strategy]} {REGION_TYPE_LABELS[region.region_type]}
                  </text>
                </g>
              )}

              {/* 처리 완료 표시 */}
              {region.processed && (
                <circle
                  cx={scaled.x + scaled.width - 10}
                  cy={scaled.y + 10}
                  r={8}
                  fill="#22c55e"
                  stroke="white"
                  strokeWidth={2}
                />
              )}
            </g>
          );
        })}
      </svg>

      {/* 컨트롤 패널 */}
      <div className="absolute top-2 right-2 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-3 max-w-xs">
        {/* 통계 */}
        <div className="mb-3 pb-3 border-b">
          <h4 className="font-semibold text-sm text-gray-700 mb-2">영역 분할 통계</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-gray-100 rounded px-2 py-1">
              <span className="text-gray-500">전체:</span>{' '}
              <span className="font-medium">{statistics.total}</span>
            </div>
            <div className="bg-green-100 rounded px-2 py-1">
              <span className="text-gray-500">처리됨:</span>{' '}
              <span className="font-medium text-green-700">{statistics.processed}</span>
            </div>
          </div>

          {/* 타입별 분포 */}
          <div className="mt-2 flex flex-wrap gap-1">
            {Object.entries(statistics.byType).map(([type, count]) => (
              <span
                key={type}
                className="inline-flex items-center px-2 py-0.5 rounded text-xs"
                style={{
                  backgroundColor: REGION_TYPE_COLORS[type as RegionType] + '20',
                  color: REGION_TYPE_COLORS[type as RegionType],
                }}
              >
                {REGION_TYPE_LABELS[type as RegionType]}: {count}
              </span>
            ))}
          </div>
        </div>

        {/* 액션 버튼 */}
        <div className="space-y-2">
          <button
            onClick={onSegment}
            disabled={isProcessing}
            className="w-full px-3 py-2 bg-blue-500 text-white rounded-md text-sm font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isProcessing ? (
              <>
                <span className="animate-spin">⏳</span>
                분할 중...
              </>
            ) : (
              <>
                <span>🔲</span>
                영역 분할 실행
              </>
            )}
          </button>

          <button
            onClick={onProcessAll}
            disabled={isProcessing || regions.length === 0}
            className="w-full px-3 py-2 bg-green-500 text-white rounded-md text-sm font-medium hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <span>▶️</span>
            모든 영역 처리
          </button>
        </div>
      </div>

      {/* 선택된 영역 편집 패널 */}
      {selectedRegion && (
        <div className="absolute bottom-2 left-2 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-3 max-w-sm">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-sm text-gray-700">
              영역 편집
            </h4>
            <button
              onClick={() => onRegionSelect?.(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div className="space-y-3">
            {/* 영역 타입 */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">영역 타입</label>
              <select
                value={selectedRegion.region_type}
                onChange={(e) => handleTypeChange(selectedRegion.id, e.target.value as RegionType)}
                className="w-full px-2 py-1 border rounded text-sm"
              >
                {Object.entries(REGION_TYPE_LABELS).map(([type, label]) => (
                  <option key={type} value={type}>{label}</option>
                ))}
              </select>
            </div>

            {/* 처리 전략 */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">처리 전략</label>
              <select
                value={selectedRegion.processing_strategy}
                onChange={(e) => handleStrategyChange(selectedRegion.id, e.target.value as ProcessingStrategy)}
                className="w-full px-2 py-1 border rounded text-sm"
              >
                {Object.entries(STRATEGY_LABELS).map(([strategy, label]) => (
                  <option key={strategy} value={strategy}>
                    {STRATEGY_ICONS[strategy as ProcessingStrategy]} {label}
                  </option>
                ))}
              </select>
            </div>

            {/* 상태 정보 */}
            <div className="flex items-center gap-2 text-xs">
              <span className={`px-2 py-0.5 rounded ${
                selectedRegion.processed ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
              }`}>
                {selectedRegion.processed ? '처리 완료' : '미처리'}
              </span>
              <span className="text-gray-400">
                신뢰도: {(selectedRegion.confidence * 100).toFixed(0)}%
              </span>
            </div>

            {/* 액션 버튼 */}
            <div className="flex gap-2">
              <button
                onClick={() => onProcessRegion?.(selectedRegion.id)}
                disabled={isProcessing}
                className="flex-1 px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 disabled:opacity-50"
              >
                처리 실행
              </button>
              <button
                onClick={() => onRegionDelete?.(selectedRegion.id)}
                className="px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600"
              >
                삭제
              </button>
            </div>

            {/* 처리 결과 (있는 경우) */}
            {selectedRegion.processing_result && (
              <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                <div className="font-medium text-gray-600 mb-1">처리 결과:</div>
                <pre className="text-gray-500 whitespace-pre-wrap overflow-auto max-h-32">
                  {JSON.stringify(selectedRegion.processing_result, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 범례 */}
      <div className="absolute bottom-2 right-2 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-2">
        <div className="text-xs text-gray-500 mb-1">영역 타입</div>
        <div className="grid grid-cols-2 gap-1">
          {Object.entries(REGION_TYPE_LABELS).slice(0, 6).map(([type, label]) => (
            <div key={type} className="flex items-center gap-1">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: REGION_TYPE_COLORS[type as RegionType] }}
              />
              <span className="text-xs text-gray-600">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
