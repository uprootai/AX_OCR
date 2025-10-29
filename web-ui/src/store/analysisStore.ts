import { create } from 'zustand';
import type { AnalysisResult, AnalysisOptions } from '../types/api';

interface AnalysisState {
  // Current Analysis
  currentFile: File | null;
  currentFilePreview: string | null;
  options: AnalysisOptions;
  status: 'idle' | 'uploading' | 'analyzing' | 'complete' | 'error';
  progress: number;
  result: AnalysisResult | null;
  error: string | null;

  // Actions
  setFile: (file: File | null) => void;
  setFilePreview: (preview: string | null) => void;
  setOptions: (options: Partial<AnalysisOptions>) => void;
  setStatus: (status: AnalysisState['status']) => void;
  setProgress: (progress: number) => void;
  setResult: (result: AnalysisResult | null) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const defaultOptions: AnalysisOptions = {
  ocr: true,
  segmentation: true,
  tolerance: true,
  visualize: true,
};

export const useAnalysisStore = create<AnalysisState>((set) => ({
  currentFile: null,
  currentFilePreview: null,
  options: defaultOptions,
  status: 'idle',
  progress: 0,
  result: null,
  error: null,

  setFile: (file) => set({ currentFile: file }),

  setFilePreview: (preview) => set({ currentFilePreview: preview }),

  setOptions: (options) =>
    set((state) => ({
      options: { ...state.options, ...options },
    })),

  setStatus: (status) => set({ status }),

  setProgress: (progress) => set({ progress }),

  setResult: (result) => set({ result, status: 'complete' }),

  setError: (error) => set({ error, status: 'error' }),

  reset: () =>
    set({
      currentFile: null,
      currentFilePreview: null,
      options: defaultOptions,
      status: 'idle',
      progress: 0,
      result: null,
      error: null,
    }),
}));
