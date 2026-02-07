/**
 * AssemblyBreakdown - 어셈블리 단위 견적 그룹 테이블
 *
 * web-ui 네이티브 구현 (다크모드 지원)
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Box, ChevronDown, ChevronRight, ExternalLink, Play } from 'lucide-react';
import type { AssemblyQuotationGroup } from '../../../lib/blueprintBomApi';

interface AssemblyBreakdownProps {
  groups: AssemblyQuotationGroup[];
  onStartBatch?: (rootDrawingNumber: string) => void;
  isBatchRunning?: boolean;
}

export function AssemblyBreakdown({ groups, onStartBatch, isBatchRunning }: AssemblyBreakdownProps) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  const toggleGroup = (dwg: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(dwg)) next.delete(dwg);
      else next.add(dwg);
      return next;
    });
  };

  const totalSubtotal = groups.reduce((s, g) => s + g.subtotal, 0);
  const fmt = (v: number) => (v > 0 ? `₩${v.toLocaleString()}` : '-');

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
        <Box className="w-5 h-5 text-pink-400 dark:text-pink-500" />
        <h3 className="font-semibold text-gray-900 dark:text-white">어셈블리별 견적</h3>
        <span className="text-xs text-gray-400 dark:text-gray-500 ml-auto">{groups.length}개 어셈블리</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr className="text-left text-gray-500 dark:text-gray-400">
              <th className="px-4 py-2 w-8"></th>
              <th className="px-4 py-2">어셈블리</th>
              <th className="px-4 py-2">품명</th>
              <th className="px-4 py-2 text-center">부품수</th>
              <th className="px-4 py-2 text-right">중량(kg)</th>
              <th className="px-4 py-2 text-right">소계</th>
              <th className="px-4 py-2 text-right">비율</th>
              <th className="px-4 py-2 text-center">진행률</th>
              {onStartBatch && <th className="px-4 py-2 w-10"></th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {groups.map((group) => {
              const isExpanded = expandedGroups.has(group.assembly_drawing_number);
              const ratio = totalSubtotal > 0
                ? (group.subtotal / totalSubtotal) * 100
                : 0;
              return (
                <AssemblyRow
                  key={group.assembly_drawing_number}
                  group={group}
                  isExpanded={isExpanded}
                  ratio={ratio}
                  onToggle={() => toggleGroup(group.assembly_drawing_number)}
                  fmt={fmt}
                  onStartBatch={onStartBatch}
                  isBatchRunning={isBatchRunning}
                />
              );
            })}
          </tbody>
          <tfoot className="bg-gray-50 dark:bg-gray-700 font-semibold">
            <tr>
              <td className="px-4 py-2"></td>
              <td className="px-4 py-2 text-gray-900 dark:text-white">합계</td>
              <td className="px-4 py-2"></td>
              <td className="px-4 py-2 text-center text-gray-900 dark:text-white">
                {groups.reduce((s, g) => s + g.total_parts, 0)}
              </td>
              <td className="px-4 py-2 text-right text-gray-900 dark:text-white">
                {groups.reduce((s, g) => s + g.bom_weight_kg, 0) > 0
                  ? groups.reduce((s, g) => s + g.bom_weight_kg, 0).toFixed(1)
                  : '-'}
              </td>
              <td className="px-4 py-2 text-right text-gray-900 dark:text-white">
                {fmt(totalSubtotal)}
              </td>
              <td className="px-4 py-2 text-right text-gray-900 dark:text-white">100%</td>
              <td className="px-4 py-2"></td>
              {onStartBatch && <td className="px-4 py-2"></td>}
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}

function AssemblyRow({
  group,
  isExpanded,
  ratio,
  onToggle,
  fmt,
  onStartBatch,
  isBatchRunning,
}: {
  group: AssemblyQuotationGroup;
  isExpanded: boolean;
  ratio: number;
  onToggle: () => void;
  fmt: (v: number) => string;
  onStartBatch?: (rootDrawingNumber: string) => void;
  isBatchRunning?: boolean;
}) {
  return (
    <>
      <tr
        className="hover:bg-pink-50 dark:hover:bg-pink-900/20 cursor-pointer"
        onClick={onToggle}
      >
        <td className="px-4 py-2 text-gray-400 dark:text-gray-500">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </td>
        <td className="px-4 py-2 font-mono text-xs font-medium text-pink-700 dark:text-pink-400">
          {group.assembly_drawing_number}
        </td>
        <td className="px-4 py-2 text-gray-700 dark:text-gray-300 text-xs">
          {group.assembly_description || '-'}
        </td>
        <td className="px-4 py-2 text-center text-gray-700 dark:text-gray-300">
          {group.total_parts}
        </td>
        <td className="px-4 py-2 text-right text-gray-700 dark:text-gray-300">
          {group.bom_weight_kg > 0 ? group.bom_weight_kg.toFixed(1) : '-'}
        </td>
        <td className="px-4 py-2 text-right font-medium text-gray-900 dark:text-white">
          {fmt(group.subtotal)}
        </td>
        <td className="px-4 py-2 text-right text-gray-500 dark:text-gray-400">
          {ratio > 0 ? `${ratio.toFixed(1)}%` : '-'}
        </td>
        <td className="px-4 py-2">
          <div className="flex items-center gap-1">
            <div className="flex-1 h-1.5 bg-gray-100 dark:bg-gray-600 rounded-full overflow-hidden">
              <div
                className="h-full bg-pink-500 dark:bg-pink-400 transition-all"
                style={{ width: `${group.progress_percent}%` }}
              />
            </div>
            <span className="text-[10px] text-gray-500 dark:text-gray-400 w-8 text-right">
              {group.progress_percent}%
            </span>
          </div>
        </td>
        {onStartBatch && (
          <td className="px-4 py-2 text-center">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onStartBatch(group.assembly_drawing_number);
              }}
              disabled={isBatchRunning}
              className="p-1 rounded hover:bg-pink-100 dark:hover:bg-pink-900/30 text-pink-600 dark:text-pink-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              title={`${group.assembly_drawing_number} 분석`}
            >
              <Play className="w-3.5 h-3.5" />
            </button>
          </td>
        )}
      </tr>
      {isExpanded && group.items.map((item) => (
        <tr
          key={item.session_id || item.bom_item_no}
          className="bg-pink-50/30 dark:bg-pink-900/10 hover:bg-pink-50 dark:hover:bg-pink-900/20"
        >
          <td className="px-4 py-1.5"></td>
          <td className="px-4 py-1.5 pl-8 font-mono text-[11px] text-gray-600 dark:text-gray-400">
            {item.drawing_number}
          </td>
          <td className="px-4 py-1.5 text-[11px] text-gray-500 dark:text-gray-400">
            {item.description || item.material || '-'}
          </td>
          <td className="px-4 py-1.5 text-center text-[11px] text-gray-600 dark:text-gray-400">
            {item.bom_quantity}
          </td>
          <td className="px-4 py-1.5 text-right text-[11px] text-gray-600 dark:text-gray-400">
            {item.weight_kg > 0 ? item.weight_kg.toFixed(1) : '-'}
          </td>
          <td className="px-4 py-1.5 text-right text-[11px] text-gray-700 dark:text-gray-300">
            {fmt(item.subtotal)}
          </td>
          <td className="px-4 py-1.5 text-right text-[11px] text-gray-400 dark:text-gray-500">
            {item.doc_revision ? `Rev.${item.doc_revision}` : ''}
          </td>
          <td className="px-4 py-1.5 text-center">
            {item.session_id ? (
              <Link
                to={`/blueprintflow/builder?session=${item.session_id}`}
                className="text-blue-500 dark:text-blue-400 hover:text-blue-600 dark:hover:text-blue-300"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink className="w-3 h-3" />
              </Link>
            ) : (
              <span className="text-gray-300 dark:text-gray-600 text-[10px]">-</span>
            )}
          </td>
        </tr>
      ))}
    </>
  );
}
