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
  category: 'input' | 'detection' | 'ocr' | 'segmentation' | 'preprocessing' | 'analysis' | 'knowledge' | 'ai' | 'control';
  description: string;
  enabled: boolean;
  // BlueprintFlow 노드 정보
  inputs: {
    name: string;
    type: string;
    description: string;
    required?: boolean;
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
    required?: boolean;
  }[];
  // ✅ 백엔드 연동 정보 추가
  endpoint?: string;           // API 엔드포인트 (예: /api/v1/detect)
  method?: string;             // HTTP 메서드 (POST, GET 등)
  requiresImage?: boolean;     // 이미지 필요 여부
  outputMappings?: Record<string, string>; // 응답 필드 매핑 (예: {"detections": "data.results"})
  inputMappings?: Record<string, string>;  // 입력 필드 매핑 (예: {"prompt": "inputs.text", "style": "parameters.style"})
}

interface APIConfigStore {
  customAPIs: APIConfig[];
  addAPI: (config: APIConfig) => Promise<void>;
  removeAPI: (id: string) => Promise<void>;
  updateAPI: (id: string, updates: Partial<APIConfig>) => Promise<void>;
  toggleAPI: (id: string) => Promise<void>;
  getAPIById: (id: string) => APIConfig | undefined;
  getAllAPIs: () => APIConfig[];
}

export const useAPIConfigStore = create<APIConfigStore>()(
  persist(
    (set, get) => ({
      customAPIs: [],

      addAPI: async (config: APIConfig) => {
        // 중복 체크
        const existing = get().customAPIs.find(api => api.id === config.id);
        if (existing) {
          console.error(`API with id "${config.id}" already exists`);
          return;
        }

        // ✅ 1. localStorage에 저장
        set((state) => ({
          customAPIs: [...state.customAPIs, config],
        }));

        // ✅ 2. 백엔드에 동기화
        try {
          const response = await fetch('http://localhost:8000/api/v1/api-configs', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(config),
          });

          if (!response.ok) {
            console.error('Failed to sync API config to backend:', await response.text());
          } else {
            console.log(`✅ API config synced to backend: ${config.id}`);
          }
        } catch (error) {
          console.error('Failed to sync API config to backend:', error);
          // localStorage는 이미 저장되었으므로 프론트엔드는 동작함
          // 백엔드 동기화 실패는 경고만 표시
        }
      },

      removeAPI: async (id: string) => {
        // ✅ 1. localStorage에서 삭제
        set((state) => ({
          customAPIs: state.customAPIs.filter(api => api.id !== id),
        }));

        // ✅ 2. 백엔드에서 삭제
        try {
          await fetch(`http://localhost:8000/api/v1/api-configs/${id}`, {
            method: 'DELETE',
          });
          console.log(`✅ API config removed from backend: ${id}`);
        } catch (error) {
          console.error('Failed to remove API config from backend:', error);
        }
      },

      updateAPI: async (id: string, updates: Partial<APIConfig>) => {
        // ✅ 1. localStorage 업데이트
        set((state) => ({
          customAPIs: state.customAPIs.map(api =>
            api.id === id ? { ...api, ...updates } : api
          ),
        }));

        // ✅ 2. 백엔드 업데이트
        try {
          await fetch(`http://localhost:8000/api/v1/api-configs/${id}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(updates),
          });
          console.log(`✅ API config updated in backend: ${id}`);
        } catch (error) {
          console.error('Failed to update API config in backend:', error);
        }
      },

      toggleAPI: async (id: string) => {
        // ✅ 1. localStorage 토글
        set((state) => ({
          customAPIs: state.customAPIs.map(api =>
            api.id === id ? { ...api, enabled: !api.enabled } : api
          ),
        }));

        // ✅ 2. 백엔드 토글
        try {
          await fetch(`http://localhost:8000/api/v1/api-configs/${id}/toggle`, {
            method: 'POST',
          });
          console.log(`✅ API config toggled in backend: ${id}`);
        } catch (error) {
          console.error('Failed to toggle API config in backend:', error);
        }
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
