import { create } from 'zustand';
import { addEdge, applyNodeChanges, applyEdgeChanges } from 'reactflow';
import type { Node, Edge, Connection, NodeChange, EdgeChange } from 'reactflow';
import { getNodeDefinition } from '../config/nodeDefinitions';

// Type definitions
type ParameterValue = string | number | boolean | null | undefined;
type ParameterRecord = Record<string, ParameterValue>;

// Workflow result type
interface WorkflowExecutionResult {
  status: string;
  execution_time_ms?: number;
  node_statuses?: Array<{
    node_id: string;
    status: string;
    execution_time?: number;
    start_time?: string;
    end_time?: string;
    output?: Record<string, unknown>;
    error?: string;
  }>;
  final_output?: Record<string, unknown>;
}

// Workflow template type for loading (accepts looser types for compatibility)
interface WorkflowTemplate {
  name?: string;
  description?: string;
  nodes?: Array<{
    id: string;
    type?: string;
    label?: string;
    position?: { x: number; y: number };
    parameters?: Record<string, unknown>;
    data?: { label?: string; parameters?: Record<string, unknown> };
  }>;
  edges?: Array<{
    id: string;
    source: string;
    target: string;
    sourceHandle?: string;
    targetHandle?: string;
  }>;
}

// Helper: Get saved hyperparameters from localStorage for a specific node type
const getSavedHyperparameters = (nodeType: string): ParameterRecord => {
  try {
    const savedHyperParams = localStorage.getItem('hyperParameters');
    if (!savedHyperParams) return {};

    const allParams = JSON.parse(savedHyperParams) as Record<string, ParameterValue>;
    const result: ParameterRecord = {};

    // Map node types to their localStorage prefixes
    const prefixMap: Record<string, string> = {
      yolo: 'yolo',
      edocr2: 'edocr2_v2',
      edocr2_v1: 'edocr2_v1',
      edocr2_v2: 'edocr2_v2',
      edgnet: 'edgnet',
      paddleocr: 'paddleocr',
      surya_ocr: 'surya_ocr',
      doctr: 'doctr',
      easyocr: 'easyocr',
      skinmodel: 'skinmodel',
      vl: 'vl',
    };

    const prefix = prefixMap[nodeType.toLowerCase()] || nodeType.toLowerCase();

    // Extract parameters for this node type
    Object.keys(allParams).forEach((key) => {
      if (key.startsWith(`${prefix}_`)) {
        // Remove prefix to get the parameter name
        const paramName = key.substring(prefix.length + 1);
        result[paramName] = allParams[key];
      }
    });

    return result;
  } catch (e) {
    console.error('Failed to load saved hyperparameters:', e);
    return {};
  }
};

export interface NodeStatus {
  nodeId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  error?: string;
  output?: Record<string, unknown>;
}

// Execution mode type
type ExecutionMode = 'sequential' | 'parallel';

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
  executionResult: WorkflowExecutionResult | null;
  executionError: string | null;

  // Real-time node statuses (SSE)
  nodeStatuses: Record<string, NodeStatus>;
  executionId: string | null;

  // Uploaded image (persistent across navigation)
  uploadedImage: string | null;
  uploadedFileName: string | null;

  // Execution mode (default: sequential)
  executionMode: ExecutionMode;

  // Actions
  setWorkflowName: (name: string) => void;
  setWorkflowDescription: (description: string) => void;
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  addNode: (node: Node) => void;
  removeNode: (nodeId: string) => void;
  updateNodeData: (nodeId: string, data: Record<string, unknown>) => void;
  setSelectedNode: (node: Node | null) => void;
  clearWorkflow: () => void;
  loadWorkflow: (workflow: WorkflowTemplate) => void;
  setExecuting: (isExecuting: boolean) => void;
  setExecutionResult: (result: WorkflowExecutionResult | null) => void;
  setExecutionError: (error: string | null) => void;
  executeWorkflow: (inputImage: string) => Promise<void>;
  executeWorkflowStream: (inputImage: string) => Promise<void>;
  updateNodeStatus: (nodeId: string, status: Partial<NodeStatus>) => void;
  clearNodeStatuses: () => void;
  setUploadedImage: (image: string | null, fileName?: string | null) => void;
  setExecutionMode: (mode: ExecutionMode) => void;
}

// Helper to load image from sessionStorage
const loadPersistedImage = (): { uploadedImage: string | null; uploadedFileName: string | null } => {
  if (typeof window === 'undefined') return { uploadedImage: null, uploadedFileName: null };
  try {
    const image = sessionStorage.getItem('blueprintflow-uploadedImage');
    const fileName = sessionStorage.getItem('blueprintflow-uploadedFileName');
    return { uploadedImage: image, uploadedFileName: fileName };
  } catch {
    return { uploadedImage: null, uploadedFileName: null };
  }
};

// Helper to save image to sessionStorage
const persistImage = (image: string | null, fileName: string | null) => {
  if (typeof window === 'undefined') return;
  try {
    if (image) {
      sessionStorage.setItem('blueprintflow-uploadedImage', image);
      sessionStorage.setItem('blueprintflow-uploadedFileName', fileName || '');
    } else {
      sessionStorage.removeItem('blueprintflow-uploadedImage');
      sessionStorage.removeItem('blueprintflow-uploadedFileName');
    }
  } catch (e) {
    console.warn('Failed to persist image to sessionStorage:', e);
  }
};

// Load persisted image on init
const persistedImage = loadPersistedImage();

export const useWorkflowStore = create<WorkflowState>()((set, get) => ({
  // Initial state
  workflowName: 'Untitled Workflow',
  workflowDescription: '',
  nodes: [],
  edges: [],
  selectedNode: null,
  isExecuting: false,
  executionResult: null,
  executionError: null,
  nodeStatuses: {},
  executionId: null,
  uploadedImage: persistedImage.uploadedImage,
  uploadedFileName: persistedImage.uploadedFileName,
  executionMode: 'sequential', // Default: sequential execution

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

      // Build workflow definition with default parameters merged
      const workflowDefinition = {
        id: `workflow-${Date.now()}`,
        name: workflowName,
        nodes: nodes.map((node) => {
          // Get node definition to merge default parameters
          const nodeDefinition = getNodeDefinition(node.type || '');
          const defaultParams: ParameterRecord = {};

          // Extract default values from node definition
          if (nodeDefinition?.parameters) {
            nodeDefinition.parameters.forEach((param) => {
              defaultParams[param.name] = param.default;
            });
          }

          // Get saved hyperparameters from localStorage (API Settings page)
          const savedParams = getSavedHyperparameters(node.type || '');

          // Merge order: defaults <- saved hyperparameters <- user-set parameters
          const mergedParameters = {
            ...defaultParams,
            ...savedParams,
            ...(node.data?.parameters || {}),
          };

          return {
            id: node.id,
            type: node.type || 'unknown',
            position: node.position,
            parameters: mergedParameters,
          };
        }),
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
    } catch (error) {
      console.error('❌ Workflow execution failed:', error);
      set({
        isExecuting: false,
        executionError: error instanceof Error ? error.message : 'Unknown error occurred',
        executionResult: null,
      });
    }
  },

  executeWorkflowStream: async (inputImage: string) => {
    const { nodes, edges, workflowName, executionMode } = get();

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
      set({
        isExecuting: true,
        executionError: null,
        executionResult: null,
        nodeStatuses: {},
        executionId: null,
      });

      // Build workflow definition with default parameters merged
      const workflowDefinition = {
        id: `workflow-${Date.now()}`,
        name: workflowName,
        nodes: nodes.map((node) => {
          // Get node definition to merge default parameters
          const nodeDefinition = getNodeDefinition(node.type || '');
          const defaultParams: ParameterRecord = {};

          // Extract default values from node definition
          if (nodeDefinition?.parameters) {
            nodeDefinition.parameters.forEach((param) => {
              defaultParams[param.name] = param.default;
            });
          }

          // Get saved hyperparameters from localStorage (API Settings page)
          const savedParams = getSavedHyperparameters(node.type || '');

          // Merge order: defaults <- saved hyperparameters <- user-set parameters
          const mergedParameters = {
            ...defaultParams,
            ...savedParams,
            ...(node.data?.parameters || {}),
          };

          return {
            id: node.id,
            type: node.type || 'unknown',
            position: node.position,
            parameters: mergedParameters,
          };
        }),
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
          image: inputImage,
        },
        config: {
          execution_mode: executionMode, // 'sequential' or 'parallel'
        },
      };

      console.log('🚀 [SSE] Executing workflow:', workflowDefinition.name);
      console.log('📋 [SSE] Workflow definition:', workflowDefinition);
      console.log('⚙️ [SSE] Execution mode:', executionMode);

      // Use EventSource for SSE
      const response = await fetch('http://localhost:8000/api/v1/workflow/execute-stream', {
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

      // Read SSE stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          console.log('✅ [SSE] Stream ended');
          break;
        }

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete messages (SSE format: "data: {...}\n\n")
        const messages = buffer.split('\n\n');
        buffer = messages.pop() || ''; // Keep incomplete message in buffer

        for (const message of messages) {
          if (!message.trim() || !message.startsWith('data: ')) continue;

          try {
            const jsonStr = message.replace('data: ', '');
            const event = JSON.parse(jsonStr);

            console.log('📨 [SSE] Event received:', event.type, event);

            // Handle different event types
            switch (event.type) {
              case 'workflow_start':
                set({ executionId: event.execution_id });
                break;

              case 'execution_plan': {
                // Initialize node statuses
                const statuses: Record<string, NodeStatus> = {};
                nodes.forEach((node) => {
                  statuses[node.id] = {
                    nodeId: node.id,
                    status: 'pending',
                    progress: 0,
                  };
                });
                set({ nodeStatuses: statuses });
                break;
              }

              case 'node_start':
                get().updateNodeStatus(event.node_id, {
                  nodeId: event.node_id,
                  status: 'running',
                  progress: 0,
                });
                break;

              case 'node_update':
                get().updateNodeStatus(event.node_id, {
                  nodeId: event.node_id,
                  status: event.status,
                  progress: event.progress,
                  error: event.error,
                  output: event.output,  // ✅ output 추가!
                });
                break;

              case 'node_complete':
                get().updateNodeStatus(event.node_id, {
                  nodeId: event.node_id,
                  status: event.status === 'failed' ? 'failed' : 'completed',
                  progress: event.progress || 1.0,
                  error: event.error,
                  output: event.output,  // ✅ output 추가!
                });
                break;

              case 'node_error':
                get().updateNodeStatus(event.node_id, {
                  nodeId: event.node_id,
                  status: 'failed',
                  progress: 0,
                  error: event.error,
                });
                break;

              case 'workflow_complete':
                set({
                  isExecuting: false,
                  executionResult: {
                    status: event.status,
                    execution_time_ms: event.execution_time_ms,
                    node_statuses: event.node_statuses,
                    final_output: event.final_output,
                  },
                  executionError: null,
                });
                console.log('✅ [SSE] Workflow completed:', event.status);
                break;

              case 'error':
                throw new Error(event.message);
            }
          } catch (parseError) {
            console.error('❌ [SSE] Failed to parse event:', parseError, message);
          }
        }
      }
    } catch (error) {
      console.error('❌ [SSE] Workflow execution failed:', error);
      set({
        isExecuting: false,
        executionError: error instanceof Error ? error.message : 'Unknown error occurred',
        executionResult: null,
      });
    }
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

  setUploadedImage: (image, fileName = null) => {
    set({ uploadedImage: image, uploadedFileName: fileName });
    persistImage(image, fileName);
  },

  setExecutionMode: (mode) => set({ executionMode: mode }),
}));
