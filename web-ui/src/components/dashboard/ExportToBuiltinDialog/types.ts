import type { APIConfig } from '../../../store/apiConfigStore';

export interface ExportToBuiltinDialogProps {
  isOpen: boolean;
  onClose: () => void;
  apiConfig: APIConfig | null;
}

export type { APIConfig };
