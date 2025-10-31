import { create } from 'zustand';
import type { ServiceHealth, RequestTrace } from '../types/api';

interface MonitoringState {
  // Service Health
  services: {
    gateway: ServiceHealth | null;
    edocr2_v1: ServiceHealth | null;
    edocr2_v2: ServiceHealth | null;
    edgnet: ServiceHealth | null;
    skinmodel: ServiceHealth | null;
  };

  // Request Traces
  traces: RequestTrace[];
  maxTraces: number;

  // Performance Metrics
  metrics: {
    avgResponseTime: number;
    successRate: number;
    errorRate: number;
  };

  // Actions
  updateServiceHealth: (service: keyof MonitoringState['services'], health: ServiceHealth) => void;
  addTrace: (trace: RequestTrace) => void;
  clearTraces: () => void;
  updateMetrics: () => void;
}

export const useMonitoringStore = create<MonitoringState>((set, get) => ({
  services: {
    gateway: null,
    edocr2_v1: null,
    edocr2_v2: null,
    edgnet: null,
    skinmodel: null,
  },

  traces: [],
  maxTraces: 50,

  metrics: {
    avgResponseTime: 0,
    successRate: 100,
    errorRate: 0,
  },

  updateServiceHealth: (service, health) =>
    set((state) => ({
      services: {
        ...state.services,
        [service]: health,
      },
    })),

  addTrace: (trace) =>
    set((state) => {
      const newTraces = [trace, ...state.traces].slice(0, state.maxTraces);
      return { traces: newTraces };
    }),

  clearTraces: () => set({ traces: [] }),

  updateMetrics: () => {
    const { traces } = get();
    if (traces.length === 0) return;

    const totalTime = traces.reduce((sum, t) => sum + t.duration, 0);
    const successCount = traces.filter((t) => t.status >= 200 && t.status < 300).length;
    const errorCount = traces.filter((t) => t.status >= 400).length;

    set({
      metrics: {
        avgResponseTime: totalTime / traces.length,
        successRate: (successCount / traces.length) * 100,
        errorRate: (errorCount / traces.length) * 100,
      },
    });
  },
}));
