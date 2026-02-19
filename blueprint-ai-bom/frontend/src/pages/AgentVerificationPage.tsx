/**
 * AgentVerificationPage - Agent-Native Verification UI
 *
 * Multimodal LLM Agent 전용 검증 페이지
 * - Playwright 자동화 친화적 (data-action, id 속성)
 * - 고정 레이아웃 (스크린샷 일관성)
 * - 키보드 단축키 지원
 */

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { CheckCircle, XCircle, Edit3, ChevronLeft, ChevronRight, SkipForward } from 'lucide-react';
import { api } from '../lib/api/client';

// ==================== Types ====================

interface QueueItem {
  id: string;
  class_name: string;
  confidence: number;
  priority: string;
  reason: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
}

interface ItemDetail {
  detection_id: string;
  class_name: string;
  confidence: number;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  verification_status: string;
  crop_image: string | null;
  context_image: string | null;
  reference_images: string[];
  metadata: { class_id: number; model_id: string; drawing_type: string };
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

// ==================== Component ====================

export function AgentVerificationPage() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session') || '';

  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [detail, setDetail] = useState<ItemDetail | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [deciding, setDeciding] = useState(false);
  const [error, setError] = useState('');
  const [showModify, setShowModify] = useState(false);
  const [modifyClass, setModifyClass] = useState('');
  const [allClassNames, setAllClassNames] = useState<string[]>([]);
  const [completed, setCompleted] = useState(false);

  // 큐 로드
  const loadQueue = useCallback(async () => {
    if (!sessionId) {
      setError('session 파라미터가 필요합니다');
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const res = await api.get(`/verification/agent/queue/${sessionId}?item_type=symbol`);
      const data = res.data;
      setQueue(data.queue || []);
      setStats(data.stats || null);

      // 전체 클래스명 수집 (수정 드롭다운용)
      const names = [...new Set((data.queue || []).map((q: QueueItem) => q.class_name))].sort();
      setAllClassNames(names as string[]);

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
  }, [sessionId]);

  // 현재 항목 상세 로드
  const loadDetail = useCallback(async (detectionId: string) => {
    try {
      const res = await api.get(`/verification/agent/item/${sessionId}/${detectionId}`);
      setDetail(res.data);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(`항목 로드 실패: ${msg}`);
    }
  }, [sessionId]);

  // 초기 로드
  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  // 현재 항목 변경 시 상세 로드
  useEffect(() => {
    if (queue.length > 0 && currentIndex < queue.length) {
      loadDetail(queue[currentIndex].id);
    }
  }, [queue, currentIndex, loadDetail]);

  // 결정 처리
  const handleDecide = useCallback(async (action: string, modifiedClass?: string) => {
    if (!queue[currentIndex]) return;
    setDeciding(true);
    try {
      const res = await api.post(
        `/verification/agent/decide/${sessionId}/${queue[currentIndex].id}`,
        { action, modified_class: modifiedClass || undefined }
      );
      const data = res.data;

      if (data.remaining_count === 0) {
        setCompleted(true);
      } else {
        // 큐에서 현재 항목 제거 후 다음으로
        setQueue(prev => prev.filter((_, i) => i !== currentIndex));
        setCurrentIndex(prev => Math.min(prev, Math.max(0, queue.length - 2)));
        if (data.stats) setStats(data.stats);
      }
      setShowModify(false);
      setModifyClass('');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(`결정 실패: ${msg}`);
    } finally {
      setDeciding(false);
    }
  }, [queue, currentIndex, sessionId]);

  // 키보드 단축키
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) return;
      switch (e.key.toLowerCase()) {
        case 'a': handleDecide('approve'); break;
        case 'r': handleDecide('reject'); break;
        case 's': setCurrentIndex(prev => Math.min(prev + 1, queue.length - 1)); break;
        case 'arrowright': setCurrentIndex(prev => Math.min(prev + 1, queue.length - 1)); break;
        case 'arrowleft': setCurrentIndex(prev => Math.max(prev - 1, 0)); break;
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleDecide, queue.length]);

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
          모든 항목의 검증이 완료되었습니다.
          {stats && ` (총 ${stats.total}개, 승인 ${stats.verified}개)`}
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

  return (
    <div className="min-h-screen bg-gray-50 p-4 flex flex-col gap-4">
      {/* Error banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded">
          {error}
        </div>
      )}

      {/* Header: Progress + Class Info */}
      <div className="bg-white rounded-lg shadow-sm p-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span id="progress-indicator" className="text-lg font-mono font-bold text-gray-700">
            [{currentIndex + 1}/{queue.length}]
          </span>
          <span className="text-xl font-semibold text-gray-900">
            {current?.class_name || '-'}
          </span>
          <span className="text-sm text-gray-500">
            confidence: {((current?.confidence || 0) * 100).toFixed(1)}%
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
            style={{ width: stats ? `${((stats.verified) / Math.max(stats.total, 1)) * 100}%` : '0%' }}
          />
        </div>
      </div>

      {/* Images: Crop + Context */}
      <div className="grid grid-cols-2 gap-4">
        {/* Crop Image */}
        <div className="bg-white rounded-lg shadow-sm p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Crop (검출 영역)</h3>
          <div className="flex items-center justify-center min-h-[300px] bg-gray-100 rounded">
            {detail?.crop_image ? (
              <img
                id="crop-image"
                src={`data:image/jpeg;base64,${detail.crop_image}`}
                alt="Detection crop"
                className="max-w-[400px] max-h-[400px] object-contain"
              />
            ) : (
              <span className="text-gray-400">이미지 없음</span>
            )}
          </div>
        </div>

        {/* Context Image */}
        <div className="bg-white rounded-lg shadow-sm p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Context (전체 도면)</h3>
          <div className="flex items-center justify-center min-h-[300px] bg-gray-100 rounded">
            {detail?.context_image ? (
              <img
                id="context-image"
                src={`data:image/jpeg;base64,${detail.context_image}`}
                alt="Full drawing context"
                className="max-w-[500px] max-h-[400px] object-contain"
              />
            ) : (
              <span className="text-gray-400">이미지 없음</span>
            )}
          </div>
        </div>
      </div>

      {/* Reference Images */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <h3 className="text-sm font-medium text-gray-500 mb-2">
          참조 이미지 ({detail?.class_name || '-'})
        </h3>
        <div className="flex gap-4 min-h-[120px] items-center">
          {detail?.reference_images && detail.reference_images.length > 0 ? (
            detail.reference_images.map((ref, i) => (
              <img
                key={i}
                src={`data:image/jpeg;base64,${ref}`}
                alt={`Reference ${i + 1}`}
                className="w-[150px] h-[150px] object-contain bg-gray-50 rounded border"
              />
            ))
          ) : (
            <span className="text-gray-400">참조 이미지 없음</span>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="bg-white rounded-lg shadow-sm p-4 flex items-center gap-4">
        {/* Approve */}
        <button
          id="btn-approve"
          data-action="approve"
          disabled={deciding}
          onClick={() => handleDecide('approve')}
          className="flex-1 h-14 bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white font-bold rounded-lg flex items-center justify-center gap-2 text-lg transition-colors"
        >
          <CheckCircle className="w-6 h-6" />
          승인 (A)
        </button>

        {/* Reject */}
        <button
          id="btn-reject"
          data-action="reject"
          disabled={deciding}
          onClick={() => handleDecide('reject')}
          className="flex-1 h-14 bg-red-500 hover:bg-red-600 disabled:bg-red-300 text-white font-bold rounded-lg flex items-center justify-center gap-2 text-lg transition-colors"
        >
          <XCircle className="w-6 h-6" />
          거부 (R)
        </button>

        {/* Modify */}
        <div className="flex-1 flex gap-2">
          {showModify ? (
            <>
              <select
                id="select-modify"
                data-action="modify-select"
                value={modifyClass}
                onChange={e => setModifyClass(e.target.value)}
                className="flex-1 h-14 border rounded-lg px-3 text-lg"
              >
                <option value="">클래스 선택...</option>
                {allClassNames.map(name => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
              <button
                id="btn-modify-confirm"
                data-action="modify"
                disabled={deciding || !modifyClass}
                onClick={() => handleDecide('modify', modifyClass)}
                className="h-14 px-6 bg-amber-500 hover:bg-amber-600 disabled:bg-amber-300 text-white font-bold rounded-lg transition-colors"
              >
                확인
              </button>
            </>
          ) : (
            <button
              id="btn-modify"
              data-action="modify-open"
              onClick={() => setShowModify(true)}
              className="w-full h-14 bg-amber-500 hover:bg-amber-600 text-white font-bold rounded-lg flex items-center justify-center gap-2 text-lg transition-colors"
            >
              <Edit3 className="w-6 h-6" />
              수정
            </button>
          )}
        </div>
      </div>

      {/* Navigation Footer */}
      <div className="bg-white rounded-lg shadow-sm p-3 flex items-center justify-between">
        <div className="flex gap-2">
          <button
            id="btn-prev"
            data-action="prev"
            disabled={currentIndex === 0}
            onClick={() => setCurrentIndex(prev => Math.max(prev - 1, 0))}
            className="h-10 px-4 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400 rounded-lg flex items-center gap-1 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" /> 이전
          </button>
          <button
            id="btn-next"
            data-action="next"
            disabled={currentIndex >= queue.length - 1}
            onClick={() => setCurrentIndex(prev => Math.min(prev + 1, queue.length - 1))}
            className="h-10 px-4 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 disabled:text-gray-400 rounded-lg flex items-center gap-1 transition-colors"
          >
            다음 <ChevronRight className="w-4 h-4" />
          </button>
          <button
            id="btn-skip"
            data-action="skip"
            disabled={currentIndex >= queue.length - 1}
            onClick={() => setCurrentIndex(prev => Math.min(prev + 1, queue.length - 1))}
            className="h-10 px-4 bg-gray-100 hover:bg-gray-200 disabled:text-gray-400 rounded-lg flex items-center gap-1 transition-colors"
          >
            <SkipForward className="w-4 h-4" /> 건너뛰기 (S)
          </button>
        </div>
        <div className="text-xs text-gray-400">
          단축키: A=승인 | R=거부 | S=건너뛰기 | ←→=이동
        </div>
      </div>
    </div>
  );
}
