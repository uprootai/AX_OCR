import { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import {
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Server,
  ExternalLink,
  Clock,
  ChevronDown,
  ChevronUp,
  Settings
} from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { checkAllServicesIncludingCustom } from '../../lib/api';
import { useAPIConfigStore } from '../../store/apiConfigStore';

interface APIInfo {
  id: string;
  name: string;
  display_name: string;
  base_url: string;
  port: number;
  status: 'healthy' | 'unhealthy' | 'unknown';
  category: string;
  description: string;
  icon: string;
  color: string;
  last_check: string | null;
}

// 기본 API 정의 (실제 Docker 컨테이너 기준)
const DEFAULT_APIS: APIInfo[] = [
  // Orchestrator
  { id: 'gateway', name: 'gateway', display_name: 'Gateway API', base_url: 'http://localhost:8000', port: 8000, status: 'unknown', category: 'orchestrator', description: 'API Gateway & Orchestrator', icon: '🚀', color: '#6366f1', last_check: null },
  // Detection
  { id: 'yolo', name: 'yolo', display_name: 'YOLOv11', base_url: 'http://localhost:5005', port: 5005, status: 'unknown', category: 'detection', description: '14가지 도면 심볼 검출', icon: '🎯', color: '#ef4444', last_check: null },
  // OCR
  { id: 'edocr2_v1', name: 'edocr2_v1', display_name: 'eDOCr v1 (Fast)', base_url: 'http://localhost:5001', port: 5001, status: 'unknown', category: 'ocr', description: '빠른 OCR 처리', icon: '📝', color: '#3b82f6', last_check: null },
  { id: 'edocr2_v2', name: 'edocr2_v2', display_name: 'eDOCr v2 (Advanced)', base_url: 'http://localhost:5002', port: 5002, status: 'unknown', category: 'ocr', description: '고급 한국어 치수 인식', icon: '📐', color: '#3b82f6', last_check: null },
  { id: 'paddleocr', name: 'paddleocr', display_name: 'PaddleOCR', base_url: 'http://localhost:5006', port: 5006, status: 'unknown', category: 'ocr', description: '다국어 OCR', icon: '🔤', color: '#3b82f6', last_check: null },
  { id: 'surya_ocr', name: 'surya_ocr', display_name: 'Surya OCR', base_url: 'http://localhost:5013', port: 5013, status: 'unknown', category: 'ocr', description: '90+ 언어, 레이아웃 분석', icon: '🌞', color: '#3b82f6', last_check: null },
  { id: 'doctr', name: 'doctr', display_name: 'DocTR', base_url: 'http://localhost:5014', port: 5014, status: 'unknown', category: 'ocr', description: '2단계 파이프라인 OCR', icon: '📑', color: '#3b82f6', last_check: null },
  { id: 'easyocr', name: 'easyocr', display_name: 'EasyOCR', base_url: 'http://localhost:5015', port: 5015, status: 'unknown', category: 'ocr', description: '80+ 언어, CPU 친화적', icon: '👁️', color: '#3b82f6', last_check: null },
  // Segmentation
  { id: 'edgnet', name: 'edgnet', display_name: 'EDGNet', base_url: 'http://localhost:5012', port: 5012, status: 'unknown', category: 'segmentation', description: '엣지 기반 세그멘테이션', icon: '🔲', color: '#22c55e', last_check: null },
  // Analysis
  { id: 'skinmodel', name: 'skinmodel', display_name: 'SkinModel', base_url: 'http://localhost:5003', port: 5003, status: 'unknown', category: 'analysis', description: '공차 분석 & 제조성 예측', icon: '📊', color: '#8b5cf6', last_check: null },
  // AI
  { id: 'vl', name: 'vl', display_name: 'VL (Vision-Language)', base_url: 'http://localhost:5004', port: 5004, status: 'unknown', category: 'ai', description: 'Vision-Language 멀티모달', icon: '🤖', color: '#06b6d4', last_check: null },
];

export default function APIStatusMonitor() {
  const [apis, setApis] = useState<APIInfo[]>(DEFAULT_APIS);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const { customAPIs } = useAPIConfigStore();

  const fetchStatus = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setIsRefreshing(true);

    // 직접 각 서비스에 헬스체크 (확실한 방식)
    try {
      const healthResults = await checkAllServicesIncludingCustom();

      // Gateway API에서 추가 정보 가져오기 시도 (병합용)
      let registryApis: APIInfo[] = [];
      try {
        const registryResponse = await axios.get('http://localhost:8000/api/v1/registry/list', { timeout: 3000 });
        if (registryResponse.data.apis) {
          registryApis = registryResponse.data.apis as APIInfo[];
        }
      } catch {
        // Gateway 실패해도 계속 진행
      }

      // 기본 API 목록 업데이트
      const updatedApis = DEFAULT_APIS.map(api => {
        // Registry에서 해당 API 찾기 (추가 정보용)
        const registryApi = registryApis.find(r => r.id === api.id || r.name === api.id);

        return {
          ...api,
          // Registry 정보가 있으면 일부 필드 업데이트
          display_name: registryApi?.display_name || api.display_name,
          description: registryApi?.description || api.description,
          icon: registryApi?.icon || api.icon,
          color: registryApi?.color || api.color,
          // 헬스체크 결과로 상태 결정
          status: healthResults[api.id] ? 'healthy' as const : 'unhealthy' as const,
          last_check: new Date().toISOString(),
        };
      });

      // Registry에만 있고 DEFAULT_APIS에 없는 API 추가 (포트 번호로 중복 체크)
      const defaultPorts = DEFAULT_APIS.map(api => api.port);
      const additionalApis = registryApis
        .filter(api => !defaultPorts.includes(api.port))
        .map(api => ({
          ...api,
          status: api.status === 'healthy' ? 'healthy' as const : 'unhealthy' as const,
        }));

      // 커스텀 API 추가
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

      // 모든 API 합친 후 포트 번호로 중복 제거 (첫 번째 것 유지)
      const combinedApis = [...updatedApis, ...additionalApis, ...customApiInfos];
      const seenPorts = new Set<number>();
      const allApis = combinedApis.filter(api => {
        if (seenPorts.has(api.port)) {
          return false;
        }
        seenPorts.add(api.port);
        return true;
      });
      setApis(allApis);
      setLastUpdate(new Date());

      // 처음 로드 시 모든 카테고리 펼치기
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
      // 무시 - 직접 체크로 대체됨
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
    const interval = setInterval(() => fetchStatus(), 30000); // 30초마다 자동 갱신
    return () => clearInterval(interval);
  }, [fetchStatus]);

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

  const healthyAPIs = apis.filter(api => api.status === 'healthy');
  const unhealthyAPIs = apis.filter(api => api.status !== 'healthy');
  const categories = [...new Set(apis.map(api => api.category))];

  // 카테고리별 정렬 순서
  const categoryOrder = ['orchestrator', 'detection', 'ocr', 'segmentation', 'preprocessing', 'analysis', 'knowledge', 'ai'];
  categories.sort((a, b) => {
    const aIndex = categoryOrder.indexOf(a);
    const bIndex = categoryOrder.indexOf(b);
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
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchStatus(true)}
              disabled={isRefreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              새로고침
            </Button>
            <Button
              size="sm"
              onClick={triggerHealthCheck}
              disabled={isRefreshing}
            >
              <Server className="h-4 w-4 mr-2" />
              헬스체크
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3 bg-muted/50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">전체</span>
              <Server className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className="text-2xl font-bold">{apis.length}</p>
          </div>
          <div className="p-3 bg-green-50 dark:bg-green-950 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm text-green-600 dark:text-green-400">정상</span>
              <CheckCircle className="h-4 w-4 text-green-500" />
            </div>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">{healthyAPIs.length}</p>
          </div>
          <div className="p-3 bg-red-50 dark:bg-red-950 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm text-red-600 dark:text-red-400">오류</span>
              <AlertCircle className="h-4 w-4 text-red-500" />
            </div>
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">{unhealthyAPIs.length}</p>
          </div>
          <div className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm text-blue-600 dark:text-blue-400">가동률</span>
              <span className="text-xs text-blue-500">{categories.length} 카테고리</span>
            </div>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {apis.length > 0 ? Math.round((healthyAPIs.length / apis.length) * 100) : 0}%
            </p>
          </div>
        </div>

        {/* Unhealthy APIs Alert */}
        {unhealthyAPIs.length > 0 && (
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
        )}

        {/* APIs by Category */}
        <div className="space-y-3">
          {categories.map(category => {
            const categoryAPIs = apis.filter(api => api.category === category);
            const categoryHealthy = categoryAPIs.filter(api => api.status === 'healthy').length;
            const isExpanded = expandedCategories.has(category);

            // 카테고리 라벨
            const categoryLabels: Record<string, string> = {
              orchestrator: 'Orchestrator',
              detection: 'Detection',
              ocr: 'OCR',
              segmentation: 'Segmentation',
              preprocessing: 'Preprocessing',
              analysis: 'Analysis',
              knowledge: 'Knowledge',
              ai: 'AI',
            };

            return (
              <div key={category} className="border rounded-lg overflow-hidden">
                {/* Category Header */}
                <button
                  onClick={() => toggleCategory(category)}
                  className="w-full flex items-center justify-between p-3 bg-muted/30 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{categoryLabels[category] || category}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      categoryHealthy === categoryAPIs.length
                        ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                        : categoryHealthy > 0
                        ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                        : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                    }`}>
                      {categoryHealthy}/{categoryAPIs.length}
                    </span>
                  </div>
                  {isExpanded ? (
                    <ChevronUp className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  )}
                </button>

                {/* Category Content */}
                {isExpanded && (
                  <div className="p-3 grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {categoryAPIs.map(api => (
                      <div
                        key={api.id}
                        className={`p-3 rounded-lg border-2 transition-all ${
                          api.status === 'healthy'
                            ? 'border-green-200 bg-green-50/50 dark:border-green-800 dark:bg-green-950/50'
                            : 'border-red-200 bg-red-50/50 dark:border-red-800 dark:bg-red-950/50'
                        }`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span
                              className="w-7 h-7 rounded flex items-center justify-center text-sm"
                              style={{ backgroundColor: api.color + '25' }}
                            >
                              {api.icon}
                            </span>
                            <div>
                              <h4 className="font-medium text-sm leading-tight">{api.display_name}</h4>
                              <code className="text-[10px] text-muted-foreground">{api.id}</code>
                            </div>
                          </div>
                          <span
                            className={`px-1.5 py-0.5 text-[10px] font-semibold rounded ${
                              api.status === 'healthy'
                                ? 'bg-green-600 text-white'
                                : 'bg-red-600 text-white'
                            }`}
                          >
                            {api.status === 'healthy' ? 'OK' : 'ERR'}
                          </span>
                        </div>

                        <p className="text-xs text-muted-foreground mb-2 line-clamp-1">
                          {api.description}
                        </p>

                        <div className="flex items-center justify-between text-[10px]">
                          <span className="text-muted-foreground">:{api.port}</span>
                          <div className="flex items-center gap-2">
                            <a
                              href={`http://localhost:${api.port}/docs`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-0.5 text-primary hover:underline"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <ExternalLink className="h-2.5 w-2.5" />
                              Swagger
                            </a>
                            <Link
                              to={`/admin/api/${api.id}`}
                              className="flex items-center gap-0.5 text-muted-foreground hover:text-primary"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <Settings className="h-2.5 w-2.5" />
                              설정
                            </Link>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
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
