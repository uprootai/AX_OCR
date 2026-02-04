/**
 * MaterialBreakdown - 재질별 분류 테이블
 * Phase 3: 견적 집계 - 재질별 그룹 표시
 */

import { Layers } from 'lucide-react';
import type { MaterialGroup } from '../../../lib/api';

interface MaterialBreakdownProps {
  groups: MaterialGroup[];
}

export function MaterialBreakdown({ groups }: MaterialBreakdownProps) {
  const totalSubtotal = groups.reduce((sum, g) => sum + g.subtotal, 0);

  return (
    <div className="bg-white rounded-xl border overflow-hidden">
      <div className="p-4 border-b flex items-center gap-2">
        <Layers className="w-5 h-5 text-gray-400" />
        <h3 className="font-semibold text-gray-900">재질별 분류</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr className="text-left text-gray-500">
              <th className="px-4 py-2">재질</th>
              <th className="px-4 py-2 text-center">품목수</th>
              <th className="px-4 py-2 text-center">총 수량</th>
              <th className="px-4 py-2 text-right">소계</th>
              <th className="px-4 py-2 text-right">비율</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {groups.map((group) => {
              const ratio = totalSubtotal > 0
                ? (group.subtotal / totalSubtotal) * 100
                : 0;
              return (
                <tr key={group.material} className="hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium text-gray-900">
                    {group.material}
                  </td>
                  <td className="px-4 py-2 text-center text-gray-700">
                    {group.item_count}
                  </td>
                  <td className="px-4 py-2 text-center text-gray-700">
                    {group.total_quantity}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-700">
                    {group.subtotal > 0
                      ? `₩${group.subtotal.toLocaleString()}`
                      : '-'}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-500">
                    {ratio > 0 ? `${ratio.toFixed(1)}%` : '-'}
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot className="bg-gray-50 font-semibold">
            <tr>
              <td className="px-4 py-2 text-gray-900">합계</td>
              <td className="px-4 py-2 text-center text-gray-900">
                {groups.reduce((s, g) => s + g.item_count, 0)}
              </td>
              <td className="px-4 py-2 text-center text-gray-900">
                {groups.reduce((s, g) => s + g.total_quantity, 0)}
              </td>
              <td className="px-4 py-2 text-right text-gray-900">
                {totalSubtotal > 0
                  ? `₩${totalSubtotal.toLocaleString()}`
                  : '-'}
              </td>
              <td className="px-4 py-2 text-right text-gray-900">100%</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
