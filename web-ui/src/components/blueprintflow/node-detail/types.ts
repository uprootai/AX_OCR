import type { Node } from 'reactflow';
import type { SelectOption, CheckboxOption } from '../../../config/nodes/types';

export interface NodeDetailPanelProps {
  selectedNode: Node | null;
  onClose: () => void;
  onUpdateNode: (nodeId: string, data: Record<string, unknown>) => void;
  onAddNode?: (nodeType: string) => void;
}

// Helper to check if option is SelectOption object
export const isSelectOption = (opt: string | SelectOption): opt is SelectOption => {
  return typeof opt === 'object' && 'value' in opt;
};

// Helper to check if option is CheckboxOption object
export const isCheckboxOption = (opt: unknown): opt is CheckboxOption => {
  return typeof opt === 'object' && opt !== null && 'value' in opt && 'label' in opt;
};
