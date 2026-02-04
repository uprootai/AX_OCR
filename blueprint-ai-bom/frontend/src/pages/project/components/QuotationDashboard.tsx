/**
 * QuotationDashboard - 견적 현황 대시보드
 * Phase 3: BOM 항목 + 견적 집계 통합 표시
 * - 견적 집계 API 호출 (자동 로드 + 수동 새로고침)
 * - 통계 카드 (소계/VAT/합계/진행률)
 * - 재질별 분류 테이블
 * - 세션별 견적 항목 테이블
 * - PDF/Excel 다운로드
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart3,
  ExternalLink,
  FileText,
  RefreshCw,
  Download,
  Loader2,
  FileSpreadsheet,
} from 'lucide-react';
import {
  projectApi,
  type BOMItem,
  type ProjectDetail,
  type ProjectQuotationResponse,
} from '../../../lib/api';
import { MaterialBreakdown } from './MaterialBreakdown';

type FilterType = 'all' | 'completed' | 'pending' | 'no_session';

interface QuotationDashboardProps {
  projectId: string;
  project: ProjectDetail;
  bomItems: BOMItem[];
}

const STATUS_BADGE: Record<string, string> = {
  completed: 'bg-green-100 text-green-600',
  detecting: 'bg-blue-100 text-blue-600',
  detected: 'bg-blue-100 text-blue-600',
  verifying: 'bg-yellow-100 text-yellow-600',
  error: 'bg-red-100 text-red-600',
};

export function QuotationDashboard({
  projectId,
  project,
  bomItems,
}: QuotationDashboardProps) {
  const [filter, setFilter] = useState<FilterType>('all');
  const [quotation, setQuotation] = useState<ProjectQuotationResponse | null>(null);
  const [isAggregating, setIsAggregating] = useState(false);

  // 견적 집계 로드
  const loadQuotation = useCallback(async (refresh = false) => {
    setIsAggregating(true);
    try {
      const data = await projectApi.getQuotation(projectId, refresh);
      setQuotation(data);
    } catch (err) {
      console.error('Failed to load quotation:', err);
    } finally {
      setIsAggregating(false);
    }
  }, [projectId]);

  // 마운트 시 자동 로드
  useEffect(() => {
    loadQuotation(false);
  }, [loadQuotation]);

  // 세션 맵 (기존 bomItems + sessions 조인)
  const sessionMap = useMemo(() => {
    const map = new Map<string, (typeof project.sessions)[0]>();
    for (const s of project.sessions) {
      map.set(s.session_id, s);
    }
    return map;
  }, [project.sessions]);

  // quotation items에서 소계 맵핑
  const quotationSubtotalMap = useMemo(() => {
    const map = new Map<string, number>();
    if (quotation) {
      for (const item of quotation.items) {
        map.set(item.session_id, item.subtotal);
      }
    }
    return map;
  }, [quotation]);

  const quotationItems = useMemo(
    () => bomItems.filter((i) => i.needs_quotation),
    [bomItems]
  );

  const itemsWithSession = useMemo(
    () =>
      quotationItems.map((item) => ({
        ...item,
        session: item.session_id ? sessionMap.get(item.session_id) : undefined,
        subtotal: item.session_id ? (quotationSubtotalMap.get(item.session_id) ?? 0) : 0,
      })),
    [quotationItems, sessionMap, quotationSubtotalMap]
  );

  // 통계 (quotation 우선, 없으면 기존 방식)
  const stats = useMemo(() => {
    if (quotation) {
      return {
        total: quotation.summary.total_sessions,
        completed: quotation.summary.completed_sessions,
        quoted: quotation.summary.quoted_sessions,
        subtotal: quotation.summary.subtotal,
        vat: quotation.summary.vat,
        grandTotal: quotation.summary.total,
        progress: quotation.summary.progress_percent,
      };
    }
    const total = quotationItems.length;
    const completed = itemsWithSession.filter(
      (i) => i.session?.status === 'completed'
    ).length;
    return {
      total,
      completed,
      quoted: 0,
      subtotal: 0,
      vat: 0,
      grandTotal: 0,
      progress: total > 0 ? Math.round((completed / total) * 100) : 0,
    };
  }, [quotation, quotationItems, itemsWithSession]);

  // 필터링
  const filteredItems = useMemo(() => {
    switch (filter) {
      case 'completed':
        return itemsWithSession.filter((i) => i.session?.status === 'completed');
      case 'pending':
        return itemsWithSession.filter(
          (i) => i.session && i.session.status !== 'completed'
        );
      case 'no_session':
        return itemsWithSession.filter((i) => !i.session);
      default:
        return itemsWithSession;
    }
  }, [filter, itemsWithSession]);

  const formatCurrency = (v: number) =>
    v > 0 ? `₩${v.toLocaleString()}` : '-';

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl border overflow-hidden">
        {/* 헤더 */}
        <div className="p-4 border-b flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-gray-400" />
            <h3 className="font-semibold text-gray-900">견적 현황</h3>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => loadQuotation(true)}
              disabled={isAggregating}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
              title="견적 집계"
            >
              {isAggregating ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <RefreshCw className="w-3.5 h-3.5" />
              )}
              견적 집계
            </button>
            {quotation && (
              <>
                <a
                  href={projectApi.getQuotationDownloadUrl(projectId, 'pdf')}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs border rounded-lg text-gray-600 hover:bg-gray-50 transition-colors"
                  download
                >
                  <Download className="w-3.5 h-3.5" />
                  PDF
                </a>
                <a
                  href={projectApi.getQuotationDownloadUrl(projectId, 'excel')}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs border rounded-lg text-gray-600 hover:bg-gray-50 transition-colors"
                  download
                >
                  <FileSpreadsheet className="w-3.5 h-3.5" />
                  Excel
                </a>
              </>
            )}
          </div>
        </div>

        {/* 통계 카드 */}
        <div className="p-4 border-b">
          <div className="grid grid-cols-4 gap-3 mb-3">
            <StatCard label="견적대상" value={`${stats.total}개`} color="text-gray-900" />
            <StatCard label="분석완료" value={`${stats.completed}개`} color="text-green-600" />
            <StatCard
              label="소계"
              value={formatCurrency(stats.subtotal)}
              color="text-blue-600"
            />
            <StatCard
              label="합계 (VAT포함)"
              value={formatCurrency(stats.grandTotal)}
              color="text-purple-600"
            />
          </div>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all"
                style={{ width: `${stats.progress}%` }}
              />
            </div>
            <span className="text-sm font-medium text-gray-600">
              {stats.progress}%
            </span>
          </div>
        </div>

        {/* 필터 */}
        <div className="px-4 py-2 border-b bg-gray-50 flex items-center gap-2">
          <span className="text-sm text-gray-500">필터:</span>
          {(['all', 'completed', 'pending', 'no_session'] as FilterType[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                filter === f
                  ? 'bg-blue-500 text-white'
                  : 'bg-white border text-gray-600 hover:bg-gray-100'
              }`}
            >
              {f === 'all' && '전체'}
              {f === 'completed' && '완료'}
              {f === 'pending' && '진행중'}
              {f === 'no_session' && '미생성'}
            </button>
          ))}
        </div>

        {/* 테이블 */}
        <div className="max-h-[400px] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 sticky top-0">
              <tr className="text-left text-gray-500">
                <th className="px-4 py-2">도면번호</th>
                <th className="px-4 py-2">재질</th>
                <th className="px-4 py-2 w-14 text-center">수량</th>
                <th className="px-4 py-2">세션상태</th>
                <th className="px-4 py-2 w-14 text-center">검출</th>
                <th className="px-4 py-2 w-14 text-center">검증</th>
                <th className="px-4 py-2 w-24 text-right">소계</th>
                <th className="px-4 py-2 w-10"></th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredItems.map((item) => (
                <tr key={item.item_no} className="hover:bg-gray-50">
                  <td className="px-4 py-2 font-mono text-gray-900">
                    {item.drawing_number}
                  </td>
                  <td className="px-4 py-2 text-gray-500">{item.material || '-'}</td>
                  <td className="px-4 py-2 text-center text-gray-700">{item.quantity}</td>
                  <td className="px-4 py-2">
                    {item.session ? (
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          STATUS_BADGE[item.session.status] || 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {item.session.status}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">미생성</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-center text-gray-600">
                    {item.session?.detection_count ?? '-'}
                  </td>
                  <td className="px-4 py-2 text-center text-gray-600">
                    {item.session?.verified_count ?? '-'}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-600">
                    {formatCurrency(item.subtotal)}
                  </td>
                  <td className="px-4 py-2">
                    {item.session_id ? (
                      <Link
                        to={`/workflow?session=${item.session_id}`}
                        className="text-blue-500 hover:text-blue-600"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </Link>
                    ) : (
                      <span className="text-gray-300">-</span>
                    )}
                  </td>
                </tr>
              ))}
              {filteredItems.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center">
                    <FileText className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <p className="text-gray-400">해당 조건의 항목이 없습니다.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 재질별 분류 */}
      {quotation && quotation.material_groups.length > 0 && (
        <MaterialBreakdown groups={quotation.material_groups} />
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="bg-gray-50 rounded-lg p-3 text-center">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-lg font-bold ${color} truncate`}>{value}</p>
    </div>
  );
}
