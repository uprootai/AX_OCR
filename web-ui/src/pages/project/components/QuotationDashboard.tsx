/**
 * QuotationDashboard - 견적 현황 대시보드
 * Phase 3: BOM 항목 + 견적 집계 통합 표시
 *
 * web-ui 네이티브 구현 (다크모드 지원)
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
  Play,
  Square,
} from 'lucide-react';
import {
  projectApi,
  type BOMItem,
  type ProjectDetail,
  type ProjectQuotationResponse,
} from '../../../lib/blueprintBomApi';
import { MaterialBreakdown } from './MaterialBreakdown';
import { AssemblyBreakdown } from './AssemblyBreakdown';

type FilterType = 'all' | 'completed' | 'pending' | 'no_session';

interface QuotationDashboardProps {
  projectId: string;
  project: ProjectDetail;
  bomItems: BOMItem[];
}

const STATUS_BADGE: Record<string, string> = {
  completed: 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400',
  detecting: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
  detected: 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
  verifying: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-400',
  error: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
};

export function QuotationDashboard({
  projectId,
  project,
  bomItems,
}: QuotationDashboardProps) {
  const [filter, setFilter] = useState<FilterType>('all');
  const [quotation, setQuotation] = useState<ProjectQuotationResponse | null>(null);
  const [isAggregating, setIsAggregating] = useState(false);
  const [batchStatus, setBatchStatus] = useState<{
    status: string;
    total: number;
    completed: number;
    failed: number;
    skipped: number;
    current_drawing: string | null;
  } | null>(null);

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

  const startBatch = useCallback(async (rootDrawingNumber?: string) => {
    try {
      await projectApi.startBatchAnalysis(projectId, rootDrawingNumber);
      pollBatchStatus();
    } catch (err) {
      console.error('배치 분석 시작 실패:', err);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const cancelBatch = useCallback(async () => {
    try {
      await projectApi.cancelBatchAnalysis(projectId);
    } catch {
      // ignore
    }
  }, [projectId]);

  const pollBatchStatus = useCallback(() => {
    const interval = setInterval(async () => {
      try {
        const status = await projectApi.getBatchStatus(projectId);
        setBatchStatus(status);
        if (status.status !== 'running') {
          clearInterval(interval);
          if (status.completed > 0) {
            loadQuotation(true);
          }
        }
      } catch {
        clearInterval(interval);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [projectId, loadQuotation]);

  useEffect(() => {
    loadQuotation(false);
    projectApi.getBatchStatus(projectId).then((status) => {
      setBatchStatus(status);
      if (status.status === 'running') {
        pollBatchStatus();
      }
    }).catch(() => {});
  }, [loadQuotation, projectId, pollBatchStatus]);

  const sessionMap = useMemo(() => {
    const sessions = project.sessions ?? [];
    const map = new Map<string, (typeof sessions)[0]>();
    for (const s of sessions) {
      map.set(s.session_id, s);
    }
    return map;
  }, [project.sessions]);

  const quotationItemMap = useMemo(() => {
    const map = new Map<string, {
      subtotal: number;
      material_cost: number;
      machining_cost: number;
      weight_kg: number;
      cost_source: string;
      original_dimensions?: Record<string, number>;
      raw_dimensions?: Record<string, number>;
      allowance_applied?: boolean;
    }>();
    if (quotation) {
      for (const item of quotation.items) {
        map.set(item.session_id, {
          subtotal: item.subtotal,
          material_cost: item.material_cost,
          machining_cost: item.machining_cost,
          weight_kg: item.weight_kg,
          cost_source: item.cost_source,
          original_dimensions: item.original_dimensions,
          raw_dimensions: item.raw_dimensions,
          allowance_applied: item.allowance_applied,
        });
      }
    }
    return map;
  }, [quotation]);

  const quotationItems = useMemo(() => {
    const all = bomItems.filter((i) => i.needs_quotation);
    const grouped = new Map<string, BOMItem & { totalQuantity: number }>();
    for (const item of all) {
      const key = item.drawing_number || item.item_no.toString();
      const existing = grouped.get(key);
      if (existing) {
        existing.totalQuantity += item.quantity;
      } else {
        grouped.set(key, { ...item, totalQuantity: item.quantity });
      }
    }
    return Array.from(grouped.values());
  }, [bomItems]);

  const itemsWithSession = useMemo(
    () =>
      quotationItems.map((item) => {
        const costInfo = item.session_id ? quotationItemMap.get(item.session_id) : undefined;
        return {
          ...item,
          quantity: (item as typeof item & { totalQuantity: number }).totalQuantity ?? item.quantity,
          session: item.session_id ? sessionMap.get(item.session_id) : undefined,
          subtotal: costInfo?.subtotal ?? 0,
          material_cost: costInfo?.material_cost ?? 0,
          machining_cost: costInfo?.machining_cost ?? 0,
          weight_kg: costInfo?.weight_kg ?? 0,
          cost_source: costInfo?.cost_source ?? 'none',
          original_dimensions: costInfo?.original_dimensions,
          raw_dimensions: costInfo?.raw_dimensions,
          allowance_applied: costInfo?.allowance_applied,
        };
      }),
    [quotationItems, sessionMap, quotationItemMap]
  );

  const stats = useMemo(() => {
    if (quotation) {
      const totalMaterialCost = quotation.items.reduce((s, i) => s + (i.material_cost || 0), 0);
      const totalMachiningCost = quotation.items.reduce((s, i) => s + (i.machining_cost || 0), 0);
      return {
        total: quotation.summary.total_sessions,
        completed: quotation.summary.completed_sessions,
        quoted: quotation.summary.quoted_sessions,
        subtotal: quotation.summary.subtotal,
        vat: quotation.summary.vat,
        grandTotal: quotation.summary.total,
        progress: quotation.summary.progress_percent,
        totalMaterialCost,
        totalMachiningCost,
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
      totalMaterialCost: 0,
      totalMachiningCost: 0,
    };
  }, [quotation, quotationItems, itemsWithSession]);

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
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {/* 헤더 */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-gray-400 dark:text-gray-500" />
            <h3 className="font-semibold text-gray-900 dark:text-white">견적 현황</h3>
          </div>
          <div className="flex items-center gap-2">
            {batchStatus?.status === 'running' ? (
              <button
                onClick={cancelBatch}
                className="flex items-center gap-1 px-3 py-1.5 text-xs bg-red-500 dark:bg-red-600 text-white rounded-lg hover:bg-red-600 dark:hover:bg-red-700 transition-colors"
              >
                <Square className="w-3.5 h-3.5" />
                분석 중단 ({batchStatus.completed + batchStatus.skipped + batchStatus.failed}/{batchStatus.total})
              </button>
            ) : (
              <button
                onClick={() => startBatch()}
                className="flex items-center gap-1 px-3 py-1.5 text-xs bg-green-500 dark:bg-green-600 text-white rounded-lg hover:bg-green-600 dark:hover:bg-green-700 transition-colors"
              >
                <Play className="w-3.5 h-3.5" />
                전체 분석
              </button>
            )}
            <button
              onClick={() => loadQuotation(true)}
              disabled={isAggregating}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-blue-500 dark:bg-blue-600 text-white rounded-lg hover:bg-blue-600 dark:hover:bg-blue-700 transition-colors disabled:opacity-50"
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
                  className="flex items-center gap-1 px-3 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  download
                >
                  <Download className="w-3.5 h-3.5" />
                  PDF
                </a>
                <a
                  href={projectApi.getQuotationDownloadUrl(projectId, 'excel')}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
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
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-3 gap-3 mb-3">
            <StatCard label="견적대상" value={`${stats.total}개`} color="text-gray-900 dark:text-white" />
            <StatCard label="분석완료" value={`${stats.completed}개`} color="text-green-600 dark:text-green-400" />
            <StatCard
              label="합계 (VAT포함)"
              value={formatCurrency(stats.grandTotal)}
              color="text-purple-600 dark:text-purple-400"
            />
          </div>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <StatCard
              label="총 재료비"
              value={formatCurrency(stats.totalMaterialCost)}
              color="text-blue-600 dark:text-blue-400"
            />
            <StatCard
              label="총 가공비"
              value={formatCurrency(stats.totalMachiningCost)}
              color="text-orange-600 dark:text-orange-400"
            />
            <StatCard
              label="소계"
              value={formatCurrency(stats.subtotal)}
              color="text-gray-700 dark:text-gray-300"
            />
          </div>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 dark:bg-green-400 transition-all"
                style={{ width: `${stats.progress}%` }}
              />
            </div>
            <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
              {stats.progress}%
            </span>
          </div>
          {batchStatus?.status === 'running' && (
            <div className="mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex items-center justify-between text-xs text-blue-700 dark:text-blue-300 mb-1">
                <span className="flex items-center gap-1">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  AI 분석 중: {batchStatus.current_drawing || '...'}
                </span>
                <span>{batchStatus.completed + batchStatus.skipped + batchStatus.failed}/{batchStatus.total}</span>
              </div>
              <div className="h-1.5 bg-blue-100 dark:bg-blue-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 dark:bg-blue-400 transition-all"
                  style={{ width: `${batchStatus.total > 0 ? ((batchStatus.completed + batchStatus.skipped + batchStatus.failed) / batchStatus.total * 100) : 0}%` }}
                />
              </div>
              {batchStatus.failed > 0 && (
                <p className="text-xs text-red-500 dark:text-red-400 mt-1">실패: {batchStatus.failed}개</p>
              )}
            </div>
          )}
          {batchStatus?.status === 'completed' && batchStatus.completed > 0 && (
            <p className="mt-2 text-xs text-green-600 dark:text-green-400">
              배치 분석 완료: {batchStatus.completed}개 성공, {batchStatus.skipped}개 스킵, {batchStatus.failed}개 실패
            </p>
          )}
        </div>

        {/* 필터 */}
        <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50 flex items-center gap-2">
          <span className="text-sm text-gray-500 dark:text-gray-400">필터:</span>
          {(['all', 'completed', 'pending', 'no_session'] as FilterType[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                filter === f
                  ? 'bg-blue-500 dark:bg-blue-600 text-white'
                  : 'bg-white dark:bg-gray-600 border border-gray-200 dark:border-gray-500 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-500'
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
            <thead className="bg-gray-50 dark:bg-gray-700 sticky top-0">
              <tr className="text-left text-gray-500 dark:text-gray-400">
                <th className="px-3 py-2">도면번호</th>
                <th className="px-3 py-2">재질</th>
                <th className="px-3 py-2 w-12 text-center">수량</th>
                <th className="px-3 py-2">상태</th>
                <th className="px-3 py-2 w-20 text-right">재료비</th>
                <th className="px-3 py-2 w-20 text-right">가공비</th>
                <th className="px-3 py-2 w-20 text-right">소계</th>
                <th className="px-3 py-2 w-32 text-center">치수</th>
                <th className="px-3 py-2 w-16 text-center">산출</th>
                <th className="px-3 py-2 w-8"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {filteredItems.map((item) => (
                <tr key={item.item_no} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="px-3 py-2 font-mono text-gray-900 dark:text-white text-xs">
                    {item.drawing_number}
                  </td>
                  <td className="px-3 py-2 text-gray-500 dark:text-gray-400 text-xs">{item.material || '-'}</td>
                  <td className="px-3 py-2 text-center text-gray-700 dark:text-gray-300">{item.quantity}</td>
                  <td className="px-3 py-2">
                    {item.session ? (
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          STATUS_BADGE[item.session.status] || 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                        }`}
                      >
                        {item.session.status}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400 dark:text-gray-500">미생성</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-right text-xs text-gray-600 dark:text-gray-400">
                    {formatCurrency(item.material_cost)}
                  </td>
                  <td className="px-3 py-2 text-right text-xs text-gray-600 dark:text-gray-400">
                    {formatCurrency(item.machining_cost)}
                  </td>
                  <td className="px-3 py-2 text-right text-xs font-medium text-gray-900 dark:text-white">
                    {formatCurrency(item.subtotal)}
                  </td>
                  <td className="px-3 py-2 text-center text-[10px]">
                    {item.original_dimensions ? (
                      <div className="space-y-0.5">
                        <div className="text-gray-500 dark:text-gray-400">
                          {formatDims(item.original_dimensions)}
                        </div>
                        {item.allowance_applied && item.raw_dimensions && (
                          <div className="text-amber-600 dark:text-amber-400 font-medium">
                            → {formatDims(item.raw_dimensions)}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-300 dark:text-gray-600">-</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-center">
                    <CostSourceBadge source={item.cost_source} />
                  </td>
                  <td className="px-3 py-2">
                    {item.session_id ? (
                      <Link
                        to={`/blueprintflow/builder?session=${item.session_id}`}
                        className="text-blue-500 dark:text-blue-400 hover:text-blue-600 dark:hover:text-blue-300"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </Link>
                    ) : (
                      <span className="text-gray-300 dark:text-gray-600">-</span>
                    )}
                  </td>
                </tr>
              ))}
              {filteredItems.length === 0 && (
                <tr>
                  <td colSpan={10} className="px-4 py-8 text-center">
                    <FileText className="w-8 h-8 mx-auto mb-2 text-gray-300 dark:text-gray-600" />
                    <p className="text-gray-400 dark:text-gray-500">해당 조건의 항목이 없습니다.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 어셈블리별 견적 */}
      {quotation && quotation.assembly_groups?.length > 0 && (
        <AssemblyBreakdown
          groups={quotation.assembly_groups}
          onStartBatch={(dwg) => startBatch(dwg)}
          isBatchRunning={batchStatus?.status === 'running'}
        />
      )}

      {/* 재질별 분류 */}
      {quotation && quotation.material_groups.length > 0 && (
        <MaterialBreakdown groups={quotation.material_groups} />
      )}
    </div>
  );
}

function formatDims(dims: Record<string, number>): string {
  const parts: string[] = [];
  if (dims.od) parts.push(`\u00D8${dims.od}`);
  if (dims.id) parts.push(`\u00F8${dims.id}`);
  if (dims.length) parts.push(`L${dims.length}`);
  return parts.join(' \u00D7 ') || '-';
}

const COST_SOURCE_STYLES: Record<string, { label: string; className: string }> = {
  calculated: { label: '계산', className: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' },
  estimated: { label: '추정', className: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' },
  standard_catalog: { label: '카탈로그', className: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' },
  none: { label: '-', className: 'bg-gray-50 dark:bg-gray-700 text-gray-400 dark:text-gray-500' },
};

function CostSourceBadge({ source }: { source: string }) {
  const style = COST_SOURCE_STYLES[source] || COST_SOURCE_STYLES.none;
  return (
    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${style.className}`}>
      {style.label}
    </span>
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
    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{label}</p>
      <p className={`text-lg font-bold ${color} truncate`}>{value}</p>
    </div>
  );
}
