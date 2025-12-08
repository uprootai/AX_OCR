import { useCallback, useRef, useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
} from 'reactflow';
import type { ReactFlowInstance, OnSelectionChangeParams, NodeTypes } from 'reactflow';
import 'reactflow/dist/style.css';

import { nodeDefinitions } from '../../config/nodeDefinitions';
import { useWorkflowStore, type NodeStatus } from '../../store/workflowStore';

// API response node status type (snake_case from backend)
interface APINodeStatus {
  node_id: string;
  status: string;
  execution_time?: number;
  start_time?: string;
  end_time?: string;
  output?: Record<string, unknown>;
  error?: string;
}

// API result types for type-safe rendering
interface Detection {
  class_name?: string;
  class?: string;
  confidence: number;
  bbox?: { x: number; y: number; width: number; height: number };
  class_id?: number;
}

interface DimensionResult {
  type?: string;
  value?: number | string;
  text?: string;
  unit?: string;
  tolerance?: string | number;
}

interface TextResult {
  text?: string;
  content?: string;
  confidence?: number;
}

interface OCRBlock {
  text?: string;
  confidence?: number;
}

interface SegmentResult {
  class?: string;
  type?: string;
  confidence?: number;
}

interface ToleranceItem {
  dimension?: string;
  name?: string;
  value?: string | number;
}

// GDT type for OCR results
interface GDTItem {
  type: string;
  value: number;
  datum: string | null;
  bbox?: { x: number; y: number; width: number; height: number };
}

// Flexible output type for pipeline results
interface PipelineOutput {
  [key: string]: unknown;
  detections?: Detection[];
  dimensions?: DimensionResult[];
  text_results?: TextResult[];
  blocks?: OCRBlock[];
  segments?: SegmentResult[];
  tolerances?: ToleranceItem[];
  analysis?: Record<string, unknown>;
  result?: string;
  description?: string;
  image?: string;
  visualized_image?: string;
  gdt?: GDTItem[];
  text?: string | { total_blocks?: number };
  manufacturability?: { score: number; difficulty: string };
  predicted_tolerances?: Record<string, number>;
  // Segmentation specific
  num_components?: number;
  classifications?: { contour: number; text: number; dimension: number };
  graph?: { nodes: number; edges: number; avg_degree: number };
  vectorization?: { num_bezier_curves: number; total_length: number };
}
import { useAPIConfigStore } from '../../store/apiConfigStore';
import NodePalette from '../../components/blueprintflow/NodePalette';
import NodeDetailPanel from '../../components/blueprintflow/NodeDetailPanel';
import {
  ImageInputNode,
  TextInputNode,
  YoloNode,
  Edocr2Node,
  EdgnetNode,
  SkinmodelNode,
  PaddleocrNode,
  VlNode,
  IfNode,
  LoopNode,
  MergeNode,
} from '../../components/blueprintflow/nodes';
import DynamicNode from '../../components/blueprintflow/nodes/DynamicNode';
import { Button } from '../../components/ui/Button';
import { Play, Save, Trash2, Upload, X, Bug, Download, RotateCcw } from 'lucide-react';
import { workflowApi } from '../../lib/api';
import type { SampleFile } from '../../components/upload/SampleFileGrid';
import DebugPanel from '../../components/blueprintflow/DebugPanel';
import OCRVisualization from '../../components/debug/OCRVisualization';
import ToleranceVisualization from '../../components/debug/ToleranceVisualization';
import SegmentationVisualization from '../../components/debug/SegmentationVisualization';
import ResultSummaryCard from '../../components/blueprintflow/ResultSummaryCard';
import PipelineConclusionCard from '../../components/blueprintflow/PipelineConclusionCard';

// Base node type mapping
const baseNodeTypes = {
  imageinput: ImageInputNode,
  textinput: TextInputNode,
  yolo: YoloNode,
  edocr2: Edocr2Node,
  edgnet: EdgnetNode,
  skinmodel: SkinmodelNode,
  paddleocr: PaddleocrNode,
  vl: VlNode,
  if: IfNode,
  loop: LoopNode,
  merge: MergeNode,
};

let nodeId = 0;
const getId = () => `node_${nodeId++}`;

// BlueprintFlow 샘플 이미지 (이미지 2개만)
const BLUEPRINT_SAMPLES: SampleFile[] = [
  {
    id: 'sample-1',
    name: 'Intermediate Shaft (Image)',
    path: '/samples/sample2_interm_shaft.jpg',
    description: '선박 중간축 도면 - 모든 분석 지원',
    type: 'image',
    recommended: true
  },
  {
    id: 'sample-2',
    name: 'S60ME-C Shaft (Korean)',
    path: '/samples/sample3_s60me_shaft.jpg',
    description: 'S60ME-C 중간축 도면 - 한글 포함',
    type: 'image'
  }
];

function WorkflowBuilderCanvas() {
  const { t } = useTranslation();
  const customAPIs = useAPIConfigStore((state) => state.customAPIs);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isDebugPanelOpen, setIsDebugPanelOpen] = useState(false);
  const [isStatusCollapsed, setIsStatusCollapsed] = useState(false);

  // Uploaded image from store (persists across navigation)
  const uploadedImage = useWorkflowStore((state) => state.uploadedImage);
  const uploadedFileName = useWorkflowStore((state) => state.uploadedFileName);
  const setUploadedImage = useWorkflowStore((state) => state.setUploadedImage);

  // nodes 배열 가져오기 (먼저 선언)
  const nodes = useWorkflowStore((state) => state.nodes);

  // nodes 배열에서 선택된 노드 찾기 (항상 최신 데이터 반영)
  const selectedNode = useMemo(() => {
    if (!selectedNodeId) return null;
    return nodes.find((n) => n.id === selectedNodeId) || null;
  }, [selectedNodeId, nodes]);

  // 동적으로 nodeTypes 생성 (기본 노드 + 커스텀 노드)
  const nodeTypes = useMemo(() => {
    const types: NodeTypes = { ...baseNodeTypes };

    // 커스텀 API를 모두 DynamicNode로 등록
    customAPIs.forEach((api) => {
      if (api.enabled) {
        types[api.id] = DynamicNode;
      }
    });

    return types;
  }, [customAPIs]);

  const {
    edges,
    workflowName,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
    clearWorkflow,
    isExecuting,
    executionResult,
    executionError,
    executeWorkflowStream,
    updateNodeData,
    nodeStatuses,
    executionId,
    executionMode,
    setExecutionMode,
  } = useWorkflowStore();

  // Track selected node
  const onSelectionChange = useCallback(
    ({ nodes: selectedNodes }: OnSelectionChangeParams) => {
      if (selectedNodes && Array.isArray(selectedNodes) && selectedNodes.length === 1) {
        setSelectedNodeId(selectedNodes[0]?.id || null);
      } else {
        setSelectedNodeId(null);
      }
    },
    []
  );

  // Download execution result as JSON
  const handleDownloadJSON = useCallback(() => {
    if (!executionResult) return;

    const dataStr = JSON.stringify(executionResult, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `blueprintflow-result-${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [executionResult]);

  // Handle drag and drop
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow-type');
      const label = event.dataTransfer.getData('application/reactflow-label');

      if (!type || !reactFlowInstance) return;

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      // 커스텀 API인지 확인하고 아이콘/색상 정보 추가
      const customAPI = customAPIs.find((api) => api.id === type);

      const newNode = {
        id: getId(),
        type,
        position,
        data: {
          label: label || type,
          description: `${label} node`,
          parameters: {},
          // 커스텀 API인 경우 추가 정보 포함
          ...(customAPI && {
            icon: customAPI.icon,
            color: customAPI.color,
          }),
        },
        selected: false, // ReactFlow requires this property
      };

      addNode(newNode);
    },
    [reactFlowInstance, addNode, customAPIs]
  );

  const onNodeDragStart = useCallback((event: React.DragEvent, nodeType: string, label: string) => {
    event.dataTransfer.setData('application/reactflow-type', nodeType);
    event.dataTransfer.setData('application/reactflow-label', label);
    event.dataTransfer.effectAllowed = 'move';
  }, []);

  // Save workflow
  const handleSave = async () => {
    try {
      const workflow = {
        name: workflowName,
        description: '',
        nodes: nodes.map((n) => ({
          id: n.id,
          type: n.type || '',
          label: n.data.label,
          parameters: n.data.parameters || {},
          position: n.position,
        })),
        edges: edges.map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          sourceHandle: e.sourceHandle || undefined,
          targetHandle: e.targetHandle || undefined,
        })),
      };

      await workflowApi.saveWorkflow(workflow);
      alert('Workflow saved successfully!');
    } catch (error) {
      console.error('Failed to save workflow:', error);
      alert('Failed to save workflow');
    }
  };

  // Image upload handler
  const handleImageUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Check if file is an image
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target?.result as string;
      setUploadedImage(base64, file.name);
    };
    reader.readAsDataURL(file);
  }, [setUploadedImage]);

  // Handle file selection from FileUploadSection (supports both upload and sample selection)
  const handleFileSelect = useCallback((file: File | null) => {
    if (!file) {
      setUploadedImage(null, null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      return;
    }

    // Check if file is an image
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target?.result as string;
      setUploadedImage(base64, file.name);
    };
    reader.readAsDataURL(file);
  }, [setUploadedImage]);

  const handleRemoveImage = useCallback(() => {
    setUploadedImage(null, null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [setUploadedImage]);

  // Delete selected nodes/edges with Delete key
  const onNodesDelete = useCallback(
    (deleted: { id: string }[]) => {
      const deletedIds = deleted.map((n) => n.id);
      console.log('Deleting nodes:', deletedIds);
    },
    []
  );

  const onEdgesDelete = useCallback(
    (deleted: { id: string }[]) => {
      const deletedIds = deleted.map((e) => e.id);
      console.log('Deleting edges:', deletedIds);
    },
    []
  );

  const handleExecute = async () => {
    if (nodes.length === 0) {
      alert('Please add at least one node to the workflow');
      return;
    }

    if (!uploadedImage) {
      alert('Please upload an image first');
      return;
    }

    // Use store's executeWorkflowStream method for real-time updates
    await executeWorkflowStream(uploadedImage);
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Node Palette */}
      <NodePalette
        onNodeDragStart={onNodeDragStart}
        uploadedImage={uploadedImage}
        uploadedFileName={uploadedFileName}
      />

      {/* Main Canvas */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-4">
            <input
              type="text"
              value={workflowName}
              onChange={(e) => useWorkflowStore.setState({ workflowName: e.target.value })}
              className="px-3 py-2 border rounded-md text-lg font-semibold flex-1 max-w-md text-gray-900 dark:text-white bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
              placeholder={t('blueprintflow.workflowName')}
            />

            {/* Image Upload */}
            <div className="flex items-center gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
              <Button
                onClick={() => fileInputRef.current?.click()}
                variant="outline"
                className="flex items-center gap-2"
                title="Upload input image"
              >
                <Upload className="w-4 h-4" />
                {uploadedFileName || 'Upload Image'}
              </Button>

              {/* Sample Selection Dropdown */}
              {!uploadedImage && (
                <div className="relative group">
                  <Button
                    variant="outline"
                    className="flex items-center gap-2"
                    title="Select sample image"
                  >
                    <span>또는 샘플 선택</span>
                    <span className="text-xs">▼</span>
                  </Button>
                  <div className="absolute top-full left-0 mt-1 hidden group-hover:block z-50 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg p-2 min-w-[280px]">
                    {BLUEPRINT_SAMPLES.map((sample) => (
                      <button
                        key={sample.id}
                        onClick={async () => {
                          const response = await fetch(sample.path);
                          const blob = await response.blob();
                          const filename = sample.path.split('/').pop() || 'sample.jpg';
                          const file = new File([blob], filename, { type: 'image/jpeg' });
                          handleFileSelect(file);
                        }}
                        className="w-full text-left px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded flex flex-col gap-1"
                      >
                        <div className="font-medium text-sm flex items-center gap-2">
                          {sample.name}
                          {sample.recommended && (
                            <span className="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-1.5 py-0.5 rounded">
                              추천
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          {sample.description}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {uploadedImage && (
                <Button
                  onClick={handleRemoveImage}
                  variant="outline"
                  size="sm"
                  className="p-2"
                  title="Remove image"
                >
                  <X className="w-4 h-4" />
                </Button>
              )}
            </div>

            <div className="flex gap-2 ml-auto">
              <Button
                onClick={handleSave}
                variant="outline"
                className="flex items-center gap-2"
                title={t('blueprintflow.saveTooltip')}
              >
                <Save className="w-4 h-4" />
                {t('blueprintflow.save')}
              </Button>
              {/* Execution Mode Toggle */}
              <div className="flex items-center gap-1 border rounded-md overflow-hidden">
                <button
                  onClick={() => setExecutionMode('sequential')}
                  className={`px-2 py-1.5 text-xs flex items-center gap-1 transition-colors ${
                    executionMode === 'sequential'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                  }`}
                  title="Sequential execution (one node at a time)"
                >
                  <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="4" y1="12" x2="20" y2="12" />
                    <circle cx="6" cy="12" r="2" fill="currentColor" />
                    <circle cx="12" cy="12" r="2" fill="currentColor" />
                    <circle cx="18" cy="12" r="2" fill="currentColor" />
                  </svg>
                  Sequential
                </button>
                <button
                  onClick={() => setExecutionMode('parallel')}
                  className={`px-2 py-1.5 text-xs flex items-center gap-1 transition-colors ${
                    executionMode === 'parallel'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                  }`}
                  title="Parallel execution (concurrent nodes)"
                >
                  <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="4" y1="6" x2="20" y2="6" />
                    <line x1="4" y1="12" x2="20" y2="12" />
                    <line x1="4" y1="18" x2="20" y2="18" />
                    <circle cx="12" cy="6" r="2" fill="currentColor" />
                    <circle cx="12" cy="12" r="2" fill="currentColor" />
                    <circle cx="12" cy="18" r="2" fill="currentColor" />
                  </svg>
                  Parallel
                </button>
              </div>
              <Button
                onClick={handleExecute}
                disabled={isExecuting || !uploadedImage}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400"
                title={uploadedImage ? t('blueprintflow.executeTooltip') : 'Upload an image first'}
              >
                <Play className="w-4 h-4" />
                {isExecuting ? t('blueprintflow.executing') : t('blueprintflow.execute')}
              </Button>
              <Button
                onClick={clearWorkflow}
                variant="outline"
                className="flex items-center gap-2"
                title={t('blueprintflow.clearTooltip')}
              >
                <Trash2 className="w-4 h-4" />
                {t('blueprintflow.clear')}
              </Button>
              <Button
                onClick={() => setIsDebugPanelOpen(!isDebugPanelOpen)}
                variant={isDebugPanelOpen ? 'default' : 'outline'}
                className="flex items-center gap-2"
                title="Toggle Debug Panel"
              >
                <Bug className="w-4 h-4" />
                Debug
              </Button>
            </div>
          </div>

          {/* Execution Status */}
          {(isExecuting || executionResult || executionError || Object.keys(nodeStatuses).length > 0) && (
            <div className="mt-3 rounded-md bg-gray-100 dark:bg-gray-700">
              {/* Collapse/Expand Header */}
              <div className="flex items-center justify-between p-2 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-t-md">
                <div
                  className="flex items-center gap-2 cursor-pointer flex-1"
                  onClick={() => setIsStatusCollapsed(!isStatusCollapsed)}
                >
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
                    {isStatusCollapsed ? '▶' : '▼'} Execution Status
                    {executionResult?.status && (
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        executionResult.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                        executionResult.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
                        'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                      }`}>
                        {executionResult.status}
                      </span>
                    )}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {/* Re-run Button */}
                  {!isExecuting && executionResult && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleExecute();
                      }}
                      className="text-xs px-2 py-1 h-6"
                      title="Re-run workflow"
                    >
                      <RotateCcw className="w-3 h-3 mr-1" />
                      Re-run
                    </Button>
                  )}
                  <span
                    className="text-xs text-gray-500 cursor-pointer"
                    onClick={() => setIsStatusCollapsed(!isStatusCollapsed)}
                  >
                    {isStatusCollapsed ? 'Expand' : 'Collapse'}
                  </span>
                </div>
              </div>

              {/* Collapsible Content */}
              {!isStatusCollapsed && (
              <div className="p-3 pt-0">
              {executionError && (
                <div className="text-red-600 dark:text-red-400 flex items-center gap-2">
                  <span className="font-semibold">Error:</span>
                  <span>{executionError}</span>
                </div>
              )}

              {/* Real-time Node Status (SSE) */}
              {isExecuting && Object.keys(nodeStatuses).length > 0 && (
                <div className="mb-3">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold text-blue-600 dark:text-blue-400">
                      ⚡ Executing Workflow
                    </span>
                    {executionId && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        (ID: {executionId.slice(0, 8)})
                      </span>
                    )}
                  </div>
                  <div className="text-sm space-y-1">
                    {Object.values(nodeStatuses).map((nodeStatus: NodeStatus) => (
                      <div key={nodeStatus.nodeId} className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${
                          nodeStatus.status === 'completed' ? 'bg-green-500' :
                          nodeStatus.status === 'failed' ? 'bg-red-500' :
                          nodeStatus.status === 'running' ? 'bg-yellow-500 animate-pulse' :
                          'bg-gray-400'
                        }`} />
                        <span className="text-gray-700 dark:text-gray-300 flex-1">
                          {nodeStatus.nodeId}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          nodeStatus.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                          nodeStatus.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
                          nodeStatus.status === 'running' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' :
                          'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                        }`}>
                          {nodeStatus.status}
                        </span>
                        {nodeStatus.progress !== undefined && (
                          <span className="text-xs text-gray-500">
                            {(nodeStatus.progress * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Final Result */}
              {executionResult && !isExecuting && (
                <div className="space-y-3">
                  <div className="text-green-600 dark:text-green-400">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">Status:</span>
                        <span className="px-2 py-1 rounded bg-green-100 dark:bg-green-900 text-xs">
                          {executionResult.status}
                        </span>
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          ({executionResult.execution_time_ms?.toFixed(0) || 0}ms)
                        </span>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleDownloadJSON}
                        className="text-xs"
                      >
                        <Download className="w-3 h-3 mr-1" />
                        JSON
                      </Button>
                    </div>
                    {executionResult.node_statuses && (
                      <div className="text-sm space-y-1">
                        {executionResult.node_statuses.map((nodeStatus: APINodeStatus) => (
                          <div key={nodeStatus.node_id} className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${
                              nodeStatus.status === 'completed' ? 'bg-green-500' :
                              nodeStatus.status === 'failed' ? 'bg-red-500' :
                              nodeStatus.status === 'running' ? 'bg-yellow-500' :
                              'bg-gray-500'
                            }`} />
                            <span className="text-gray-700 dark:text-gray-300">
                              {nodeStatus.node_id}: {nodeStatus.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Result Summary Card */}
                  {executionResult.node_statuses && executionResult.node_statuses.length > 0 && (
                    <ResultSummaryCard
                      results={executionResult.node_statuses.map((nodeStatus: APINodeStatus) => {
                        const workflowNode = nodes.find((n) => n.id === nodeStatus.node_id);
                        return {
                          nodeId: nodeStatus.node_id,
                          nodeType: workflowNode?.type || 'unknown',
                          status: nodeStatus.status === 'completed' ? 'success' :
                                  nodeStatus.status === 'failed' ? 'error' :
                                  nodeStatus.status === 'running' ? 'running' : 'pending',
                          executionTime: nodeStatus.execution_time,
                          output: (nodeStatus.output || executionResult.final_output?.[nodeStatus.node_id]) as Record<string, unknown> | undefined,
                        };
                      })}
                      totalExecutionTime={executionResult.execution_time_ms}
                    />
                  )}

                  {/* Pipeline Conclusion Card - 분석 결론 */}
                  {executionResult.node_statuses && executionResult.node_statuses.length > 0 && (
                    <PipelineConclusionCard
                      executionResult={{
                        status: executionResult.status as string,
                        execution_time_ms: executionResult.execution_time_ms as number | undefined,
                        node_statuses: executionResult.node_statuses?.map((ns: APINodeStatus) => ({
                          node_id: ns.node_id,
                          node_type: nodes.find(n => n.id === ns.node_id)?.type,
                          status: ns.status,
                          output: (ns.output || executionResult.final_output?.[ns.node_id]) as Record<string, unknown> | undefined,
                        })),
                        final_output: executionResult.final_output as Record<string, Record<string, unknown>> | undefined,
                      }}
                      nodes={nodes.map(n => ({
                        id: n.id,
                        type: n.type,
                        data: { label: n.data?.label as string | undefined },
                      }))}
                    />
                  )}

                  {/* Progressive Pipeline Results */}
                  {executionResult.node_statuses && executionResult.node_statuses.length > 0 && (
                    <div className="p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
                      {/* 🔍 DEBUG: executionResult 전체 구조 확인 */}
                      {(() => {
                        console.log('\n🔍 ========== EXECUTION RESULT ==========');
                        console.log('executionResult:', executionResult);
                        console.log('executionResult.node_statuses:', executionResult.node_statuses);
                        console.log('executionResult.final_output:', executionResult.final_output);
                        console.log('node_statuses length:', executionResult.node_statuses?.length);
                        return null;
                      })()}

                      {/* Pipeline Results Header with Execution Pattern Analysis */}
                      {(() => {
                        // Analyze execution pattern: identify parallel groups
                        const nodeStatuses = executionResult.node_statuses || [];

                        // Group nodes by execution time overlap
                        interface ExecutionGroup {
                          type: 'parallel' | 'sequential';
                          nodes: APINodeStatus[];
                          startTime?: string;
                          endTime?: string;
                        }

                        const groups: ExecutionGroup[] = [];
                        const processed = new Set<string>();

                        nodeStatuses.forEach((node: APINodeStatus) => {
                          if (processed.has(node.node_id)) return;

                          // Find all nodes that overlapped with this node's execution
                          const parallelNodes = [node];
                          processed.add(node.node_id);

                          if (node.start_time && node.end_time) {
                            const nodeStart = new Date(node.start_time).getTime();
                            const nodeEnd = new Date(node.end_time).getTime();

                            nodeStatuses.forEach((other: APINodeStatus) => {
                              if (processed.has(other.node_id)) return;
                              if (!other.start_time || !other.end_time) return;

                              const otherStart = new Date(other.start_time).getTime();
                              const otherEnd = new Date(other.end_time).getTime();

                              // Check if time ranges overlap
                              const overlaps = (nodeStart < otherEnd && nodeEnd > otherStart);

                              if (overlaps) {
                                parallelNodes.push(other);
                                processed.add(other.node_id);
                              }
                            });
                          }

                          groups.push({
                            type: parallelNodes.length > 1 ? 'parallel' : 'sequential',
                            nodes: parallelNodes,
                            startTime: node.start_time,
                            endTime: node.end_time,
                          });
                        });

                        const totalNodes = nodeStatuses.length;
                        const parallelGroups = groups.filter(g => g.type === 'parallel').length;
                        const sequentialNodes = groups.filter(g => g.type === 'sequential').length;

                        return (
                          <div className="flex items-center gap-2 mb-3">
                            <span className="font-semibold text-gray-900 dark:text-white">🔄 Pipeline Results</span>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              ({totalNodes} nodes
                              {parallelGroups > 0 && (
                                <span className="ml-1 text-cyan-600 dark:text-cyan-400 font-semibold">
                                  • {parallelGroups} parallel group{parallelGroups > 1 ? 's' : ''}
                                </span>
                              )}
                              {sequentialNodes > 0 && (
                                <span className="ml-1">
                                  • {sequentialNodes} sequential
                                </span>
                              )}
                              )
                            </span>
                          </div>
                        );
                      })()}

                      {/* Grouped execution display */}
                      <div className="space-y-4">
                        {(() => {
                          // Group nodes by parallel execution
                          const nodeStatuses = executionResult.node_statuses || [];

                          interface ExecutionGroup {
                            type: 'parallel' | 'sequential';
                            nodes: APINodeStatus[];
                          }

                          const groups: ExecutionGroup[] = [];
                          const processed = new Set<string>();

                          nodeStatuses.forEach((node: APINodeStatus) => {
                            if (processed.has(node.node_id)) return;

                            const parallelNodes = [node];
                            processed.add(node.node_id);

                            if (node.start_time && node.end_time) {
                              const nodeStart = new Date(node.start_time).getTime();
                              const nodeEnd = new Date(node.end_time).getTime();

                              nodeStatuses.forEach((other: APINodeStatus) => {
                                if (processed.has(other.node_id)) return;
                                if (!other.start_time || !other.end_time) return;

                                const otherStart = new Date(other.start_time).getTime();
                                const otherEnd = new Date(other.end_time).getTime();

                                const overlaps = (nodeStart < otherEnd && nodeEnd > otherStart);

                                if (overlaps) {
                                  parallelNodes.push(other);
                                  processed.add(other.node_id);
                                }
                              });
                            }

                            groups.push({
                              type: parallelNodes.length > 1 ? 'parallel' : 'sequential',
                              nodes: parallelNodes,
                            });
                          });

                          let globalIndex = 0;

                          return groups.map((group, groupIndex) => (
                            <div key={groupIndex}>
                              {/* Parallel Group Indicator */}
                              {group.type === 'parallel' && (
                                <div className="mb-2 flex items-center gap-2 px-3 py-1.5 bg-cyan-50 dark:bg-cyan-900/30 border-l-4 border-cyan-500 rounded">
                                  <span className="text-xs font-semibold text-cyan-700 dark:text-cyan-300">
                                    ⚡ Parallel Execution ({group.nodes.length} nodes running simultaneously)
                                  </span>
                                </div>
                              )}

                              {/* Nodes in this group */}
                              <div className={group.type === 'parallel' ? 'ml-4 space-y-3' : 'space-y-3'}>
                                {group.nodes.map((nodeStatus: APINodeStatus) => {
                                  const currentIndex = globalIndex++;
                                  const workflowNode = nodes.find((n) => n.id === nodeStatus.node_id);
                                  const nodeLabel = workflowNode?.data?.label || nodeStatus.node_id;
                                  const nodeType = workflowNode?.type || 'unknown';
                                  const output = (nodeStatus.output || executionResult.final_output?.[nodeStatus.node_id]) as PipelineOutput | undefined;

                                  // Debug logging
                                  console.log(`\n🔍 [Node ${currentIndex}] ${nodeLabel} (${nodeStatus.node_id})`);
                                  console.log('  nodeStatus:', nodeStatus);
                                  console.log('  output variable:', output);
                                  console.log('  output?.image:', output?.image ? `[${output.image.length} chars]` : 'undefined');
                                  console.log('  output?.visualized_image:', output?.visualized_image ? `[${output.visualized_image.length} chars]` : 'undefined');

                                  return (
                                    <div key={nodeStatus.node_id} className="relative">
                                      <div className="flex items-start gap-3">
                                        {/* Step Number */}
                                        <div className={`flex-shrink-0 w-8 h-8 text-white rounded-full flex items-center justify-center font-bold text-sm ${
                                          group.type === 'parallel' ? 'bg-cyan-500' : 'bg-cyan-600'
                                        }`}>
                                          {currentIndex + 1}
                                        </div>

                                        {/* Node Info & Results */}
                                        <div className="flex-1 bg-gray-50 dark:bg-gray-700 rounded-lg p-3 border border-gray-200 dark:border-gray-600">
                                          {/* Node Header */}
                                          <div className="flex items-center justify-between mb-2">
                                            <div>
                                              <div className="font-medium text-sm text-gray-900 dark:text-white">
                                                {nodeLabel}
                                              </div>
                                              <div className="text-xs text-gray-500 dark:text-gray-400">
                                                {nodeType} • {nodeStatus.node_id}
                                              </div>
                                              {/* Node Description */}
                                              {nodeDefinitions[nodeType as keyof typeof nodeDefinitions]?.description && (
                                                <div className="text-xs text-blue-600 dark:text-blue-400 mt-1 italic">
                                                  💡 {nodeDefinitions[nodeType as keyof typeof nodeDefinitions].description}
                                                </div>
                                              )}
                                            </div>
                                            <div className={`px-2 py-1 rounded text-xs font-semibold ${
                                              nodeStatus.status === 'completed'
                                                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                                : nodeStatus.status === 'failed'
                                                ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                                : 'bg-gray-100 text-gray-800 dark:bg-gray-600 dark:text-gray-200'
                                            }`}>
                                              {nodeStatus.status}
                                            </div>
                                          </div>

                                          {/* Parameters Used */}
                                          {workflowNode?.data?.parameters && Object.keys(workflowNode.data.parameters).length > 0 && (
                                            <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-600">
                                              <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                                                ⚙️ Parameters:
                                              </div>
                                              <div className="text-xs text-gray-600 dark:text-gray-400 space-y-0.5">
                                                {Object.entries(workflowNode.data.parameters).map(([key, value]) => (
                                                  <div key={key} className="flex gap-1">
                                                    <span className="font-mono text-blue-600 dark:text-blue-400">{key}:</span>
                                                    <span className="font-mono">{String(value)}</span>
                                                  </div>
                                                ))}
                                              </div>
                                            </div>
                                          )}

                                          {/* Output Image - support both 'image' and 'visualized_image' */}
                                          {(output?.image || output?.visualized_image) && (
                                            <div className="mt-3">
                                              <div className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                                                📸 Output Image:
                                              </div>
                                              <img
                                                src={(() => {
                                                  const imgData = output.image || output.visualized_image || '';
                                                  return imgData.startsWith('data:') ? imgData : `data:image/jpeg;base64,${imgData}`;
                                                })()}
                                                alt={`${nodeLabel} result`}
                                                className="w-full h-auto rounded border border-gray-300 dark:border-gray-600 shadow-sm cursor-pointer hover:shadow-lg transition-shadow"
                                                onClick={(e) => {
                                                  // 이미지 클릭 시 새 창에서 크게 보기
                                                  const img = e.currentTarget;
                                                  const win = window.open('', '_blank');
                                                  if (win) {
                                                    win.document.write(`<img src="${img.src}" style="max-width:100%; height:auto;" />`);
                                                  }
                                                }}
                                                title="클릭하여 크게 보기"
                                              />
                                            </div>
                                          )}

                                          {/* Detections (YOLO) */}
                                          {output?.detections && Array.isArray(output.detections) && (
                                            <div className="mt-2 p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
                                              <div className="text-xs font-semibold text-blue-900 dark:text-blue-100">
                                                🎯 Detections: {output.detections.length} objects
                                              </div>
                                              <div className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                                                {output.detections.slice(0, 3).map((det: Detection, i: number) => (
                                                  <div key={i}>
                                                    • {det.class_name || det.class || 'Unknown'} ({(det.confidence * 100).toFixed(1)}%)
                                                  </div>
                                                ))}
                                                {output.detections.length > 3 && (
                                                  <div className="text-blue-500 dark:text-blue-400">
                                                    ... and {output.detections.length - 3} more
                                                  </div>
                                                )}
                                              </div>
                                            </div>
                                          )}

                                          {/* eDOCr2 Dimensions */}
                                          {output?.dimensions && Array.isArray(output.dimensions) && (
                                            <div className="mt-2 p-2 bg-indigo-50 dark:bg-indigo-900/20 rounded border border-indigo-200 dark:border-indigo-800">
                                              <div className="text-xs font-semibold text-indigo-900 dark:text-indigo-100">
                                                📏 Dimensions: {output.dimensions.length}
                                                {(output.gdt?.length ?? 0) > 0 && ` | GD&T: ${output.gdt?.length}`}
                                              </div>
                                              <div className="text-xs text-indigo-700 dark:text-indigo-300 mt-1">
                                                {output.dimensions.slice(0, 5).map((dim: DimensionResult, i: number) => (
                                                  <div key={i}>
                                                    • {dim.type && `[${dim.type}] `}{dim.value || dim.text || JSON.stringify(dim).slice(0, 50)}{dim.unit || ''}{dim.tolerance ? ` ±${dim.tolerance}` : ''}
                                                  </div>
                                                ))}
                                                {output.dimensions.length > 5 && (
                                                  <div className="text-indigo-500 dark:text-indigo-400">
                                                    ... and {output.dimensions.length - 5} more
                                                  </div>
                                                )}
                                              </div>
                                            </div>
                                          )}

                                          {/* OCR Visualization (eDOCr2) */}
                                          {(nodeType === 'edocr2' || nodeType.includes('ocr')) &&
                                           (output?.dimensions || output?.gdt) &&
                                           uploadedImage && (
                                            <div className="mt-3">
                                              <OCRVisualization
                                                imageBase64={uploadedImage}
                                                ocrResult={{
                                                  dimensions: (output.dimensions || []) as { type: string; value: number; unit: string; tolerance: string | number | null }[],
                                                  gdt: (output.gdt || []) as { type: string; value: number; datum: string | null }[],
                                                  text: (typeof output.text === 'object' ? output.text : { total_blocks: 0 }) as { total_blocks?: number },
                                                }}
                                                compact={true}
                                              />
                                            </div>
                                          )}

                                          {/* OCR Text Results (eDOCr2, PaddleOCR) */}
                                          {output?.text && typeof output.text === 'string' && (
                                            <div className="mt-2 p-2 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
                                              <div className="text-xs font-semibold text-purple-900 dark:text-purple-100">
                                                📝 Extracted Text:
                                              </div>
                                              <div className="text-xs text-purple-700 dark:text-purple-300 mt-1 whitespace-pre-wrap">
                                                {output.text.slice(0, 200)}
                                                {output.text.length > 200 && '...'}
                                              </div>
                                            </div>
                                          )}

                                          {/* PaddleOCR Text Results */}
                                          {output?.text_results && Array.isArray(output.text_results) && (
                                            <div className="mt-2 p-2 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
                                              <div className="text-xs font-semibold text-purple-900 dark:text-purple-100">
                                                📝 OCR Text Results: {output.text_results.length}
                                              </div>
                                              <div className="text-xs text-purple-700 dark:text-purple-300 mt-1">
                                                {output.text_results.slice(0, 5).map((textResult: TextResult, i: number) => (
                                                  <div key={i}>
                                                    • {textResult.text || textResult.content || JSON.stringify(textResult).slice(0, 50)}
                                                  </div>
                                                ))}
                                                {output.text_results.length > 5 && (
                                                  <div className="text-purple-500 dark:text-purple-400">
                                                    ... and {output.text_results.length - 5} more
                                                  </div>
                                                )}
                                              </div>
                                            </div>
                                          )}

                                          {/* OCR Blocks (Structured OCR) */}
                                          {output?.blocks && Array.isArray(output.blocks) && (
                                            <div className="mt-2 p-2 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800">
                                              <div className="text-xs font-semibold text-purple-900 dark:text-purple-100">
                                                📝 OCR Blocks: {output.blocks.length}
                                              </div>
                                              <div className="text-xs text-purple-700 dark:text-purple-300 mt-1">
                                                {output.blocks.slice(0, 3).map((block: OCRBlock, i: number) => (
                                                  <div key={i}>• {block.text || JSON.stringify(block).slice(0, 50)}</div>
                                                ))}
                                                {output.blocks.length > 3 && (
                                                  <div className="text-purple-500 dark:text-purple-400">
                                                    ... and {output.blocks.length - 3} more
                                                  </div>
                                                )}
                                              </div>
                                            </div>
                                          )}

                                          {/* Segmentation Results (EDGNet) */}
                                          {output?.segments && Array.isArray(output.segments) && (
                                            <div className="mt-2 p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
                                              <div className="text-xs font-semibold text-green-900 dark:text-green-100">
                                                🎨 Segmentation: {output.segments.length} segments
                                              </div>
                                              <div className="text-xs text-green-700 dark:text-green-300 mt-1">
                                                {output.segments.slice(0, 3).map((seg: SegmentResult, i: number) => (
                                                  <div key={i}>
                                                    • {seg.class || seg.type || `Segment ${i + 1}`}
                                                    {seg.confidence && ` (${(seg.confidence * 100).toFixed(1)}%)`}
                                                  </div>
                                                ))}
                                                {output.segments.length > 3 && (
                                                  <div className="text-green-500 dark:text-green-400">
                                                    ... and {output.segments.length - 3} more
                                                  </div>
                                                )}
                                              </div>
                                            </div>
                                          )}
                                          {output?.mask && (
                                            <div className="mt-2 p-2 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
                                              <div className="text-xs font-semibold text-green-900 dark:text-green-100">
                                                🎨 Segmentation Mask Available
                                              </div>
                                            </div>
                                          )}

                                          {/* Segmentation Visualization (EDGNet) */}
                                          {nodeType === 'edgnet' &&
                                           (output?.num_components !== undefined || output?.classifications) && (
                                            <div className="mt-3">
                                              <SegmentationVisualization
                                                imageBase64={uploadedImage || undefined}
                                                segmentationResult={{
                                                  num_components: output.num_components || 0,
                                                  classifications: output.classifications || { contour: 0, text: 0, dimension: 0 },
                                                  graph: output.graph || { nodes: 0, edges: 0, avg_degree: 0 },
                                                  vectorization: output.vectorization || { num_bezier_curves: 0, total_length: 0 },
                                                }}
                                                compact={true}
                                              />
                                            </div>
                                          )}

                                          {/* Tolerance Analysis (SkinModel) */}
                                          {output?.tolerances && Array.isArray(output.tolerances) && (
                                            <div className="mt-2 p-2 bg-orange-50 dark:bg-orange-900/20 rounded border border-orange-200 dark:border-orange-800">
                                              <div className="text-xs font-semibold text-orange-900 dark:text-orange-100">
                                                📐 Tolerance Analysis: {output.tolerances.length} items
                                              </div>
                                              <div className="text-xs text-orange-700 dark:text-orange-300 mt-1">
                                                {output.tolerances.slice(0, 5).map((tol: ToleranceItem, i: number) => (
                                                  <div key={i}>
                                                    • {tol.dimension || tol.name || `Tolerance ${i + 1}`}
                                                    {tol.value && `: ${tol.value}`}
                                                  </div>
                                                ))}
                                                {output.tolerances.length > 5 && (
                                                  <div className="text-orange-500 dark:text-orange-400">
                                                    ... and {output.tolerances.length - 5} more
                                                  </div>
                                                )}
                                              </div>
                                            </div>
                                          )}
                                          {output?.analysis && typeof output.analysis === 'object' && (
                                            <div className="mt-2 p-2 bg-orange-50 dark:bg-orange-900/20 rounded border border-orange-200 dark:border-orange-800">
                                              <div className="text-xs font-semibold text-orange-900 dark:text-orange-100">
                                                📐 Analysis Details:
                                              </div>
                                              <div className="text-xs text-orange-700 dark:text-orange-300 mt-1">
                                                {Object.entries(output.analysis).slice(0, 5).map(([key, value]: [string, unknown]) => (
                                                  <div key={key}>• {key}: {String(value).slice(0, 50)}</div>
                                                ))}
                                              </div>
                                            </div>
                                          )}

                                          {/* Tolerance Visualization (SkinModel) */}
                                          {nodeType === 'skinmodel' && output &&
                                           (output.manufacturability || output.predicted_tolerances) && (
                                            <div className="mt-3">
                                              <ToleranceVisualization
                                                toleranceData={{
                                                  manufacturability: output.manufacturability,
                                                  predicted_tolerances: output.predicted_tolerances,
                                                  analysis: output.analysis,
                                                }}
                                                compact={true}
                                              />
                                            </div>
                                          )}

                                          {/* Vision-Language Results (VL) */}
                                          {output?.result && typeof output.result === 'string' && (
                                            <div className="mt-2 p-2 bg-pink-50 dark:bg-pink-900/20 rounded border border-pink-200 dark:border-pink-800">
                                              <div className="text-xs font-semibold text-pink-900 dark:text-pink-100">
                                                🤖 VL Result:
                                              </div>
                                              <div className="text-xs text-pink-700 dark:text-pink-300 mt-1 whitespace-pre-wrap">
                                                {output.result.slice(0, 300)}
                                                {output.result.length > 300 && '...'}
                                              </div>
                                            </div>
                                          )}
                                          {output?.description && typeof output.description === 'string' && (
                                            <div className="mt-2 p-2 bg-pink-50 dark:bg-pink-900/20 rounded border border-pink-200 dark:border-pink-800">
                                              <div className="text-xs font-semibold text-pink-900 dark:text-pink-100">
                                                🤖 AI Description:
                                              </div>
                                              <div className="text-xs text-pink-700 dark:text-pink-300 mt-1 whitespace-pre-wrap">
                                                {output.description.slice(0, 300)}
                                                {output.description.length > 300 && '...'}
                                              </div>
                                            </div>
                                          )}

                                          {/* Raw Data Viewer */}
                                          {output && Object.keys(output).length > 0 && (
                                            <details className="mt-2">
                                              <summary className="text-xs font-medium text-gray-600 dark:text-gray-400 cursor-pointer hover:text-gray-900 dark:hover:text-gray-200">
                                                🔍 View Raw Data ({Object.keys(output).length} fields)
                                              </summary>
                                              <pre className="mt-2 p-2 bg-white dark:bg-gray-900 rounded text-xs overflow-auto max-h-60 border border-gray-200 dark:border-gray-700">
                                                {JSON.stringify(output, null, 2)}
                                              </pre>
                                            </details>
                                          )}

                                          {/* Error Display */}
                                          {nodeStatus.error && (
                                            <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded border border-red-200 dark:border-red-800">
                                              <div className="text-xs font-semibold text-red-900 dark:text-red-100">
                                                ❌ Error:
                                              </div>
                                              <div className="text-xs text-red-700 dark:text-red-300 mt-1">
                                                {nodeStatus.error}
                                              </div>
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>

                              {/* Group separator arrow */}
                              {groupIndex < groups.length - 1 && (
                                <div className="flex justify-center py-2 my-2">
                                  <div className="w-0.5 h-6 bg-gradient-to-b from-cyan-400 to-cyan-600"></div>
                                  <div className="absolute mt-5 text-cyan-600">
                                    ▼
                                  </div>
                                </div>
                              )}
                            </div>
                          ));
                        })()}
                      </div>
                    </div>
                  )}
                </div>
              )}
              </div>
              )}
            </div>
          )}
        </div>

        {/* ReactFlow Canvas */}
        <div ref={reactFlowWrapper} className="flex-1">
          <ReactFlow
            nodes={nodes.filter((n) => n && n.id)}
            edges={edges.filter((e) => e && e.id)}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodesDelete={onNodesDelete}
            onEdgesDelete={onEdgesDelete}
            onSelectionChange={onSelectionChange}
            onInit={setReactFlowInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            nodeTypes={nodeTypes}
            fitView
            deleteKeyCode="Delete"
            className="bg-gray-50 dark:bg-gray-900"
          >
            <Background />
            <Controls position="bottom-left" />
            <MiniMap
              position="top-right"
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
              maskColor="rgba(0, 0, 0, 0.1)"
              nodeColor={(node) => {
                switch (node.type) {
                  case 'imageinput': return '#22c55e';
                  case 'yolo': return '#3b82f6';
                  case 'edocr2': return '#8b5cf6';
                  case 'skinmodel': return '#f59e0b';
                  default: return '#6b7280';
                }
              }}
              pannable
              zoomable
            />
          </ReactFlow>
        </div>
      </div>

      {/* Node Detail Panel */}
      <NodeDetailPanel
        selectedNode={selectedNode}
        onClose={() => setSelectedNodeId(null)}
        onUpdateNode={updateNodeData}
      />

      {/* Debug Panel */}
      <DebugPanel
        isOpen={isDebugPanelOpen}
        onToggle={() => setIsDebugPanelOpen(!isDebugPanelOpen)}
        executionResult={executionResult as Record<string, unknown> | null}
        executionError={executionError}
      />
    </div>
  );
}

export default function WorkflowBuilderNew() {
  return (
    <ReactFlowProvider>
      <WorkflowBuilderCanvas />
    </ReactFlowProvider>
  );
}
