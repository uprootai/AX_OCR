/**
 * BOMHierarchyTree - BOM 계층 트리뷰
 *
 * web-ui 네이티브 구현 (다크모드 지원)
 */

import { useState, useCallback, useMemo } from 'react';
import { ChevronRight, ChevronDown, FileText } from 'lucide-react';
import type { BOMHierarchyResponse } from '../../../lib/blueprintBomApi';

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
  children?: HierarchyNode[];
}

interface BOMHierarchyTreeProps {
  bomData: BOMHierarchyResponse;
}

const LEVEL_STYLES = {
  assembly: {
    bg: 'bg-pink-50 dark:bg-pink-900/20',
    border: 'border-l-4 border-l-pink-400 dark:border-l-pink-500',
    badge: 'bg-pink-100 dark:bg-pink-900/40 text-pink-700 dark:text-pink-300',
    label: 'ASSY',
  },
  subassembly: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-l-4 border-l-blue-400 dark:border-l-blue-500',
    badge: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
    label: 'SUB',
  },
  part: {
    bg: 'bg-white dark:bg-gray-800',
    border: 'border-l-4 border-l-gray-300 dark:border-l-gray-600',
    badge: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300',
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
        className={`flex items-center gap-2 py-2 px-3 ${style.bg} ${style.border} hover:brightness-95 dark:hover:brightness-110 transition-all`}
        style={{ paddingLeft: `${depth * 24 + 12}px` }}
      >
        {hasChildren ? (
          <button
            onClick={() => onToggle(node.item_no)}
            className="p-0.5 hover:bg-black/5 dark:hover:bg-white/10 rounded"
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            )}
          </button>
        ) : (
          <span className="w-5 flex justify-center text-gray-300 dark:text-gray-600">-</span>
        )}

        <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${style.badge}`}>
          {style.label}
        </span>

        <span className="text-sm font-mono text-gray-500 dark:text-gray-400 w-16 shrink-0">
          {node.item_no}
        </span>

        <span className="text-sm font-medium text-gray-900 dark:text-white w-32 shrink-0 truncate">
          {node.drawing_number}
        </span>

        <span className="text-sm text-gray-700 dark:text-gray-300 flex-1 truncate">
          {node.description}
        </span>

        <span className="text-sm text-gray-500 dark:text-gray-400 w-20 shrink-0 text-right truncate">
          {node.material || '-'}
        </span>

        <span className="text-sm text-gray-700 dark:text-gray-300 w-10 shrink-0 text-right">
          {node.quantity}
        </span>

        {node.needs_quotation && (
          <span className="px-1.5 py-0.5 rounded text-xs bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 shrink-0">
            견적
          </span>
        )}
      </div>

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
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-gray-400 dark:text-gray-500" />
          <h3 className="font-semibold text-gray-900 dark:text-white">
            BOM 구조 ({bomData.bom_source})
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={expandAll}
            className="px-3 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors"
          >
            모두 펼치기
          </button>
          <button
            onClick={collapseAll}
            className="px-3 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors"
          >
            모두 접기
          </button>
        </div>
      </div>

      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50 flex items-center gap-4 text-sm">
        <span className="text-gray-600 dark:text-gray-300">
          전체 <span className="font-bold">{bomData.total_items}</span>개
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-pink-400 dark:bg-pink-500 inline-block" />
          <span className="text-gray-600 dark:text-gray-300">ASSY <span className="font-bold">{bomData.assembly_count}</span>개</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-blue-400 dark:bg-blue-500 inline-block" />
          <span className="text-gray-600 dark:text-gray-300">SUB <span className="font-bold">{bomData.subassembly_count}</span>개</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded bg-gray-300 dark:bg-gray-500 inline-block" />
          <span className="text-gray-600 dark:text-gray-300">PART <span className="font-bold">{bomData.part_count}</span>개</span>
        </span>
      </div>

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
          <div className="p-8 text-center text-gray-400 dark:text-gray-500">
            BOM 계층 데이터가 없습니다.
          </div>
        )}
      </div>
    </div>
  );
}
