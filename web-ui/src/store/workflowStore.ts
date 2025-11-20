import { create } from 'zustand';
import { addEdge, applyNodeChanges, applyEdgeChanges } from 'reactflow';
import type { Node, Edge, Connection } from 'reactflow';

interface WorkflowState {
  // Workflow metadata
  workflowName: string;
  workflowDescription: string;

  // ReactFlow state
  nodes: Node[];
  edges: Edge[];

  // Selected node for properties panel
  selectedNode: Node | null;

  // Execution state
  isExecuting: boolean;
  executionResult: any | null;
  executionError: string | null;

  // Actions
  setWorkflowName: (name: string) => void;
  setWorkflowDescription: (description: string) => void;
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: (changes: any) => void;
  onEdgesChange: (changes: any) => void;
  onConnect: (connection: Connection) => void;
  addNode: (node: Node) => void;
  removeNode: (nodeId: string) => void;
  updateNodeData: (nodeId: string, data: any) => void;
  setSelectedNode: (node: Node | null) => void;
  clearWorkflow: () => void;
  loadWorkflow: (workflow: any) => void;
  setExecuting: (isExecuting: boolean) => void;
  setExecutionResult: (result: any) => void;
  setExecutionError: (error: string | null) => void;
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  // Initial state
  workflowName: 'Untitled Workflow',
  workflowDescription: '',
  nodes: [],
  edges: [],
  selectedNode: null,
  isExecuting: false,
  executionResult: null,
  executionError: null,

  // Actions
  setWorkflowName: (name) => set({ workflowName: name }),

  setWorkflowDescription: (description) => set({ workflowDescription: description }),

  setNodes: (nodes) => set({ nodes }),

  setEdges: (edges) => set({ edges }),

  onNodesChange: (changes) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    });
  },

  onEdgesChange: (changes) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },

  onConnect: (connection) => {
    set({
      edges: addEdge(connection, get().edges),
    });
  },

  addNode: (node) => {
    set({
      nodes: [...get().nodes, node],
    });
  },

  removeNode: (nodeId) => {
    set({
      nodes: get().nodes.filter((n) => n.id !== nodeId),
      edges: get().edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
      selectedNode: get().selectedNode?.id === nodeId ? null : get().selectedNode,
    });
  },

  updateNodeData: (nodeId, data) => {
    set({
      nodes: get().nodes.map((node) =>
        node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
      ),
    });
  },

  setSelectedNode: (node) => set({ selectedNode: node }),

  clearWorkflow: () => {
    set({
      workflowName: 'Untitled Workflow',
      workflowDescription: '',
      nodes: [],
      edges: [],
      selectedNode: null,
      executionResult: null,
      executionError: null,
    });
  },

  loadWorkflow: (workflow) => {
    set({
      workflowName: workflow.name || 'Untitled Workflow',
      workflowDescription: workflow.description || '',
      nodes: workflow.nodes || [],
      edges: workflow.edges || [],
      selectedNode: null,
      executionResult: null,
      executionError: null,
    });
  },

  setExecuting: (isExecuting) => set({ isExecuting }),

  setExecutionResult: (result) => set({ executionResult: result, executionError: null }),

  setExecutionError: (error) => set({ executionError: error, executionResult: null }),
}));
