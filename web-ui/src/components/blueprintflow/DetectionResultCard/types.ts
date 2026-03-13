import type { NodeStatus } from '../../../store/workflowStore';

export interface DetectionResultCardProps {
  nodeStatus: NodeStatus;
  uploadedImage: string | null;
  uploadedFileName: string | null;
}

export interface MetricCardProps {
  label: string;
  value: number;
  color: string;
}

export interface FilterCheckboxProps {
  label: string;
  icon: string;
  count: number;
  checked: boolean;
  onChange: (checked: boolean) => void;
  color: string;
}
