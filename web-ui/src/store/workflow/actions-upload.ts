import type { WorkflowState } from './types';
import { persistImage } from './types';

type ZustandSet = (
  partial: WorkflowState | Partial<WorkflowState> | ((state: WorkflowState) => WorkflowState | Partial<WorkflowState>),
  replace?: false
) => void;

export const createUploadActions = (set: ZustandSet) => ({
  setWorkflowName: (name: string) => set({ workflowName: name }),

  setWorkflowDescription: (description: string) => set({ workflowDescription: description }),

  setUploadedImage: (image: string | null, fileName: string | null = null) => {
    set({ uploadedImage: image, uploadedFileName: fileName });
    persistImage(image, fileName);
  },

  setUploadedGTFile: (file: { name: string; content: string } | null) =>
    set({ uploadedGTFile: file }),

  setUploadedPricingFile: (file: { name: string; content: string } | null) =>
    set({ uploadedPricingFile: file }),

  setSelectedProjectId: (id: string | null) => set({ selectedProjectId: id }),
});
