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
import { Play, Save, Trash2 } from 'lucide-react';
import { workflowApi, type WorkflowExecutionRequest } from '../../lib/api';

// Base node type mapping
const baseNodeTypes = {
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
  const { customAPIs } = useAPIConfigStore();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);

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
    setExecuting,
    setExecutionResult,
    setExecutionError,
    updateNodeData,
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

  // Execute workflow
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
      alert('Please add at least one node');
      return;
    }

    setExecuting(true);
    setExecutionError(null);

    try {
      const request: WorkflowExecutionRequest = {
        workflow: {
          name: workflowName,
          description: '',
          nodes: nodes.map((n) => ({
            id: n.id,
            type: n.type || '',
            label: n.data.label,
            parameters: n.data.parameters || {},
          })),
          edges: edges.map((e) => ({
            id: e.id,
            source: e.source,
            target: e.target,
          })),
        },
        inputs: {
          // TODO: Get image from file input
          image: '',
        },
      };

      const result = await workflowApi.execute(request);
      setExecutionResult(result);
      alert(`Execution completed! Status: ${result.status}`);
    } catch (error: any) {
      console.error('Failed to execute workflow:', error);
      setExecutionError(error.message || 'Failed to execute workflow');
      alert('Failed to execute workflow: ' + (error.message || 'Unknown error'));
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Node Palette */}
      <NodePalette onNodeDragStart={onNodeDragStart} />

      {/* Main Canvas */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 flex items-center gap-4">
          <input
            type="text"
            value={workflowName}
            onChange={(e) => useWorkflowStore.setState({ workflowName: e.target.value })}
            className="px-3 py-2 border rounded-md text-lg font-semibold flex-1 max-w-md text-gray-900 dark:text-white bg-white dark:bg-gray-700"
            placeholder={t('blueprintflow.workflowName')}
          />
          <div className="flex gap-2 ml-auto">
            <Button
              onClick={handleSave}
              className="flex items-center gap-2"
              title={t('blueprintflow.saveTooltip')}
            >
              <Save className="w-4 h-4" />
              {t('blueprintflow.save')}
            </Button>
            <Button
              onClick={handleExecute}
              disabled={isExecuting}
              className="flex items-center gap-2 bg-green-600 hover:bg-green-700"
              title={t('blueprintflow.executeTooltip')}
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
