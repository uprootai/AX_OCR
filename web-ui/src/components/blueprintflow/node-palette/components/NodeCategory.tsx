/**
 * NodeCategory Component
 * 카테고리별 노드 그룹 렌더링
 */

import { NodeItem } from './NodeItem';
import type { NodeConfig } from '../types';

interface NodeCategoryProps {
  title: string;
  emoji: string;
  nodes: NodeConfig[];
  isNodeActive: (nodeType: string) => boolean;
  onNodeDragStart: (e: React.DragEvent, nodeType: string, label: string) => void;
  tooltipColorScheme?: 'green' | 'purple' | 'red' | 'cyan';
  // Input 노드 전용 props
  uploadedImage?: string | null;
  uploadedFileName?: string | null;
  onImageClick?: () => void;
}

/**
 * NodeCategory 컴포넌트
 * 특정 카테고리의 노드들을 그룹으로 렌더링
 */
export function NodeCategory({
  title,
  emoji,
  nodes,
  isNodeActive,
  onNodeDragStart,
  tooltipColorScheme = 'green',
  uploadedImage,
  uploadedFileName,
  onImageClick,
}: NodeCategoryProps) {
  if (nodes.length === 0) {
    return null;
  }

  return (
    <div className="mb-6">
      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
        {emoji} {title}
      </h3>
      <div className="space-y-2">
        {nodes.map((node) => (
          <NodeItem
            key={node.type}
            node={node}
            isActive={isNodeActive(node.type)}
            onDragStart={onNodeDragStart}
            tooltipColorScheme={tooltipColorScheme}
            isImageInputNode={node.type === 'imageinput'}
            uploadedImage={uploadedImage}
            uploadedFileName={uploadedFileName}
            onImageClick={onImageClick}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * ControlFlowCategory 컴포넌트
 * Control Flow 노드 전용 (항상 활성화)
 */
export function ControlFlowCategory({
  nodes,
  onNodeDragStart,
}: {
  nodes: NodeConfig[];
  onNodeDragStart: (e: React.DragEvent, nodeType: string, label: string) => void;
}) {
  return (
    <div className="mb-6">
      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
        Control Flow
      </h3>
      <div className="space-y-2">
        {nodes.map((node) => {
          const isEmojiIcon = typeof node.icon === 'string';
          const Icon = !isEmojiIcon ? (node.icon as React.ElementType) : null;
          return (
            <div
              key={node.type}
              draggable
              onDragStart={(e) => onNodeDragStart(e, node.type, node.label)}
              className="flex items-start gap-2 p-3 rounded-lg border-2 cursor-move bg-white dark:bg-gray-700 hover:shadow-md transition-shadow"
              style={{ borderColor: `${node.color}40` }}
            >
              {isEmojiIcon ? (
                <span className="text-xl mt-0.5 flex-shrink-0">{String(node.icon)}</span>
              ) : Icon ? (
                <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: node.color }} />
              ) : null}
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm" style={{ color: node.color }}>
                  {node.label}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">{node.description}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
