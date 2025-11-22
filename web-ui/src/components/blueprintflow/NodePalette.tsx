import { useEffect, useState } from 'react';
import {
  Image,
  Target,
  FileText,
  Network,
  Ruler,
  FileSearch,
  Eye,
  GitBranch,
  Repeat,
  Merge as MergeIcon,
  Lightbulb,
  ArrowRight,
} from 'lucide-react';
import { useAPIConfigStore } from '../../store/apiConfigStore';
import { getNodeDefinition } from '../../config/nodeDefinitions';

interface NodeConfig {
  type: string;
  label: string;
  description: string;
  icon: React.ElementType | string; // 아이콘은 컴포넌트 또는 이모지
  color: string;
  category: 'input' | 'api' | 'control';
}

const baseNodeConfigs: NodeConfig[] = [
  // Input Node
  {
    type: 'imageinput',
    label: 'Image Input',
    description: 'Workflow starting point',
    icon: Image,
    color: '#f97316',
    category: 'input',
  },
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
  uploadedImage?: string | null;
  uploadedFileName?: string | null;
}

export default function NodePalette({ onNodeDragStart, uploadedImage, uploadedFileName }: NodePaletteProps) {
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

  const inputNodes = allNodeConfigs.filter((n) => n.category === 'input');
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

      {/* Input Nodes */}
      {inputNodes.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
            Input Nodes
          </h3>
          <div className="space-y-2">
            {inputNodes.map((node) => {
              const isEmojiIcon = typeof node.icon === 'string';
              const Icon = !isEmojiIcon ? (node.icon as React.ElementType) : null;
              const isImageInputNode = node.type === 'imageinput';

              return (
                <div key={node.type}>
                  <div
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

                  {/* 업로드된 이미지 썸네일 표시 (Image Input 노드만) */}
                  {isImageInputNode && uploadedImage && (
                    <div className="mt-2 ml-2 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
                        <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                          Uploaded Image
                        </span>
                      </div>
                      <div className="relative group">
                        <img
                          src={uploadedImage}
                          alt="Uploaded preview"
                          className="w-full h-20 object-cover rounded border border-gray-300 dark:border-gray-600"
                        />
                        {uploadedFileName && (
                          <div className="mt-1 text-xs text-gray-500 dark:text-gray-400 truncate">
                            📁 {uploadedFileName}
                          </div>
                        )}
                        {/* Hover to show larger preview */}
                        <div className="absolute left-full ml-2 top-0 hidden group-hover:block z-50">
                          <div className="bg-white dark:bg-gray-800 p-2 rounded-lg shadow-xl border border-gray-300 dark:border-gray-600">
                            <img
                              src={uploadedImage}
                              alt="Uploaded preview large"
                              className="w-64 h-auto rounded"
                            />
                            {uploadedFileName && (
                              <div className="mt-2 text-xs text-gray-600 dark:text-gray-400 text-center">
                                {uploadedFileName}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
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
            const definition = getNodeDefinition(node.type);
            const hasRecommendedInputs = definition?.recommendedInputs && definition.recommendedInputs.length > 0;

            return (
              <div key={node.type} className="relative group">
                <div
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
                    <div className="flex items-center gap-1.5">
                      <div className="font-medium text-sm" style={{ color: node.color }}>
                        {node.label}
                      </div>
                      {hasRecommendedInputs && (
                        <Lightbulb className="w-3 h-3 text-yellow-500" />
                      )}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {node.description}
                    </div>
                  </div>
                </div>

                {/* Hover Tooltip - Recommended Connections */}
                {hasRecommendedInputs && (
                  <div className="absolute left-full ml-2 top-0 hidden group-hover:block z-50 w-72">
                    <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/90 dark:to-emerald-900/90 p-3 rounded-lg shadow-xl border-2 border-green-300 dark:border-green-700">
                      <div className="flex items-center gap-2 mb-2 pb-2 border-b border-green-200 dark:border-green-700">
                        <Lightbulb className="w-4 h-4 text-green-700 dark:text-green-300" />
                        <span className="text-xs font-semibold text-green-900 dark:text-green-100">
                          추천 연결 패턴
                        </span>
                      </div>
                      <div className="space-y-2">
                        {definition.recommendedInputs!.map((rec, idx) => (
                          <div key={idx} className="text-xs">
                            <div className="flex items-center gap-1.5 mb-1">
                              <span className="font-mono font-semibold text-green-800 dark:text-green-200">
                                {rec.from}
                              </span>
                              <ArrowRight className="w-3 h-3 text-green-600" />
                              <span className="font-mono text-green-700 dark:text-green-300">
                                {rec.field}
                              </span>
                            </div>
                            <p className="text-green-800 dark:text-green-100 leading-relaxed pl-2 border-l-2 border-green-400">
                              {rec.reason}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
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
