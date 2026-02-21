/**
 * AgentVerificationPage - Agent-Native Verification UI
 *
 * Multimodal LLM Agent 전용 검증 페이지
 * - symbol(검출) + dimension(치수) 모두 지원
 * - dimension 수정: value/unit/type/tolerance 개별 수정 가능
 * - 빠른 거부: "치수 아님" / "가비지" 원클릭 거부
 * - Playwright 자동화 친화적 (data-action, id 속성)
 */

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { CheckCircle, XCircle, Edit3, ChevronLeft, ChevronRight, SkipForward, Ban, Trash2 } from 'lucide-react';
import { api } from '../lib/api/client';

// ==================== Types ====================

interface QueueItem {
  id: string;
  class_name?: string;
  value?: string;
  unit?: string;
  dimension_type?: string;
  tolerance?: string | null;
  confidence: number;
  priority: string;
  reason: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
}

// drawing_type별 뱃지 색상과 라벨
const DRAWING_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  pid: { label: 'P&ID', color: 'bg-emerald-100 text-emerald-800' },
  electrical: { label: '전기', color: 'bg-blue-100 text-blue-800' },
  dimension_bom: { label: '치수/BOM', color: 'bg-violet-100 text-violet-800' },
  mechanical: { label: '기계', color: 'bg-slate-100 text-slate-800' },
  auto: { label: '자동', color: 'bg-gray-100 text-gray-600' },
};

interface ItemDetail {
  item_id: string;
  item_type: string;
  class_name?: string;
  value?: string;
  raw_text?: string;
  unit?: string;
  dimension_type?: string;
  tolerance?: string | null;
  linked_to?: string | null;
  confidence: number;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  verification_status: string;
  crop_image: string | null;
  context_image: string | null;
  reference_images: string[];
  metadata: { model_id: string; drawing_type: string; class_id?: number };
  verified_by?: string;
}

interface Stats {
  total: number;
  verified: number;
  pending: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

// Dimension 타입 옵션
const DIMENSION_TYPES = [
  { value: 'length', label: '길이' },
  { value: 'diameter', label: '직경 (⌀)' },
  { value: 'radius', label: '반지름 (R)' },
  { value: 'chamfer', label: '챔퍼 (C)' },
  { value: 'angle', label: '각도 (°)' },
  { value: 'gdt', label: 'GD&T 공차' },
  { value: 'surface_roughness', label: '표면거칠기 (▽)' },
  { value: 'note', label: '주석/노트' },
  { value: 'label', label: '라벨/참조' },
  { value: 'unknown', label: '미분류' },
];

const UNIT_OPTIONS = [
  { value: 'mm', label: 'mm' },
  { value: '°', label: '° (도)' },
  { value: 'μm', label: 'μm' },
  { value: '-', label: '없음' },
];

// dimension_type별 배지 색상
const typeColor: Record<string, string> = {
  length: 'bg-blue-100 text-blue-800',
  diameter: 'bg-indigo-100 text-indigo-800',
  radius: 'bg-cyan-100 text-cyan-800',
  chamfer: 'bg-teal-100 text-teal-800',
  angle: 'bg-orange-100 text-orange-800',
  gdt: 'bg-purple-100 text-purple-800',
  surface_roughness: 'bg-pink-100 text-pink-800',
  note: 'bg-gray-200 text-gray-700',
  label: 'bg-gray-200 text-gray-700',
  unknown: 'bg-yellow-100 text-yellow-800',
};

// ==================== Component ====================

export function AgentVerificationPage() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session') || '';
  const itemType = searchParams.get('type') || 'symbol';
  const isDimension = itemType === 'dimension';

  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [detail, setDetail] = useState<ItemDetail | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [deciding, setDeciding] = useState(false);
  const [error, setError] = useState('');
  const [showModify, setShowModify] = useState(false);
  const [allClassNames, setAllClassNames] = useState<string[]>([]);
  const [completed, setCompleted] = useState(false);
  const [drawingType, setDrawingType] = useState('auto');

  // 수정 폼 state (dimension)
  const [modValue, setModValue] = useState('');
  const [modUnit, setModUnit] = useState('');
  const [modType, setModType] = useState('');
  const [modTolerance, setModTolerance] = useState('');
  // 수정 폼 state (symbol)
  const [modClass, setModClass] = useState('');

  // 항목 표시 라벨
  const getItemLabel = (item: QueueItem | null) => {
    if (!item) return '-';
    if (isDimension) return `${item.value || '?'} ${item.unit || 'mm'}`;
    return item.class_name || '-';
  };

  // 수정 폼 초기화 (현재 항목 값으로)
  const initModifyForm = useCallback(() => {
    if (isDimension && detail) {
      setModValue(detail.value || '');
      setModUnit(detail.unit || 'mm');
      setModType(detail.dimension_type || 'unknown');
      setModTolerance(detail.tolerance || '');
    }
    setShowModify(true);
  }, [isDimension, detail]);

  // 큐 로드
  const loadQueue = useCallback(async () => {
    if (!sessionId) {
      setError('session 파라미터가 필요합니다');
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const res = await api.get(`/verification/agent/queue/${sessionId}?item_type=${itemType}`);
      const data = res.data;
      setQueue(data.queue || []);
      setStats(data.stats || null);
      if (data.drawing_type) setDrawingType(data.drawing_type);

      if (!isDimension) {
        const names = [...new Set((data.queue || []).map((q: QueueItem) => q.class_name))].sort();
        setAllClassNames(names as string[]);
      }

      if (!data.queue || data.queue.length === 0) {
        setCompleted(true);
      }
      setError('');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(`큐 로드 실패: ${msg}`);
    } finally {
      setLoading(false);
    }
  }, [sessionId, itemType, isDimension]);

  // 현재 항목 상세 로드
  const loadDetail = useCallback(async (itemId: string) => {
    try {
      const res = await api.get(`/verification/agent/item/${sessionId}/${itemId}?item_type=${itemType}`);
      setDetail(res.data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(`항목 로드 실패: ${msg}`);
    }
  }, [sessionId, itemType]);

  useEffect(() => { loadQueue(); }, [loadQueue]);

  useEffect(() => {
    if (queue.length > 0 && currentIndex < queue.length) {
      loadDetail(queue[currentIndex].id);
      setShowModify(false);
    }
  }, [queue, currentIndex, loadDetail]);

  // 결정 처리
  const handleDecide = useCallback(async (
    action: string,
    extra?: { modified_class?: string; modified_value?: string; modified_unit?: string; modified_type?: string; modified_tolerance?: string; reject_reason?: string }
  ) => {
    if (!queue[currentIndex]) return;
    setDeciding(true);
    try {
      const body: Record<string, string | undefined> = { action, ...extra };
      const res = await api.post(
        `/verification/agent/decide/${sessionId}/${queue[currentIndex].id}?item_type=${itemType}`,
        body
      );
      const data = res.data;

      if (data.remaining_count === 0) {
        setCompleted(true);
      } else {
        setQueue(prev => prev.filter((_, i) => i !== currentIndex));
        setCurrentIndex(prev => Math.min(prev, Math.max(0, queue.length - 2)));
        if (data.stats) setStats(data.stats);
      }
      setShowModify(false);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(`결정 실패: ${msg}`);
    } finally {
      setDeciding(false);
    }
  }, [queue, currentIndex, sessionId, itemType]);

  // 편의 핸들러
  const approve = useCallback(() => handleDecide('approve'), [handleDecide]);
  const reject = useCallback(() => handleDecide('reject'), [handleDecide]);
  const rejectWithReason = useCallback((reason: string) =>
    handleDecide('reject', { reject_reason: reason }), [handleDecide]);
  const modifyDimension = useCallback(() => {
    const extra: Record<string, string> = {};
    if (modValue !== (detail?.value || '')) extra.modified_value = modValue;
    if (modUnit !== (detail?.unit || 'mm')) extra.modified_unit = modUnit;
    if (modType !== (detail?.dimension_type || '')) extra.modified_type = modType;
    if (modTolerance !== (detail?.tolerance || '')) extra.modified_tolerance = modTolerance;
    if (Object.keys(extra).length === 0) return;
    handleDecide('modify', extra);
  }, [handleDecide, modValue, modUnit, modType, modTolerance, detail]);
  const modifySymbol = useCallback(() => {
    if (!modClass) return;
    handleDecide('modify', { modified_class: modClass });
  }, [handleDecide, modClass]);

  // 키보드 단축키
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) return;
      switch (e.key.toLowerCase()) {
        case 'a': approve(); break;
        case 'r': reject(); break;
        case 'n': if (isDimension) rejectWithReason('not_dimension'); break;
        case 's': setCurrentIndex(prev => Math.min(prev + 1, queue.length - 1)); break;
        case 'arrowright': setCurrentIndex(prev => Math.min(prev + 1, queue.length - 1)); break;
        case 'arrowleft': setCurrentIndex(prev => Math.max(prev - 1, 0)); break;
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [approve, reject, rejectWithReason, isDimension, queue.length]);

  // ==================== Render ====================

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-lg text-gray-500">Loading...</div>
      </div>
    );
  }

  if (completed) {
    return (
      <div id="completion-screen" className="flex flex-col items-center justify-center h-screen bg-gray-50 gap-4">
        <CheckCircle className="w-16 h-16 text-green-500" />
        <h1 className="text-2xl font-bold text-gray-800">검증 완료</h1>
        <p className="text-gray-500">
          모든 {isDimension ? '치수' : '심볼'} 항목의 검증이 완료되었습니다.
          {stats && ` (총 ${stats.total}개, 완료 ${stats.verified}개)`}
        </p>
      </div>
    );
  }

  if (error && queue.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  const current = queue[currentIndex];
  const priorityColor: Record<string, string> = {
    critical: 'bg-red-100 text-red-800',
    high: 'bg-orange-100 text-orange-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-green-100 text-green-800',
  };
  const dimType = current?.dimension_type || detail?.dimension_type || 'unknown';

  return (
    <div className="min-h-screen bg-gray-50 p-4 flex flex-col gap-3">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded">
          {error}
        </div>
      )}

      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span id="progress-indicator" className="text-lg font-mono font-bold text-gray-700">
            [{currentIndex + 1}/{queue.length}]
          </span>
          {(() => {
            const dt = DRAWING_TYPE_LABELS[drawingType] || { label: drawingType, color: 'bg-gray-100 text-gray-600' };
            return <span id="drawing-type-badge" className={`px-2 py-0.5 rounded text-xs font-medium ${dt.color}`}>{dt.label}</span>;
          })()}
          <span className="text-xl font-semibold text-gray-900">
            {getItemLabel(current)}
          </span>
          {isDimension && (
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${typeColor[dimType] || 'bg-gray-100'}`}>
              {dimType}
            </span>
          )}
          <span className="text-sm text-gray-500">
            conf: {((current?.confidence || 0) * 100).toFixed(1)}%
          </span>
          {current && (
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityColor[current.priority] || 'bg-gray-100'}`}>
              {current.priority}
            </span>
          )}
        </div>
        {stats && (
          <div className="flex gap-4 text-sm text-gray-500">
            <span>전체: {stats.total}</span>
            <span>대기: {stats.pending}</span>
            <span>완료: {stats.verified}</span>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div className="bg-white rounded-lg shadow-sm p-2">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            id="progress-bar"
            className="bg-blue-500 h-2 rounded-full transition-all"
            style={{ width: stats ? `${(stats.verified / Math.max(stats.total, 1)) * 100}%` : '0%' }}
          />
        </div>
      </div>

      {/* Images */}
      <div className="grid grid-cols-2 gap-4">
        {/* Crop Image */}
        <div className="bg-white rounded-lg shadow-sm p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            {isDimension ? 'Crop (치수 영역)' : 'Crop (검출 영역)'}
          </h3>
          <div className="flex items-center justify-center min-h-[280px] bg-gray-100 rounded">
            {detail?.crop_image ? (
              <img id="crop-image" src={`data:image/jpeg;base64,${detail.crop_image}`} alt="Crop"
                className="max-w-[400px] max-h-[400px] object-contain" />
            ) : (
              <span className="text-gray-400">이미지 없음</span>
            )}
          </div>
          {/* Dimension 메타데이터 - 항상 raw_text 표시 */}
          {isDimension && detail && (
            <div id="dimension-meta" className="mt-3 flex flex-wrap gap-2 text-sm">
              <span className="bg-blue-50 text-blue-700 px-2 py-1 rounded font-medium">
                값: {detail.value} {detail.unit}
              </span>
              <span className="bg-gray-100 text-gray-600 px-2 py-1 rounded">
                raw: {detail.raw_text}
              </span>
              {detail.tolerance && (
                <span className="bg-purple-50 text-purple-700 px-2 py-1 rounded">
                  공차: {detail.tolerance}
                </span>
              )}
              <span className={`px-2 py-1 rounded ${typeColor[detail.dimension_type || 'unknown'] || 'bg-gray-100'}`}>
                {detail.dimension_type || 'unknown'}
              </span>
            </div>
          )}
        </div>

        {/* Context Image */}
        <div className="bg-white rounded-lg shadow-sm p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Context (전체 도면)</h3>
          <div className="flex items-center justify-center min-h-[280px] bg-gray-100 rounded">
            {detail?.context_image ? (
              <img id="context-image" src={`data:image/jpeg;base64,${detail.context_image}`} alt="Context"
                className="max-w-[500px] max-h-[400px] object-contain" />
            ) : (
              <span className="text-gray-400">이미지 없음</span>
            )}
          </div>
        </div>
      </div>

      {/* Dimension: linked_to + OCR detail panel */}
      {isDimension && detail && (detail.linked_to || detail.verified_by === 'agent') && (
        <div id="dimension-detail-panel" className="bg-white rounded-lg shadow-sm p-4 flex flex-wrap gap-4 text-sm">
          {detail.linked_to && (
            <div className="flex items-center gap-2">
              <span className="text-gray-500 font-medium">연결 심볼:</span>
              <span className="bg-indigo-50 text-indigo-700 px-2 py-1 rounded font-mono">{detail.linked_to}</span>
            </div>
          )}
          {detail.verified_by === 'agent' && (
            <span className="bg-cyan-50 text-cyan-700 px-2 py-1 rounded text-xs font-medium">Agent 검증</span>
          )}
        </div>
      )}

      {/* P&ID: 심볼 태그/연결 정보 */}
      {!isDimension && drawingType === 'pid' && detail && (
        <div id="pid-info-panel" className="bg-white rounded-lg shadow-sm p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-2">P&ID 심볼 정보</h3>
          <div className="flex flex-wrap gap-3 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-500">클래스:</span>
              <span className="bg-emerald-50 text-emerald-700 px-2 py-1 rounded font-medium">{detail.class_name}</span>
            </div>
            {detail.metadata?.class_id != null && (
              <div className="flex items-center gap-2">
                <span className="text-gray-500">클래스 ID:</span>
                <span className="font-mono text-gray-700">{detail.metadata.class_id}</span>
              </div>
            )}
            <div className="text-gray-400 text-xs italic">
              연결 정보는 메인 검증 페이지에서 확인 가능
            </div>
          </div>
        </div>
      )}

      {/* Reference Images (symbol only) */}
      {!isDimension && (
        <div className="bg-white rounded-lg shadow-sm p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-2">
            참조 이미지 ({detail?.class_name || '-'})
          </h3>
          <div className="flex gap-4 min-h-[120px] items-center">
            {detail?.reference_images && detail.reference_images.length > 0 ? (
              detail.reference_images.map((ref, i) => (
                <img key={i} src={`data:image/jpeg;base64,${ref}`} alt={`Ref ${i + 1}`}
                  className="w-[150px] h-[150px] object-contain bg-gray-50 rounded border" />
              ))
            ) : (
              <span className="text-gray-400">참조 이미지 없음</span>
            )}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="bg-white rounded-lg shadow-sm p-4 flex flex-col gap-3">
        {/* Row 1: 승인 / 거부 / 수정(열기) + 빠른 거부 */}
        <div className="flex items-center gap-3">
          <button id="btn-approve" data-action="approve" disabled={deciding} onClick={approve}
            className="flex-1 h-14 bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white font-bold rounded-lg flex items-center justify-center gap-2 text-lg transition-colors">
            <CheckCircle className="w-6 h-6" /> 승인 (A)
          </button>
          <button id="btn-reject" data-action="reject" disabled={deciding} onClick={reject}
            className="flex-1 h-14 bg-red-500 hover:bg-red-600 disabled:bg-red-300 text-white font-bold rounded-lg flex items-center justify-center gap-2 text-lg transition-colors">
            <XCircle className="w-6 h-6" /> 거부 (R)
          </button>

          {isDimension ? (
            <>
              <button id="btn-not-dimension" data-action="reject-not-dimension" disabled={deciding}
                onClick={() => rejectWithReason('not_dimension')}
                className="h-14 px-5 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white font-bold rounded-lg flex items-center justify-center gap-2 transition-colors whitespace-nowrap">
                <Ban className="w-5 h-5" /> 치수아님 (N)
              </button>
              <button id="btn-garbage" data-action="reject-garbage" disabled={deciding}
                onClick={() => rejectWithReason('garbage')}
                className="h-14 px-5 bg-gray-500 hover:bg-gray-600 disabled:bg-gray-400 text-white font-bold rounded-lg flex items-center justify-center gap-2 transition-colors whitespace-nowrap">
                <Trash2 className="w-5 h-5" /> 가비지
              </button>
            </>
          ) : null}

          {!showModify && (
            <button id="btn-modify" data-action="modify-open" onClick={initModifyForm}
              className="flex-1 h-14 bg-amber-500 hover:bg-amber-600 text-white font-bold rounded-lg flex items-center justify-center gap-2 text-lg transition-colors">
              <Edit3 className="w-6 h-6" /> 수정
            </button>
          )}
        </div>

        {/* Row 2: 수정 폼 (열렸을 때) */}
        {showModify && isDimension && (
          <div id="modify-form" data-action="modify-form" className="flex items-center gap-2 bg-amber-50 p-3 rounded-lg border border-amber-200">
            <label className="text-sm font-medium text-gray-600 shrink-0">값:</label>
            <input id="input-modify-value" data-action="modify-value" type="text" value={modValue}
              onChange={e => setModValue(e.target.value)}
              className="w-28 h-10 border rounded px-2 text-base" />
            <label className="text-sm font-medium text-gray-600 shrink-0">단위:</label>
            <select id="select-modify-unit" data-action="modify-unit" value={modUnit}
              onChange={e => setModUnit(e.target.value)}
              className="h-10 border rounded px-2 text-sm">
              {UNIT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <label className="text-sm font-medium text-gray-600 shrink-0">타입:</label>
            <select id="select-modify-type" data-action="modify-type" value={modType}
              onChange={e => setModType(e.target.value)}
              className="h-10 border rounded px-2 text-sm">
              {DIMENSION_TYPES.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
            <label className="text-sm font-medium text-gray-600 shrink-0">공차:</label>
            <input id="input-modify-tolerance" data-action="modify-tolerance" type="text" value={modTolerance}
              onChange={e => setModTolerance(e.target.value)} placeholder="±0.2"
              className="w-24 h-10 border rounded px-2 text-base" />
            <button id="btn-modify-confirm" data-action="modify" disabled={deciding}
              onClick={modifyDimension}
              className="h-10 px-6 bg-amber-500 hover:bg-amber-600 disabled:bg-amber-300 text-white font-bold rounded-lg transition-colors shrink-0">
              확인
            </button>
            <button data-action="modify-cancel" onClick={() => setShowModify(false)}
              className="h-10 px-3 bg-gray-200 hover:bg-gray-300 rounded-lg text-sm transition-colors shrink-0">
              취소
            </button>
          </div>
        )}

        {showModify && !isDimension && (
          <div className="flex items-center gap-2 bg-amber-50 p-3 rounded-lg border border-amber-200">
            <select id="select-modify" data-action="modify-select" value={modClass}
              onChange={e => setModClass(e.target.value)}
              className="flex-1 h-10 border rounded px-3 text-base">
              <option value="">클래스 선택...</option>
              {allClassNames.map(name => <option key={name} value={name}>{name}</option>)}
            </select>
            <button id="btn-modify-confirm" data-action="modify" disabled={deciding || !modClass}
              onClick={modifySymbol}
              className="h-10 px-6 bg-amber-500 hover:bg-amber-600 disabled:bg-amber-300 text-white font-bold rounded-lg transition-colors">
              확인
            </button>
            <button onClick={() => setShowModify(false)}
              className="h-10 px-3 bg-gray-200 hover:bg-gray-300 rounded-lg text-sm transition-colors">
              취소
            </button>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="bg-white rounded-lg shadow-sm p-3 flex items-center justify-between">
        <div className="flex gap-2">
          <button id="btn-prev" data-action="prev" disabled={currentIndex === 0}
            onClick={() => setCurrentIndex(prev => Math.max(prev - 1, 0))}
            className="h-10 px-4 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400 rounded-lg flex items-center gap-1 transition-colors">
            <ChevronLeft className="w-4 h-4" /> 이전
          </button>
          <button id="btn-next" data-action="next" disabled={currentIndex >= queue.length - 1}
            onClick={() => setCurrentIndex(prev => Math.min(prev + 1, queue.length - 1))}
            className="h-10 px-4 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400 rounded-lg flex items-center gap-1 transition-colors">
            다음 <ChevronRight className="w-4 h-4" />
          </button>
          <button id="btn-skip" data-action="skip" disabled={currentIndex >= queue.length - 1}
            onClick={() => setCurrentIndex(prev => Math.min(prev + 1, queue.length - 1))}
            className="h-10 px-4 bg-gray-100 hover:bg-gray-200 disabled:text-gray-400 rounded-lg flex items-center gap-1 transition-colors">
            <SkipForward className="w-4 h-4" /> 건너뛰기 (S)
          </button>
        </div>
        <div className="text-xs text-gray-400">
          단축키: A=승인 | R=거부 | {isDimension ? 'N=치수아님 | ' : ''}S=건너뛰기 | ←→=이동
        </div>
      </div>
    </div>
  );
}
