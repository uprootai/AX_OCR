import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import type { LucideIcon } from 'lucide-react';

interface BaseNodeProps extends NodeProps {
  icon: LucideIcon;
  title: string;
  color: string;
  category: 'api' | 'control';
}

export const BaseNode = memo(({ data, selected, icon: Icon, title, color, category }: BaseNodeProps) => {
  const isSelected = selected || data.selected;

  return (
    <div
      className={`
        relative rounded-lg border-2 bg-white dark:bg-gray-800 shadow-lg
        transition-all duration-200
        hover:shadow-xl
      `}
      style={{
        minWidth: category === 'control' ? '180px' : '200px',
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
        className={`!w-3 !h-3 !border-2 !border-white`}
        style={{ left: -6, backgroundColor: color }}
      />

      {/* Header */}
      <div
        className="flex items-center gap-2 px-3 py-2 rounded-t-md"
        style={{ backgroundColor: `${color}20` }}
      >
        <Icon className={`w-4 h-4`} style={{ color }} />
        <span className="font-semibold text-sm" style={{ color }}>
          {title}
        </span>
      </div>

      {/* Body */}
      <div className="px-3 py-2 text-xs text-gray-600 dark:text-gray-300">
        {data.label || data.description || 'No description'}
      </div>

      {/* Status Indicator */}
      {data.status && (
        <div className="px-3 pb-2">
          <div
            className={`
              text-xs px-2 py-1 rounded flex items-center gap-1
              ${data.status === 'completed' ? 'bg-green-100 text-green-700' : ''}
              ${data.status === 'running' ? 'bg-blue-100 text-blue-700 animate-pulse' : ''}
              ${data.status === 'failed' ? 'bg-red-100 text-red-700' : ''}
              ${data.status === 'pending' ? 'bg-gray-100 text-gray-700' : ''}
            `}
          >
            <div className="w-2 h-2 rounded-full bg-current" />
            {data.status}
          </div>
        </div>
      )}

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        className={`!w-3 !h-3 !border-2 !border-white`}
        style={{ right: -6, backgroundColor: color }}
      />
    </div>
  );
});

BaseNode.displayName = 'BaseNode';
