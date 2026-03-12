/**
 * BlueprintFlow Workflow Builder — entry point / barrel
 *
 * Splits:
 *   builder/WorkflowBuilderCanvas.tsx  — main canvas + state orchestration
 *   builder/BuilderToolbar.tsx         — toolbar JSX
 *   builder/ExecutionModeToggle.tsx    — execution mode toggle buttons
 *   builder/types.ts                   — shared ReactFlowNode type
 */

import { ReactFlowProvider } from 'reactflow';
import { WorkflowBuilderCanvas } from './builder/WorkflowBuilderCanvas';

export default function WorkflowBuilderNew() {
  return (
    <ReactFlowProvider>
      <WorkflowBuilderCanvas />
    </ReactFlowProvider>
  );
}
