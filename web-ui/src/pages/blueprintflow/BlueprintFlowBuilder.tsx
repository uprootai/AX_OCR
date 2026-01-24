/**
 * BlueprintFlow Workflow Builder
 * 워크플로우 빌더 메인 컴포넌트
 */

import { useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
} from 'reactflow';
import type { ReactFlowInstance, OnSelectionChangeParams, NodeTypes, Connection } from 'reactflow';
import 'reactflow/dist/style.css';

import { useWorkflowStore } from '../../store/workflowStore';
import { useAPIConfigStore } from '../../store/apiConfigStore';
import NodePalette from '../../components/blueprintflow/NodePalette';
import NodeDetailPanel from '../../components/blueprintflow/NodeDetailPanel';
import DynamicNode from '../../components/blueprintflow/nodes/DynamicNode';
import { Button } from '../../components/ui/Button';
import Toast from '../../components/ui/Toast';
import { Play, Save, Trash2, Upload, X, Bug, Loader2, StopCircle, FolderOpen, FileDown } from 'lucide-react';
import { workflowApi, type TemplateDetail } from '../../lib/api';
import DebugPanel from '../../components/blueprintflow/DebugPanel';

// Toast 알림 타입
interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

// Local imports
import { baseNodeTypes, getId, BLUEPRINT_SAMPLES, getNodeColor } from './constants';
import { useContainerStatus, useImageUpload } from './hooks';
import { ContainerWarningModal, ExecutionStatusPanel, SaveTemplateModal, LoadTemplateModal } from './components';

function WorkflowBuilderCanvas() {
  const { t } = useTranslation();
  const customAPIs = useAPIConfigStore((state) => state.customAPIs);

  // Image upload hook
  const {
    fileInputRef,
    uploadedImage,
    uploadedFileName,
    handleImageUpload,
    handleRemoveImage,
    triggerFileInput,
    loadSampleImage,
  } = useImageUpload({
    onShowToast: (message, type) => setToast({ show: true, message, type }),
  });

  // Workflow store
  const nodes = useWorkflowStore((state) => state.nodes);
  const {
    edges,
    workflowName,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addNode,
    clearWorkflow,
    loadWorkflow,
    isExecuting,
    executionResult,
    executionError,
    executeWorkflowStream,
    updateNodeData,
    nodeStatuses,
    executionId,
    executionMode,
    setExecutionMode,
    cancelExecution,
  } = useWorkflowStore();

  // Container status hook
  const {
    isCheckingContainers,
    containerWarningModal,
    executeWithContainerCheck,
    startContainers,
    closeWarningModal,
  } = useContainerStatus({
    onExecute: () => executeWorkflowStream(uploadedImage!),
    onShowToast: (message, type) => setToast({ show: true, message, type }),
  });

  // ReactFlow instance
  const [reactFlowInstance, setReactFlowInstance] = React.useState<ReactFlowInstance | null>(null);
  const [selectedNodeId, setSelectedNodeId] = React.useState<string | null>(null);
  const [isDebugPanelOpen, setIsDebugPanelOpen] = React.useState(false);

  // Template modal state
  const [isSaveTemplateModalOpen, setIsSaveTemplateModalOpen] = React.useState(false);
  const [isLoadTemplateModalOpen, setIsLoadTemplateModalOpen] = React.useState(false);

  // Toast 알림 상태
  const [toast, setToast] = React.useState<ToastState>({ show: false, message: '', type: 'info' });

  // Toast 표시 헬퍼 함수
  const showToast = useCallback((message: string, type: ToastState['type'] = 'info') => {
    setToast({ show: true, message, type });
  }, []);

  // Selected node from nodes array
  const selectedNode = useMemo(() => {
    if (!selectedNodeId) return null;
    return nodes.find((n) => n.id === selectedNodeId) || null;
  }, [selectedNodeId, nodes]);

  // Dynamic nodeTypes (base + custom APIs)
  const nodeTypes = useMemo(() => {
    const types: NodeTypes = { ...baseNodeTypes };
    customAPIs.forEach((api) => {
      if (api.enabled) {
        types[api.id] = DynamicNode;
      }
    });
    return types;
  }, [customAPIs]);

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

  // Validate connection
  const isValidConnection = useCallback((connection: Connection) => {
    if (connection.source === connection.target) {
      showToast('자기 자신으로의 연결은 허용되지 않습니다', 'warning');
      return false;
    }
    return true;
  }, [showToast]);

  // Handle connect
  const handleConnect = useCallback((connection: Connection) => {
    onConnect(connection);
  }, [onConnect]);

  // Download result as JSON
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

  // Drag and drop handlers
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

      const customAPI = customAPIs.find((api) => api.id === type);
      const newNode = {
        id: getId(),
        type,
        position,
        data: {
          label: label || type,
          description: `${label} node`,
          parameters: {},
          ...(customAPI && {
            icon: customAPI.icon,
            color: customAPI.color,
          }),
        },
        selected: false,
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

  // 추천 노드 추가 콜백 (NodeDetailPanel에서 사용)
  const handleAddRecommendedNode = useCallback(
    (nodeType: string) => {
      if (!reactFlowInstance) return;

      // 선택된 노드 위치를 기준으로 오른쪽에 배치
      const selectedNode = nodes.find(n => n.id === selectedNodeId);
      const basePosition = selectedNode?.position || { x: 300, y: 200 };

      // 기존 노드들과 겹치지 않도록 위치 조정
      const existingNodePositions = nodes.map(n => n.position);
      const offsetX = 250;
      let offsetY = 0;

      // 이미 해당 위치에 노드가 있으면 아래로 이동
      while (existingNodePositions.some(p =>
        Math.abs(p.x - (basePosition.x + offsetX)) < 100 &&
        Math.abs(p.y - (basePosition.y + offsetY)) < 80
      )) {
        offsetY += 100;
      }

      const position = {
        x: basePosition.x + offsetX,
        y: basePosition.y + offsetY,
      };

      const customAPI = customAPIs.find((api) => api.id === nodeType);
      const newNode = {
        id: getId(),
        type: nodeType,
        position,
        data: {
          label: customAPI?.displayName || nodeType,
          description: `${nodeType} node`,
          parameters: {},
          ...(customAPI && {
            icon: customAPI.icon,
            color: customAPI.color,
          }),
        },
        selected: false,
      };
      addNode(newNode);
    },
    [reactFlowInstance, nodes, selectedNodeId, customAPIs, addNode]
  );

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
      showToast('✓ 워크플로우가 저장되었습니다', 'success');
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : '알 수 없는 오류';
      showToast(`✗ 워크플로우 저장 실패\n${errorMsg}`, 'error');
    }
  };

  // Load template into workflow
  const handleLoadTemplate = useCallback((template: TemplateDetail) => {
    loadWorkflow({
      name: template.name,
      description: template.description,
      nodes: template.nodes.map((n) => ({
        id: n.id,
        type: n.type,
        label: n.label,
        position: n.position,
        parameters: n.parameters,
      })),
      edges: template.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle,
      })),
    });
    showToast(`✓ 템플릿 '${template.name}' 불러오기 완료`, 'success');
  }, [loadWorkflow, showToast]);

  // Handle template save success
  const handleTemplateSaveSuccess = useCallback((templateId: string) => {
    showToast(`✓ 템플릿 저장 완료 (ID: ${templateId.slice(0, 8)}...)`, 'success');
  }, [showToast]);

  // Execute workflow
  const handleExecute = () => {
    executeWithContainerCheck(nodes, uploadedImage);
  };

  // Delete handlers
  const onNodesDelete = useCallback((deleted: { id: string }[]) => {
    console.log('Deleting nodes:', deleted.map((n) => n.id));
  }, []);

  const onEdgesDelete = useCallback((deleted: { id: string }[]) => {
    console.log('Deleting edges:', deleted.map((e) => e.id));
  }, []);

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
            {/* Workflow Name */}
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
                onClick={triggerFileInput}
                variant="outline"
                className="flex items-center gap-2"
                title="Upload input image"
              >
                <Upload className="w-4 h-4" />
                {uploadedFileName || 'Upload Image'}
              </Button>

              {/* Sample Selection */}
              {!uploadedImage && (
                <div className="relative group">
                  <Button variant="outline" className="flex items-center gap-2" title="Select sample image">
                    <span>또는 샘플 선택</span>
                    <span className="text-xs">▼</span>
                  </Button>
                  <div className="absolute top-full left-0 mt-1 hidden group-hover:block z-50 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg p-2 min-w-[320px] max-h-[400px] overflow-y-auto">
                    <div className="text-xs text-gray-500 dark:text-gray-400 px-3 py-1 mb-1 border-b border-gray-200 dark:border-gray-700">
                      샘플 이미지 ({BLUEPRINT_SAMPLES.length}개)
                    </div>
                    {BLUEPRINT_SAMPLES.map((sample) => (
                      <button
                        key={sample.id}
                        onClick={() => loadSampleImage(sample.path)}
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

            {/* Action Buttons */}
            <div className="flex gap-2 ml-auto">
              {/* Template Buttons */}
              <Button
                onClick={() => setIsLoadTemplateModalOpen(true)}
                variant="outline"
                className="flex items-center gap-2"
                title={t('blueprintflow.loadTemplateTooltip', 'Load template')}
              >
                <FolderOpen className="w-4 h-4" />
                {t('blueprintflow.loadTemplate', 'Load Template')}
              </Button>

              <Button
                onClick={() => setIsSaveTemplateModalOpen(true)}
                variant="outline"
                className="flex items-center gap-2"
                disabled={nodes.length === 0}
                title={t('blueprintflow.saveAsTemplateTooltip', 'Save current workflow as reusable template')}
              >
                <FileDown className="w-4 h-4" />
                {t('blueprintflow.saveAsTemplate', 'Save as Template')}
              </Button>

              <div className="w-px h-8 bg-gray-300 dark:bg-gray-600 mx-1" />

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
              <ExecutionModeToggle
                executionMode={executionMode}
                setExecutionMode={setExecutionMode}
              />

              {/* Execute Button */}
              <Button
                onClick={handleExecute}
                disabled={isExecuting || isCheckingContainers || !uploadedImage}
                className={`flex items-center gap-2 ${
                  isExecuting || isCheckingContainers
                    ? 'bg-gray-500 hover:bg-gray-500 cursor-not-allowed opacity-70'
                    : 'bg-green-600 hover:bg-green-700'
                } disabled:bg-gray-400 disabled:cursor-not-allowed`}
                title={
                  isCheckingContainers
                    ? t('blueprintflow.checkingContainers', '컨테이너 확인 중...')
                    : isExecuting
                      ? t('blueprintflow.executingTooltip', '실행 중입니다...')
                      : (uploadedImage ? t('blueprintflow.executeTooltip') : 'Upload an image first')
                }
              >
                {isExecuting || isCheckingContainers ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                {isCheckingContainers
                  ? t('blueprintflow.checkingContainers', '확인 중...')
                  : isExecuting
                    ? t('blueprintflow.executing')
                    : t('blueprintflow.execute')}
              </Button>

              {isExecuting && (
                <Button
                  onClick={cancelExecution}
                  className="flex items-center gap-2 bg-red-600 hover:bg-red-700"
                  title={t('blueprintflow.cancel', 'Cancel execution')}
                >
                  <StopCircle className="w-4 h-4" />
                  {t('blueprintflow.cancel', 'Cancel')}
                </Button>
              )}

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

          {/* Execution Status Panel */}
          <ExecutionStatusPanel
            isExecuting={isExecuting}
            executionResult={executionResult as Record<string, unknown> | null}
            executionError={executionError}
            nodeStatuses={nodeStatuses}
            executionId={executionId}
            nodes={nodes}
            uploadedImage={uploadedImage}
            onRerun={handleExecute}
            onDownloadJSON={handleDownloadJSON}
          />
        </div>

        {/* ReactFlow Canvas */}
        <div className="flex-1">
          <ReactFlow
            nodes={nodes.filter((n) => n && n.id)}
            edges={edges.filter((e) => e && e.id)}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={handleConnect}
            isValidConnection={isValidConnection}
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
              nodeColor={(node) => getNodeColor(node.type)}
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
        onAddNode={handleAddRecommendedNode}
      />

      {/* Debug Panel */}
      <DebugPanel
        isOpen={isDebugPanelOpen}
        onToggle={() => setIsDebugPanelOpen(!isDebugPanelOpen)}
        executionResult={executionResult as Record<string, unknown> | null}
        executionError={executionError}
      />

      {/* Container Warning Modal */}
      <ContainerWarningModal
        modalState={containerWarningModal}
        onClose={closeWarningModal}
        onStartContainers={startContainers}
      />

      {/* Toast 알림 */}
      {toast.show && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={toast.type === 'error' ? 15000 : 10000}
          onClose={() => setToast(prev => ({ ...prev, show: false }))}
        />
      )}

      {/* Template Modals */}
      <SaveTemplateModal
        isOpen={isSaveTemplateModalOpen}
        onClose={() => setIsSaveTemplateModalOpen(false)}
        workflowName={workflowName}
        nodes={nodes}
        edges={edges}
        onSuccess={handleTemplateSaveSuccess}
      />

      <LoadTemplateModal
        isOpen={isLoadTemplateModalOpen}
        onClose={() => setIsLoadTemplateModalOpen(false)}
        onLoad={handleLoadTemplate}
      />
    </div>
  );
}

// Execution mode toggle component
function ExecutionModeToggle({
  executionMode,
  setExecutionMode,
}: {
  executionMode: 'sequential' | 'parallel';
  setExecutionMode: (mode: 'sequential' | 'parallel') => void;
}) {
  return (
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
  );
}

// Import React for useState
import React from 'react';

export default function WorkflowBuilderNew() {
  return (
    <ReactFlowProvider>
      <WorkflowBuilderCanvas />
    </ReactFlowProvider>
  );
}
