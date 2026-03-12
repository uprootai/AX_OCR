/**
 * Shared types for the builder subdirectory.
 * Avoids importing directly from reactflow in every file.
 */
import type { Node } from 'reactflow';
import type { WorkflowNodeData } from '../types';

export type ReactFlowNode = Node<WorkflowNodeData>;
