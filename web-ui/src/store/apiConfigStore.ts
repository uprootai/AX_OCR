import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface APIConfig {
  id: string;
  name: string;
  displayName: string;
  baseUrl: string;
  port: number;
  icon: string;
  color: string;
  category: 'api' | 'control';
  description: string;
  enabled: boolean;
  // BlueprintFlow 노드 정보
  inputs: {
    name: string;
    type: string;
    description: string;
  }[];
  outputs: {
    name: string;
    type: string;
    description: string;
  }[];
  parameters: {
    name: string;
    type: 'number' | 'string' | 'boolean' | 'select';
    default: any;
    min?: number;
    max?: number;
    step?: number;
    options?: string[];
    description: string;
  }[];
}

interface APIConfigStore {
  customAPIs: APIConfig[];
  addAPI: (config: APIConfig) => void;
  removeAPI: (id: string) => void;
  updateAPI: (id: string, updates: Partial<APIConfig>) => void;
  toggleAPI: (id: string) => void;
  getAPIById: (id: string) => APIConfig | undefined;
  getAllAPIs: () => APIConfig[];
}

export const useAPIConfigStore = create<APIConfigStore>()(
  persist(
    (set, get) => ({
      customAPIs: [],

      addAPI: (config: APIConfig) => {
        set((state) => {
          // 중복 체크
          if (state.customAPIs.find(api => api.id === config.id)) {
            console.error(`API with id "${config.id}" already exists`);
            return state;
          }
          return {
            customAPIs: [...state.customAPIs, config],
          };
        });
      },

      removeAPI: (id: string) => {
        set((state) => ({
          customAPIs: state.customAPIs.filter(api => api.id !== id),
        }));
      },

      updateAPI: (id: string, updates: Partial<APIConfig>) => {
        set((state) => ({
          customAPIs: state.customAPIs.map(api =>
            api.id === id ? { ...api, ...updates } : api
          ),
        }));
      },

      toggleAPI: (id: string) => {
        set((state) => ({
          customAPIs: state.customAPIs.map(api =>
            api.id === id ? { ...api, enabled: !api.enabled } : api
          ),
        }));
      },

      getAPIById: (id: string) => {
        return get().customAPIs.find(api => api.id === id);
      },

      getAllAPIs: () => {
        return get().customAPIs;
      },
    }),
    {
      name: 'custom-apis-storage',
    }
  )
);
