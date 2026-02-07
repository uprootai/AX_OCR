/**
 * BOMHierarchyTree - BOM 계층 트리뷰
 * PINK/BLUE/WHITE 색상 코딩, 펼치기/접기 기능
 */

import { useState, useCallback, useMemo } from 'react';
import { ChevronRight, ChevronDown, FileText } from 'lucide-react';
import type { BOMHierarchyResponse } from '../../../lib/api';

interface HierarchyNode {
  item_no: string;
  level: 'assembly' | 'subassembly' | 'part';
  drawing_number: string;
  description: string;
  material: string;
  quantity: number;
  needs_quotation: boolean;
  matched_file?: string;
  session_id?: string;
  doc_revision?: string;
  children?: HierarchyNode[];
}

interface BOMHierarchyTreeProps {
  bomData: BOMHierarchyResponse;
}

const LEVEL_STYLES = {
  assembly: {
    bg: 'bg-pink-50',
    border: 'border-l-4 border-l-pink-400',
    badge: 'bg-pink-100 text-pink-700',
    label: 'ASSY',
  },
  subassembly: {
    bg: 'bg-blue-50',
    border: 'border-l-4 border-l-blue-400',
    badge: 'bg-blue-100 text-blue-700',
    label: 'SUB',
  },
  part: {
    bg: 'bg-white',
    border: 'border-l-4 border-l-gray-300',
    badge: 'bg-gray-100 text-gray-700',
    label: 'PART',
  },
};

function collectAllNodeIds(nodes: HierarchyNode[]): string[] {
  const ids: string[] = [];
  for (const node of nodes) {
    if (node.children && node.children.length > 0) {
      ids.push(node.item_no);
      ids.push(...collectAllNodeIds(node.children));
    }
  }
  return ids;
}

function TreeNode({
  node,
  depth,
  expandedNodes,
  onToggle,
}: {
  node: HierarchyNode;
  depth: number;
  expandedNodes: Set<string>;
  onToggle: (id: string) => void;
}) {
  const style = LEVEL_STYLES[node.level];
  const hasChildren = node.children && node.children.length > 0;
  const isExpanded = expandedNodes.has(node.item_no);

  return (
    <div>
      <div
        className={`flex items-center gap-2 py-2 px-3 ${style.bg} ${style.border} hover:brightness-95 transition-all`}
        style={{ paddingLeft: `${depth * 24 + 12}px` }}
      >
        {/* 펼치기/접기 버튼 */}
        {hasChildren ? (
          <button
            onClick={() => onToggle(node.item_no)}
            className="p-0.5 hover:bg-black/5 rounded"
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-500" />
            )}
          </button>
        ) : (
          <span className="w-5 flex justify-center text-gray-300">-</span>
        )}

        {/* 레벨 뱃지 */}
        <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${style.badge}`}>
          {style.label}
        </span>

        {/* 아이템 번호 */}
        <span className="text-sm font-mono text-gray-500 w-16 shrink-0">
          {node.item_no}
        </span>

        {/* 도면 번호 */}
        <span className="text-sm font-medium text-gray-900 w-32 shrink-0 truncate">
          {node.drawing_number}
        </span>

        {/* 개정 번호 */}
        {node.doc_revision && (
          <span className="px-1.5 py-0.5 rounded text-xs bg-purple-100 text-purple-700 shrink-0">
            Rev.{node.doc_revision}
          </span>
        )}

        {/* 품명 */}
        <span className="text-sm text-gray-700 flex-1 truncate">
          {node.description}
        </span>

        {/* 재질 */}
        <span className="text-sm text-gray-500 w-20 shrink-0 text-right truncate">
          {node.material || '-'}
        </span>

        {/* 수량 */}
        <span className="text-sm text-gray-700 w-10 shrink-0 text-right">
          {node.quantity}
        </span>

        {/* 견적 필요 뱃지 */}
        {node.needs_quotation && (
          <span className="px-1.5 py-0.5 rounded text-xs bg-yellow-100 text-yellow-700 shrink-0">
            견적
          </span>
        )}
      </div>

      {/* 자식 노드 */}
      {hasChildren && isExpanded && (
        <div>
          {node.children!.map((child) => (
            <TreeNode
              key={child.item_no}
              node={child}
              depth={depth + 1}
              expandedNodes={expandedNodes}
              onToggle={onToggle}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function BOMHierarchyTree({ bomData }: BOMHierarchyTreeProps) {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(() => new Set());

  const hierarchy = useMemo(
    () => bomData.hierarchy as unknown as HierarchyNode[],
    [bomData.hierarchy]
  );

  const allExpandableIds = useMemo(
    () => collectAllNodeIds(hierarchy),
    [hierarchy]
  );

  const toggleNode = useCallback((id: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const expandAll = useCallback(() => {
    setExpandedNodes(new Set(allExpandableIds));
  }, [allExpandableIds]);

  const collapseAll = useCallback(() => {
    setExpandedNodes(new Set());
  }, []);

  return (
    <div className="bg-white rounded-xl border overflow-hidden">
      {/* 헤더 */}
      <div className="p-4 border-b flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-gray-400" />
          <h3 className="font-semibold text-gray-900">
            BOM 구조 ({bomData.bom_source})
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={expandAll}
            className="px-3 py-1 text-xs border rounded hover:bg-gray-50 transition-colors"
          >
            모두 펼치기
          </button>
          <button
            onClick={collapseAll}
            className="px-3 py-1 text-xs border rounded hover:bg-gray-50 transition-colors"
          >
            모두 접기
          </button>
        </div>
      </div>

      {/* 요약 통계 */}
      <div className="px-4 py-3 border-b bg-gray-50 flex items-center gap-4 text-sm">
        <span className="text-gray-600">
          전체 <span className="font-bold">{bomData.total_items}</span>개
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-pink-400 inline-block" />
          ASSY <span className="font-bold">{bomData.assembly_count}</span>개
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-blue-400 inline-block" />
          SUB <span className="font-bold">{bomData.subassembly_count}</span>개
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-gray-300 inline-block" />
          PART <span className="font-bold">{bomData.part_count}</span>개
        </span>
      </div>

      {/* 트리 */}
      <div className="max-h-[500px] overflow-y-auto">
        {hierarchy.length > 0 ? (
          hierarchy.map((node) => (
            <TreeNode
              key={node.item_no}
              node={node}
              depth={0}
              expandedNodes={expandedNodes}
              onToggle={toggleNode}
            />
          ))
        ) : (
          <div className="p-8 text-center text-gray-400">
            BOM 계층 데이터가 없습니다.
          </div>
        )}
      </div>
    </div>
  );
}
