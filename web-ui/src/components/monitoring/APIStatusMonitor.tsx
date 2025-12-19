/**
 * API Status Monitor
 * API 상태 모니터링 대시보드
 */

import { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import {
  RefreshCw,
  Server,
  ExternalLink,
  Clock,
  ChevronDown,
  ChevronUp,
  Settings,
  Trash2,
  Square,
  Play,
  AlertCircle,
  Cpu,
  MemoryStick,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { checkAllServicesIncludingCustom } from '../../lib/api';
import { useAPIConfigStore } from '../../store/apiConfigStore';
import { API_TO_CONTAINER, API_TO_SPEC_ID } from '../../config/apiRegistry';

// Local imports
import type { APIInfo, ContainerStats, APIResourceSpec } from './types';
import { CATEGORY_LABELS, CATEGORY_ORDER } from './types';
import { DEFAULT_APIS, DELETED_APIS_KEY } from './constants';
import { useResourceStats } from './hooks';
import { ResourcePanel, QuickStats } from './components';

export default function APIStatusMonitor() {
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
  const { customAPIs } = useAPIConfigStore();

  // Resource stats hook
  const { containerStats, gpuStats, gpuAvailable, apiResources, fetchResourceStats } = useResourceStats();

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

  // Get spec ID from API ID
  const getSpecId = (apiId: string): string => API_TO_SPEC_ID[apiId] || apiId;

  // Handle category action (start/stop all in category)
  const handleCategoryAction = async (category: string, action: 'stop' | 'start') => {
    const categoryAPIs = apis.filter(api => api.category === category && !deletedApis.has(api.id));
    const targetAPIs = action === 'stop'
      ? categoryAPIs.filter(api => api.status === 'healthy')
      : categoryAPIs.filter(api => api.status !== 'healthy');

    if (targetAPIs.length === 0) {
      alert(action === 'stop' ? '중지할 API가 없습니다.' : '시작할 API가 없습니다.');
      return;
    }

    const actionText = action === 'stop' ? '중지' : '시작';
    const dependencyNote = category === 'knowledge' ? '\n\n⚠️ Neo4j 데이터베이스도 함께 ' + actionText + '됩니다.' : '';
    if (!confirm(`${category.toUpperCase()} 카테고리의 ${targetAPIs.length}개 API를 ${actionText}하시겠습니까?\n\n${targetAPIs.map(a => a.display_name).join(', ')}${dependencyNote}`)) {
      return;
    }

    setCategoryActionLoading(category);
    let successCount = 0;
    let failCount = 0;
    const failedAPIs: string[] = [];
    const dependentContainers = category === 'knowledge' ? ['neo4j'] : [];

    // Start dependencies first
    if (action === 'start') {
      for (const depContainer of dependentContainers) {
        try {
          await axios.post(`http://localhost:8000/api/v1/containers/${depContainer}/${action}`, {}, { timeout: 30000 });
        } catch (error) {
          console.warn(`Failed to ${action} dependent container ${depContainer}:`, error);
        }
      }
      if (dependentContainers.length > 0) {
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }

    for (const api of targetAPIs) {
      const containerName = API_TO_CONTAINER[api.id];
      if (!containerName) {
        failCount++;
        failedAPIs.push(`${api.display_name} (매핑 없음)`);
        continue;
      }

      try {
        const response = await axios.post(`http://localhost:8000/api/v1/containers/${containerName}/${action}`, {}, { timeout: 30000 });
        if (response.data?.success === true) {
          successCount++;
        } else {
          failCount++;
          failedAPIs.push(`${api.display_name} (${response.data?.message || '알 수 없는 오류'})`);
        }
      } catch (error) {
        failCount++;
        const errorMsg = error instanceof Error ? error.message : '연결 실패';
        failedAPIs.push(`${api.display_name} (${errorMsg})`);
      }
    }

    // Stop dependencies last
    if (action === 'stop') {
      for (const depContainer of dependentContainers) {
        try {
          await axios.post(`http://localhost:8000/api/v1/containers/${depContainer}/${action}`, {}, { timeout: 30000 });
        } catch (error) {
          console.warn(`Failed to ${action} dependent container ${depContainer}:`, error);
        }
      }
    }

    setCategoryActionLoading(null);
    await fetchStatus(true);

    if (successCount > 0 && failCount > 0) {
      alert(`${actionText} 일부 완료\n\n✓ 성공: ${successCount}개\n✗ 실패: ${failCount}개\n\n실패 목록:\n${failedAPIs.join('\n')}`);
    } else if (successCount === 0 && failCount > 0) {
      alert(`${actionText} 실패\n\n실패 목록:\n${failedAPIs.join('\n')}`);
    }
  };

  // Fetch API status
  const fetchStatus = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setIsRefreshing(true);

    try {
      const healthResults = await checkAllServicesIncludingCustom();

      let registryApis: APIInfo[] = [];
      try {
        const registryResponse = await axios.get('http://localhost:8000/api/v1/registry/list', { timeout: 3000 });
        if (registryResponse.data.apis) {
          registryApis = registryResponse.data.apis as APIInfo[];
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
      await axios.post('http://localhost:8000/api/v1/registry/health-check', {}, { timeout: 10000 });
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

  useEffect(() => {
    fetchStatus();
    fetchResourceStats();
    const interval = setInterval(() => {
      fetchStatus();
      fetchResourceStats();
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus, fetchResourceStats]);

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center gap-2">
            <RefreshCw className="h-5 w-5 animate-spin text-primary" />
            <span className="text-muted-foreground">API 상태 확인 중...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const visibleApis = apis.filter(api => !deletedApis.has(api.id));
  const healthyAPIs = visibleApis.filter(api => api.status === 'healthy');
  const unhealthyAPIs = visibleApis.filter(api => api.status !== 'healthy');
  const categories = [...new Set(visibleApis.map(api => api.category))];

  categories.sort((a, b) => {
    const aIndex = CATEGORY_ORDER.indexOf(a);
    const bIndex = CATEGORY_ORDER.indexOf(b);
    if (aIndex === -1 && bIndex === -1) return a.localeCompare(b);
    if (aIndex === -1) return 1;
    if (bIndex === -1) return -1;
    return aIndex - bIndex;
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            API Health Status
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => fetchStatus(true)} disabled={isRefreshing}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              새로고침
            </Button>
            <Button size="sm" onClick={triggerHealthCheck} disabled={isRefreshing}>
              <Server className="h-4 w-4 mr-2" />
              헬스체크
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Quick Stats */}
        <QuickStats
          totalCount={apis.length}
          healthyCount={healthyAPIs.length}
          unhealthyCount={unhealthyAPIs.length}
          categoryCount={categories.length}
        />

        {/* Resource Usage Panel */}
        <ResourcePanel
          gpuAvailable={gpuAvailable}
          gpuStats={gpuStats}
          containerStats={containerStats}
          apis={apis}
        />

        {/* Unhealthy APIs Alert */}
        {unhealthyAPIs.length > 0 && (
          <UnhealthyAPIsAlert unhealthyAPIs={unhealthyAPIs} />
        )}

        {/* APIs by Category */}
        <div className="space-y-3">
          {categories.map(category => (
            <CategoryCard
              key={category}
              category={category}
              apis={visibleApis.filter(api => api.category === category)}
              isExpanded={expandedCategories.has(category)}
              onToggle={() => toggleCategory(category)}
              onCategoryAction={handleCategoryAction}
              categoryActionLoading={categoryActionLoading}
              containerStats={containerStats}
              apiResources={apiResources}
              getSpecId={getSpecId}
              onDeleteApi={deleteApi}
            />
          ))}
        </div>

        {/* Last Updated */}
        {lastUpdate && (
          <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground pt-2 border-t">
            <Clock className="h-3 w-3" />
            <span>마지막 업데이트: {lastUpdate.toLocaleTimeString('ko-KR')}</span>
            <span className="text-muted-foreground/50">• 30초마다 자동 갱신</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Unhealthy APIs Alert component
function UnhealthyAPIsAlert({ unhealthyAPIs }: { unhealthyAPIs: APIInfo[] }) {
  return (
    <div className="p-4 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg">
      <div className="flex items-center gap-2 mb-3">
        <AlertCircle className="h-5 w-5 text-red-500" />
        <span className="font-semibold text-red-700 dark:text-red-300">
          연결 실패 API ({unhealthyAPIs.length}개)
        </span>
      </div>
      <div className="grid md:grid-cols-2 gap-2">
        {unhealthyAPIs.map(api => (
          <div
            key={api.id}
            className="flex items-center justify-between p-2 bg-white dark:bg-gray-900 rounded border border-red-200 dark:border-red-800"
          >
            <div className="flex items-center gap-2">
              <span>{api.icon}</span>
              <span className="font-medium text-sm">{api.display_name}</span>
            </div>
            <span className="text-xs text-red-600">:{api.port}</span>
          </div>
        ))}
      </div>
      <p className="mt-3 text-xs text-muted-foreground">
        Docker 컨테이너 확인: <code className="bg-muted px-1 rounded">docker-compose ps</code>
      </p>
    </div>
  );
}

// Category Card component
function CategoryCard({
  category,
  apis,
  isExpanded,
  onToggle,
  onCategoryAction,
  categoryActionLoading,
  containerStats,
  apiResources,
  getSpecId,
  onDeleteApi,
}: {
  category: string;
  apis: APIInfo[];
  isExpanded: boolean;
  onToggle: () => void;
  onCategoryAction: (category: string, action: 'stop' | 'start') => void;
  categoryActionLoading: string | null;
  containerStats: Record<string, ContainerStats>;
  apiResources: Record<string, APIResourceSpec>;
  getSpecId: (apiId: string) => string;
  onDeleteApi: (apiId: string) => void;
}) {
  const categoryHealthy = apis.filter(api => api.status === 'healthy').length;

  return (
    <div className="border rounded-lg overflow-hidden">
      {/* Category Header */}
      <div className="flex items-center justify-between p-3 bg-muted/30">
        <button onClick={onToggle} className="flex items-center gap-2 hover:opacity-70 transition-opacity">
          <span className="font-semibold">{CATEGORY_LABELS[category] || category}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${
            categoryHealthy === apis.length
              ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
              : categoryHealthy > 0
              ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
              : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
          }`}>
            {categoryHealthy}/{apis.length}
          </span>
          {isExpanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </button>

        {/* Category Actions */}
        <div className="flex items-center gap-1">
          {categoryHealthy > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => { e.stopPropagation(); onCategoryAction(category, 'stop'); }}
              disabled={categoryActionLoading === category}
              className="h-7 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              {categoryActionLoading === category ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Square className="h-3.5 w-3.5" />}
              <span className="ml-1 text-xs">Stop All</span>
            </Button>
          )}
          {categoryHealthy < apis.length && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => { e.stopPropagation(); onCategoryAction(category, 'start'); }}
              disabled={categoryActionLoading === category}
              className="h-7 px-2 text-green-600 hover:text-green-700 hover:bg-green-50"
            >
              {categoryActionLoading === category ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
              <span className="ml-1 text-xs">Start All</span>
            </Button>
          )}
        </div>
      </div>

      {/* Category Content */}
      {isExpanded && (
        <div className="p-3 grid md:grid-cols-2 lg:grid-cols-3 gap-3">
          {apis.map(api => (
            <APICard
              key={api.id}
              api={api}
              containerStats={containerStats[api.id]}
              resourceSpec={apiResources[getSpecId(api.id)]}
              onDelete={() => onDeleteApi(api.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// API Card component
function APICard({
  api,
  containerStats,
  resourceSpec,
  onDelete,
}: {
  api: APIInfo;
  containerStats?: ContainerStats;
  resourceSpec?: APIResourceSpec;
  onDelete: () => void;
}) {
  return (
    <div className={`p-3 rounded-lg border-2 transition-all ${
      api.status === 'healthy'
        ? 'border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-950/50'
        : 'border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-950/50'
    }`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="w-7 h-7 rounded flex items-center justify-center text-sm" style={{ backgroundColor: api.color + '25' }}>
            {api.icon}
          </span>
          <div>
            <h4 className="font-medium text-sm leading-tight">{api.display_name}</h4>
            <code className="text-[10px] text-muted-foreground">{api.id}</code>
          </div>
        </div>
        <span className={`px-1.5 py-0.5 text-[10px] font-semibold rounded ${
          api.status === 'healthy' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
        }`}>
          {api.status === 'healthy' ? 'OK' : 'ERR'}
        </span>
      </div>

      <p className="text-xs text-muted-foreground mb-2 line-clamp-1">{api.description}</p>

      {/* Resource Usage */}
      <div className="mb-2 space-y-1">
        {api.status === 'healthy' && containerStats && (
          <div className="flex items-center gap-2 text-[10px] text-blue-600 dark:text-blue-400">
            {containerStats.memory_usage && (
              <span className="flex items-center gap-0.5">
                <MemoryStick className="h-2.5 w-2.5" />
                {containerStats.memory_usage}
              </span>
            )}
            {containerStats.cpu_percent !== null && (
              <span className="flex items-center gap-0.5">
                <Cpu className="h-2.5 w-2.5" />
                {containerStats.cpu_percent?.toFixed(1)}%
              </span>
            )}
          </div>
        )}

        {resourceSpec && (
          <div className="space-y-1">
            <div className="flex flex-wrap gap-1 text-[9px]">
              {resourceSpec.gpu && (
                <span className={`px-1.5 py-0.5 rounded cursor-help ${
                  resourceSpec.gpu.vram === 'N/A'
                    ? 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
                    : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                }`} title={resourceSpec.gpu.recommended || ''}>
                  🎮 {resourceSpec.gpu.vram || '-'}
                </span>
              )}
              {resourceSpec.cpu && (
                <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 rounded cursor-help"
                  title={resourceSpec.cpu.note || ''}>
                  💻 {resourceSpec.cpu.ram || '?'}/{resourceSpec.cpu.cores || '?'}c
                </span>
              )}
            </div>
            {resourceSpec.parameterImpact && resourceSpec.parameterImpact.length > 0 && (
              <div className="text-[8px] text-amber-600 dark:text-amber-400 truncate"
                title={resourceSpec.parameterImpact.map(p => `${p.parameter}: ${p.impact}`).join('\n')}>
                ⚠️ {resourceSpec.parameterImpact[0].impact}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between text-[10px]">
        <span className="text-muted-foreground">:{api.port}</span>
        <div className="flex items-center gap-2">
          <a href={`http://localhost:${api.port}/docs`} target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-0.5 text-primary hover:underline" onClick={(e) => e.stopPropagation()}>
            <ExternalLink className="h-2.5 w-2.5" />
            Swagger
          </a>
          <Link to={`/admin/api/${api.id}`} className="flex items-center gap-0.5 text-muted-foreground hover:text-primary"
            onClick={(e) => e.stopPropagation()}>
            <Settings className="h-2.5 w-2.5" />
            설정
          </Link>
          <button onClick={(e) => { e.stopPropagation(); onDelete(); }}
            className="flex items-center gap-0.5 text-muted-foreground hover:text-destructive" title="목록에서 삭제">
            <Trash2 className="h-2.5 w-2.5" />
            삭제
          </button>
        </div>
      </div>
    </div>
  );
}
