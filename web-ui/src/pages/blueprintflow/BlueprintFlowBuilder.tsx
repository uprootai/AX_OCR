import { useCallback, useRef, useState, useMemo, useEffect } from 'react';
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
import { workflowApi, type WorkflowExecutionRequest } from '../../lib/api';

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
      <NodePalette onNodeDragStart={onNodeDragStart} />

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
