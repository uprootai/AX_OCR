/**
 * RelationList - 치수-객체 관계 목록 컴포넌트
 * Phase 2: 치수선 기반 관계 추출 시각화
 */

import { useState } from 'react';
import {
  Link2,
  Unlink,
  ArrowRight,
  Target,
  ChevronDown,
  ChevronUp,
  Zap,
  Ruler,
  Hand,
  MapPin,
  CheckCircle,
  AlertCircle,
  XCircle,
  Trash2,
} from 'lucide-react';
import type { DimensionRelation, RelationStatistics, Detection } from '../types';

interface RelationListProps {
  relations: DimensionRelation[];
  statistics: RelationStatistics | null;
  dimensions: Array<{ id: string; value: string; bbox: { x1: number; y1: number; x2: number; y2: number } }>;
  detections: Detection[];
  onManualLink?: (dimensionId: string, targetId: string) => void;
  onDeleteRelation?: (relationId: string) => void;
  onSelectDimension?: (dimensionId: string) => void;
  selectedDimensionId?: string | null;
  isLoading?: boolean;
}

// 방법별 아이콘 및 색상
const METHOD_CONFIG = {
  dimension_line: {
    icon: Ruler,
    label: '치수선',
    color: 'text-green-600',
    bg: 'bg-green-100',
  },
  extension_line: {
    icon: ArrowRight,
    label: '연장선',
    color: 'text-blue-600',
    bg: 'bg-blue-100',
  },
  proximity: {
    icon: MapPin,
    label: '근접성',
    color: 'text-yellow-600',
    bg: 'bg-yellow-100',
  },
  manual: {
    icon: Hand,
    label: '수동',
    color: 'text-purple-600',
    bg: 'bg-purple-100',
  },
};

// 신뢰도별 색상
function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.85) return 'text-green-600';
  if (confidence >= 0.6) return 'text-yellow-600';
  return 'text-red-600';
}

function getConfidenceBg(confidence: number): string {
  if (confidence >= 0.85) return 'bg-green-100';
  if (confidence >= 0.6) return 'bg-yellow-100';
  return 'bg-red-100';
}

function getConfidenceIcon(confidence: number) {
  if (confidence >= 0.85) return CheckCircle;
  if (confidence >= 0.6) return AlertCircle;
  return XCircle;
}

export function RelationList({
  relations,
  statistics,
  dimensions,
  detections,
  onManualLink,
  onDeleteRelation,
  onSelectDimension,
  selectedDimensionId,
  isLoading = false,
}: RelationListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [linkingDimensionId, setLinkingDimensionId] = useState<string | null>(null);

  // 치수 ID로 치수 값 찾기
  const getDimensionValue = (dimensionId: string): string => {
    const dim = dimensions.find((d) => d.id === dimensionId);
    return dim?.value || dimensionId.slice(0, 8);
  };

  // 타겟 ID로 심볼 이름 찾기
  const getTargetName = (targetId: string | null): string => {
    if (!targetId) return '없음';
    const det = detections.find((d) => d.id === targetId);
    return det?.class_name || targetId.slice(0, 8);
  };

  // 수동 연결 핸들러
  const handleLink = (dimensionId: string, targetId: string) => {
    if (onManualLink) {
      onManualLink(dimensionId, targetId);
    }
    setLinkingDimensionId(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8 text-gray-500">
        <div className="animate-spin h-6 w-6 border-2 border-blue-500 rounded-full border-t-transparent mr-2" />
        관계 추출 중...
      </div>
    );
  }

  if (relations.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        <Unlink className="h-12 w-12 mx-auto mb-3 text-gray-300" />
        <p className="text-sm">추출된 관계가 없습니다</p>
        <p className="text-xs mt-1">분석을 실행하면 치수-객체 관계가 자동으로 추출됩니다</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 통계 요약 */}
      {statistics && (
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-sm flex items-center gap-2">
              <Zap className="h-4 w-4 text-yellow-500" />
              관계 추출 통계
            </h4>
            <span className="text-xs text-gray-500">총 {statistics.total}개</span>
          </div>

          {/* 방법별 통계 */}
          <div className="grid grid-cols-2 gap-2 mb-3">
            {Object.entries(statistics.by_method).map(([method, count]) => {
              const config = METHOD_CONFIG[method as keyof typeof METHOD_CONFIG] || {
                icon: Link2,
                label: method,
                color: 'text-gray-600',
                bg: 'bg-gray-100',
              };
              const Icon = config.icon;
              const percentage = statistics.total > 0 ? ((count / statistics.total) * 100).toFixed(0) : 0;

              return (
                <div
                  key={method}
                  className={`flex items-center gap-2 px-2 py-1 rounded ${config.bg}`}
                >
                  <Icon className={`h-3 w-3 ${config.color}`} />
                  <span className="text-xs font-medium">{config.label}</span>
                  <span className={`text-xs ml-auto ${config.color}`}>
                    {count}개 ({percentage}%)
                  </span>
                </div>
              );
            })}
          </div>

          {/* 연결 상태 */}
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1">
              <Link2 className="h-3 w-3 text-green-500" />
              <span>연결됨: {statistics.linked_count}</span>
            </div>
            <div className="flex items-center gap-1">
              <Unlink className="h-3 w-3 text-gray-400" />
              <span>미연결: {statistics.unlinked_count}</span>
            </div>
          </div>

          {/* 신뢰도별 통계 */}
          <div className="flex items-center gap-2 mt-2 text-xs">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              높음: {statistics.by_confidence.high}
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-yellow-500" />
              중간: {statistics.by_confidence.medium}
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              낮음: {statistics.by_confidence.low}
            </span>
          </div>
        </div>
      )}

      {/* 관계 목록 */}
      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {relations.map((relation) => {
          const methodConfig = METHOD_CONFIG[relation.method] || METHOD_CONFIG.proximity;
          const MethodIcon = methodConfig.icon;
          const ConfIcon = getConfidenceIcon(relation.confidence);
          const isExpanded = expandedId === relation.id;
          const isSelected = selectedDimensionId === relation.dimension_id;
          const isLinking = linkingDimensionId === relation.dimension_id;

          return (
            <div
              key={relation.id}
              className={`border rounded-lg overflow-hidden transition-all ${
                isSelected
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
              }`}
            >
              {/* 헤더 */}
              <div
                className="flex items-center gap-2 p-3 cursor-pointer"
                onClick={() => {
                  setExpandedId(isExpanded ? null : relation.id);
                  onSelectDimension?.(relation.dimension_id);
                }}
              >
                {/* 방법 아이콘 */}
                <div className={`p-1.5 rounded ${methodConfig.bg}`}>
                  <MethodIcon className={`h-3.5 w-3.5 ${methodConfig.color}`} />
                </div>

                {/* 치수 값 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-medium text-sm truncate">
                      {getDimensionValue(relation.dimension_id)}
                    </span>
                    <ArrowRight className="h-3 w-3 text-gray-400 flex-shrink-0" />
                    <span
                      className={`text-sm truncate ${
                        relation.target_id ? 'text-gray-700 dark:text-gray-300' : 'text-gray-400 italic'
                      }`}
                    >
                      {getTargetName(relation.target_id)}
                    </span>
                  </div>
                </div>

                {/* 신뢰도 배지 */}
                <div
                  className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${getConfidenceBg(
                    relation.confidence
                  )} ${getConfidenceColor(relation.confidence)}`}
                >
                  <ConfIcon className="h-3 w-3" />
                  {(relation.confidence * 100).toFixed(0)}%
                </div>

                {/* 확장 토글 */}
                {isExpanded ? (
                  <ChevronUp className="h-4 w-4 text-gray-400" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-gray-400" />
                )}
              </div>

              {/* 상세 정보 (확장 시) */}
              {isExpanded && (
                <div className="px-3 pb-3 pt-0 space-y-2 border-t border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50">
                  <div className="grid grid-cols-2 gap-2 text-xs mt-2">
                    <div>
                      <span className="text-gray-500">추출 방법:</span>
                      <span className={`ml-1 font-medium ${methodConfig.color}`}>{methodConfig.label}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">관계 유형:</span>
                      <span className="ml-1 font-medium">{relation.relation_type}</span>
                    </div>
                    {relation.direction && (
                      <div>
                        <span className="text-gray-500">방향:</span>
                        <span className="ml-1 font-medium">
                          {relation.direction === 'horizontal' ? '수평' : '수직'}
                        </span>
                      </div>
                    )}
                    {relation.notes && (
                      <div className="col-span-2">
                        <span className="text-gray-500">비고:</span>
                        <span className="ml-1">{relation.notes}</span>
                      </div>
                    )}
                  </div>

                  {/* 수동 연결 및 삭제 버튼 */}
                  {!isLinking ? (
                    <div className="flex gap-2 mt-2">
                      <button
                        className="flex-1 px-3 py-1.5 text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 rounded flex items-center justify-center gap-1"
                        onClick={(e) => {
                          e.stopPropagation();
                          setLinkingDimensionId(relation.dimension_id);
                        }}
                      >
                        <Target className="h-3 w-3" />
                        수동 연결
                      </button>
                      {onDeleteRelation && (
                        <button
                          className="px-3 py-1.5 text-xs bg-red-100 hover:bg-red-200 text-red-700 rounded flex items-center justify-center gap-1"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (confirm('이 관계를 삭제하시겠습니까?')) {
                              onDeleteRelation(relation.id);
                            }
                          }}
                        >
                          <Trash2 className="h-3 w-3" />
                          삭제
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="mt-2">
                      <label className="text-xs text-gray-500 mb-1 block">대상 심볼 선택:</label>
                      <select
                        className="w-full px-2 py-1.5 text-xs border rounded bg-white dark:bg-gray-700"
                        onChange={(e) => handleLink(relation.dimension_id, e.target.value)}
                        defaultValue=""
                      >
                        <option value="" disabled>
                          심볼 선택...
                        </option>
                        {detections.map((det) => (
                          <option key={det.id} value={det.id}>
                            {det.class_name} ({det.id.slice(0, 8)})
                          </option>
                        ))}
                      </select>
                      <button
                        className="w-full mt-1 px-2 py-1 text-xs text-gray-500 hover:text-gray-700"
                        onClick={(e) => {
                          e.stopPropagation();
                          setLinkingDimensionId(null);
                        }}
                      >
                        취소
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
