import { useCallback, useRef, useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
} from 'reactflow';
import type { ReactFlowInstance } from 'reactflow';
import 'reactflow/dist/style.css';

import { useWorkflowStore } from '../../store/workflowStore';
import { useAPIConfigStore } from '../../store/apiConfigStore';
import NodePalette from '../../components/blueprintflow/NodePalette';
import NodeDetailPanel from '../../components/blueprintflow/NodeDetailPanel';
import {
  ImageInputNode,
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
import { Play, Save, Trash2, Upload, X } from 'lucide-react';
import { workflowApi } from '../../lib/api';
import type { SampleFile } from '../../components/upload/SampleFileGrid';

// Base node type mapping
const baseNodeTypes = {
  imageinput: ImageInputNode,
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
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);

  // 동적으로 nodeTypes 생성 (기본 노드 + 커스텀 노드)
  const nodeTypes = useMemo(() => {
    const types: Record<string, any> = { ...baseNodeTypes };

    // 커스텀 API를 모두 DynamicNode로 등록
    customAPIs.forEach((api) => {
      if (api.enabled) {
        types[api.id] = DynamicNode;
      }
    });

    return types;
  }, [customAPIs]);

  const {
    nodes,
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
  } = useWorkflowStore();

  // Track selected node
  const onSelectionChange = useCallback(
    ({ nodes: selectedNodes }: any) => {
      if (selectedNodes && Array.isArray(selectedNodes) && selectedNodes.length === 1) {
        setSelectedNode(selectedNodes[0]);
      } else {
        setSelectedNode(null);
      }
    },
    []
  );

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
      setUploadedImage(base64);
      setUploadedFileName(file.name);
    };
    reader.readAsDataURL(file);
  }, []);

  // Handle file selection from FileUploadSection (supports both upload and sample selection)
  const handleFileSelect = useCallback((file: File | null) => {
    if (!file) {
      setUploadedImage(null);
      setUploadedFileName(null);
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
      setUploadedImage(base64);
      setUploadedFileName(file.name);
    };
    reader.readAsDataURL(file);
  }, []);

  const handleRemoveImage = useCallback(() => {
    setUploadedImage(null);
    setUploadedFileName(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  // Delete selected nodes/edges with Delete key
  const onNodesDelete = useCallback(
    (deleted: any[]) => {
      const deletedIds = deleted.map((n) => n.id);
      console.log('Deleting nodes:', deletedIds);
    },
    []
  );

  const onEdgesDelete = useCallback(
    (deleted: any[]) => {
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
            </div>
          </div>

          {/* Execution Status */}
          {(isExecuting || executionResult || executionError || Object.keys(nodeStatuses).length > 0) && (
            <div className="mt-3 p-3 rounded-md bg-gray-100 dark:bg-gray-700">
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
                    {Object.values(nodeStatuses).map((nodeStatus: any) => (
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
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-semibold">Status:</span>
                      <span className="px-2 py-1 rounded bg-green-100 dark:bg-green-900 text-xs">
                        {executionResult.status}
                      </span>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        ({executionResult.execution_time_ms?.toFixed(0) || 0}ms)
                      </span>
                    </div>
                    {executionResult.node_statuses && (
                      <div className="text-sm space-y-1">
                        {executionResult.node_statuses.map((nodeStatus: any) => (
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
                          nodes: any[];
                          startTime?: string;
                          endTime?: string;
                        }

                        const groups: ExecutionGroup[] = [];
                        const processed = new Set<string>();

                        nodeStatuses.forEach((node: any) => {
                          if (processed.has(node.node_id)) return;

                          // Find all nodes that overlapped with this node's execution
                          const parallelNodes = [node];
                          processed.add(node.node_id);

                          if (node.start_time && node.end_time) {
                            const nodeStart = new Date(node.start_time).getTime();
                            const nodeEnd = new Date(node.end_time).getTime();

                            nodeStatuses.forEach((other: any) => {
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
                            nodes: any[];
                          }

                          const groups: ExecutionGroup[] = [];
                          const processed = new Set<string>();

                          nodeStatuses.forEach((node: any) => {
                            if (processed.has(node.node_id)) return;

                            const parallelNodes = [node];
                            processed.add(node.node_id);

                            if (node.start_time && node.end_time) {
                              const nodeStart = new Date(node.start_time).getTime();
                              const nodeEnd = new Date(node.end_time).getTime();

                              nodeStatuses.forEach((other: any) => {
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
                                {group.nodes.map((nodeStatus: any) => {
                                  const currentIndex = globalIndex++;
                                  const workflowNode = nodes.find((n) => n.id === nodeStatus.node_id);
                                  const nodeLabel = workflowNode?.data?.label || nodeStatus.node_id;
                                  const nodeType = workflowNode?.type || 'unknown';
                                  const output = nodeStatus.output || executionResult.final_output?.[nodeStatus.node_id];

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
                                                src={(output.image || output.visualized_image).startsWith('data:')
                                                  ? (output.image || output.visualized_image)
                                                  : `data:image/jpeg;base64,${output.image || output.visualized_image}`}
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
                                                {output.detections.slice(0, 3).map((det: any, i: number) => (
                                                  <div key={i}>
                                                    • {det.class || 'Unknown'} ({(det.confidence * 100).toFixed(1)}%)
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
                                              </div>
                                              <div className="text-xs text-indigo-700 dark:text-indigo-300 mt-1">
                                                {output.dimensions.slice(0, 5).map((dim: any, i: number) => (
                                                  <div key={i}>
                                                    • {dim.value || dim.text || JSON.stringify(dim).slice(0, 50)}
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
                                                {output.text_results.slice(0, 5).map((textResult: any, i: number) => (
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
                                                {output.blocks.slice(0, 3).map((block: any, i: number) => (
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
                                                {output.segments.slice(0, 3).map((seg: any, i: number) => (
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

                                          {/* Tolerance Analysis (SkinModel) */}
                                          {output?.tolerances && Array.isArray(output.tolerances) && (
                                            <div className="mt-2 p-2 bg-orange-50 dark:bg-orange-900/20 rounded border border-orange-200 dark:border-orange-800">
                                              <div className="text-xs font-semibold text-orange-900 dark:text-orange-100">
                                                📐 Tolerance Analysis: {output.tolerances.length} items
                                              </div>
                                              <div className="text-xs text-orange-700 dark:text-orange-300 mt-1">
                                                {output.tolerances.slice(0, 5).map((tol: any, i: number) => (
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
                                                {Object.entries(output.analysis).slice(0, 5).map(([key, value]: [string, any]) => (
                                                  <div key={key}>• {key}: {String(value).slice(0, 50)}</div>
                                                ))}
                                              </div>
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
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>
      </div>

      {/* Node Detail Panel */}
      <NodeDetailPanel
        selectedNode={selectedNode}
        onClose={() => setSelectedNode(null)}
        onUpdateNode={updateNodeData}
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
