import type { Node, Edge } from 'reactflow';

// Type definitions
export type ParameterValue = string | number | boolean | string[] | null | undefined;
export type ParameterRecord = Record<string, ParameterValue>;

// Execution mode type
export type ExecutionMode = 'sequential' | 'parallel' | 'eager';

// Workflow result type
export interface WorkflowExecutionResult {
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
export interface WorkflowTemplate {
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

export interface NodeStatus {
  nodeId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  error?: string;
  output?: Record<string, unknown>;
  elapsedSeconds?: number;  // 하트비트: 경과 시간 (초)
  message?: string;         // 하트비트: 상태 메시지
}

export interface WorkflowState {
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

  // AbortController for canceling execution
  abortController: AbortController | null;

  // Uploaded image (persistent across navigation)
  uploadedImage: string | null;
  uploadedFileName: string | null;

  // Uploaded GT file (optional, for GT comparison in pipeline)
  uploadedGTFile: { name: string; content: string } | null;

  // Uploaded pricing file (optional, for session-specific pricing)
  uploadedPricingFile: { name: string; content: string } | null;

  // Execution mode (default: sequential)
  executionMode: ExecutionMode;

  // Project association
  selectedProjectId: string | null;

  // Actions
  setWorkflowName: (name: string) => void;
  setWorkflowDescription: (description: string) => void;
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: (changes: import('reactflow').NodeChange[]) => void;
  onEdgesChange: (changes: import('reactflow').EdgeChange[]) => void;
  onConnect: (connection: import('reactflow').Connection) => void;
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
  setUploadedGTFile: (file: { name: string; content: string } | null) => void;
  setUploadedPricingFile: (file: { name: string; content: string } | null) => void;
  setExecutionMode: (mode: ExecutionMode) => void;
  cancelExecution: () => Promise<void>;
  setSelectedProjectId: (id: string | null) => void;
}

// Helper: Get saved hyperparameters from localStorage for a specific node type
export const getSavedHyperparameters = (nodeType: string): ParameterRecord => {
  try {
    const savedHyperParams = localStorage.getItem('hyperParameters');
    if (!savedHyperParams) return {};

    const allParams = JSON.parse(savedHyperParams) as Record<string, ParameterValue>;
    const result: ParameterRecord = {};

    // Map node types to their localStorage prefixes
    const prefixMap: Record<string, string> = {
      yolo: 'yolo',
      edocr2: 'edocr2',
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

// Helper to load image from sessionStorage
export const loadPersistedImage = (): { uploadedImage: string | null; uploadedFileName: string | null } => {
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
export const persistImage = (image: string | null, fileName: string | null) => {
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
