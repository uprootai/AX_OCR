import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import { getNodeDefinition } from '../../../config/nodeDefinitions';

interface DynamicNodeData {
  label?: string;
  icon?: string;
  color?: string;
  description?: string;
  status?: 'pending' | 'running' | 'completed' | 'failed';
  selected?: boolean;
}

/**
 * Lucide 아이콘 이름 → 이모지 매핑
 * DynamicNode에서 nodeDefinitions의 아이콘 이름을 이모지로 변환
 */
const ICON_EMOJI_MAP: Record<string, string> = {
  // Detection
  Target: '🎯',
  CircuitBoard: '🔧',
  // OCR
  FileText: '📄',
  FileSearch: '🔍',
  ScanText: '📝',
  Wand2: '✨',
  Layers: '📚',
  Languages: '🌐',
  // Segmentation
  Network: '🔗',
  Minus: '➖',
  // Preprocessing
  Maximize2: '🔎',
  // Analysis
  Ruler: '📏',
  ShieldCheck: '✅',
  // Knowledge
  Database: '🗄️',
  // AI
  Sparkles: '✨',
  Eye: '👁️',
  // Control
  GitBranch: '🔀',
  Repeat: '🔄',
  Merge: '🔗',
  // Input
  Image: '🖼️',
  Type: '📝',
  // Default
  FileSpreadsheet: '📋',
};

/**
 * 아이콘 문자열을 이모지로 변환
 * - 이미 이모지인 경우 그대로 반환
 * - Lucide 아이콘 이름인 경우 매핑된 이모지 반환
 */
const getIconEmoji = (icon: string | undefined): string => {
  if (!icon) return '📦';
  // 이미 이모지인 경우 (첫 문자가 유니코드 이모지 범위)
  if (/^[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/u.test(icon)) {
    return icon;
  }
  // Lucide 아이콘 이름인 경우 매핑
  return ICON_EMOJI_MAP[icon] || '📦';
};

/**
 * 동적으로 생성된 노드를 렌더링합니다.
 * - Dashboard에서 추가한 커스텀 API
 * - nodeDefinitions에 정의되어 있지만 전용 컴포넌트가 없는 노드 (blueprint-ai-bom, yolo-pid 등)
 */
export default memo(function DynamicNode({ data, selected, type }: NodeProps<DynamicNodeData>) {
  // nodeDefinitions에서 정의를 가져와서 색상과 라벨 결정
  const definition = type ? getNodeDefinition(type) : null;

  const nodeColor = data?.color || definition?.color || '#6b7280';
  const nodeLabel = data?.label || definition?.label || type || 'Unknown';
  const rawIcon = data?.icon || definition?.icon;
  const nodeIcon = getIconEmoji(rawIcon);
  const nodeDescription = data?.description || definition?.description || '';
  const isSelected = selected || data?.selected;

  return (
    <div
      className="relative rounded-lg border-2 bg-white dark:bg-gray-800 shadow-lg transition-all duration-200 hover:shadow-xl"
      style={{
        minWidth: '200px',
        borderColor: isSelected ? nodeColor : `${nodeColor}80`,
        borderWidth: isSelected ? '3px' : '2px',
        boxShadow: isSelected
          ? `0 0 0 3px ${nodeColor}40, 0 10px 15px -3px rgba(0, 0, 0, 0.1)`
          : '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      }}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-3 !h-3 !border-2 !border-white"
        style={{ left: -6, backgroundColor: nodeColor }}
      />

      {/* Header */}
      <div
        className="flex items-center gap-2 px-3 py-2 rounded-t-md"
        style={{ backgroundColor: `${nodeColor}20` }}
      >
        <span className="text-base">{nodeIcon}</span>
        <span className="font-semibold text-sm" style={{ color: nodeColor }}>
          {nodeLabel}
        </span>
      </div>

      {/* Body */}
      <div className="px-3 py-2 text-xs text-gray-600 dark:text-gray-300 line-clamp-2">
        {nodeDescription || type || 'Dynamic Node'}
      </div>

      {/* Status Indicator */}
      {data?.status && (
        <div className="px-3 pb-2">
          <div
            className={`
              text-xs px-2 py-1 rounded flex items-center gap-1
              ${data.status === 'completed' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : ''}
              ${data.status === 'running' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 animate-pulse' : ''}
              ${data.status === 'failed' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' : ''}
              ${data.status === 'pending' ? 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300' : ''}
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
        className="!w-3 !h-3 !border-2 !border-white"
        style={{ right: -6, backgroundColor: nodeColor }}
      />
    </div>
  );
});
