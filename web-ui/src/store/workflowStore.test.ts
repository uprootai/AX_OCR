import { describe, it, expect, beforeEach, vi } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { useWorkflowStore } from './workflowStore';

// Mock fetch for API calls
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(globalThis as any).fetch = vi.fn();

describe('workflowStore', () => {
  beforeEach(() => {
    // Reset store state between tests
    act(() => {
      useWorkflowStore.getState().clearWorkflow();
      useWorkflowStore.getState().clearNodeStatuses();
      useWorkflowStore.setState({
        uploadedImage: null,
        uploadedFileName: null,
      });
    });
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
  });

  describe('Initial state', () => {
    it('should have default workflow name', () => {
      const { result } = renderHook(() => useWorkflowStore());
      expect(result.current.workflowName).toBe('Untitled Workflow');
    });

    it('should have empty workflow description', () => {
      const { result } = renderHook(() => useWorkflowStore());
      expect(result.current.workflowDescription).toBe('');
    });

    it('should have empty nodes array', () => {
      const { result } = renderHook(() => useWorkflowStore());
      expect(result.current.nodes).toEqual([]);
    });

    it('should have empty edges array', () => {
      const { result } = renderHook(() => useWorkflowStore());
      expect(result.current.edges).toEqual([]);
    });

    it('should have no selected node', () => {
      const { result } = renderHook(() => useWorkflowStore());
      expect(result.current.selectedNode).toBeNull();
    });

    it('should not be executing', () => {
      const { result } = renderHook(() => useWorkflowStore());
      expect(result.current.isExecuting).toBe(false);
    });

    it('should have no execution result', () => {
      const { result } = renderHook(() => useWorkflowStore());
      expect(result.current.executionResult).toBeNull();
    });

    it('should have no execution error', () => {
      const { result } = renderHook(() => useWorkflowStore());
      expect(result.current.executionError).toBeNull();
    });
  });

  describe('Workflow metadata', () => {
    it('should set workflow name', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.setWorkflowName('My Workflow');
      });

      expect(result.current.workflowName).toBe('My Workflow');
    });

    it('should set workflow description', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.setWorkflowDescription('A test workflow');
      });

      expect(result.current.workflowDescription).toBe('A test workflow');
    });
  });

  describe('Node operations', () => {
    it('should add a node', () => {
      const { result } = renderHook(() => useWorkflowStore());
      const node = {
        id: 'node-1',
        type: 'yolo',
        position: { x: 100, y: 100 },
        data: { label: 'YOLO Detection' },
      };

      act(() => {
        result.current.addNode(node);
      });

      expect(result.current.nodes).toHaveLength(1);
      expect(result.current.nodes[0].id).toBe('node-1');
      expect(result.current.nodes[0].selected).toBe(false);
    });

    it('should remove a node', () => {
      const { result } = renderHook(() => useWorkflowStore());
      const node = {
        id: 'node-1',
        type: 'yolo',
        position: { x: 100, y: 100 },
        data: { label: 'YOLO Detection' },
      };

      act(() => {
        result.current.addNode(node);
      });
      expect(result.current.nodes).toHaveLength(1);

      act(() => {
        result.current.removeNode('node-1');
      });
      expect(result.current.nodes).toHaveLength(0);
    });

    it('should remove associated edges when removing a node', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.setNodes([
          { id: 'node-1', type: 'imageinput', position: { x: 0, y: 0 }, data: {} },
          { id: 'node-2', type: 'yolo', position: { x: 200, y: 0 }, data: {} },
        ]);
        result.current.setEdges([
          { id: 'edge-1', source: 'node-1', target: 'node-2' },
        ]);
      });

      expect(result.current.edges).toHaveLength(1);

      act(() => {
        result.current.removeNode('node-1');
      });

      expect(result.current.nodes).toHaveLength(1);
      expect(result.current.edges).toHaveLength(0);
    });

    it('should update node data', () => {
      const { result } = renderHook(() => useWorkflowStore());
      const node = {
        id: 'node-1',
        type: 'yolo',
        position: { x: 100, y: 100 },
        data: { label: 'YOLO Detection', parameters: {} },
      };

      act(() => {
        result.current.addNode(node);
      });

      act(() => {
        result.current.updateNodeData('node-1', {
          parameters: { confidence: 0.7 },
        });
      });

      expect(result.current.nodes[0].data.parameters).toEqual({ confidence: 0.7 });
    });

    it('should update selected node data when updating the selected node', () => {
      const { result } = renderHook(() => useWorkflowStore());
      const node = {
        id: 'node-1',
        type: 'yolo',
        position: { x: 100, y: 100 },
        data: { label: 'YOLO Detection', parameters: {} },
      };

      act(() => {
        result.current.addNode(node);
      });

      // Select node in separate act to ensure state is updated
      act(() => {
        result.current.setSelectedNode(result.current.nodes[0]);
      });

      act(() => {
        result.current.updateNodeData('node-1', {
          parameters: { confidence: 0.8 },
        });
      });

      expect(result.current.selectedNode?.data.parameters).toEqual({ confidence: 0.8 });
    });

    it('should set nodes directly', () => {
      const { result } = renderHook(() => useWorkflowStore());
      const nodes = [
        { id: 'node-1', type: 'imageinput', position: { x: 0, y: 0 }, data: {} },
        { id: 'node-2', type: 'yolo', position: { x: 200, y: 0 }, data: {} },
      ];

      act(() => {
        result.current.setNodes(nodes);
      });

      expect(result.current.nodes).toHaveLength(2);
    });
  });

  describe('Edge operations', () => {
    it('should set edges directly', () => {
      const { result } = renderHook(() => useWorkflowStore());
      const edges = [
        { id: 'edge-1', source: 'node-1', target: 'node-2' },
      ];

      act(() => {
        result.current.setEdges(edges);
      });

      expect(result.current.edges).toHaveLength(1);
    });

    it('should add edge on connect', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.onConnect({
          source: 'node-1',
          target: 'node-2',
          sourceHandle: null,
          targetHandle: null,
        });
      });

      expect(result.current.edges).toHaveLength(1);
      expect(result.current.edges[0].source).toBe('node-1');
      expect(result.current.edges[0].target).toBe('node-2');
    });
  });

  describe('Selection state', () => {
    it('should set selected node', () => {
      const { result } = renderHook(() => useWorkflowStore());
      const node = {
        id: 'node-1',
        type: 'yolo',
        position: { x: 100, y: 100 },
        data: { label: 'YOLO Detection' },
      };

      act(() => {
        result.current.addNode(node);
      });

      act(() => {
        result.current.setSelectedNode(result.current.nodes[0]);
      });

      expect(result.current.selectedNode?.id).toBe('node-1');
    });

    it('should clear selected node when node is removed', () => {
      const { result } = renderHook(() => useWorkflowStore());
      const node = {
        id: 'node-1',
        type: 'yolo',
        position: { x: 100, y: 100 },
        data: { label: 'YOLO Detection' },
      };

      act(() => {
        result.current.addNode(node);
      });

      act(() => {
        result.current.setSelectedNode(result.current.nodes[0]);
      });

      expect(result.current.selectedNode?.id).toBe('node-1');

      act(() => {
        result.current.removeNode('node-1');
      });

      expect(result.current.selectedNode).toBeNull();
    });

    it('should not clear selection when removing a different node', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.setNodes([
          { id: 'node-1', type: 'imageinput', position: { x: 0, y: 0 }, data: {} },
          { id: 'node-2', type: 'yolo', position: { x: 200, y: 0 }, data: {} },
        ]);
        result.current.setSelectedNode({ id: 'node-2', type: 'yolo', position: { x: 200, y: 0 }, data: {} });
      });

      act(() => {
        result.current.removeNode('node-1');
      });

      expect(result.current.selectedNode?.id).toBe('node-2');
    });
  });

  describe('Clear workflow', () => {
    it('should reset workflow to initial state', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.setWorkflowName('Test Workflow');
        result.current.setWorkflowDescription('Test Description');
        result.current.addNode({
          id: 'node-1',
          type: 'yolo',
          position: { x: 100, y: 100 },
          data: {},
        });
        result.current.setEdges([{ id: 'edge-1', source: 'a', target: 'b' }]);
      });

      expect(result.current.workflowName).toBe('Test Workflow');
      expect(result.current.nodes).toHaveLength(1);

      act(() => {
        result.current.clearWorkflow();
      });

      expect(result.current.workflowName).toBe('Untitled Workflow');
      expect(result.current.workflowDescription).toBe('');
      expect(result.current.nodes).toHaveLength(0);
      expect(result.current.edges).toHaveLength(0);
      expect(result.current.selectedNode).toBeNull();
    });
  });

  describe('Load workflow', () => {
    it('should load workflow from template', () => {
      const { result } = renderHook(() => useWorkflowStore());

      const workflow = {
        name: 'Loaded Workflow',
        description: 'A loaded workflow',
        nodes: [
          { id: 'node-1', type: 'imageinput', position: { x: 0, y: 0 }, label: 'Image Input' },
          { id: 'node-2', type: 'yolo', position: { x: 200, y: 0 }, label: 'YOLO' },
        ],
        edges: [
          { id: 'edge-1', source: 'node-1', target: 'node-2' },
        ],
      };

      act(() => {
        result.current.loadWorkflow(workflow);
      });

      expect(result.current.workflowName).toBe('Loaded Workflow');
      expect(result.current.workflowDescription).toBe('A loaded workflow');
      expect(result.current.nodes).toHaveLength(2);
      expect(result.current.edges).toHaveLength(1);
    });

    it('should handle empty workflow', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.loadWorkflow({});
      });

      expect(result.current.workflowName).toBe('Untitled Workflow');
      expect(result.current.nodes).toHaveLength(0);
      expect(result.current.edges).toHaveLength(0);
    });

    it('should filter out invalid nodes', () => {
      const { result } = renderHook(() => useWorkflowStore());

      const workflow = {
        nodes: [
          { id: 'node-1', type: 'yolo', position: { x: 0, y: 0 } },
          null,
          { id: '', type: 'invalid' },
          undefined,
        ] as unknown[],
        edges: [],
      };

      act(() => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        result.current.loadWorkflow(workflow as any);
      });

      expect(result.current.nodes).toHaveLength(1);
      expect(result.current.nodes[0].id).toBe('node-1');
    });

    it('should provide default position for nodes without position', () => {
      const { result } = renderHook(() => useWorkflowStore());

      const workflow = {
        nodes: [
          { id: 'node-1', type: 'yolo' },
        ],
        edges: [],
      };

      act(() => {
        result.current.loadWorkflow(workflow);
      });

      expect(result.current.nodes[0].position).toEqual({ x: 0, y: 0 });
    });
  });

  describe('Execution state', () => {
    it('should set executing state', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.setExecuting(true);
      });

      expect(result.current.isExecuting).toBe(true);

      act(() => {
        result.current.setExecuting(false);
      });

      expect(result.current.isExecuting).toBe(false);
    });

    it('should set execution result and clear error', () => {
      const { result } = renderHook(() => useWorkflowStore());
      const mockResult = {
        status: 'completed',
        execution_time_ms: 1000,
        node_statuses: [],
      };

      act(() => {
        result.current.setExecutionError('Previous error');
        result.current.setExecutionResult(mockResult);
      });

      expect(result.current.executionResult).toEqual(mockResult);
      expect(result.current.executionError).toBeNull();
    });

    it('should set execution error and clear result', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.setExecutionResult({ status: 'completed' });
        result.current.setExecutionError('Execution failed');
      });

      expect(result.current.executionError).toBe('Execution failed');
      expect(result.current.executionResult).toBeNull();
    });
  });

  describe('Node statuses', () => {
    it('should update node status', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.updateNodeStatus('node-1', {
          nodeId: 'node-1',
          status: 'running',
          progress: 0.5,
        });
      });

      expect(result.current.nodeStatuses['node-1']).toEqual({
        nodeId: 'node-1',
        status: 'running',
        progress: 0.5,
      });
    });

    it('should merge with existing status', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.updateNodeStatus('node-1', {
          nodeId: 'node-1',
          status: 'running',
          progress: 0.5,
        });
      });

      act(() => {
        result.current.updateNodeStatus('node-1', {
          progress: 0.8,
          output: { result: 'test' },
        });
      });

      expect(result.current.nodeStatuses['node-1'].status).toBe('running');
      expect(result.current.nodeStatuses['node-1'].progress).toBe(0.8);
      expect(result.current.nodeStatuses['node-1'].output).toEqual({ result: 'test' });
    });

    it('should clear node statuses', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.updateNodeStatus('node-1', {
          nodeId: 'node-1',
          status: 'completed',
          progress: 1,
        });
        result.current.updateNodeStatus('node-2', {
          nodeId: 'node-2',
          status: 'failed',
          progress: 0,
          error: 'Error',
        });
      });

      expect(Object.keys(result.current.nodeStatuses)).toHaveLength(2);

      act(() => {
        result.current.clearNodeStatuses();
      });

      expect(Object.keys(result.current.nodeStatuses)).toHaveLength(0);
      expect(result.current.executionId).toBeNull();
    });
  });

  describe('Uploaded image', () => {
    it('should set uploaded image', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.setUploadedImage('base64-image-data', 'test.png');
      });

      expect(result.current.uploadedImage).toBe('base64-image-data');
      expect(result.current.uploadedFileName).toBe('test.png');
    });

    it('should clear uploaded image', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.setUploadedImage('base64-image-data', 'test.png');
      });

      act(() => {
        result.current.setUploadedImage(null);
      });

      expect(result.current.uploadedImage).toBeNull();
      expect(result.current.uploadedFileName).toBeNull();
    });

    it('should persist image to sessionStorage', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.setUploadedImage('base64-image-data', 'test.png');
      });

      expect(sessionStorage.getItem('blueprintflow-uploadedImage')).toBe('base64-image-data');
      expect(sessionStorage.getItem('blueprintflow-uploadedFileName')).toBe('test.png');
    });

    it('should remove from sessionStorage when clearing image', () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.setUploadedImage('base64-image-data', 'test.png');
      });

      act(() => {
        result.current.setUploadedImage(null);
      });

      expect(sessionStorage.getItem('blueprintflow-uploadedImage')).toBeNull();
      expect(sessionStorage.getItem('blueprintflow-uploadedFileName')).toBeNull();
    });
  });

  describe('Execute workflow validation', () => {
    it('should error when workflow is empty', async () => {
      const { result } = renderHook(() => useWorkflowStore());

      await act(async () => {
        await result.current.executeWorkflow('base64-image');
      });

      expect(result.current.executionError).toBe('Workflow is empty. Add nodes to execute.');
    });

    it('should error when no image is provided', async () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.addNode({
          id: 'node-1',
          type: 'yolo',
          position: { x: 0, y: 0 },
          data: {},
        });
      });

      await act(async () => {
        await result.current.executeWorkflow('');
      });

      expect(result.current.executionError).toBe('Input image is required. Please upload an image first.');
    });
  });

  describe('Execute workflow stream validation', () => {
    it('should error when workflow is empty', async () => {
      const { result } = renderHook(() => useWorkflowStore());

      await act(async () => {
        await result.current.executeWorkflowStream('base64-image');
      });

      expect(result.current.executionError).toBe('Workflow is empty. Add nodes to execute.');
    });

    it('should error when no image is provided', async () => {
      const { result } = renderHook(() => useWorkflowStore());

      act(() => {
        result.current.addNode({
          id: 'node-1',
          type: 'yolo',
          position: { x: 0, y: 0 },
          data: {},
        });
      });

      await act(async () => {
        await result.current.executeWorkflowStream('');
      });

      expect(result.current.executionError).toBe('Input image is required. Please upload an image first.');
    });
  });
});
