import { useEffect, useState } from 'react';
import {
  Target,
  FileText,
  Network,
  Ruler,
  FileSearch,
  Eye,
  GitBranch,
  Repeat,
  Merge as MergeIcon,
} from 'lucide-react';
import { useAPIConfigStore } from '../../store/apiConfigStore';

interface NodeConfig {
  type: string;
  label: string;
  description: string;
  icon: React.ElementType | string; // 아이콘은 컴포넌트 또는 이모지
  color: string;
  category: 'api' | 'control';
}

const baseNodeConfigs: NodeConfig[] = [
  // API Nodes
  {
    type: 'yolo',
    label: 'YOLO',
    description: 'Object detection',
    icon: Target,
    color: '#10b981',
    category: 'api',
  },
  {
    type: 'edocr2',
    label: 'eDOCr2',
    description: 'Korean OCR',
    icon: FileText,
    color: '#3b82f6',
    category: 'api',
  },
  {
    type: 'edgnet',
    label: 'EDGNet',
    description: 'Segmentation',
    icon: Network,
    color: '#8b5cf6',
    category: 'api',
  },
  {
    type: 'skinmodel',
    label: 'SkinModel',
    description: 'Tolerance analysis',
    icon: Ruler,
    color: '#f59e0b',
    category: 'api',
  },
  {
    type: 'paddleocr',
    label: 'PaddleOCR',
    description: 'Multi-language OCR',
    icon: FileSearch,
    color: '#06b6d4',
    category: 'api',
  },
  {
    type: 'vl',
    label: 'VL Model',
    description: 'Vision-Language',
    icon: Eye,
    color: '#ec4899',
    category: 'api',
  },
  // Control Nodes
  {
    type: 'if',
    label: 'IF',
    description: 'Conditional branching',
    icon: GitBranch,
    color: '#ef4444',
    category: 'control',
  },
  {
    type: 'loop',
    label: 'Loop',
    description: 'Iterate over items',
    icon: Repeat,
    color: '#f97316',
    category: 'control',
  },
  {
    type: 'merge',
    label: 'Merge',
    description: 'Combine outputs',
    icon: MergeIcon,
    color: '#14b8a6',
    category: 'control',
  },
];

interface NodePaletteProps {
  onNodeDragStart: (event: React.DragEvent, nodeType: string, label: string) => void;
}

export default function NodePalette({ onNodeDragStart }: NodePaletteProps) {
  const { customAPIs } = useAPIConfigStore();
  const [allNodeConfigs, setAllNodeConfigs] = useState<NodeConfig[]>(baseNodeConfigs);

  useEffect(() => {
    // 커스텀 API를 NodeConfig로 변환
    const customNodeConfigs: NodeConfig[] = customAPIs
      .filter((api) => api.enabled)
      .map((api) => ({
        type: api.id,
        label: api.displayName,
        description: api.description,
        icon: api.icon, // 이모지 문자열
        color: api.color,
        category: api.category,
      }));

    // 기본 노드 + 커스텀 노드 병합
    setAllNodeConfigs([...baseNodeConfigs, ...customNodeConfigs]);
  }, [customAPIs]);

  const apiNodes = allNodeConfigs.filter((n) => n.category === 'api');
  const controlNodes = allNodeConfigs.filter((n) => n.category === 'control');

  return (
    <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-4 overflow-y-auto">
      <h2 className="text-lg font-semibold mb-4">Node Palette</h2>

      {/* 동적 API 안내 */}
      {customAPIs.length > 0 && (
        <div className="mb-4 p-3 bg-cyan-50 dark:bg-cyan-950 border border-cyan-200 dark:border-cyan-800 rounded-lg">
          <div className="flex items-start gap-2">
            <span className="text-sm flex-shrink-0">➕</span>
            <div>
              <p className="text-xs font-semibold text-cyan-900 dark:text-cyan-100 mb-1">
                동적 API {customAPIs.length}개 추가됨
              </p>
              <p className="text-xs text-cyan-700 dark:text-cyan-300">
                Dashboard에서 추가한 API가 자동으로 노드 팔레트에 추가되었습니다.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* API Nodes */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
          API Nodes
        </h3>
        <div className="space-y-2">
          {apiNodes.map((node) => {
            const isEmojiIcon = typeof node.icon === 'string';
            const Icon = !isEmojiIcon ? (node.icon as React.ElementType) : null;

            return (
              <div
                key={node.type}
                draggable
                onDragStart={(e) => onNodeDragStart(e, node.type, node.label)}
                className="
                  flex items-start gap-2 p-3 rounded-lg border-2 cursor-move
                  bg-white dark:bg-gray-700
                  hover:shadow-md transition-shadow
                "
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
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {node.description}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Control Nodes */}
      <div>
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
          Control Nodes
        </h3>
        <div className="space-y-2">
          {controlNodes.map((node) => {
            const isEmojiIcon = typeof node.icon === 'string';
            const Icon = !isEmojiIcon ? (node.icon as React.ElementType) : null;

            return (
              <div
                key={node.type}
                draggable
                onDragStart={(e) => onNodeDragStart(e, node.type, node.label)}
                className="
                  flex items-start gap-2 p-3 rounded-lg border-2 cursor-move
                  bg-white dark:bg-gray-700
                  hover:shadow-md transition-shadow
                "
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
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {node.description}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
