/**
 * API Status Monitor
 * API 상태 모니터링 대시보드
 */

import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import Toast from '../ui/Toast';
import { RefreshCw, Server, Clock } from 'lucide-react';

import { CATEGORY_ORDER } from './types';
import { ResourcePanel, QuickStats } from './components';
import {
  UnhealthyAPIsAlert,
  CategoryCard,
  GlobalLoadingOverlay,
  useAPIStatusMonitor,
} from './api-status-monitor';

export default function APIStatusMonitor() {
  const {
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
    containerStats,
    gpuStats,
    gpuAvailable,
    apiResources,
    fetchStatus,
    triggerHealthCheck,
    toggleCategory,
    deleteApi,
    getSpecId,
    handleSingleAPIAction,
    handleCategoryAction,
    hideToast,
  } = useAPIStatusMonitor();

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
              onSingleApiAction={handleSingleAPIAction}
              singleApiActionLoading={singleApiActionLoading}
              isGlobalLoading={globalLoading.isLoading}
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

      {/* 전역 로딩 오버레이 */}
      <GlobalLoadingOverlay globalLoading={globalLoading} />

      {/* Toast 알림 */}
      {toast.show && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={toast.type === 'error' ? 15000 : 10000}
          onClose={hideToast}
        />
      )}
    </Card>
  );
}
