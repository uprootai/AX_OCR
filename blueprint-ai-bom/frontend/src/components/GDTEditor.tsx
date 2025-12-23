/**
 * GDTEditor - GD&T (기하공차) 편집 컴포넌트
 * Phase 7: 도면에서 기하공차를 검출하고 편집하는 기능
 *
 * - Feature Control Frame (FCF): 기하공차 프레임
 * - 14가지 기하 특성: 직진도, 평면도, 원통도, 위치도 등
 * - 데이텀 참조: A, B, C 등
 * - 재료 조건 수정자: MMC, LMC, RFS
 */

import { useState, useCallback, useMemo } from 'react';
import type { BoundingBox, VerificationStatus } from '../types';

// 기하 특성 타입 (14종)
export type GeometricCharacteristic =
  | 'straightness'      // 직진도
  | 'flatness'          // 평면도
  | 'circularity'       // 진원도
  | 'cylindricity'      // 원통도
  | 'profile_line'      // 선의 윤곽도
  | 'profile_surface'   // 면의 윤곽도
  | 'angularity'        // 경사도
  | 'perpendicularity'  // 직각도
  | 'parallelism'       // 평행도
  | 'position'          // 위치도
  | 'concentricity'     // 동심도
  | 'symmetry'          // 대칭도
  | 'circular_runout'   // 원주 흔들림
  | 'total_runout'      // 전체 흔들림
  | 'unknown';

// GD&T 카테고리
export type GDTCategory =
  | 'form'        // 형상 공차
  | 'profile'     // 윤곽 공차
  | 'orientation' // 방향 공차
  | 'location'    // 위치 공차
  | 'runout';     // 흔들림 공차

// 재료 조건 수정자
export type MaterialCondition = 'mmc' | 'lmc' | 'rfs' | 'none';

// 데이텀 참조
export interface DatumReference {
  label: string;
  material_condition: MaterialCondition;
  order: number;
}

// 공차 영역
export interface ToleranceZone {
  value: number;
  unit: string;
  diameter: boolean;
  projected: boolean;
  material_condition: MaterialCondition;
}

// Feature Control Frame
export interface FeatureControlFrame {
  id: string;
  characteristic: GeometricCharacteristic;
  category?: GDTCategory;
  tolerance: ToleranceZone;
  datums: DatumReference[];
  bbox: BoundingBox;
  bbox_normalized?: number[];
  linked_feature_id?: string;
  linked_dimension_id?: string;
  confidence: number;
  verification_status: VerificationStatus;
  raw_text?: string;
  notes?: string;
}

// 데이텀 형상
export interface DatumFeature {
  id: string;
  label: string;
  bbox: BoundingBox;
  bbox_normalized?: number[];
  datum_type: string;
  linked_feature_bbox?: BoundingBox;
  confidence: number;
  verification_status: VerificationStatus;
}

// GD&T 요약
export interface GDTSummary {
  session_id: string;
  total_fcf: number;
  fcf_by_category: Record<string, number>;
  fcf_by_characteristic: Record<string, number>;
  total_datums: number;
  datum_labels: string[];
  verified_fcf: number;
  pending_fcf: number;
  avg_confidence: number;
  low_confidence_count: number;
}

interface GDTEditorProps {
  sessionId: string;
  fcfList: FeatureControlFrame[];
  datums: DatumFeature[];
  imageSize: { width: number; height: number };
  containerSize: { width: number; height: number };
  selectedFCFId?: string | null;
  selectedDatumId?: string | null;
  onFCFSelect?: (fcfId: string | null) => void;
  onDatumSelect?: (datumId: string | null) => void;
  onFCFUpdate?: (fcfId: string, updates: Partial<FeatureControlFrame>) => void;
  onFCFDelete?: (fcfId: string) => void;
  onDatumDelete?: (datumId: string) => void;
  onParse?: () => void;
  isProcessing?: boolean;
  showLabels?: boolean;
}

// 기하 특성별 기호
const CHARACTERISTIC_SYMBOLS: Record<GeometricCharacteristic, string> = {
  straightness: '─',
  flatness: '▱',
  circularity: '○',
  cylindricity: '⌭',
  profile_line: '⌒',
  profile_surface: '⌓',
  angularity: '∠',
  perpendicularity: '⊥',
  parallelism: '∥',
  position: '⌖',
  concentricity: '◎',
  symmetry: '⌯',
  circular_runout: '↗',
  total_runout: '⇗',
  unknown: '?',
};

// 기하 특성별 한글명
const CHARACTERISTIC_LABELS: Record<GeometricCharacteristic, string> = {
  straightness: '직진도',
  flatness: '평면도',
  circularity: '진원도',
  cylindricity: '원통도',
  profile_line: '선의 윤곽도',
  profile_surface: '면의 윤곽도',
  angularity: '경사도',
  perpendicularity: '직각도',
  parallelism: '평행도',
  position: '위치도',
  concentricity: '동심도',
  symmetry: '대칭도',
  circular_runout: '원주 흔들림',
  total_runout: '전체 흔들림',
  unknown: '미분류',
};

// 카테고리별 색상
const CATEGORY_COLORS: Record<GDTCategory, string> = {
  form: '#3b82f6',       // blue - 형상 공차
  profile: '#22c55e',    // green - 윤곽 공차
  orientation: '#f97316', // orange - 방향 공차
  location: '#8b5cf6',   // purple - 위치 공차
  runout: '#ef4444',     // red - 흔들림 공차
};

// 카테고리별 한글명
const CATEGORY_LABELS: Record<GDTCategory, string> = {
  form: '형상 공차',
  profile: '윤곽 공차',
  orientation: '방향 공차',
  location: '위치 공차',
  runout: '흔들림 공차',
};

// 특성 → 카테고리 매핑
const CHARACTERISTIC_TO_CATEGORY: Record<GeometricCharacteristic, GDTCategory> = {
  straightness: 'form',
  flatness: 'form',
  circularity: 'form',
  cylindricity: 'form',
  profile_line: 'profile',
  profile_surface: 'profile',
  angularity: 'orientation',
  perpendicularity: 'orientation',
  parallelism: 'orientation',
  position: 'location',
  concentricity: 'location',
  symmetry: 'location',
  circular_runout: 'runout',
  total_runout: 'runout',
  unknown: 'form',
};

// 재료 조건 기호
const MATERIAL_CONDITION_SYMBOLS: Record<MaterialCondition, string> = {
  mmc: 'Ⓜ',
  lmc: 'Ⓛ',
  rfs: 'Ⓢ',
  none: '',
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

// FCF 표시 텍스트 생성
function formatFCFDisplay(fcf: FeatureControlFrame): string {
  const symbol = CHARACTERISTIC_SYMBOLS[fcf.characteristic];
  const tolerance = fcf.tolerance.diameter ? `⌀${fcf.tolerance.value}` : `${fcf.tolerance.value}`;
  const mc = MATERIAL_CONDITION_SYMBOLS[fcf.tolerance.material_condition];
  const datums = fcf.datums.map(d => d.label + MATERIAL_CONDITION_SYMBOLS[d.material_condition]).join('-');

  return `${symbol} ${tolerance}${mc}${datums ? ` | ${datums}` : ''}`;
}

export default function GDTEditor({
  fcfList,
  datums,
  imageSize,
  containerSize,
  selectedFCFId,
  selectedDatumId,
  onFCFSelect,
  onDatumSelect,
  onFCFUpdate,
  onFCFDelete,
  onDatumDelete,
  onParse,
  isProcessing = false,
  showLabels = true,
}: GDTEditorProps) {
  const [hoveredFCFId, setHoveredFCFId] = useState<string | null>(null);
  const [hoveredDatumId, setHoveredDatumId] = useState<string | null>(null);

  // 통계 계산
  const statistics = useMemo(() => {
    const stats = {
      totalFCF: fcfList.length,
      totalDatums: datums.length,
      byCategory: {} as Record<string, number>,
      byCharacteristic: {} as Record<string, number>,
      verified: 0,
      pending: 0,
      avgConfidence: 0,
    };

    let totalConfidence = 0;

    fcfList.forEach((fcf) => {
      // 카테고리별 카운트
      const category = fcf.category || CHARACTERISTIC_TO_CATEGORY[fcf.characteristic];
      stats.byCategory[category] = (stats.byCategory[category] || 0) + 1;

      // 특성별 카운트
      stats.byCharacteristic[fcf.characteristic] = (stats.byCharacteristic[fcf.characteristic] || 0) + 1;

      // 검증 상태
      if (fcf.verification_status === 'approved') {
        stats.verified++;
      } else if (fcf.verification_status === 'pending') {
        stats.pending++;
      }

      // 신뢰도
      totalConfidence += fcf.confidence;
    });

    stats.avgConfidence = fcfList.length > 0 ? totalConfidence / fcfList.length : 0;

    return stats;
  }, [fcfList, datums]);

  // FCF 클릭 핸들러
  const handleFCFClick = useCallback((fcfId: string) => {
    if (selectedFCFId === fcfId) {
      onFCFSelect?.(null);
    } else {
      onFCFSelect?.(fcfId);
      onDatumSelect?.(null);
    }
  }, [selectedFCFId, onFCFSelect, onDatumSelect]);

  // 데이텀 클릭 핸들러
  const handleDatumClick = useCallback((datumId: string) => {
    if (selectedDatumId === datumId) {
      onDatumSelect?.(null);
    } else {
      onDatumSelect?.(datumId);
      onFCFSelect?.(null);
    }
  }, [selectedDatumId, onDatumSelect, onFCFSelect]);

  // 특성 변경 핸들러
  const handleCharacteristicChange = useCallback((fcfId: string, newChar: GeometricCharacteristic) => {
    onFCFUpdate?.(fcfId, {
      characteristic: newChar,
      category: CHARACTERISTIC_TO_CATEGORY[newChar],
    });
  }, [onFCFUpdate]);

  // 선택된 FCF
  const selectedFCF = useMemo(() => {
    return fcfList.find(f => f.id === selectedFCFId);
  }, [fcfList, selectedFCFId]);

  // 선택된 데이텀
  const selectedDatum = useMemo(() => {
    return datums.find(d => d.id === selectedDatumId);
  }, [datums, selectedDatumId]);

  return (
    <div className="relative w-full h-full">
      {/* SVG 오버레이 */}
      <svg
        className="absolute inset-0 pointer-events-none"
        width={containerSize.width}
        height={containerSize.height}
        viewBox={`0 0 ${containerSize.width} ${containerSize.height}`}
      >
        {/* 데이텀 렌더링 */}
        {datums.map((datum) => {
          const scaled = scaleBbox(datum.bbox, imageSize, containerSize);
          const isSelected = selectedDatumId === datum.id;
          const isHovered = hoveredDatumId === datum.id;

          return (
            <g
              key={datum.id}
              className="pointer-events-auto cursor-pointer"
              onClick={() => handleDatumClick(datum.id)}
              onMouseEnter={() => setHoveredDatumId(datum.id)}
              onMouseLeave={() => setHoveredDatumId(null)}
            >
              {/* 데이텀 삼각형 표시 */}
              <polygon
                points={`${scaled.x + scaled.width / 2},${scaled.y} ${scaled.x + scaled.width},${scaled.y + scaled.height} ${scaled.x},${scaled.y + scaled.height}`}
                fill={isSelected ? '#fbbf24' : isHovered ? '#fcd34d' : '#fef3c7'}
                stroke="#f59e0b"
                strokeWidth={isSelected ? 3 : isHovered ? 2 : 1}
              />

              {/* 데이텀 레이블 */}
              <text
                x={scaled.x + scaled.width / 2}
                y={scaled.y + scaled.height / 2 + 4}
                textAnchor="middle"
                fill="#92400e"
                fontSize={14}
                fontWeight="bold"
              >
                {datum.label}
              </text>
            </g>
          );
        })}

        {/* FCF 렌더링 */}
        {fcfList.map((fcf) => {
          const scaled = scaleBbox(fcf.bbox, imageSize, containerSize);
          const category = fcf.category || CHARACTERISTIC_TO_CATEGORY[fcf.characteristic];
          const color = CATEGORY_COLORS[category];
          const isSelected = selectedFCFId === fcf.id;
          const isHovered = hoveredFCFId === fcf.id;

          return (
            <g
              key={fcf.id}
              className="pointer-events-auto cursor-pointer"
              onClick={() => handleFCFClick(fcf.id)}
              onMouseEnter={() => setHoveredFCFId(fcf.id)}
              onMouseLeave={() => setHoveredFCFId(null)}
            >
              {/* FCF 박스 */}
              <rect
                x={scaled.x}
                y={scaled.y}
                width={scaled.width}
                height={scaled.height}
                fill={color}
                fillOpacity={isSelected ? 0.3 : isHovered ? 0.2 : 0.1}
                stroke={color}
                strokeWidth={isSelected ? 3 : isHovered ? 2 : 1}
              />

              {/* 레이블 */}
              {showLabels && (
                <g>
                  {/* 배경 */}
                  <rect
                    x={scaled.x}
                    y={scaled.y - 22}
                    width={Math.max(scaled.width, 100)}
                    height={20}
                    fill={color}
                    rx={4}
                  />
                  {/* 텍스트 */}
                  <text
                    x={scaled.x + 4}
                    y={scaled.y - 7}
                    fill="white"
                    fontSize={11}
                    fontFamily="monospace"
                  >
                    {formatFCFDisplay(fcf)}
                  </text>
                </g>
              )}

              {/* 검증 상태 표시 */}
              {fcf.verification_status === 'approved' && (
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
          <h4 className="font-semibold text-sm text-gray-700 mb-2">GD&T 분석 통계</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-gray-100 rounded px-2 py-1">
              <span className="text-gray-500">FCF:</span>{' '}
              <span className="font-medium">{statistics.totalFCF}</span>
            </div>
            <div className="bg-amber-100 rounded px-2 py-1">
              <span className="text-gray-500">데이텀:</span>{' '}
              <span className="font-medium text-amber-700">{statistics.totalDatums}</span>
            </div>
            <div className="bg-green-100 rounded px-2 py-1">
              <span className="text-gray-500">검증됨:</span>{' '}
              <span className="font-medium text-green-700">{statistics.verified}</span>
            </div>
            <div className="bg-yellow-100 rounded px-2 py-1">
              <span className="text-gray-500">대기중:</span>{' '}
              <span className="font-medium text-yellow-700">{statistics.pending}</span>
            </div>
          </div>

          {/* 카테고리별 분포 */}
          <div className="mt-2 flex flex-wrap gap-1">
            {Object.entries(statistics.byCategory).map(([cat, count]) => (
              <span
                key={cat}
                className="inline-flex items-center px-2 py-0.5 rounded text-xs"
                style={{
                  backgroundColor: CATEGORY_COLORS[cat as GDTCategory] + '20',
                  color: CATEGORY_COLORS[cat as GDTCategory],
                }}
              >
                {CATEGORY_LABELS[cat as GDTCategory]}: {count}
              </span>
            ))}
          </div>
        </div>

        {/* 액션 버튼 */}
        <div className="space-y-2">
          <button
            onClick={onParse}
            disabled={isProcessing}
            className="w-full px-3 py-2 bg-purple-500 text-white rounded-md text-sm font-medium hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isProcessing ? (
              <>
                <span className="animate-spin">&#9203;</span>
                파싱 중...
              </>
            ) : (
              <>
                <span>&#128270;</span>
                GD&T 파싱 실행
              </>
            )}
          </button>
        </div>
      </div>

      {/* 선택된 FCF 편집 패널 */}
      {selectedFCF && (
        <div className="absolute bottom-2 left-2 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-3 max-w-sm">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-sm text-gray-700">
              FCF 편집
            </h4>
            <button
              onClick={() => onFCFSelect?.(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              &#10005;
            </button>
          </div>

          <div className="space-y-3">
            {/* 기하 특성 */}
            <div>
              <label className="block text-xs text-gray-500 mb-1">기하 특성</label>
              <select
                value={selectedFCF.characteristic}
                onChange={(e) => handleCharacteristicChange(selectedFCF.id, e.target.value as GeometricCharacteristic)}
                className="w-full px-2 py-1 border rounded text-sm"
              >
                {Object.entries(CHARACTERISTIC_LABELS).map(([char, label]) => (
                  <option key={char} value={char}>
                    {CHARACTERISTIC_SYMBOLS[char as GeometricCharacteristic]} {label}
                  </option>
                ))}
              </select>
            </div>

            {/* 공차 정보 */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs text-gray-500 mb-1">공차값</label>
                <div className="px-2 py-1 border rounded text-sm bg-gray-50">
                  {selectedFCF.tolerance.diameter && '⌀'}
                  {selectedFCF.tolerance.value} {selectedFCF.tolerance.unit}
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">재료 조건</label>
                <div className="px-2 py-1 border rounded text-sm bg-gray-50">
                  {selectedFCF.tolerance.material_condition === 'none'
                    ? '-'
                    : MATERIAL_CONDITION_SYMBOLS[selectedFCF.tolerance.material_condition]}
                </div>
              </div>
            </div>

            {/* 데이텀 참조 */}
            {selectedFCF.datums.length > 0 && (
              <div>
                <label className="block text-xs text-gray-500 mb-1">데이텀 참조</label>
                <div className="flex gap-2">
                  {selectedFCF.datums.map((datum, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded text-sm font-medium"
                    >
                      {datum.label}
                      {MATERIAL_CONDITION_SYMBOLS[datum.material_condition]}
                      <span className="text-xs text-amber-600 ml-1">
                        ({datum.order === 1 ? '1차' : datum.order === 2 ? '2차' : '3차'})
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 상태 정보 */}
            <div className="flex items-center gap-2 text-xs">
              <span className={`px-2 py-0.5 rounded ${
                selectedFCF.verification_status === 'approved'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-yellow-100 text-yellow-700'
              }`}>
                {selectedFCF.verification_status === 'approved' ? '검증됨' : '대기중'}
              </span>
              <span className="text-gray-400">
                신뢰도: {(selectedFCF.confidence * 100).toFixed(0)}%
              </span>
            </div>

            {/* 원본 텍스트 */}
            {selectedFCF.raw_text && (
              <div className="text-xs text-gray-500">
                <span className="font-medium">OCR:</span> {selectedFCF.raw_text}
              </div>
            )}

            {/* 액션 버튼 */}
            <div className="flex gap-2">
              <button
                onClick={() => onFCFUpdate?.(selectedFCF.id, { verification_status: 'approved' })}
                className="flex-1 px-2 py-1 bg-green-500 text-white rounded text-xs hover:bg-green-600"
              >
                &#10004; 승인
              </button>
              <button
                onClick={() => onFCFDelete?.(selectedFCF.id)}
                className="px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600"
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 선택된 데이텀 편집 패널 */}
      {selectedDatum && (
        <div className="absolute bottom-2 left-2 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-3 max-w-sm">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-sm text-gray-700">
              &#9651; 데이텀 {selectedDatum.label}
            </h4>
            <button
              onClick={() => onDatumSelect?.(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              &#10005;
            </button>
          </div>

          <div className="space-y-2">
            <div className="text-sm">
              <span className="text-gray-500">타입:</span>{' '}
              <span className="font-medium">{selectedDatum.datum_type}</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className={`px-2 py-0.5 rounded ${
                selectedDatum.verification_status === 'approved'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-yellow-100 text-yellow-700'
              }`}>
                {selectedDatum.verification_status === 'approved' ? '검증됨' : '대기중'}
              </span>
              <span className="text-gray-400">
                신뢰도: {(selectedDatum.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <button
              onClick={() => onDatumDelete?.(selectedDatum.id)}
              className="w-full px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600"
            >
              삭제
            </button>
          </div>
        </div>
      )}

      {/* 범례 */}
      <div className="absolute bottom-2 right-2 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-2">
        <div className="text-xs text-gray-500 mb-1">GD&T 카테고리</div>
        <div className="grid grid-cols-1 gap-1">
          {Object.entries(CATEGORY_LABELS).map(([cat, label]) => (
            <div key={cat} className="flex items-center gap-1">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: CATEGORY_COLORS[cat as GDTCategory] }}
              />
              <span className="text-xs text-gray-600">{label}</span>
            </div>
          ))}
          <div className="flex items-center gap-1 mt-1 pt-1 border-t">
            <div className="w-3 h-3 rounded bg-amber-400" />
            <span className="text-xs text-gray-600">데이텀</span>
          </div>
        </div>
      </div>
    </div>
  );
}
