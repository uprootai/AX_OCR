import { useEffect, useState, useMemo, useCallback } from 'react';
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
  Type,
  Database,
  ScanText,
  Wand2,
  Maximize2,
  Layers,
  Minus,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  FileSpreadsheet,
  ExternalLink,
  ClipboardList,
} from 'lucide-react';
import { useAPIConfigStore } from '../../store/apiConfigStore';
import { getNodeDefinition } from '../../config/nodeDefinitions';
import { NODE_TO_CONTAINER } from '../../config/apiRegistry';

interface NodeConfig {
  type: string;
  label: string;
  description: string;
  icon: React.ElementType | string; // 아이콘은 컴포넌트 또는 이모지
  color: string;
  category: 'input' | 'detection' | 'ocr' | 'segmentation' | 'preprocessing' | 'analysis' | 'knowledge' | 'ai' | 'control';
}

const baseNodeConfigs: NodeConfig[] = [
  // Input Nodes
  {
    type: 'imageinput',
    label: 'Image Input',
    description: 'Workflow starting point',
    icon: Image,
    color: '#f97316',
    category: 'input',
  },
  {
    type: 'textinput',
    label: 'Text Input',
    description: 'Text input for non-image APIs',
    icon: Type,
    color: '#8b5cf6',
    category: 'input',
  },
  // Detection Nodes
  {
    type: 'yolo',
    label: 'YOLO (통합)',
    description: '기계도면 + P&ID 심볼 검출',
    icon: Target,
    color: '#10b981',
    category: 'detection',
  },
  {
    type: 'linedetector',
    label: 'Line Detector',
    description: 'P&ID line detection',
    icon: Minus,
    color: '#0d9488',
    category: 'segmentation',
  },
  // YOLO-PID removed - use YOLO node with model_type=pid_symbol
  // OCR Nodes
  {
    type: 'edocr2',
    label: 'eDOCr2',
    description: 'Korean OCR',
    icon: FileText,
    color: '#3b82f6',
    category: 'ocr',
  },
  {
    type: 'paddleocr',
    label: 'PaddleOCR',
    description: 'Multi-language OCR',
    icon: FileSearch,
    color: '#06b6d4',
    category: 'ocr',
  },
  // Segmentation Nodes
  {
    type: 'edgnet',
    label: 'EDGNet',
    description: 'Edge segmentation',
    icon: Network,
    color: '#8b5cf6',
    category: 'segmentation',
  },
  // Analysis Nodes
  {
    type: 'skinmodel',
    label: 'SkinModel',
    description: 'Tolerance analysis',
    icon: Ruler,
    color: '#f59e0b',
    category: 'analysis',
  },
  {
    type: 'pidanalyzer',
    label: 'P&ID Analyzer',
    description: 'BOM & connectivity analysis',
    icon: Network,
    color: '#7c3aed',
    category: 'analysis',
  },
  {
    type: 'designchecker',
    label: 'Design Checker',
    description: 'Design rule validation',
    icon: ShieldCheck,
    color: '#ef4444',
    category: 'analysis',
  },
  {
    type: 'blueprint-ai-bom',
    label: 'Blueprint AI BOM',
    description: 'Human-in-the-Loop BOM 생성',
    icon: FileSpreadsheet,
    color: '#8b5cf6',
    category: 'analysis',
  },
  // AI Nodes
  {
    type: 'vl',
    label: 'VL Model',
    description: 'Vision-Language AI',
    icon: Eye,
    color: '#ec4899',
    category: 'ai',
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
  // Knowledge Nodes
  {
    type: 'knowledge',
    label: 'Knowledge',
    description: 'Domain knowledge engine',
    icon: Database,
    color: '#9333ea',
    category: 'knowledge',
  },
  // Preprocessing Nodes
  {
    type: 'esrgan',
    label: 'ESRGAN',
    description: '4x image upscaling',
    icon: Maximize2,
    color: '#dc2626',
    category: 'preprocessing',
  },
  // OCR Nodes
  {
    type: 'tesseract',
    label: 'Tesseract',
    description: 'Google Tesseract OCR',
    icon: ScanText,
    color: '#059669',
    category: 'ocr',
  },
  {
    type: 'trocr',
    label: 'TrOCR',
    description: 'Transformer OCR',
    icon: Wand2,
    color: '#7c3aed',
    category: 'ocr',
  },
  {
    type: 'ocr_ensemble',
    label: 'OCR Ensemble',
    description: '4-way OCR voting',
    icon: Layers,
    color: '#0891b2',
    category: 'ocr',
  },
  {
    type: 'suryaocr',
    label: 'Surya OCR',
    description: '90+ language OCR',
    icon: '🌞',
    color: '#f59e0b',
    category: 'ocr',
  },
  {
    type: 'doctr',
    label: 'DocTR',
    description: '2-stage OCR pipeline',
    icon: '📄',
    color: '#6366f1',
    category: 'ocr',
  },
  {
    type: 'easyocr',
    label: 'EasyOCR',
    description: '80+ language OCR',
    icon: '👁️',
    color: '#22c55e',
    category: 'ocr',
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
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [stoppedContainers, setStoppedContainers] = useState<Set<string>>(new Set());
  const [statusFetched, setStatusFetched] = useState(false);

  // 컨테이너 상태 가져오기
  const fetchContainerStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/containers');
      const data = await response.json();
      if (data.success && data.containers) {
        const stopped = new Set<string>(
          data.containers
            .filter((c: { status: string }) => c.status !== 'running')
            .map((c: { name: string }) => c.name)
        );
        setStoppedContainers(stopped);
        setStatusFetched(true);
      }
    } catch (error) {
      console.error('Failed to fetch container status:', error);
      setStatusFetched(true);
    }
  }, []);

  // 컨테이너 상태 주기적 갱신 (5초마다)
  useEffect(() => {
    fetchContainerStatus();
    const interval = setInterval(fetchContainerStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchContainerStatus]);

  // 노드가 활성화 상태인지 확인
  const isNodeActive = useCallback((nodeType: string): boolean => {
    // Input, Control 노드는 항상 활성화
    if (['imageinput', 'textinput', 'if', 'loop', 'merge'].includes(nodeType)) {
      return true;
    }
    // 상태를 아직 가져오지 않았으면 기본 활성화
    if (!statusFetched) {
      return true;
    }
    const containerName = NODE_TO_CONTAINER[nodeType];
    if (!containerName) return true; // 매핑 없으면 활성화로 간주
    return !stoppedContainers.has(containerName);
  }, [statusFetched, stoppedContainers]);

  useEffect(() => {
    // 기본 노드 타입 집합
    const baseTypes = new Set(baseNodeConfigs.map((n) => n.type));

    // 커스텀 API를 NodeConfig로 변환 (기본 노드와 중복되지 않는 것만)
    const customNodeConfigs: NodeConfig[] = customAPIs
      .filter((api) => api.enabled && !baseTypes.has(api.id))
      .map((api) => ({
        type: api.id,
        label: api.displayName,
        description: api.description,
        icon: api.icon, // 이모지 문자열
        color: api.color,
        category: api.category,
      }));

    // 기본 노드 + 커스텀 노드 병합 (중복 제거됨)
    setAllNodeConfigs([...baseNodeConfigs, ...customNodeConfigs]);
  }, [customAPIs]);

  const inputNodes = useMemo(() => allNodeConfigs.filter((n) => n.category === 'input'), [allNodeConfigs]);
  const detectionNodes = useMemo(() => allNodeConfigs.filter((n) => n.category === 'detection'), [allNodeConfigs]);
  const ocrNodes = useMemo(() => allNodeConfigs.filter((n) => n.category === 'ocr'), [allNodeConfigs]);
  const segmentationNodes = useMemo(() => allNodeConfigs.filter((n) => n.category === 'segmentation'), [allNodeConfigs]);
  const preprocessingNodes = useMemo(() => allNodeConfigs.filter((n) => n.category === 'preprocessing'), [allNodeConfigs]);
  const analysisNodes = useMemo(() => allNodeConfigs.filter((n) => n.category === 'analysis'), [allNodeConfigs]);
  const knowledgeNodes = useMemo(() => allNodeConfigs.filter((n) => n.category === 'knowledge'), [allNodeConfigs]);
  const aiNodes = useMemo(() => allNodeConfigs.filter((n) => n.category === 'ai'), [allNodeConfigs]);
  const controlNodes = useMemo(() => allNodeConfigs.filter((n) => n.category === 'control'), [allNodeConfigs]);

  return (
    <div className={`${isCollapsed ? 'w-12' : 'w-64'} bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-y-auto transition-all duration-300 relative flex flex-col`}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute -right-3 top-4 z-10 w-6 h-6 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-full flex items-center justify-center shadow-md hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
        title={isCollapsed ? 'Expand palette' : 'Collapse palette'}
      >
        {isCollapsed ? (
          <ChevronRight className="w-4 h-4 text-gray-600 dark:text-gray-300" />
        ) : (
          <ChevronLeft className="w-4 h-4 text-gray-600 dark:text-gray-300" />
        )}
      </button>

      {/* Collapsed View - Icons Only */}
      {isCollapsed ? (
        <div className="p-2 pt-10 space-y-2">
          {/* Input icon */}
          <div className="w-8 h-8 flex items-center justify-center rounded bg-orange-100 dark:bg-orange-900/30" title="Input">
            <Image className="w-4 h-4 text-orange-500" />
          </div>
          {/* Detection icon */}
          <div className="w-8 h-8 flex items-center justify-center rounded bg-green-100 dark:bg-green-900/30" title="Detection">
            <Target className="w-4 h-4 text-green-500" />
          </div>
          {/* OCR icon */}
          <div className="w-8 h-8 flex items-center justify-center rounded bg-blue-100 dark:bg-blue-900/30" title="OCR">
            <FileText className="w-4 h-4 text-blue-500" />
          </div>
          {/* Segmentation icon */}
          <div className="w-8 h-8 flex items-center justify-center rounded bg-purple-100 dark:bg-purple-900/30" title="Segmentation">
            <Network className="w-4 h-4 text-purple-500" />
          </div>
          {/* Analysis icon */}
          <div className="w-8 h-8 flex items-center justify-center rounded bg-amber-100 dark:bg-amber-900/30" title="Analysis">
            <Ruler className="w-4 h-4 text-amber-500" />
          </div>
          {/* AI icon */}
          <div className="w-8 h-8 flex items-center justify-center rounded bg-pink-100 dark:bg-pink-900/30" title="AI">
            <Eye className="w-4 h-4 text-pink-500" />
          </div>
          {/* Control icon */}
          <div className="w-8 h-8 flex items-center justify-center rounded bg-red-100 dark:bg-red-900/30" title="Control">
            <GitBranch className="w-4 h-4 text-red-500" />
          </div>
        </div>
      ) : (
        <div className="p-4 flex-1">
          <h2 className="text-lg font-semibold mb-4">Node Palette</h2>

      {/* Input Nodes */}
      {inputNodes.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
            📥 Input
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

      {/* Detection Nodes */}
      {detectionNodes.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
            🎯 Detection
          </h3>
          <div className="space-y-2">
            {detectionNodes.map((node) => {
              const isEmojiIcon = typeof node.icon === 'string';
              const Icon = !isEmojiIcon ? (node.icon as React.ElementType) : null;
              const definition = getNodeDefinition(node.type);
              const hasRecommendedInputs = definition?.recommendedInputs && definition.recommendedInputs.length > 0;
              const isActive = isNodeActive(node.type);

              return (
                <div key={node.type} className="relative group">
                  <div
                    draggable={isActive}
                    onDragStart={(e) => isActive && onNodeDragStart(e, node.type, node.label)}
                    className={`flex items-start gap-2 p-3 rounded-lg border-2 transition-shadow ${
                      isActive
                        ? 'cursor-move bg-white dark:bg-gray-700 hover:shadow-md'
                        : 'cursor-not-allowed bg-gray-100 dark:bg-gray-800 opacity-50'
                    }`}
                    style={{ borderColor: isActive ? `${node.color}40` : '#9ca3af40' }}
                    title={isActive ? undefined : 'Container is stopped'}
                  >
                    {isEmojiIcon ? (
                      <span className={`text-xl mt-0.5 flex-shrink-0 ${!isActive && 'grayscale'}`}>{String(node.icon)}</span>
                    ) : Icon ? (
                      <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: isActive ? node.color : '#9ca3af' }} />
                    ) : null}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <div className="font-medium text-sm" style={{ color: isActive ? node.color : '#9ca3af' }}>{node.label}</div>
                        {hasRecommendedInputs && isActive && <Lightbulb className="w-3 h-3 text-yellow-500" />}
                        {!isActive && <AlertCircle className="w-3 h-3 text-red-400" />}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{node.description}</div>
                    </div>
                  </div>
                  {hasRecommendedInputs && isActive && (
                    <div className="absolute left-full ml-2 top-0 hidden group-hover:block z-50 w-72">
                      <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/90 dark:to-emerald-900/90 p-3 rounded-lg shadow-xl border-2 border-green-300 dark:border-green-700">
                        <div className="flex items-center gap-2 mb-2 pb-2 border-b border-green-200 dark:border-green-700">
                          <Lightbulb className="w-4 h-4 text-green-700 dark:text-green-300" />
                          <span className="text-xs font-semibold text-green-900 dark:text-green-100">추천 연결 패턴</span>
                        </div>
                        <div className="space-y-2">
                          {definition.recommendedInputs!.map((rec, idx) => (
                            <div key={idx} className="text-xs">
                              <div className="flex items-center gap-1.5 mb-1">
                                <span className="font-mono font-semibold text-green-800 dark:text-green-200">{rec.from}</span>
                                <ArrowRight className="w-3 h-3 text-green-600" />
                                <span className="font-mono text-green-700 dark:text-green-300">{rec.field}</span>
                              </div>
                              <p className="text-green-800 dark:text-green-100 leading-relaxed pl-2 border-l-2 border-green-400">{rec.reason}</p>
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
      )}

      {/* Segmentation Nodes */}
      {segmentationNodes.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
            🔲 Segmentation
          </h3>
          <div className="space-y-2">
            {segmentationNodes.map((node) => {
              const isEmojiIcon = typeof node.icon === 'string';
              const Icon = !isEmojiIcon ? (node.icon as React.ElementType) : null;
              const definition = getNodeDefinition(node.type);
              const hasRecommendedInputs = definition?.recommendedInputs && definition.recommendedInputs.length > 0;
              const isActive = isNodeActive(node.type);
              return (
                <div key={node.type} className="relative group">
                  <div
                    draggable={isActive}
                    onDragStart={(e) => isActive && onNodeDragStart(e, node.type, node.label)}
                    className={`flex items-start gap-2 p-3 rounded-lg border-2 transition-shadow ${
                      isActive ? 'cursor-move bg-white dark:bg-gray-700 hover:shadow-md' : 'cursor-not-allowed bg-gray-100 dark:bg-gray-800 opacity-50'
                    }`}
                    style={{ borderColor: isActive ? `${node.color}40` : '#9ca3af40' }}
                    title={isActive ? undefined : 'Container is stopped'}
                  >
                    {isEmojiIcon ? <span className={`text-xl mt-0.5 flex-shrink-0 ${!isActive && 'grayscale'}`}>{String(node.icon)}</span> : Icon ? <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: isActive ? node.color : '#9ca3af' }} /> : null}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <div className="font-medium text-sm" style={{ color: isActive ? node.color : '#9ca3af' }}>{node.label}</div>
                        {hasRecommendedInputs && isActive && <Lightbulb className="w-3 h-3 text-yellow-500" />}
                        {!isActive && <AlertCircle className="w-3 h-3 text-red-400" />}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{node.description}</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Analysis Nodes */}
      {analysisNodes.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
            📐 Analysis
          </h3>
          <div className="space-y-2">
            {analysisNodes.map((node) => {
              const isEmojiIcon = typeof node.icon === 'string';
              const Icon = !isEmojiIcon ? (node.icon as React.ElementType) : null;
              const definition = getNodeDefinition(node.type);
              const hasRecommendedInputs = definition?.recommendedInputs && definition.recommendedInputs.length > 0;
              const isActive = isNodeActive(node.type);
              return (
                <div key={node.type} className="relative group">
                  <div
                    draggable={isActive}
                    onDragStart={(e) => isActive && onNodeDragStart(e, node.type, node.label)}
                    className={`flex items-start gap-2 p-3 rounded-lg border-2 transition-shadow ${
                      isActive ? 'cursor-move bg-white dark:bg-gray-700 hover:shadow-md' : 'cursor-not-allowed bg-gray-100 dark:bg-gray-800 opacity-50'
                    }`}
                    style={{ borderColor: isActive ? `${node.color}40` : '#9ca3af40' }}
                    title={isActive ? undefined : 'Container is stopped'}
                  >
                    {isEmojiIcon ? <span className={`text-xl mt-0.5 flex-shrink-0 ${!isActive && 'grayscale'}`}>{String(node.icon)}</span> : Icon ? <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: isActive ? node.color : '#9ca3af' }} /> : null}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <div className="font-medium text-sm" style={{ color: isActive ? node.color : '#9ca3af' }}>{node.label}</div>
                        {hasRecommendedInputs && isActive && <Lightbulb className="w-3 h-3 text-yellow-500" />}
                        {!isActive && <AlertCircle className="w-3 h-3 text-red-400" />}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{node.description}</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Knowledge Nodes */}
      {knowledgeNodes.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
            🧠 Knowledge
          </h3>
          <div className="space-y-2">
            {knowledgeNodes.map((node) => {
              const isEmojiIcon = typeof node.icon === 'string';
              const Icon = !isEmojiIcon ? (node.icon as React.ElementType) : null;
              const definition = getNodeDefinition(node.type);
              const hasRecommendedInputs = definition?.recommendedInputs && definition.recommendedInputs.length > 0;
              const isActive = isNodeActive(node.type);

              return (
                <div key={node.type} className="relative group">
                  <div
                    draggable={isActive}
                    onDragStart={(e) => isActive && onNodeDragStart(e, node.type, node.label)}
                    className={`flex items-start gap-2 p-3 rounded-lg border-2 transition-shadow ${
                      isActive ? 'cursor-move bg-white dark:bg-gray-700 hover:shadow-md' : 'cursor-not-allowed bg-gray-100 dark:bg-gray-800 opacity-50'
                    }`}
                    style={{ borderColor: isActive ? `${node.color}40` : '#9ca3af40' }}
                    title={isActive ? undefined : 'Container is stopped'}
                  >
                    {isEmojiIcon ? (
                      <span className={`text-xl mt-0.5 flex-shrink-0 ${!isActive && 'grayscale'}`}>{String(node.icon)}</span>
                    ) : Icon ? (
                      <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: isActive ? node.color : '#9ca3af' }} />
                    ) : null}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <div className="font-medium text-sm" style={{ color: isActive ? node.color : '#9ca3af' }}>
                          {node.label}
                        </div>
                        {hasRecommendedInputs && isActive && <Lightbulb className="w-3 h-3 text-yellow-500" />}
                        {!isActive && <AlertCircle className="w-3 h-3 text-red-400" />}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {node.description}
                      </div>
                    </div>
                  </div>

                  {/* Hover Tooltip - Recommended Connections */}
                  {hasRecommendedInputs && isActive && (
                    <div className="absolute left-full ml-2 top-0 hidden group-hover:block z-50 w-72">
                      <div className="bg-gradient-to-br from-purple-50 to-violet-50 dark:from-purple-900/90 dark:to-violet-900/90 p-3 rounded-lg shadow-xl border-2 border-purple-300 dark:border-purple-700">
                        <div className="flex items-center gap-2 mb-2 pb-2 border-b border-purple-200 dark:border-purple-700">
                          <Lightbulb className="w-4 h-4 text-purple-700 dark:text-purple-300" />
                          <span className="text-xs font-semibold text-purple-900 dark:text-purple-100">
                            추천 연결 패턴
                          </span>
                        </div>
                        <div className="space-y-2">
                          {definition.recommendedInputs!.map((rec, idx) => (
                            <div key={idx} className="text-xs">
                              <div className="flex items-center gap-1.5 mb-1">
                                <span className="font-mono font-semibold text-purple-800 dark:text-purple-200">
                                  {rec.from}
                                </span>
                                <ArrowRight className="w-3 h-3 text-purple-600" />
                                <span className="font-mono text-purple-700 dark:text-purple-300">
                                  {rec.field}
                                </span>
                              </div>
                              <p className="text-purple-800 dark:text-purple-100 leading-relaxed pl-2 border-l-2 border-purple-400">
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
      )}

      {/* AI Nodes (VL) */}
      {aiNodes.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
            🤖 AI / LLM
          </h3>
          <div className="space-y-2">
            {aiNodes.map((node) => {
              const isEmojiIcon = typeof node.icon === 'string';
              const Icon = !isEmojiIcon ? (node.icon as React.ElementType) : null;
              const definition = getNodeDefinition(node.type);
              const hasRecommendedInputs = definition?.recommendedInputs && definition.recommendedInputs.length > 0;
              const isActive = isNodeActive(node.type);
              return (
                <div key={node.type} className="relative group">
                  <div
                    draggable={isActive}
                    onDragStart={(e) => isActive && onNodeDragStart(e, node.type, node.label)}
                    className={`flex items-start gap-2 p-3 rounded-lg border-2 transition-shadow ${
                      isActive ? 'cursor-move bg-white dark:bg-gray-700 hover:shadow-md' : 'cursor-not-allowed bg-gray-100 dark:bg-gray-800 opacity-50'
                    }`}
                    style={{ borderColor: isActive ? `${node.color}40` : '#9ca3af40' }}
                    title={isActive ? undefined : 'Container is stopped'}
                  >
                    {isEmojiIcon ? <span className={`text-xl mt-0.5 flex-shrink-0 ${!isActive && 'grayscale'}`}>{String(node.icon)}</span> : Icon ? <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: isActive ? node.color : '#9ca3af' }} /> : null}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <div className="font-medium text-sm" style={{ color: isActive ? node.color : '#9ca3af' }}>{node.label}</div>
                        {hasRecommendedInputs && isActive && <Lightbulb className="w-3 h-3 text-yellow-500" />}
                        {!isActive && <AlertCircle className="w-3 h-3 text-red-400" />}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{node.description}</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Preprocessing Nodes */}
      {preprocessingNodes.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
            ⚡ Preprocessing
          </h3>
          <div className="space-y-2">
            {preprocessingNodes.map((node) => {
              const isEmojiIcon = typeof node.icon === 'string';
              const Icon = !isEmojiIcon ? (node.icon as React.ElementType) : null;
              const definition = getNodeDefinition(node.type);
              const hasRecommendedInputs = definition?.recommendedInputs && definition.recommendedInputs.length > 0;
              const isActive = isNodeActive(node.type);

              return (
                <div key={node.type} className="relative group">
                  <div
                    draggable={isActive}
                    onDragStart={(e) => isActive && onNodeDragStart(e, node.type, node.label)}
                    className={`flex items-start gap-2 p-3 rounded-lg border-2 transition-shadow ${
                      isActive ? 'cursor-move bg-white dark:bg-gray-700 hover:shadow-md' : 'cursor-not-allowed bg-gray-100 dark:bg-gray-800 opacity-50'
                    }`}
                    style={{ borderColor: isActive ? `${node.color}40` : '#9ca3af40' }}
                    title={isActive ? undefined : 'Container is stopped'}
                  >
                    {isEmojiIcon ? (
                      <span className={`text-xl mt-0.5 flex-shrink-0 ${!isActive && 'grayscale'}`}>{String(node.icon)}</span>
                    ) : Icon ? (
                      <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: isActive ? node.color : '#9ca3af' }} />
                    ) : null}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <div className="font-medium text-sm" style={{ color: isActive ? node.color : '#9ca3af' }}>
                          {node.label}
                        </div>
                        {hasRecommendedInputs && isActive && <Lightbulb className="w-3 h-3 text-yellow-500" />}
                        {!isActive && <AlertCircle className="w-3 h-3 text-red-400" />}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {node.description}
                      </div>
                    </div>
                  </div>

                  {/* Hover Tooltip */}
                  {hasRecommendedInputs && isActive && (
                    <div className="absolute left-full ml-2 top-0 hidden group-hover:block z-50 w-72">
                      <div className="bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-900/90 dark:to-orange-900/90 p-3 rounded-lg shadow-xl border-2 border-red-300 dark:border-red-700">
                        <div className="flex items-center gap-2 mb-2 pb-2 border-b border-red-200 dark:border-red-700">
                          <Lightbulb className="w-4 h-4 text-red-700 dark:text-red-300" />
                          <span className="text-xs font-semibold text-red-900 dark:text-red-100">
                            추천 연결 패턴
                          </span>
                        </div>
                        <div className="space-y-2">
                          {definition.recommendedInputs!.map((rec, idx) => (
                            <div key={idx} className="text-xs">
                              <div className="flex items-center gap-1.5 mb-1">
                                <span className="font-mono font-semibold text-red-800 dark:text-red-200">
                                  {rec.from}
                                </span>
                                <ArrowRight className="w-3 h-3 text-red-600" />
                                <span className="font-mono text-red-700 dark:text-red-300">
                                  {rec.field}
                                </span>
                              </div>
                              <p className="text-red-800 dark:text-red-100 leading-relaxed pl-2 border-l-2 border-red-400">
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
      )}

      {/* OCR Nodes */}
      {ocrNodes.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
            📝 OCR
          </h3>
          <div className="space-y-2">
            {ocrNodes.map((node) => {
              const isEmojiIcon = typeof node.icon === 'string';
              const Icon = !isEmojiIcon ? (node.icon as React.ElementType) : null;
              const definition = getNodeDefinition(node.type);
              const hasRecommendedInputs = definition?.recommendedInputs && definition.recommendedInputs.length > 0;
              const isActive = isNodeActive(node.type);

              return (
                <div key={node.type} className="relative group">
                  <div
                    draggable={isActive}
                    onDragStart={(e) => isActive && onNodeDragStart(e, node.type, node.label)}
                    className={`flex items-start gap-2 p-3 rounded-lg border-2 transition-shadow ${
                      isActive ? 'cursor-move bg-white dark:bg-gray-700 hover:shadow-md' : 'cursor-not-allowed bg-gray-100 dark:bg-gray-800 opacity-50'
                    }`}
                    style={{ borderColor: isActive ? `${node.color}40` : '#9ca3af40' }}
                    title={isActive ? undefined : 'Container is stopped'}
                  >
                    {isEmojiIcon ? (
                      <span className={`text-xl mt-0.5 flex-shrink-0 ${!isActive && 'grayscale'}`}>{String(node.icon)}</span>
                    ) : Icon ? (
                      <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: isActive ? node.color : '#9ca3af' }} />
                    ) : null}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <div className="font-medium text-sm" style={{ color: isActive ? node.color : '#9ca3af' }}>
                          {node.label}
                        </div>
                        {hasRecommendedInputs && isActive && <Lightbulb className="w-3 h-3 text-yellow-500" />}
                        {!isActive && <AlertCircle className="w-3 h-3 text-red-400" />}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {node.description}
                      </div>
                    </div>
                  </div>

                  {/* Hover Tooltip */}
                  {hasRecommendedInputs && isActive && (
                    <div className="absolute left-full ml-2 top-0 hidden group-hover:block z-50 w-72">
                      <div className="bg-gradient-to-br from-cyan-50 to-teal-50 dark:from-cyan-900/90 dark:to-teal-900/90 p-3 rounded-lg shadow-xl border-2 border-cyan-300 dark:border-cyan-700">
                        <div className="flex items-center gap-2 mb-2 pb-2 border-b border-cyan-200 dark:border-cyan-700">
                          <Lightbulb className="w-4 h-4 text-cyan-700 dark:text-cyan-300" />
                          <span className="text-xs font-semibold text-cyan-900 dark:text-cyan-100">
                            추천 연결 패턴
                          </span>
                        </div>
                        <div className="space-y-2">
                          {definition.recommendedInputs!.map((rec, idx) => (
                            <div key={idx} className="text-xs">
                              <div className="flex items-center gap-1.5 mb-1">
                                <span className="font-mono font-semibold text-cyan-800 dark:text-cyan-200">
                                  {rec.from}
                                </span>
                                <ArrowRight className="w-3 h-3 text-cyan-600" />
                                <span className="font-mono text-cyan-700 dark:text-cyan-300">
                                  {rec.field}
                                </span>
                              </div>
                              <p className="text-cyan-800 dark:text-cyan-100 leading-relaxed pl-2 border-l-2 border-cyan-400">
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
      )}

      {/* Control Nodes - Always at the end */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
          🔀 Control Flow
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
                className="flex items-start gap-2 p-3 rounded-lg border-2 cursor-move bg-white dark:bg-gray-700 hover:shadow-md transition-shadow"
                style={{ borderColor: `${node.color}40` }}
              >
                {isEmojiIcon ? (
                  <span className="text-xl mt-0.5 flex-shrink-0">{String(node.icon)}</span>
                ) : Icon ? (
                  <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: node.color }} />
                ) : null}
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm" style={{ color: node.color }}>{node.label}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">{node.description}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Quick Links */}
      <div className="mb-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2 uppercase">
          🔗 Quick Links
        </h3>
        <div className="space-y-2">
          <a
            href="http://localhost:3000"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-2 p-3 rounded-lg border-2 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/30 dark:to-teal-900/30 hover:shadow-md transition-shadow border-emerald-300 dark:border-emerald-700"
          >
            <ClipboardList className="w-5 h-5 mt-0.5 flex-shrink-0 text-emerald-600 dark:text-emerald-400" />
            <div className="flex-1 min-w-0">
              <div className="font-medium text-sm text-emerald-700 dark:text-emerald-300 flex items-center gap-1">
                Quick BOM
                <ExternalLink className="w-3 h-3" />
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                간편 BOM 생성 워크플로우
              </div>
            </div>
          </a>
        </div>
      </div>
        </div>
      )}
    </div>
  );
}
