/**
 * QuotationDashboard - 필터 + 테이블 UI
 */

import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { ExternalLink, FileText } from 'lucide-react';
import type { FilterType } from './QuotationDashboard.types';
import { STATUS_BADGE } from './QuotationDashboard.types';
import { CostSourceBadge, formatCurrency, formatDims } from './QuotationDashboard.helpers';

type ItemWithSession = {
  item_no: string;
  drawing_number?: string;
  material?: string;
  quantity: number;
  session_id?: string;
  session?: { status: string };
  subtotal: number;
  material_cost: number;
  machining_cost: number;
  cost_source: string;
  original_dimensions?: Record<string, number>;
  raw_dimensions?: Record<string, number>;
  allowance_applied?: boolean;
};

interface QuotationTableProps {
  itemsWithSession: ItemWithSession[];
}

export function QuotationTable({ itemsWithSession }: QuotationTableProps) {
  const [filter, setFilter] = useState<FilterType>('all');

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

  return (
    <>
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
    </>
  );
}
