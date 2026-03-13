import { create } from 'zustand';
import { loadPersistedImage } from './workflow/types';
import { createNodeActions } from './workflow/actions-node';
import { createExecutionActions } from './workflow/actions-execution';
import { createUploadActions } from './workflow/actions-upload';
import type { WorkflowState } from './workflow/types';

// Re-export types for consumers
export type { NodeStatus, WorkflowState, WorkflowExecutionResult, WorkflowTemplate, ExecutionMode } from './workflow/types';

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
  abortController: null,
  uploadedImage: persistedImage.uploadedImage,
  uploadedFileName: persistedImage.uploadedFileName,
  uploadedGTFile: null,
  uploadedPricingFile: null,
  executionMode: 'sequential',
  selectedProjectId: null,

  // Actions — composed from domain modules
  ...createUploadActions(set),
  ...createNodeActions(set, get),
  ...createExecutionActions(set, get),
}));
