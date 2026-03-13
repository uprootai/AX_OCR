import { addEdge, applyNodeChanges, applyEdgeChanges } from 'reactflow';
import type { Node, Connection, NodeChange, EdgeChange } from 'reactflow';
import type { WorkflowState, NodeStatus, WorkflowTemplate } from './types';

// Zustand set/get types
type ZustandSet = (
  partial: WorkflowState | Partial<WorkflowState> | ((state: WorkflowState) => WorkflowState | Partial<WorkflowState>),
  replace?: false
) => void;
type ZustandGet = () => WorkflowState;

export const createNodeActions = (set: ZustandSet, get: ZustandGet) => ({
  setNodes: (nodes: Node[]) => set({ nodes }),

  setEdges: (edges: import('reactflow').Edge[]) => set({ edges }),

  onNodesChange: (changes: NodeChange[]) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    });
  },

  onEdgesChange: (changes: EdgeChange[]) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },

  onConnect: (connection: Connection) => {
    set({
      edges: addEdge(connection, get().edges),
    });
  },

  addNode: (node: Node) => {
    set({
      nodes: [...get().nodes, { ...node, selected: false }],
    });
  },

  removeNode: (nodeId: string) => {
    set({
      nodes: get().nodes.filter((n) => n.id !== nodeId),
      edges: get().edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
      selectedNode: get().selectedNode?.id === nodeId ? null : get().selectedNode,
    });
  },

  updateNodeData: (nodeId: string, data: Record<string, unknown>) => {
    const updatedNodes = get().nodes.map((node) =>
      node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
    );
    const selectedNode = get().selectedNode;
    const updatedSelectedNode = selectedNode?.id === nodeId
      ? { ...selectedNode, data: { ...selectedNode.data, ...data } }
      : selectedNode;

    set({
      nodes: updatedNodes,
      selectedNode: updatedSelectedNode,
    });
  },

  setSelectedNode: (node: Node | null) => set({ selectedNode: node }),

  clearWorkflow: () => {
    // 세션스토리지에서 이미지 삭제
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('blueprintflow-uploadedImage');
      sessionStorage.removeItem('blueprintflow-uploadedFileName');
    }
    set({
      workflowName: 'Untitled Workflow',
      workflowDescription: '',
      nodes: [],
      edges: [],
      selectedNode: null,
      executionResult: null,
      executionError: null,
      uploadedImage: null,
      uploadedFileName: null,
      uploadedGTFile: null,
      uploadedPricingFile: null,
      nodeStatuses: {},
      isExecuting: false,
    });
  },

  loadWorkflow: (workflow: WorkflowTemplate) => {
    // Transform template nodes to ReactFlow Node format
    const transformedNodes = (workflow.nodes || [])
      .filter((node) => node && node.id) // Filter out invalid nodes
      .map((node) => ({
        ...node,
        position: node.position || { x: 0, y: 0 },
        data: {
          label: node.label || node.data?.label || '',
          parameters: node.parameters || node.data?.parameters || {},
          ...node.data,
        },
        selected: false,
      }));

    // Transform edges with selected property
    const transformedEdges = (workflow.edges || [])
      .filter((edge) => edge && edge.id) // Filter out invalid edges
      .map((edge) => ({
        ...edge,
        selected: false,
      }));

    set({
      workflowName: workflow.name || 'Untitled Workflow',
      workflowDescription: workflow.description || '',
      nodes: transformedNodes,
      edges: transformedEdges,
      selectedNode: null,
      executionResult: null,
      executionError: null,
    });
  },

  updateNodeStatus: (nodeId: string, status: Partial<NodeStatus>) => {
    set((state) => ({
      nodeStatuses: {
        ...state.nodeStatuses,
        [nodeId]: {
          ...(state.nodeStatuses[nodeId] || { nodeId, status: 'pending', progress: 0 }),
          ...status,
        },
      },
    }));
  },

  clearNodeStatuses: () => {
    set({ nodeStatuses: {}, executionId: null });
  },
});
