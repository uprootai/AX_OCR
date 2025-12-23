/**
 * VerificationQueue - Active Learning 검증 큐 컴포넌트
 *
 * 우선순위 기반 검증 큐 표시 및 일괄 승인 기능
 * - CRITICAL: 신뢰도 < 0.7 (빨간색)
 * - HIGH: 심볼 연결 없음 (주황색)
 * - MEDIUM: 신뢰도 0.7-0.9 (노란색)
 * - LOW: 신뢰도 >= 0.9 (초록색, 자동 승인 후보)
 */

import { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Clock,
  Zap,
  ChevronDown,
  ChevronUp,
  Check,
  X,
  Timer,
  TrendingUp,
} from 'lucide-react';

interface VerificationItem {
  id: string;
  item_type: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  confidence: number;
  has_relation: boolean;
  reason: string;
  data: Record<string, unknown>;
}

interface VerificationStats {
  total: number;
  verified: number;
  pending: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  auto_approve_candidates: number;
  estimated_review_time_minutes: number;
}

interface VerificationQueueProps {
  sessionId: string;
  itemType?: 'dimension' | 'symbol';
  onVerify?: (itemId: string, action: 'approved' | 'rejected' | 'modified') => void;
  onAutoApprove?: () => void;
  onItemSelect?: (itemId: string) => void;
  apiBaseUrl?: string;
}

const PRIORITY_CONFIG = {
  critical: {
    icon: AlertTriangle,
    label: 'Critical',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-700',
    badgeColor: 'bg-red-100 text-red-700',
    description: '즉시 확인 필요',
  },
  high: {
    icon: AlertCircle,
    label: 'High',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    textColor: 'text-orange-700',
    badgeColor: 'bg-orange-100 text-orange-700',
    description: '연결 확인 필요',
  },
  medium: {
    icon: Clock,
    label: 'Medium',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    textColor: 'text-yellow-700',
    badgeColor: 'bg-yellow-100 text-yellow-700',
    description: '검토 권장',
  },
  low: {
    icon: CheckCircle2,
    label: 'Low',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-700',
    badgeColor: 'bg-green-100 text-green-700',
    description: '자동 승인 후보',
  },
};

export function VerificationQueue({
  sessionId,
  itemType = 'dimension',
  onVerify,
  onAutoApprove,
  onItemSelect,
  apiBaseUrl = 'http://localhost:5020',
}: VerificationQueueProps) {
  const [queue, setQueue] = useState<VerificationItem[]>([]);
  const [stats, setStats] = useState<VerificationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedPriorities, setExpandedPriorities] = useState<Set<string>>(
    new Set(['critical', 'high'])
  );
  const [autoApproving, setAutoApproving] = useState(false);
  const [verifyingId, setVerifyingId] = useState<string | null>(null);

  // 큐 데이터 로드
  const loadQueue = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${apiBaseUrl}/verification/queue/${sessionId}?item_type=${itemType}`
      );

      if (!response.ok) {
        throw new Error('검증 큐를 불러올 수 없습니다');
      }

      const data = await response.json();
      setQueue(data.queue || []);
      setStats(data.stats || null);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  }, [sessionId, itemType, apiBaseUrl]);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  // 항목 검증
  const handleVerify = async (itemId: string, action: 'approved' | 'rejected') => {
    setVerifyingId(itemId);
    try {
      const response = await fetch(`${apiBaseUrl}/verification/verify/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          item_id: itemId,
          item_type: itemType,
          action: action,
        }),
      });

      if (!response.ok) {
        throw new Error('검증 실패');
      }

      // 외부 콜백 호출
      onVerify?.(itemId, action);

      // 큐 새로고침
      await loadQueue();
    } catch (err) {
      console.error('Verification error:', err);
    } finally {
      setVerifyingId(null);
    }
  };

  // 자동 승인
  const handleAutoApprove = async () => {
    setAutoApproving(true);
    try {
      const response = await fetch(
        `${apiBaseUrl}/verification/auto-approve/${sessionId}?item_type=${itemType}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error('일괄 승인 실패');
      }

      const result = await response.json();
      console.log('Auto-approve result:', result);

      onAutoApprove?.();
      await loadQueue();
    } catch (err) {
      console.error('Auto-approve error:', err);
    } finally {
      setAutoApproving(false);
    }
  };

  // 우선순위 섹션 토글
  const togglePriority = (priority: string) => {
    setExpandedPriorities((prev) => {
      const next = new Set(prev);
      if (next.has(priority)) {
        next.delete(priority);
      } else {
        next.add(priority);
      }
      return next;
    });
  };

  // 우선순위별 그룹화
  const groupedQueue = queue.reduce(
    (acc, item) => {
      const priority = item.priority as keyof typeof acc;
      if (!acc[priority]) acc[priority] = [];
      acc[priority].push(item);
      return acc;
    },
    { critical: [], high: [], medium: [], low: [] } as Record<string, VerificationItem[]>
  );

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6 text-center">
        <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full mx-auto mb-2" />
        <p className="text-gray-500">검증 큐 로딩 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error}
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* 헤더 */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-primary-50 to-blue-50">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <Zap className="w-5 h-5 text-primary-500" />
            Active Learning 검증 큐
          </h3>
          {stats && stats.auto_approve_candidates > 0 && (
            <button
              onClick={handleAutoApprove}
              disabled={autoApproving}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50"
            >
              {autoApproving ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  처리 중...
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  자동 승인 ({stats.auto_approve_candidates})
                </>
              )}
            </button>
          )}
        </div>

        {/* 통계 */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-white/60 rounded-lg p-2 text-center">
              <div className="text-2xl font-bold text-gray-900">{stats.pending}</div>
              <div className="text-xs text-gray-500">검토 대기</div>
            </div>
            <div className="bg-white/60 rounded-lg p-2 text-center">
              <div className="text-2xl font-bold text-green-600">{stats.verified}</div>
              <div className="text-xs text-gray-500">검증 완료</div>
            </div>
            <div className="bg-white/60 rounded-lg p-2 text-center flex items-center justify-center gap-1">
              <Timer className="w-4 h-4 text-blue-500" />
              <div>
                <span className="text-lg font-bold text-blue-600">
                  {stats.estimated_review_time_minutes}
                </span>
                <span className="text-xs text-gray-500 ml-1">분</span>
              </div>
            </div>
            <div className="bg-white/60 rounded-lg p-2 text-center flex items-center justify-center gap-1">
              <TrendingUp className="w-4 h-4 text-purple-500" />
              <div>
                <span className="text-lg font-bold text-purple-600">
                  {stats.total > 0
                    ? Math.round((stats.verified / stats.total) * 100)
                    : 0}
                </span>
                <span className="text-xs text-gray-500">%</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 우선순위별 섹션 */}
      <div className="divide-y divide-gray-100">
        {(['critical', 'high', 'medium', 'low'] as const).map((priority) => {
          const config = PRIORITY_CONFIG[priority];
          const items = groupedQueue[priority];
          const isExpanded = expandedPriorities.has(priority);
          const Icon = config.icon;

          if (items.length === 0) return null;

          return (
            <div key={priority}>
              {/* 섹션 헤더 */}
              <button
                onClick={() => togglePriority(priority)}
                className={`w-full flex items-center justify-between p-3 hover:bg-gray-50 transition-colors ${config.bgColor}`}
              >
                <div className="flex items-center gap-2">
                  <Icon className={`w-4 h-4 ${config.textColor}`} />
                  <span className={`font-medium ${config.textColor}`}>
                    {config.label}
                  </span>
                  <span
                    className={`text-xs px-1.5 py-0.5 rounded-full ${config.badgeColor}`}
                  >
                    {items.length}
                  </span>
                  <span className="text-xs text-gray-400">{config.description}</span>
                </div>
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4 text-gray-400" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                )}
              </button>

              {/* 항목 목록 */}
              {isExpanded && (
                <div className="bg-white">
                  {items.map((item) => {
                    const isVerifying = verifyingId === item.id;
                    const displayValue =
                      (item.data.modified_value as string) ||
                      (item.data.value as string) ||
                      (item.data.class_name as string) ||
                      item.id;

                    return (
                      <div
                        key={item.id}
                        onClick={() => onItemSelect?.(item.id)}
                        className={`
                          flex items-center justify-between p-3 border-b border-gray-50
                          hover:bg-gray-50 cursor-pointer transition-colors
                          ${config.borderColor} border-l-2
                        `}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-sm truncate">
                              {displayValue}
                            </span>
                            {item.data.dimension_type ? (
                              <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                                {String(item.data.dimension_type)}
                              </span>
                            ) : null}
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <span
                              className={`text-xs ${
                                item.confidence >= 0.7
                                  ? 'text-green-600'
                                  : item.confidence >= 0.5
                                  ? 'text-yellow-600'
                                  : 'text-red-600'
                              }`}
                            >
                              {(item.confidence * 100).toFixed(0)}%
                            </span>
                            <span className="text-xs text-gray-400">{item.reason}</span>
                          </div>
                        </div>

                        {/* 액션 버튼 */}
                        <div
                          className="flex items-center gap-1 ml-2"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {isVerifying ? (
                            <div className="w-6 h-6 border-2 border-gray-300 border-t-primary-500 rounded-full animate-spin" />
                          ) : (
                            <>
                              <button
                                onClick={() => handleVerify(item.id, 'approved')}
                                className="p-1.5 text-green-600 hover:bg-green-100 rounded-lg transition-colors"
                                title="승인"
                              >
                                <Check className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleVerify(item.id, 'rejected')}
                                className="p-1.5 text-red-600 hover:bg-red-100 rounded-lg transition-colors"
                                title="거부"
                              >
                                <X className="w-4 h-4" />
                              </button>
                            </>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 빈 상태 */}
      {queue.length === 0 && (
        <div className="p-8 text-center">
          <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-3" />
          <h4 className="font-medium text-gray-900 mb-1">모든 항목 검증 완료!</h4>
          <p className="text-sm text-gray-500">
            더 이상 검토할 항목이 없습니다.
          </p>
        </div>
      )}
    </div>
  );
}

export default VerificationQueue;
