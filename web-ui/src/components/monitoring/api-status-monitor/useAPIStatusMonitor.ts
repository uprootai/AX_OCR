/**
 * useAPIStatusMonitor — API 상태 모니터링 비즈니스 로직 훅
 */

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { checkAllServicesIncludingCustom, GATEWAY_URL } from '../../../lib/api';
import { useAPIConfigStore } from '../../../store/apiConfigStore';
import { API_TO_CONTAINER, API_TO_SPEC_ID } from '../../../config/apiRegistry';
import type { APIInfo } from '../types';
import { CATEGORY_LABELS } from '../types';
import { DEFAULT_APIS, DELETED_APIS_KEY } from '../constants';
import { useResourceStats } from '../hooks';
import type { ToastState, LoadingState } from './types';

export function useAPIStatusMonitor() {
  const [apis, setApis] = useState<APIInfo[]>(DEFAULT_APIS);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [deletedApis, setDeletedApis] = useState<Set<string>>(() => {
    const stored = localStorage.getItem(DELETED_APIS_KEY);
    return stored ? new Set(JSON.parse(stored)) : new Set();
  });
  const [categoryActionLoading, setCategoryActionLoading] = useState<string | null>(null);
  const [singleApiActionLoading, setSingleApiActionLoading] = useState<string | null>(null);
  const { customAPIs } = useAPIConfigStore();

  const [toast, setToast] = useState<ToastState>({ show: false, message: '', type: 'info' });
  const [globalLoading, setGlobalLoading] = useState<LoadingState>({
    isLoading: false,
    action: null,
    target: '',
    progress: null,
  });

  const showToast = (message: string, type: ToastState['type'] = 'info') => {
    setToast({ show: true, message, type });
  };

  const hideToast = () => setToast(prev => ({ ...prev, show: false }));

  const resourceStats = useResourceStats();

  // Delete API from list
  const deleteApi = (apiId: string) => {
    if (!confirm('이 API를 목록에서 삭제하시겠습니까?\n(API 자동 검색으로 다시 추가할 수 있습니다)')) {
      return;
    }
    setDeletedApis(prev => {
      const newSet = new Set(prev);
      newSet.add(apiId);
      localStorage.setItem(DELETED_APIS_KEY, JSON.stringify([...newSet]));
      return newSet;
    });
  };

  const getSpecId = (apiId: string): string => API_TO_SPEC_ID[apiId] || apiId;

  // Fetch API status
  const fetchStatus = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setIsRefreshing(true);

    try {
      const healthResults = await checkAllServicesIncludingCustom();

      let registryApis: APIInfo[] = [];
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);
        const registryResponse = await fetch(`${GATEWAY_URL}/api/v1/registry/list`, {
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        if (registryResponse.ok) {
          const data = await registryResponse.json();
          if (data.apis) {
            registryApis = data.apis as APIInfo[];
          }
        }
      } catch {
        // Gateway 실패해도 계속 진행
      }

      const updatedApis = DEFAULT_APIS.map(api => {
        const registryApi = registryApis.find(r => r.id === api.id || r.name === api.id);
        return {
          ...api,
          display_name: registryApi?.display_name || api.display_name,
          description: registryApi?.description || api.description,
          icon: registryApi?.icon || api.icon,
          color: registryApi?.color || api.color,
          status: healthResults[api.id] ? 'healthy' as const : 'unhealthy' as const,
          last_check: new Date().toISOString(),
        };
      });

      const defaultPorts = DEFAULT_APIS.map(api => api.port);
      const additionalApis = registryApis
        .filter(api => !defaultPorts.includes(api.port))
        .map(api => ({
          ...api,
          status: api.status === 'healthy' ? 'healthy' as const : 'unhealthy' as const,
        }));

      const customApiInfos: APIInfo[] = customAPIs.map(customApi => ({
        id: customApi.id,
        name: customApi.name,
        display_name: customApi.displayName,
        base_url: customApi.baseUrl,
        port: customApi.port,
        status: healthResults[customApi.id] ? 'healthy' as const : 'unhealthy' as const,
        category: customApi.category,
        description: customApi.description || '',
        icon: customApi.icon,
        color: customApi.color,
        last_check: new Date().toISOString(),
      }));

      const combinedApis = [...updatedApis, ...additionalApis, ...customApiInfos];
      const seenPorts = new Set<number>();
      const allApis = combinedApis.filter(api => {
        if (seenPorts.has(api.port)) return false;
        seenPorts.add(api.port);
        return true;
      });

      setApis(allApis);
      setLastUpdate(new Date());

      if (expandedCategories.size === 0) {
        const categories = [...new Set(allApis.map(api => api.category))];
        setExpandedCategories(new Set(categories));
      }
    } catch (err) {
      console.error('Health check failed:', err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [expandedCategories.size, customAPIs]);

  const triggerHealthCheck = async () => {
    setIsRefreshing(true);
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);
      await fetch(`${GATEWAY_URL}/api/v1/registry/health-check`, {
        method: 'POST',
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
    } catch {
      // 무시
    }
    await fetchStatus();
  };

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(category)) {
        newSet.delete(category);
      } else {
        newSet.add(category);
      }
      return newSet;
    });
  };

  // Handle single API action (start/stop one API)
  const handleSingleAPIAction = async (api: APIInfo, action: 'stop' | 'start') => {
    const containerName = API_TO_CONTAINER[api.id];
    if (!containerName) {
      showToast(`${api.display_name}: 컨테이너 매핑을 찾을 수 없습니다`, 'error');
      return;
    }

    const actionText = action === 'stop' ? '중지' : '시작';
    setSingleApiActionLoading(api.id);
    setGlobalLoading({ isLoading: true, action, target: api.display_name, progress: null });

    try {
      const response = await axios.post(
        `${GATEWAY_URL}/api/v1/containers/${containerName}/${action}`,
        {},
        { timeout: 30000 }
      );

      if (response.data?.success === true) {
        showToast(`✓ ${api.display_name} ${actionText} 완료`, 'success');
      } else {
        const errorDetail = response.data?.message || response.data?.error || '알 수 없는 오류';
        showToast(`✗ ${api.display_name} ${actionText} 실패\n${errorDetail}`, 'error');
      }
    } catch (error) {
      let errorMsg = '연결 실패';
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNABORTED') {
          errorMsg = '시간 초과 (30초)';
        } else if (error.response) {
          errorMsg = `HTTP ${error.response.status}: ${error.response.data?.detail || error.response.statusText}`;
        } else if (error.request) {
          errorMsg = '서버 응답 없음 - Gateway API가 실행 중인지 확인하세요';
        }
      } else if (error instanceof Error) {
        errorMsg = error.message;
      }
      showToast(`✗ ${api.display_name} ${actionText} 실패\n${errorMsg}`, 'error');
    } finally {
      setSingleApiActionLoading(null);
      setGlobalLoading({ isLoading: false, action: null, target: '', progress: null });
      await fetchStatus(true);
    }
  };

  // Handle category action (start/stop all in category)
  const handleCategoryAction = async (category: string, action: 'stop' | 'start') => {
    const categoryAPIs = apis.filter(api => api.category === category && !deletedApis.has(api.id));
    const targetAPIs = action === 'stop'
      ? categoryAPIs.filter(api => api.status === 'healthy')
      : categoryAPIs.filter(api => api.status !== 'healthy');

    if (targetAPIs.length === 0) {
      showToast(action === 'stop' ? '중지할 API가 없습니다.' : '시작할 API가 없습니다.', 'warning');
      return;
    }

    const actionText = action === 'stop' ? '중지' : '시작';
    setCategoryActionLoading(category);
    setGlobalLoading({
      isLoading: true,
      action,
      target: `${CATEGORY_LABELS[category] || category} 카테고리`,
      progress: { current: 0, total: targetAPIs.length },
    });

    let successCount = 0;
    let failCount = 0;
    const failedAPIs: string[] = [];
    const dependentContainers = category === 'knowledge' ? ['neo4j'] : [];

    if (action === 'start') {
      for (const depContainer of dependentContainers) {
        try {
          await axios.post(`${GATEWAY_URL}/api/v1/containers/${depContainer}/${action}`, {}, { timeout: 30000 });
        } catch (error) {
          console.warn(`Failed to ${action} dependent container ${depContainer}:`, error);
        }
      }
      if (dependentContainers.length > 0) {
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }

    for (let i = 0; i < targetAPIs.length; i++) {
      const api = targetAPIs[i];
      setGlobalLoading(prev => ({
        ...prev,
        progress: { current: i + 1, total: targetAPIs.length },
      }));

      const containerName = API_TO_CONTAINER[api.id];
      if (!containerName) {
        failCount++;
        failedAPIs.push(`${api.display_name} (매핑 없음)`);
        continue;
      }

      try {
        const response = await axios.post(
          `${GATEWAY_URL}/api/v1/containers/${containerName}/${action}`,
          {},
          { timeout: 30000 }
        );
        if (response.data?.success === true) {
          successCount++;
        } else {
          failCount++;
          failedAPIs.push(`${api.display_name} (${response.data?.message || '알 수 없는 오류'})`);
        }
      } catch (error) {
        failCount++;
        let errorMsg = '연결 실패';
        if (axios.isAxiosError(error)) {
          if (error.code === 'ECONNABORTED') {
            errorMsg = '시간 초과';
          } else if (error.response) {
            errorMsg = `HTTP ${error.response.status}`;
          }
        } else if (error instanceof Error) {
          errorMsg = error.message;
        }
        failedAPIs.push(`${api.display_name} (${errorMsg})`);
      }
    }

    if (action === 'stop') {
      for (const depContainer of dependentContainers) {
        try {
          await axios.post(`${GATEWAY_URL}/api/v1/containers/${depContainer}/${action}`, {}, { timeout: 30000 });
        } catch (error) {
          console.warn(`Failed to ${action} dependent container ${depContainer}:`, error);
        }
      }
    }

    setCategoryActionLoading(null);
    setGlobalLoading({ isLoading: false, action: null, target: '', progress: null });
    await fetchStatus(true);

    if (successCount > 0 && failCount === 0) {
      showToast(`✓ ${successCount}개 API ${actionText} 완료`, 'success');
    } else if (successCount > 0 && failCount > 0) {
      showToast(`${actionText} 일부 완료\n✓ 성공: ${successCount}개\n✗ 실패: ${failCount}개\n\n${failedAPIs.join('\n')}`, 'warning');
    } else if (successCount === 0 && failCount > 0) {
      showToast(`${actionText} 실패\n\n${failedAPIs.join('\n')}`, 'error');
    }
  };

  useEffect(() => {
    fetchStatus();
    resourceStats.fetchResourceStats();
    const interval = setInterval(() => {
      fetchStatus();
      resourceStats.fetchResourceStats();
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus, resourceStats.fetchResourceStats]);

  return {
    // State
    apis,
    loading,
    isRefreshing,
    lastUpdate,
    expandedCategories,
    deletedApis,
    categoryActionLoading,
    singleApiActionLoading,
    toast,
    globalLoading,
    // Resource stats
    ...resourceStats,
    // Actions
    fetchStatus,
    triggerHealthCheck,
    toggleCategory,
    deleteApi,
    getSpecId,
    handleSingleAPIAction,
    handleCategoryAction,
    hideToast,
  };
}
