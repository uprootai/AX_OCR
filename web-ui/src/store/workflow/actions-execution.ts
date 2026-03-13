import { getNodeDefinition } from '../../config/nodeDefinitions';
import { GATEWAY_URL } from '../../lib/api';
import type { WorkflowState, WorkflowExecutionResult, ExecutionMode, ParameterRecord, NodeStatus } from './types';
import { getSavedHyperparameters } from './types';

type ZustandSet = (
  partial: WorkflowState | Partial<WorkflowState> | ((state: WorkflowState) => WorkflowState | Partial<WorkflowState>),
  replace?: false
) => void;
type ZustandGet = () => WorkflowState;

// Build the workflow definition payload shared by both execute functions
const buildWorkflowDefinition = (state: WorkflowState) => {
  const { nodes, edges, workflowName } = state;
  return {
    id: `workflow-${Date.now()}`,
    name: workflowName,
    nodes: nodes.map((node) => {
      const nodeDefinition = getNodeDefinition(node.type || '');
      const defaultParams: ParameterRecord = {};

      if (nodeDefinition?.parameters) {
        nodeDefinition.parameters.forEach((param) => {
          defaultParams[param.name] = param.default;
        });
      }

      const savedParams = getSavedHyperparameters(node.type || '');

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
};

export const createExecutionActions = (set: ZustandSet, get: ZustandGet) => ({
  setExecuting: (isExecuting: boolean) => set({ isExecuting }),

  setExecutionResult: (result: WorkflowExecutionResult | null) =>
    set({ executionResult: result, executionError: null }),

  setExecutionError: (error: string | null) =>
    set({ executionError: error, executionResult: null }),

  setExecutionMode: (mode: ExecutionMode) => set({ executionMode: mode }),

  executeWorkflow: async (inputImage: string) => {
    const state = get();
    const { nodes } = state;

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

      const workflowDefinition = buildWorkflowDefinition(get());

      // Prepare request payload (include GT/pricing files if attached)
      const inputs: Record<string, unknown> = {
        image: inputImage, // Base64 encoded image
      };
      const gtFile = get().uploadedGTFile;
      if (gtFile) {
        inputs.gt_file = gtFile;
      }
      const pricingFile = get().uploadedPricingFile;
      if (pricingFile) {
        inputs.pricing_file = pricingFile;
      }

      const requestPayload = {
        workflow: workflowDefinition,
        inputs,
        config: {},
      };

      const response = await fetch(`${GATEWAY_URL}/api/v1/workflow/execute`, {
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
    const state = get();
    const { nodes, executionMode } = state;

    if (nodes.length === 0) {
      set({ executionError: 'Workflow is empty. Add nodes to execute.' });
      return;
    }

    if (!inputImage) {
      set({ executionError: 'Input image is required. Please upload an image first.' });
      return;
    }

    const abortController = new AbortController();

    try {
      set({
        isExecuting: true,
        executionError: null,
        executionResult: null,
        nodeStatuses: {},
        executionId: null,
        abortController,
      });

      const workflowDefinition = buildWorkflowDefinition(get());

      // Prepare request payload (include GT/pricing files if attached)
      const streamInputs: Record<string, unknown> = {
        image: inputImage,
      };
      const streamGtFile = get().uploadedGTFile;
      if (streamGtFile) {
        streamInputs.gt_file = streamGtFile;
      }
      const streamPricingFile = get().uploadedPricingFile;
      if (streamPricingFile) {
        streamInputs.pricing_file = streamPricingFile;
      }
      const selectedProjectId = get().selectedProjectId;
      if (selectedProjectId) {
        streamInputs.project_id = selectedProjectId;
      }

      const requestPayload = {
        workflow: workflowDefinition,
        inputs: streamInputs,
        config: {
          execution_mode: executionMode, // 'sequential' or 'parallel'
        },
      };

      const response = await fetch(`${GATEWAY_URL}/api/v1/workflow/execute-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestPayload),
        signal: abortController.signal,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Response body is not readable');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        // Process complete messages (SSE format: "data: {...}\n\n")
        const messages = buffer.split('\n\n');
        buffer = messages.pop() || '';

        for (const message of messages) {
          if (!message.trim() || !message.startsWith('data: ')) continue;

          try {
            const jsonStr = message.replace('data: ', '');
            const event = JSON.parse(jsonStr);

            switch (event.type) {
              case 'workflow_start':
                set({ executionId: event.execution_id });
                break;

              case 'execution_plan': {
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
                  output: event.output,
                });
                break;

              case 'node_complete':
                get().updateNodeStatus(event.node_id, {
                  nodeId: event.node_id,
                  status: event.status === 'failed' ? 'failed' : 'completed',
                  progress: event.progress || 1.0,
                  error: event.error,
                  output: event.output,
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

              case 'node_heartbeat':
                // 하트비트: 경과 시간 업데이트 (상태는 running 유지)
                get().updateNodeStatus(event.node_id, {
                  nodeId: event.node_id,
                  status: 'running',
                  progress: 0,
                  elapsedSeconds: event.elapsed_seconds,
                  message: event.message,
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
      if (error instanceof Error && error.name === 'AbortError') {
        set({
          isExecuting: false,
          executionError: 'Execution cancelled by user',
          executionResult: null,
          abortController: null,
        });
        return;
      }

      console.error('❌ [SSE] Workflow execution failed:', error);
      set({
        isExecuting: false,
        executionError: error instanceof Error ? error.message : 'Unknown error occurred',
        executionResult: null,
        abortController: null,
      });
    }
  },

  cancelExecution: async () => {
    const { abortController, executionId } = get();
    if (abortController) {
      // 1. 프론트엔드 SSE 연결 취소
      abortController.abort();

      // 2. 백엔드에 취소 요청 (executionId가 있는 경우)
      if (executionId) {
        try {
          const response = await fetch(`${GATEWAY_URL}/api/v1/workflow/cancel/${executionId}`, {
            method: 'POST',
          });
          if (!response.ok) {
            console.warn('⚠️ Backend cancellation failed:', await response.text());
          }
        } catch (error) {
          console.warn('⚠️ Failed to send cancel request to backend:', error);
        }
      }

      set({
        isExecuting: false,
        executionError: 'Execution cancelled by user',
        abortController: null,
      });
    }
  },
});
