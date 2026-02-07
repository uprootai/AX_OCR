/**
 * AssemblyBreakdown - 어셈블리 단위 견적 그룹 테이블
 * 핑크(ASSEMBLY) 단위로 하위 부품 견적을 그룹핑하여 표시
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Box, ChevronDown, ChevronRight, ExternalLink, Play, Loader2, Download, FileSpreadsheet } from 'lucide-react';
import { projectApi, type AssemblyQuotationGroup } from '../../../lib/api';

interface AssemblyBreakdownProps {
  projectId: string;
  groups: AssemblyQuotationGroup[];
  onStartBatch?: (rootDrawingNumber: string) => void;
  isBatchRunning?: boolean;
  currentBatchDrawing?: string | null; // 현재 분석 중인 도면
}

export function AssemblyBreakdown({ projectId, groups, onStartBatch, isBatchRunning, currentBatchDrawing }: AssemblyBreakdownProps) {
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
    <div className="bg-white rounded-xl border overflow-hidden">
      <div className="p-4 border-b flex items-center gap-2">
        <Box className="w-5 h-5 text-pink-400" />
        <h3 className="font-semibold text-gray-900">어셈블리별 견적</h3>
        <span className="text-xs text-gray-400 ml-auto">{groups.length}개 어셈블리</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr className="text-left text-gray-500">
              <th className="px-4 py-2 w-8"></th>
              <th className="px-4 py-2">어셈블리</th>
              <th className="px-4 py-2">품명</th>
              <th className="px-4 py-2 text-center">부품수</th>
              <th className="px-4 py-2 text-right">중량(kg)</th>
              <th className="px-4 py-2 text-right">소계</th>
              <th className="px-4 py-2 text-right">비율</th>
              <th className="px-4 py-2 text-center">진행률</th>
              <th className="px-4 py-2 w-20 text-center">내보내기</th>
              {onStartBatch && <th className="px-4 py-2 w-10"></th>}
            </tr>
          </thead>
          <tbody className="divide-y">
            {groups.map((group) => {
              const isExpanded = expandedGroups.has(group.assembly_drawing_number);
              const ratio = totalSubtotal > 0
                ? (group.subtotal / totalSubtotal) * 100
                : 0;
              return (
                <AssemblyRow
                  key={group.assembly_drawing_number}
                  projectId={projectId}
                  group={group}
                  isExpanded={isExpanded}
                  ratio={ratio}
                  onToggle={() => toggleGroup(group.assembly_drawing_number)}
                  fmt={fmt}
                  onStartBatch={onStartBatch}
                  isBatchRunning={isBatchRunning}
                  isAnalyzing={
                    !!currentBatchDrawing &&
                    group.items.some(item => item.drawing_number === currentBatchDrawing)
                  }
                />
              );
            })}
          </tbody>
          <tfoot className="bg-gray-50 font-semibold">
            <tr>
              <td className="px-4 py-2"></td>
              <td className="px-4 py-2 text-gray-900">합계</td>
              <td className="px-4 py-2"></td>
              <td className="px-4 py-2 text-center text-gray-900">
                {groups.reduce((s, g) => s + g.total_parts, 0)}
              </td>
              <td className="px-4 py-2 text-right text-gray-900">
                {groups.reduce((s, g) => s + g.bom_weight_kg, 0) > 0
                  ? groups.reduce((s, g) => s + g.bom_weight_kg, 0).toFixed(1)
                  : '-'}
              </td>
              <td className="px-4 py-2 text-right text-gray-900">
                {fmt(totalSubtotal)}
              </td>
              <td className="px-4 py-2 text-right text-gray-900">100%</td>
              <td className="px-4 py-2"></td>
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
  projectId,
  group,
  isExpanded,
  ratio,
  onToggle,
  fmt,
  onStartBatch,
  isBatchRunning,
  isAnalyzing,
}: {
  projectId: string;
  group: AssemblyQuotationGroup;
  isExpanded: boolean;
  ratio: number;
  onToggle: () => void;
  fmt: (v: number) => string;
  onStartBatch?: (rootDrawingNumber: string) => void;
  isBatchRunning?: boolean;
  isAnalyzing?: boolean;
}) {
  const handleDownload = (format: 'pdf' | 'excel') => {
    const url = projectApi.getAssemblyQuotationDownloadUrl(
      projectId,
      group.assembly_drawing_number,
      format
    );
    window.open(url, '_blank');
  };
  return (
    <>
      <tr
        className={`cursor-pointer transition-colors ${
          isAnalyzing
            ? 'bg-blue-50 hover:bg-blue-100'
            : 'hover:bg-pink-50'
        }`}
        onClick={onToggle}
      >
        <td className="px-4 py-2 text-gray-400">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </td>
        <td className="px-4 py-2 font-mono text-xs font-medium text-pink-700">
          {group.assembly_drawing_number}
        </td>
        <td className="px-4 py-2 text-gray-700 text-xs">
          {group.assembly_description || '-'}
        </td>
        <td className="px-4 py-2 text-center text-gray-700">
          {group.total_parts}
        </td>
        <td className="px-4 py-2 text-right text-gray-700">
          {group.bom_weight_kg > 0 ? group.bom_weight_kg.toFixed(1) : '-'}
        </td>
        <td className="px-4 py-2 text-right font-medium text-gray-900">
          {fmt(group.subtotal)}
        </td>
        <td className="px-4 py-2 text-right text-gray-500">
          {ratio > 0 ? `${ratio.toFixed(1)}%` : '-'}
        </td>
        <td className="px-4 py-2">
          <div className="flex items-center gap-1">
            <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-pink-500 transition-all"
                style={{ width: `${group.progress_percent}%` }}
              />
            </div>
            <span className="text-[10px] text-gray-500 w-8 text-right">
              {group.progress_percent}%
            </span>
          </div>
        </td>
        <td className="px-4 py-2">
          <div className="flex items-center justify-center gap-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDownload('pdf');
              }}
              className="p-1 rounded hover:bg-pink-100 text-pink-600 transition-colors"
              title="PDF 다운로드"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDownload('excel');
              }}
              className="p-1 rounded hover:bg-green-100 text-green-600 transition-colors"
              title="Excel 다운로드"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
            </button>
          </div>
        </td>
        {onStartBatch && (
          <td className="px-4 py-2 text-center">
            {isAnalyzing ? (
              <div className="p-1 text-blue-500" title="분석 중...">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              </div>
            ) : (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onStartBatch(group.assembly_drawing_number);
                }}
                disabled={isBatchRunning}
                className="p-1 rounded hover:bg-pink-100 text-pink-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                title={`${group.assembly_drawing_number} 분석`}
              >
                <Play className="w-3.5 h-3.5" />
              </button>
            )}
          </td>
        )}
      </tr>
      {isExpanded && group.items.map((item) => (
        <tr
          key={item.session_id || item.bom_item_no}
          className="bg-pink-50/30 hover:bg-pink-50"
        >
          <td className="px-4 py-1.5"></td>
          <td className="px-4 py-1.5 pl-8 font-mono text-[11px] text-gray-600">
            {item.drawing_number}
          </td>
          <td className="px-4 py-1.5 text-[11px] text-gray-500">
            {item.description || item.material || '-'}
          </td>
          <td className="px-4 py-1.5 text-center text-[11px] text-gray-600">
            {item.bom_quantity}
          </td>
          <td className="px-4 py-1.5 text-right text-[11px] text-gray-600">
            {item.weight_kg > 0 ? item.weight_kg.toFixed(1) : '-'}
          </td>
          <td className="px-4 py-1.5 text-right text-[11px] text-gray-700">
            {fmt(item.subtotal)}
          </td>
          <td className="px-4 py-1.5 text-right text-[11px] text-gray-400">
            {item.doc_revision ? `Rev.${item.doc_revision}` : ''}
          </td>
          <td className="px-4 py-1.5 text-center">
            {item.session_id ? (
              <Link
                to={`/workflow?session=${item.session_id}`}
                className="text-blue-500 hover:text-blue-600"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink className="w-3 h-3" />
              </Link>
            ) : (
              <span className="text-gray-300 text-[10px]">-</span>
            )}
          </td>
        </tr>
      ))}
    </>
  );
}
