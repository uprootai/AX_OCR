export interface AddAPIDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export type APICategory =
  | 'input'
  | 'detection'
  | 'ocr'
  | 'segmentation'
  | 'preprocessing'
  | 'analysis'
  | 'knowledge'
  | 'ai'
  | 'control';

export interface FormData {
  id: string;
  name: string;
  displayName: string;
  baseUrl: string;
  port: number;
  icon: string;
  color: string;
  category: APICategory;
  description: string;
  enabled: boolean;
}

export interface APIMetadata {
  inputs: Array<{ name: string; type: string; required?: boolean; description?: string }>;
  outputs: Array<{ name: string; type: string; description?: string }>;
  parameters: Array<{ name: string; type: string; default?: string | number | boolean }>;
  outputMappings?: Record<string, string>;
  inputMappings?: Record<string, string>;
  endpoint?: string;
  method?: string;
  requiresImage?: boolean;
}

export const ICON_OPTIONS = ['🎯', '📝', '🎨', '📐', '🌏', '🏷️', '📊', '🔍', '⚡', '🔮', '🚀', '💡'];

export const COLOR_OPTIONS = [
  '#10b981', // green
  '#3b82f6', // blue
  '#8b5cf6', // purple
  '#f59e0b', // amber
  '#06b6d4', // cyan
  '#ec4899', // pink
  '#ef4444', // red
  '#a855f7', // violet
  '#14b8a6', // teal
  '#f97316', // orange
];

export const DEFAULT_FORM_DATA: FormData = {
  id: '',
  name: '',
  displayName: '',
  baseUrl: '',
  port: 5007,
  icon: '🏷️',
  color: '#a855f7',
  category: 'ocr',
  description: '',
  enabled: true,
};
