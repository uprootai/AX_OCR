import { useState } from 'react';
import { Check, X, Pencil } from 'lucide-react';
import type { MatchResult, VerificationAction } from '../types';
import { VERDICT_CONFIG, SEVERITY_CONFIG } from '../constants';

interface MatchResultTableProps {
  results: MatchResult[];
  onAction: (id: string, action: VerificationAction, editedValue?: string) => void;
  filter: string;
}

export default function MatchResultTable({ results, onAction, filter }: MatchResultTableProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const filtered = filter === 'ALL'
    ? results
    : results.filter((r) => r.severity === filter);

  const handleEdit = (id: string, currentCode: string) => {
    setEditingId(id);
    setEditValue(currentCode);
  };

  const submitEdit = (id: string) => {
    onAction(id, 'edit', editValue);
    setEditingId(null);
    setEditValue('');
  };

  const highlightDiff = (partList: string, erp: string) => {
    if (partList === erp) return <span>{erp}</span>;
    return <span className="text-red-600 dark:text-red-400 font-semibold">{erp}</span>;
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 dark:bg-gray-800 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase">
            <th className="px-3 py-2.5">TAG</th>
            <th className="px-3 py-2.5">부품명</th>
            <th className="px-3 py-2.5">Part List 코드</th>
            <th className="px-3 py-2.5">ERP BOM 코드</th>
            <th className="px-3 py-2.5 text-center">수량</th>
            <th className="px-3 py-2.5">판정</th>
            <th className="px-3 py-2.5 text-center">확신도</th>
            <th className="px-3 py-2.5 text-center">조치</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
          {filtered.map((r) => {
            const sev = SEVERITY_CONFIG[r.severity];
            const vrd = VERDICT_CONFIG[r.verdict];
            const conf = Math.round(r.tag.confidence * 100);
            const isEditing = editingId === r.id;

            return (
              <tr key={r.id} className={`${sev.bgColor} transition-colors`}>
                {/* TAG */}
                <td className="px-3 py-2 font-bold text-gray-900 dark:text-gray-100 whitespace-nowrap">
                  {r.tag.tagCode}
                </td>

                {/* Part name */}
                <td className="px-3 py-2 text-gray-700 dark:text-gray-300 max-w-[160px] truncate" title={r.tag.partName}>
                  {r.tag.partName}
                </td>

                {/* Part List code */}
                <td className="px-3 py-2 font-mono text-xs text-gray-700 dark:text-gray-300">
                  {r.partListCode}
                </td>

                {/* ERP BOM code */}
                <td className="px-3 py-2 font-mono text-xs">
                  {isEditing ? (
                    <div className="flex items-center gap-1">
                      <input
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && submitEdit(r.id)}
                        className="w-28 px-1.5 py-0.5 rounded border border-blue-400 bg-white dark:bg-gray-900 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                        autoFocus
                      />
                      <button onClick={() => submitEdit(r.id)} className="text-green-600 hover:text-green-800">
                        <Check size={14} />
                      </button>
                      <button onClick={() => setEditingId(null)} className="text-gray-400 hover:text-gray-600">
                        <X size={14} />
                      </button>
                    </div>
                  ) : (
                    highlightDiff(r.partListCode, r.erpBomCode)
                  )}
                </td>

                {/* Qty */}
                <td className="px-3 py-2 text-center whitespace-nowrap">
                  <span className={r.drawingQty !== r.erpQty ? 'text-red-600 dark:text-red-400 font-semibold' : 'text-gray-700 dark:text-gray-300'}>
                    {r.drawingQty} / {r.erpQty}
                  </span>
                </td>

                {/* Verdict badge */}
                <td className="px-3 py-2">
                  <span className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-medium ${vrd.bgColor} ${vrd.color}`}>
                    {vrd.label}
                  </span>
                </td>

                {/* Confidence bar */}
                <td className="px-3 py-2">
                  <div className="flex items-center gap-1.5 justify-center">
                    <div className="w-16 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${conf >= 80 ? 'bg-green-500' : conf >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
                        style={{ width: `${conf}%` }}
                      />
                    </div>
                    <span className="text-[11px] text-gray-500 dark:text-gray-400 w-8 text-right">{conf}%</span>
                  </div>
                </td>

                {/* Actions */}
                <td className="px-3 py-2">
                  <div className="flex items-center gap-1 justify-center">
                    <button
                      title="승인"
                      onClick={() => onAction(r.id, 'approve')}
                      className={`p-1 rounded transition-colors ${r.verificationAction === 'approve' ? 'bg-green-200 dark:bg-green-800 text-green-700 dark:text-green-300' : 'text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/30'}`}
                    >
                      <Check size={14} />
                    </button>
                    <button
                      title="수정"
                      onClick={() => handleEdit(r.id, r.erpBomCode)}
                      className={`p-1 rounded transition-colors ${r.verificationAction === 'edit' ? 'bg-blue-200 dark:bg-blue-800 text-blue-700 dark:text-blue-300' : 'text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30'}`}
                    >
                      <Pencil size={14} />
                    </button>
                    <button
                      title="거부"
                      onClick={() => onAction(r.id, 'reject')}
                      className={`p-1 rounded transition-colors ${r.verificationAction === 'reject' ? 'bg-red-200 dark:bg-red-800 text-red-700 dark:text-red-300' : 'text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30'}`}
                    >
                      <X size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}

          {filtered.length === 0 && (
            <tr>
              <td colSpan={8} className="px-4 py-8 text-center text-gray-400 dark:text-gray-500 italic">
                No results for selected filter
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
