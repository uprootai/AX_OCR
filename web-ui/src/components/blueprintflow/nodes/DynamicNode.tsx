import { memo } from 'react';
import { Handle, Position } from 'reactflow';

interface DynamicNodeProps {
  data: {
    label: string;
    icon: string;
    color: string;
  };
}

/**
 * 동적으로 생성된 커스텀 API 노드를 렌더링합니다.
 * Dashboard에서 추가한 커스텀 API를 BlueprintFlow에서 사용할 수 있게 합니다.
 */
export default memo(function DynamicNode({ data }: DynamicNodeProps) {
  return (
    <div
      className="px-4 py-3 shadow-lg rounded-lg border-2 bg-white min-w-[180px]"
      style={{ borderColor: data.color }}
    >
      <Handle type="target" position={Position.Top} className="w-3 h-3" />

      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">{data.icon}</span>
        <div className="font-bold text-sm">{data.label}</div>
      </div>

      <div className="text-xs text-gray-500">Custom API Node</div>

      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </div>
  );
});
