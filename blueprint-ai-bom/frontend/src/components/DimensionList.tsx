/**
 * DimensionList - 치수 목록 및 검증 컴포넌트
 *
 * 치수 OCR 결과를 테이블 형태로 표시하고 검증 기능 제공
 */

import { useState, useMemo } from 'react';
import {
  Check,
  X,
  Edit2,
  Trash2,
  Filter,
  Download,
} from 'lucide-react';

interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

interface Dimension {
  id: string;
  bbox: BoundingBox;
  value: string;
  raw_text: string;
  unit: string | null;
  tolerance: string | null;
  dimension_type: string;
  confidence: number;
  verification_status: 'pending' | 'approved' | 'rejected' | 'modified' | 'manual';
  modified_value: string | null;
  linked_to: string | null;
}

interface DimensionStats {
  pending: number;
  approved: number;
  rejected: number;
  modified: number;
  manual: number;
}

interface DimensionListProps {
  dimensions: Dimension[];
  stats?: DimensionStats;
  onVerify?: (id: string, status: 'approved' | 'rejected') => void;
  onEdit?: (id: string, newValue: string) => void;
  onDelete?: (id: string) => void;
  onBulkApprove?: (ids: string[]) => void;
  onExport?: () => void;
  onHover?: (id: string | null) => void;
  selectedId?: string | null;
}

// 치수 유형 라벨
const DIMENSION_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  length: { label: '길이', color: 'bg-blue-100 text-blue-700' },
  diameter: { label: '직경', color: 'bg-purple-100 text-purple-700' },
  radius: { label: '반경', color: 'bg-pink-100 text-pink-700' },
  angle: { label: '각도', color: 'bg-orange-100 text-orange-700' },
  tolerance: { label: '공차', color: 'bg-yellow-100 text-yellow-700' },
  surface_finish: { label: '표면', color: 'bg-green-100 text-green-700' },
  unknown: { label: '기타', color: 'bg-gray-100 text-gray-700' },
};

// 검증 상태 스타일
const STATUS_STYLES: Record<string, { bg: string; icon: React.ReactNode }> = {
  pending: { bg: 'bg-gray-50', icon: null },
  approved: { bg: 'bg-green-50', icon: <Check className="w-4 h-4 text-green-600" /> },
  rejected: { bg: 'bg-red-50', icon: <X className="w-4 h-4 text-red-600" /> },
  modified: { bg: 'bg-blue-50', icon: <Edit2 className="w-4 h-4 text-blue-600" /> },
  manual: { bg: 'bg-purple-50', icon: <Edit2 className="w-4 h-4 text-purple-600" /> },
};

export function DimensionList({
  dimensions,
  stats,
  onVerify,
  onEdit,
  onDelete,
  onBulkApprove,
  onExport,
  onHover,
  selectedId,
}: DimensionListProps) {
  const [filter, setFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'confidence' | 'type' | 'value'>('confidence');
  const [sortAsc, setSortAsc] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  // 필터링 및 정렬
  const filteredDimensions = useMemo(() => {
    let result = [...dimensions];

    // 필터
    if (filter !== 'all') {
      result = result.filter((d) => d.verification_status === filter);
    }

    // 정렬
    result.sort((a, b) => {
      let cmp = 0;
      if (sortBy === 'confidence') {
        cmp = a.confidence - b.confidence;
      } else if (sortBy === 'type') {
        cmp = a.dimension_type.localeCompare(b.dimension_type);
      } else if (sortBy === 'value') {
        cmp = a.value.localeCompare(b.value);
      }
      return sortAsc ? cmp : -cmp;
    });

    return result;
  }, [dimensions, filter, sortBy, sortAsc]);

  // Pending 항목들
  const pendingIds = dimensions
    .filter((d) => d.verification_status === 'pending')
    .map((d) => d.id);

  // 수정 시작
  const startEdit = (dim: Dimension) => {
    setEditingId(dim.id);
    setEditValue(dim.modified_value || dim.value);
  };

  // 수정 저장
  const saveEdit = () => {
    if (editingId && onEdit) {
      onEdit(editingId, editValue);
    }
    setEditingId(null);
    setEditValue('');
  };

  // 수정 취소
  const cancelEdit = () => {
    setEditingId(null);
    setEditValue('');
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* 헤더 */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">
            치수 목록 ({dimensions.length}개)
          </h3>
          <div className="flex items-center gap-2">
            {onExport && (
              <button
                onClick={onExport}
                className="flex items-center gap-1 px-3 py-1.5 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <Download className="w-4 h-4" />
                내보내기
              </button>
            )}
          </div>
        </div>

        {/* 통계 */}
        {stats && (
          <div className="flex gap-4 text-sm">
            <span className="text-gray-500">
              대기: <span className="font-medium text-gray-700">{stats.pending}</span>
            </span>
            <span className="text-green-600">
              승인: <span className="font-medium">{stats.approved}</span>
            </span>
            <span className="text-red-600">
              거부: <span className="font-medium">{stats.rejected}</span>
            </span>
            <span className="text-blue-600">
              수정: <span className="font-medium">{stats.modified + stats.manual}</span>
            </span>
          </div>
        )}
      </div>

      {/* 필터 및 정렬 */}
      <div className="p-3 border-b border-gray-200 flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-400" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value="all">전체</option>
            <option value="pending">대기</option>
            <option value="approved">승인</option>
            <option value="rejected">거부</option>
            <option value="modified">수정</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">정렬:</span>
          <button
            onClick={() => {
              if (sortBy === 'confidence') setSortAsc(!sortAsc);
              else {
                setSortBy('confidence');
                setSortAsc(false);
              }
            }}
            className={`text-sm px-2 py-1 rounded ${
              sortBy === 'confidence' ? 'bg-primary-100 text-primary-700' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            신뢰도 {sortBy === 'confidence' && (sortAsc ? '↑' : '↓')}
          </button>
          <button
            onClick={() => {
              if (sortBy === 'type') setSortAsc(!sortAsc);
              else {
                setSortBy('type');
                setSortAsc(true);
              }
            }}
            className={`text-sm px-2 py-1 rounded ${
              sortBy === 'type' ? 'bg-primary-100 text-primary-700' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            유형 {sortBy === 'type' && (sortAsc ? '↑' : '↓')}
          </button>
        </div>

        {/* 일괄 승인 */}
        {pendingIds.length > 0 && onBulkApprove && (
          <button
            onClick={() => onBulkApprove(pendingIds)}
            className="ml-auto text-sm px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200"
          >
            전체 승인 ({pendingIds.length})
          </button>
        )}
      </div>

      {/* 목록 */}
      <div className="max-h-96 overflow-y-auto">
        {filteredDimensions.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            {filter === 'all' ? '치수가 없습니다.' : '해당 상태의 치수가 없습니다.'}
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-gray-600">값</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">유형</th>
                <th className="px-4 py-2 text-left font-medium text-gray-600">공차</th>
                <th className="px-4 py-2 text-center font-medium text-gray-600">신뢰도</th>
                <th className="px-4 py-2 text-center font-medium text-gray-600">상태</th>
                <th className="px-4 py-2 text-center font-medium text-gray-600">액션</th>
              </tr>
            </thead>
            <tbody>
              {filteredDimensions.map((dim) => {
                const typeInfo = DIMENSION_TYPE_LABELS[dim.dimension_type] || DIMENSION_TYPE_LABELS.unknown;
                const statusStyle = STATUS_STYLES[dim.verification_status] || STATUS_STYLES.pending;
                const isEditing = editingId === dim.id;
                const isSelected = selectedId === dim.id;

                return (
                  <tr
                    key={dim.id}
                    onMouseEnter={() => onHover?.(dim.id)}
                    onMouseLeave={() => onHover?.(null)}
                    className={`
                      border-t border-gray-100 transition-colors
                      ${statusStyle.bg}
                      ${isSelected ? 'ring-2 ring-primary-500 ring-inset' : ''}
                      hover:bg-gray-50
                    `}
                  >
                    {/* 값 */}
                    <td className="px-4 py-2">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') saveEdit();
                            if (e.key === 'Escape') cancelEdit();
                          }}
                          autoFocus
                          className="w-full px-2 py-1 border border-primary-500 rounded text-sm"
                        />
                      ) : (
                        <span className="font-mono">
                          {dim.modified_value || dim.value}
                          {dim.unit && <span className="text-gray-500 ml-1">{dim.unit}</span>}
                        </span>
                      )}
                    </td>

                    {/* 유형 */}
                    <td className="px-4 py-2">
                      <span className={`text-xs px-2 py-0.5 rounded ${typeInfo.color}`}>
                        {typeInfo.label}
                      </span>
                    </td>

                    {/* 공차 */}
                    <td className="px-4 py-2 text-gray-600 font-mono text-xs">
                      {dim.tolerance || '-'}
                    </td>

                    {/* 신뢰도 */}
                    <td className="px-4 py-2 text-center">
                      <span
                        className={`text-xs font-medium ${
                          dim.confidence >= 0.8
                            ? 'text-green-600'
                            : dim.confidence >= 0.5
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        }`}
                      >
                        {(dim.confidence * 100).toFixed(0)}%
                      </span>
                    </td>

                    {/* 상태 */}
                    <td className="px-4 py-2 text-center">
                      {statusStyle.icon || <span className="text-gray-400">-</span>}
                    </td>

                    {/* 액션 */}
                    <td className="px-4 py-2">
                      <div className="flex items-center justify-center gap-1">
                        {isEditing ? (
                          <>
                            <button
                              onClick={saveEdit}
                              className="p-1 text-green-600 hover:bg-green-100 rounded"
                              title="저장"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                            <button
                              onClick={cancelEdit}
                              className="p-1 text-gray-500 hover:bg-gray-100 rounded"
                              title="취소"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </>
                        ) : (
                          <>
                            {dim.verification_status === 'pending' && onVerify && (
                              <>
                                <button
                                  onClick={() => onVerify(dim.id, 'approved')}
                                  className="p-1 text-green-600 hover:bg-green-100 rounded"
                                  title="승인"
                                >
                                  <Check className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => onVerify(dim.id, 'rejected')}
                                  className="p-1 text-red-600 hover:bg-red-100 rounded"
                                  title="거부"
                                >
                                  <X className="w-4 h-4" />
                                </button>
                              </>
                            )}
                            {onEdit && (
                              <button
                                onClick={() => startEdit(dim)}
                                className="p-1 text-blue-600 hover:bg-blue-100 rounded"
                                title="수정"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                            )}
                            {onDelete && (
                              <button
                                onClick={() => onDelete(dim.id)}
                                className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-100 rounded"
                                title="삭제"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default DimensionList;
