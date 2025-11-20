import { memo } from 'react';
import type { NodeProps } from 'reactflow';
import { Handle, Position } from 'reactflow';
import { GitBranch, Repeat, Merge as MergeIcon } from 'lucide-react';
import { BaseNode } from './BaseNode';

// IF Node with True/False outputs
export const IfNode = memo((props: NodeProps) => {
  const { data, selected } = props;
  const color = '#ef4444';
  const isSelected = selected || data.selected;

  return (
    <div
      className={`
        relative rounded-lg border-2 bg-white dark:bg-gray-800 shadow-lg
        transition-all duration-200
        hover:shadow-xl
      `}
      style={{
        minWidth: '180px',
        borderColor: isSelected ? color : `${color}80`,
        borderWidth: isSelected ? '3px' : '2px',
        boxShadow: isSelected
          ? `0 0 0 3px ${color}40, 0 10px 15px -3px rgba(0, 0, 0, 0.1)`
          : '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      }}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-3 !h-3 !border-2 !border-white"
        style={{ left: -6, backgroundColor: color }}
      />

      {/* Header */}
      <div
        className="flex items-center gap-2 px-3 py-2 rounded-t-md"
        style={{ backgroundColor: `${color}20` }}
      >
        <GitBranch className="w-4 h-4" style={{ color }} />
        <span className="font-semibold text-sm" style={{ color }}>
          IF
        </span>
      </div>

      {/* Body */}
      <div className="px-3 py-2 text-xs text-gray-600 dark:text-gray-300">
        {data.label || data.description || 'Conditional branching'}
      </div>

      {/* Condition display */}
      {data.parameters?.condition && (
        <div className="px-3 pb-2 text-xs font-mono text-gray-500">
          {data.parameters.condition}
        </div>
      )}

      {/* True Output Handle (Top Right) */}
      <Handle
        type="source"
        position={Position.Right}
        id="true"
        className="!w-3 !h-3 !border-2 !border-white !bg-green-500"
        style={{ right: -6, top: '35%' }}
      />
      <div className="absolute right-2 text-[10px] font-semibold text-green-600" style={{ top: '32%' }}>
        TRUE
      </div>

      {/* False Output Handle (Bottom Right) */}
      <Handle
        type="source"
        position={Position.Right}
        id="false"
        className="!w-3 !h-3 !border-2 !border-white !bg-red-500"
        style={{ right: -6, top: '65%' }}
      />
      <div className="absolute right-2 text-[10px] font-semibold text-red-600" style={{ top: '62%' }}>
        FALSE
      </div>
    </div>
  );
});
IfNode.displayName = 'IfNode';

// Loop Node
export const LoopNode = memo((props: NodeProps) => (
  <BaseNode
    {...props}
    icon={Repeat}
    title="Loop"
    color="#f97316"
    category="control"
  />
));
LoopNode.displayName = 'LoopNode';

// Merge Node with multiple inputs
export const MergeNode = memo((props: NodeProps) => {
  const { data, selected } = props;
  const color = '#14b8a6';
  const isSelected = selected || data.selected;

  return (
    <div
      className={`
        relative rounded-lg border-2 bg-white dark:bg-gray-800 shadow-lg
        transition-all duration-200
        hover:shadow-xl
      `}
      style={{
        minWidth: '180px',
        borderColor: isSelected ? color : `${color}80`,
        borderWidth: isSelected ? '3px' : '2px',
        boxShadow: isSelected
          ? `0 0 0 3px ${color}40, 0 10px 15px -3px rgba(0, 0, 0, 0.1)`
          : '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      }}
    >
      {/* Multiple Input Handles */}
      <Handle
        type="target"
        position={Position.Left}
        id="input1"
        className="!w-3 !h-3 !border-2 !border-white"
        style={{ left: -6, top: '30%', backgroundColor: color }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="input2"
        className="!w-3 !h-3 !border-2 !border-white"
        style={{ left: -6, top: '50%', backgroundColor: color }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="input3"
        className="!w-3 !h-3 !border-2 !border-white"
        style={{ left: -6, top: '70%', backgroundColor: color }}
      />

      {/* Header */}
      <div
        className="flex items-center gap-2 px-3 py-2 rounded-t-md"
        style={{ backgroundColor: `${color}20` }}
      >
        <MergeIcon className="w-4 h-4" style={{ color }} />
        <span className="font-semibold text-sm" style={{ color }}>
          Merge
        </span>
      </div>

      {/* Body */}
      <div className="px-3 py-2 text-xs text-gray-600 dark:text-gray-300">
        {data.label || data.description || 'Combine multiple outputs'}
      </div>

      {/* Single Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        className="!w-3 !h-3 !border-2 !border-white"
        style={{ right: -6, backgroundColor: color }}
      />
    </div>
  );
});
MergeNode.displayName = 'MergeNode';
