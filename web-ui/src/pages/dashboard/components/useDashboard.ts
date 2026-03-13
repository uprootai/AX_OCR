import { useState, useEffect, useCallback } from 'react';
import { useAPIConfigStore } from '../../../store/apiConfigStore';
import { GATEWAY_URL } from '../../../lib/api';
import { projectApi } from '../../../lib/blueprintBomApi';
import { type ToastState, type ProjectWithSessions } from './types';

/**
 * Docker 내부 호스트명을 localhost로 변환
 * 예: http://yolo-api:5005 -> http://localhost:5005
 */
function convertToLocalhost(url: string): string {
  try {
    const parsed = new URL(url);
    // Docker 서비스명 패턴: xxx-api 형태
    if (parsed.hostname.includes('-api') || parsed.hostname.includes('_api')) {
      parsed.hostname = 'localhost';
    }
    return parsed.toString().replace(/\/$/, ''); // 끝의 슬래시 제거
  } catch {
    return url;
  }
}

export function useDashboard() {
  const { addAPI, customAPIs, removeAPI, toggleAPI } = useAPIConfigStore();

  // Toast 알림 상태
  const [toast, setToast] = useState<ToastState>({ show: false, message: '', type: 'info' });

  // Toast 표시 헬퍼 함수
  const showToast = useCallback((message: string, type: ToastState['type'] = 'info') => {
    setToast({ show: true, message, type });
  }, []);

  // 프로젝트 상태
  const [projectData, setProjectData] = useState<ProjectWithSessions[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(false);

  // Auto-discover 상태
  const [isAutoDiscovering, setIsAutoDiscovering] = useState(false);

  // 프로젝트 목록 + 세션 로드
  const fetchProjects = useCallback(async () => {
    setProjectsLoading(true);
    try {
      const result = await projectApi.list(undefined, 100);
      const projectList = result.projects ?? [];
      // 각 프로젝트 상세 (세션 포함) 병렬 로드
      const details = await Promise.all(
        projectList.map(async (p) => {
          try {
            const detail = await projectApi.get(p.project_id);
            return { project: p, sessions: detail.sessions ?? [] };
          } catch {
            return { project: p, sessions: [] };
          }
        })
      );
      setProjectData(details);
    } catch {
      // BOM 서버 연결 실패 시 무시
    } finally {
      setProjectsLoading(false);
    }
  }, []);

  /**
   * Gateway API Registry에서 자동으로 API 검색
   */
  const handleAutoDiscover = useCallback(async () => {
    setIsAutoDiscovering(true);
    try {
      const response = await fetch(`${GATEWAY_URL}/api/v1/registry/list`);
      if (response.ok) {
        const data = await response.json();
        const apis = data.apis || [];

        // 현재 등록된 API 목록을 store에서 직접 가져오기 (stale closure 방지)
        const currentAPIs = useAPIConfigStore.getState().customAPIs;

        let addedCount = 0;
        apis.forEach((apiInfo: {
          id: string;
          name?: string;
          base_url: string;
          display_name?: string;
          category?: string;
          port?: number;
          icon?: string;
          color?: string;
          description?: string;
          status?: string;
          inputs?: Array<{ name: string; type: string }>;
          outputs?: Array<{ name: string; type: string }>;
          parameters?: Array<{ name: string; type: string; default?: string | number | boolean }>;
        }) => {
          // 이미 추가된 API는 건너뛰기
          if (currentAPIs.find(api => api.id === apiInfo.id)) {
            return;
          }

          // Docker 내부 URL을 localhost로 변환
          const browserAccessibleUrl = convertToLocalhost(apiInfo.base_url);

          // APIConfig 형식으로 변환하여 추가
          addAPI({
            id: apiInfo.id,
            name: apiInfo.name || apiInfo.id,
            displayName: apiInfo.display_name || apiInfo.id,
            baseUrl: browserAccessibleUrl,
            port: apiInfo.port || 0,
            icon: apiInfo.icon || '🔧',
            color: apiInfo.color || '#666',
            category: (apiInfo.category || 'ocr') as 'knowledge' | 'input' | 'detection' | 'ocr' | 'segmentation' | 'preprocessing' | 'analysis' | 'ai' | 'control',
            description: apiInfo.description || '',
            enabled: apiInfo.status === 'healthy',
            inputs: (apiInfo.inputs || []).map(i => ({ ...i, description: '' })),
            outputs: (apiInfo.outputs || []).map(o => ({ ...o, description: '' })),
            parameters: (apiInfo.parameters || []).map(p => ({
              name: p.name,
              type: (p.type || 'string') as 'number' | 'string' | 'boolean' | 'select',
              default: p.default ?? '',
              description: '',
            })),
          });
          addedCount++;
        });

        if (addedCount > 0) {
          showToast(`✓ ${addedCount}개의 새 API가 추가되었습니다`, 'success');
        } else {
          showToast('모든 API가 이미 등록되어 있습니다', 'info');
        }
      }
    } catch {
      showToast('✗ API 자동 검색 실패\nGateway API가 실행 중인지 확인하세요', 'error');
    } finally {
      setIsAutoDiscovering(false);
    }
  }, [addAPI, showToast]);

  // 프로젝트 로드
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // 앱 시작 시 자동 검색 (최초 1회만)
  useEffect(() => {
    const hasAutoDiscovered = localStorage.getItem('auto-discovered');
    if (!hasAutoDiscovered) {
      handleAutoDiscover();
      localStorage.setItem('auto-discovered', 'true');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    toast,
    setToast,
    showToast,
    projectData,
    projectsLoading,
    fetchProjects,
    isAutoDiscovering,
    handleAutoDiscover,
    customAPIs,
    removeAPI,
    toggleAPI,
  };
}
