/**
 * useBuilderHandlers — workflow action handlers extracted from WorkflowBuilderCanvas.
 * Covers: save, load template, template save success, download JSON,
 * drag-and-drop node creation, add recommended node.
 */

import { useCallback } from 'react';
import type { ReactFlowInstance } from 'reactflow';
import { useWorkflowStore } from '../../../store/workflowStore';
import { useAPIConfigStore } from '../../../store/apiConfigStore';
import { workflowApi, type TemplateDetail } from '../../../lib/api';
import { getId } from '../constants';

interface UseBuilderHandlersOptions {
  reactFlowInstance: ReactFlowInstance | null;
  selectedNodeId: string | null;
  uploadedImage: string | null;
  showToast: (message: string, type?: 'success' | 'error' | 'warning' | 'info') => void;
}

export function useBuilderHandlers({
  reactFlowInstance,
  selectedNodeId,
  uploadedImage,
  showToast,
}: UseBuilderHandlersOptions) {
  const customAPIs = useAPIConfigStore((state) => state.customAPIs);
  const nodes = useWorkflowStore((state) => state.nodes);
  const { edges, workflowName, addNode, loadWorkflow } = useWorkflowStore();

  // Save workflow
  const handleSave = useCallback(async () => {
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
  }, [workflowName, nodes, edges, showToast]);

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

  // Handle template save success callback
  const handleTemplateSaveSuccess = useCallback((templateId: string) => {
    showToast(`✓ 템플릿 저장 완료 (ID: ${templateId.slice(0, 8)}...)`, 'success');
  }, [showToast]);

  // Download execution result as JSON
  const handleDownloadJSON = useCallback(() => {
    const executionResult = useWorkflowStore.getState().executionResult;
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
  }, []);

  // Generic file download helper
  const handleDownloadFile = useCallback((dataUrl: string, filename: string) => {
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }, []);

  // Drag-and-drop: onDrop
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
          ...(customAPI && { icon: customAPI.icon, color: customAPI.color }),
        },
        selected: false,
      };
      addNode(newNode);
    },
    [reactFlowInstance, addNode, customAPIs]
  );

  // Drag-and-drop: onDragOver
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // Palette drag start
  const onNodeDragStart = useCallback((event: React.DragEvent, nodeType: string, label: string) => {
    event.dataTransfer.setData('application/reactflow-type', nodeType);
    event.dataTransfer.setData('application/reactflow-label', label);
    event.dataTransfer.effectAllowed = 'move';
  }, []);

  // Add recommended node (from NodeDetailPanel)
  const handleAddRecommendedNode = useCallback(
    (nodeType: string) => {
      if (!reactFlowInstance) return;

      const currentSelectedNode = nodes.find(n => n.id === selectedNodeId);
      const basePosition = currentSelectedNode?.position || { x: 300, y: 200 };

      const existingNodePositions = nodes.map(n => n.position);
      const offsetX = 250;
      let offsetY = 0;

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
          ...(customAPI && { icon: customAPI.icon, color: customAPI.color }),
        },
        selected: false,
      };
      addNode(newNode);
    },
    [reactFlowInstance, nodes, selectedNodeId, customAPIs, addNode]
  );

  return {
    handleSave,
    handleLoadTemplate,
    handleTemplateSaveSuccess,
    handleDownloadJSON,
    handleDownloadFile,
    onDrop,
    onDragOver,
    onNodeDragStart,
    handleAddRecommendedNode,
  };
}
