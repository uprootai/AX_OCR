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
  executeWorkflow: (inputImage: string) => Promise<void>;
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
      nodes: [...get().nodes, { ...node, selected: false }],
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
    // Transform template nodes to ReactFlow Node format
    const transformedNodes = (workflow.nodes || [])
      .filter((node: any) => node && node.id) // Filter out invalid nodes
      .map((node: any) => ({
        ...node,
        data: {
          label: node.label || node.data?.label || '',
          parameters: node.parameters || node.data?.parameters || {},
          ...node.data,
        },
        selected: false,
      }));

    // Transform edges with selected property
    const transformedEdges = (workflow.edges || [])
      .filter((edge: any) => edge && edge.id) // Filter out invalid edges
      .map((edge: any) => ({
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

  setExecuting: (isExecuting) => set({ isExecuting }),

  setExecutionResult: (result) => set({ executionResult: result, executionError: null }),

  setExecutionError: (error) => set({ executionError: error, executionResult: null }),

  executeWorkflow: async (inputImage: string) => {
    const { nodes, edges, workflowName } = get();

    // Validation
    if (nodes.length === 0) {
      set({ executionError: 'Workflow is empty. Add nodes to execute.' });
      return;
    }

    if (!inputImage) {
      set({ executionError: 'Input image is required. Please upload an image first.' });
      return;
    }

    try {
      set({ isExecuting: true, executionError: null, executionResult: null });

      // Build workflow definition
      const workflowDefinition = {
        id: `workflow-${Date.now()}`,
        name: workflowName,
        nodes: nodes.map((node) => ({
          id: node.id,
          type: node.type || 'unknown',
          position: node.position,
          parameters: node.data?.parameters || {},
        })),
        edges: edges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          sourceHandle: edge.sourceHandle || null,
          targetHandle: edge.targetHandle || null,
        })),
      };

      // Prepare request payload
      const requestPayload = {
        workflow: workflowDefinition,
        inputs: {
          image: inputImage, // Base64 encoded image
        },
        config: {},
      };

      console.log('🚀 Executing workflow:', workflowDefinition.name);
      console.log('📋 Workflow definition:', workflowDefinition);

      // Call Gateway API
      const response = await fetch('http://localhost:8000/api/v1/workflow/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestPayload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      console.log('✅ Workflow execution completed:', result);

      set({
        isExecuting: false,
        executionResult: result,
        executionError: null,
      });
    } catch (error: any) {
      console.error('❌ Workflow execution failed:', error);
      set({
        isExecuting: false,
        executionError: error.message || 'Unknown error occurred',
        executionResult: null,
      });
    }
  },
}));
