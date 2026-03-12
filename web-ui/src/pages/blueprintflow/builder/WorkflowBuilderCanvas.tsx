/**
 * WorkflowBuilderCanvas — main canvas component.
 * Orchestrates state, hooks, and renders the builder layout.
 */

import React, { useCallback, useEffect, useMemo, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow';
import type { ReactFlowInstance, OnSelectionChangeParams, NodeTypes, Connection } from 'reactflow';
import 'reactflow/dist/style.css';

import { useWorkflowStore } from '../../../store/workflowStore';
import { useAPIConfigStore } from '../../../store/apiConfigStore';
import NodePalette from '../../../components/blueprintflow/NodePalette';
import NodeDetailPanel from '../../../components/blueprintflow/NodeDetailPanel';
import DynamicNode from '../../../components/blueprintflow/nodes/DynamicNode';
import Toast from '../../../components/ui/Toast';
import { projectApi, type Project } from '../../../lib/blueprintBomApi';
import DebugPanel from '../../../components/blueprintflow/DebugPanel';

import { baseNodeTypes, getNodeColor } from '../constants';
import { useContainerStatus, useImageUpload } from '../hooks';
import { ContainerWarningModal, SaveTemplateModal, LoadTemplateModal } from '../components';
import { BuilderToolbar } from './BuilderToolbar';
import { useBuilderHandlers } from './useBuilderHandlers';

// Toast 알림 타입
interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

export function WorkflowBuilderCanvas() {
  const customAPIs = useAPIConfigStore((state) => state.customAPIs);

  // Toast state (defined early — used by hooks below)
  const [toast, setToast] = React.useState<ToastState>({ show: false, message: '', type: 'info' });
  const showToast = useCallback((message: string, type: ToastState['type'] = 'info') => {
    setToast({ show: true, message, type });
  }, []);

  // Image upload hook
  const {
    fileInputRef,
    uploadedImage,
    uploadedFileName,
    handleImageUpload,
    handleRemoveImage,
    triggerFileInput,
    loadSampleImage,
  } = useImageUpload({ onShowToast: showToast });

  // Session auto-load from ?session= query parameter
  const [searchParams] = useSearchParams();
  const setUploadedImage = useWorkflowStore((state) => state.setUploadedImage);

  useEffect(() => {
    const sessionId = searchParams.get('session');
    if (!sessionId || uploadedImage) return;

    (async () => {
      try {
        const session = await projectApi.getSession(sessionId);
        const imageUrl = projectApi.getSessionImageUrl(sessionId);
        const res = await fetch(imageUrl);
        const data = await res.json();
        if (data.image_base64 && data.mime_type) {
          const dataUrl = `data:${data.mime_type};base64,${data.image_base64}`;
          setUploadedImage(dataUrl, session.drawing_number || data.filename || 'session-image');
        }
      } catch (err) {
        console.error('Failed to load session image:', err);
      }
    })();
  }, [searchParams, uploadedImage, setUploadedImage]);

  // Project association
  const [projects, setProjects] = React.useState<Project[]>([]);
  const selectedProjectId = useWorkflowStore((state) => state.selectedProjectId);
  const setSelectedProjectId = useWorkflowStore((state) => state.setSelectedProjectId);

  React.useEffect(() => {
    projectApi.list(undefined, 100)
      .then(res => setProjects(res.projects ?? []))
      .catch(() => setProjects([]));
  }, []);

  // GT file attachment
  const uploadedGTFile = useWorkflowStore((state) => state.uploadedGTFile);
  const setUploadedGTFile = useWorkflowStore((state) => state.setUploadedGTFile);
  const gtFileInputRef = useRef<HTMLInputElement>(null);

  const handleGTFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      setUploadedGTFile({ name: file.name, content: reader.result as string });
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  }, [setUploadedGTFile]);

  // Pricing file attachment
  const uploadedPricingFile = useWorkflowStore((state) => state.uploadedPricingFile);
  const setUploadedPricingFile = useWorkflowStore((state) => state.setUploadedPricingFile);
  const pricingFileInputRef = useRef<HTMLInputElement>(null);

  const handlePricingFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      setUploadedPricingFile({ name: file.name, content: reader.result as string });
    };
    reader.readAsDataURL(file);
    e.target.value = '';
  }, [setUploadedPricingFile]);

  // Workflow store
  const nodes = useWorkflowStore((state) => state.nodes);
  const {
    edges,
    workflowName,
    onNodesChange,
    onEdgesChange,
    onConnect,
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
    onShowToast: showToast,
  });

  // ReactFlow instance + UI state
  const [reactFlowInstance, setReactFlowInstance] = React.useState<ReactFlowInstance | null>(null);
  const [selectedNodeId, setSelectedNodeId] = React.useState<string | null>(null);
  const [isDebugPanelOpen, setIsDebugPanelOpen] = React.useState(false);
  const [isSaveTemplateModalOpen, setIsSaveTemplateModalOpen] = React.useState(false);
  const [isLoadTemplateModalOpen, setIsLoadTemplateModalOpen] = React.useState(false);

  // Extracted handlers hook
  const {
    handleSave,
    handleLoadTemplate,
    handleTemplateSaveSuccess,
    handleDownloadJSON,
    handleDownloadFile,
    onDrop,
    onDragOver,
    onNodeDragStart,
    handleAddRecommendedNode,
  } = useBuilderHandlers({ reactFlowInstance, selectedNodeId, uploadedImage, showToast });

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

  // Execute workflow
  const handleExecute = () => {
    executeWithContainerCheck(nodes, uploadedImage);
  };

  // Delete handlers (no-op — store handles deletion via onNodesChange)
  const onNodesDelete = useCallback((_deleted: { id: string }[]) => {}, []);
  const onEdgesDelete = useCallback((_deleted: { id: string }[]) => {}, []);

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
        <BuilderToolbar
          workflowName={workflowName}
          nodes={nodes}
          edges={edges}
          isExecuting={isExecuting}
          executionResult={executionResult as Record<string, unknown> | null}
          executionError={executionError}
          nodeStatuses={nodeStatuses}
          executionId={executionId}
          executionMode={executionMode}
          isCheckingContainers={isCheckingContainers}
          fileInputRef={fileInputRef}
          uploadedImage={uploadedImage}
          uploadedFileName={uploadedFileName}
          handleImageUpload={handleImageUpload}
          handleRemoveImage={handleRemoveImage}
          triggerFileInput={triggerFileInput}
          loadSampleImage={loadSampleImage}
          gtFileInputRef={gtFileInputRef}
          uploadedGTFile={uploadedGTFile}
          handleGTFileChange={handleGTFileChange}
          setUploadedGTFile={setUploadedGTFile}
          pricingFileInputRef={pricingFileInputRef}
          uploadedPricingFile={uploadedPricingFile}
          handlePricingFileChange={handlePricingFileChange}
          setUploadedPricingFile={setUploadedPricingFile}
          projects={projects}
          selectedProjectId={selectedProjectId}
          setSelectedProjectId={setSelectedProjectId}
          onSave={handleSave}
          onExecute={handleExecute}
          onCancelExecution={cancelExecution}
          onClearWorkflow={clearWorkflow}
          onDownloadJSON={handleDownloadJSON}
          onDownloadFile={handleDownloadFile}
          onOpenSaveTemplateModal={() => setIsSaveTemplateModalOpen(true)}
          onOpenLoadTemplateModal={() => setIsLoadTemplateModalOpen(true)}
          onToggleDebugPanel={() => setIsDebugPanelOpen(!isDebugPanelOpen)}
          onSetWorkflowName={(name) => useWorkflowStore.setState({ workflowName: name })}
          setExecutionMode={setExecutionMode}
          isDebugPanelOpen={isDebugPanelOpen}
        />

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

      {/* Toast */}
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
