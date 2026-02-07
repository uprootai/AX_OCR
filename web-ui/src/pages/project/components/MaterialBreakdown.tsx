/**
 * MaterialBreakdown - 재질별 분류 테이블
 *
 * web-ui 네이티브 구현 (다크모드 지원)
 */

import { Layers } from 'lucide-react';
import type { MaterialGroup } from '../../../lib/blueprintBomApi';

interface MaterialBreakdownProps {
  groups: MaterialGroup[];
}

export function MaterialBreakdown({ groups }: MaterialBreakdownProps) {
  const totalSubtotal = groups.reduce((sum, g) => sum + g.subtotal, 0);
  const totalWeight = groups.reduce((sum, g) => sum + (g.total_weight || 0), 0);
  const totalMaterialCost = groups.reduce((sum, g) => sum + (g.material_cost_sum || 0), 0);

  const fmt = (v: number) => (v > 0 ? `₩${v.toLocaleString()}` : '-');

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
        <Layers className="w-5 h-5 text-gray-400 dark:text-gray-500" />
        <h3 className="font-semibold text-gray-900 dark:text-white">재질별 분류</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr className="text-left text-gray-500 dark:text-gray-400">
              <th className="px-4 py-2">재질</th>
              <th className="px-4 py-2 text-center">품목수</th>
              <th className="px-4 py-2 text-center">총 수량</th>
              <th className="px-4 py-2 text-right">중량(kg)</th>
              <th className="px-4 py-2 text-right">재료비</th>
              <th className="px-4 py-2 text-right">소계</th>
              <th className="px-4 py-2 text-right">비율</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
            {groups.map((group) => {
              const ratio = totalSubtotal > 0
                ? (group.subtotal / totalSubtotal) * 100
                : 0;
              return (
                <tr key={group.material} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="px-4 py-2 font-medium text-gray-900 dark:text-white">
                    {group.material}
                  </td>
                  <td className="px-4 py-2 text-center text-gray-700 dark:text-gray-300">
                    {group.item_count}
                  </td>
                  <td className="px-4 py-2 text-center text-gray-700 dark:text-gray-300">
                    {group.total_quantity}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-700 dark:text-gray-300">
                    {(group.total_weight || 0) > 0
                      ? `${group.total_weight.toFixed(1)}`
                      : '-'}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-700 dark:text-gray-300">
                    {fmt(group.material_cost_sum || 0)}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-700 dark:text-gray-300">
                    {fmt(group.subtotal)}
                  </td>
                  <td className="px-4 py-2 text-right text-gray-500 dark:text-gray-400">
                    {ratio > 0 ? `${ratio.toFixed(1)}%` : '-'}
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot className="bg-gray-50 dark:bg-gray-700 font-semibold">
            <tr>
              <td className="px-4 py-2 text-gray-900 dark:text-white">합계</td>
              <td className="px-4 py-2 text-center text-gray-900 dark:text-white">
                {groups.reduce((s, g) => s + g.item_count, 0)}
              </td>
              <td className="px-4 py-2 text-center text-gray-900 dark:text-white">
                {groups.reduce((s, g) => s + g.total_quantity, 0)}
              </td>
              <td className="px-4 py-2 text-right text-gray-900 dark:text-white">
                {totalWeight > 0 ? `${totalWeight.toFixed(1)}` : '-'}
              </td>
              <td className="px-4 py-2 text-right text-gray-900 dark:text-white">
                {fmt(totalMaterialCost)}
              </td>
              <td className="px-4 py-2 text-right text-gray-900 dark:text-white">
                {fmt(totalSubtotal)}
              </td>
              <td className="px-4 py-2 text-right text-gray-900 dark:text-white">100%</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
