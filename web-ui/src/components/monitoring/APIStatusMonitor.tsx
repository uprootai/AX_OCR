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
  Settings,
  Trash2,
  Square,
  Play,
  Cpu,
  MemoryStick,
  Thermometer
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

// Container stats from Docker
interface ContainerStats {
  name: string;
  memory_usage: string | null;
  cpu_percent: number | null;
}

// GPU stats from nvidia-smi
interface GPUStats {
  index: number;
  name: string;
  memory_used: number;
  memory_total: number;
  memory_percent: number;
  utilization: number;
  temperature: number | null;
}

// API별 리소스 정보 타입 (스펙에서 동적으로 로드)
interface APIResourceSpec {
  gpu?: {
    vram?: string;
    minVram?: number;
    recommended?: string;
  };
  cpu?: {
    ram?: string;
    minRam?: number;
    cores?: number;
    note?: string;
  };
  parameterImpact?: Array<{
    parameter: string;
    impact: string;
    examples?: string;
  }>;
}

// 기본 API 정의 (실제 Docker 컨테이너 기준 - 22개 서비스)
const DEFAULT_APIS: APIInfo[] = [
  // Orchestrator
  { id: 'gateway', name: 'gateway', display_name: 'Gateway API', base_url: 'http://localhost:8000', port: 8000, status: 'unknown', category: 'orchestrator', description: 'API Gateway & Orchestrator', icon: '🚀', color: '#6366f1', last_check: null },
  // Detection
  { id: 'yolo', name: 'yolo', display_name: 'YOLOv11', base_url: 'http://localhost:5005', port: 5005, status: 'unknown', category: 'detection', description: '14가지 도면 심볼 검출', icon: '🎯', color: '#ef4444', last_check: null },
  { id: 'yolo_pid', name: 'yolo_pid', display_name: 'YOLO-PID', base_url: 'http://localhost:5017', port: 5017, status: 'unknown', category: 'detection', description: 'P&ID 심볼 검출 (60종)', icon: '🔧', color: '#ef4444', last_check: null },
  // OCR
  { id: 'edocr2', name: 'edocr2', display_name: 'eDOCr2', base_url: 'http://localhost:5002', port: 5002, status: 'unknown', category: 'ocr', description: '한국어 치수 인식', icon: '📐', color: '#3b82f6', last_check: null },
  { id: 'paddleocr', name: 'paddleocr', display_name: 'PaddleOCR', base_url: 'http://localhost:5006', port: 5006, status: 'unknown', category: 'ocr', description: '다국어 OCR', icon: '🔤', color: '#3b82f6', last_check: null },
  { id: 'tesseract', name: 'tesseract', display_name: 'Tesseract', base_url: 'http://localhost:5008', port: 5008, status: 'unknown', category: 'ocr', description: '문서 OCR', icon: '📄', color: '#3b82f6', last_check: null },
  { id: 'trocr', name: 'trocr', display_name: 'TrOCR', base_url: 'http://localhost:5009', port: 5009, status: 'unknown', category: 'ocr', description: '필기체 OCR', icon: '✍️', color: '#3b82f6', last_check: null },
  { id: 'ocr_ensemble', name: 'ocr_ensemble', display_name: 'OCR Ensemble', base_url: 'http://localhost:5011', port: 5011, status: 'unknown', category: 'ocr', description: '4엔진 가중 투표', icon: '🗳️', color: '#3b82f6', last_check: null },
  { id: 'surya_ocr', name: 'surya_ocr', display_name: 'Surya OCR', base_url: 'http://localhost:5013', port: 5013, status: 'unknown', category: 'ocr', description: '90+ 언어, 레이아웃 분석', icon: '🌞', color: '#3b82f6', last_check: null },
  { id: 'doctr', name: 'doctr', display_name: 'DocTR', base_url: 'http://localhost:5014', port: 5014, status: 'unknown', category: 'ocr', description: '2단계 파이프라인 OCR', icon: '📑', color: '#3b82f6', last_check: null },
  { id: 'easyocr', name: 'easyocr', display_name: 'EasyOCR', base_url: 'http://localhost:5015', port: 5015, status: 'unknown', category: 'ocr', description: '80+ 언어, CPU 친화적', icon: '👁️', color: '#3b82f6', last_check: null },
  // Segmentation
  { id: 'edgnet', name: 'edgnet', display_name: 'EDGNet', base_url: 'http://localhost:5012', port: 5012, status: 'unknown', category: 'segmentation', description: '엣지 기반 세그멘테이션', icon: '🔲', color: '#22c55e', last_check: null },
  { id: 'line_detector', name: 'line_detector', display_name: 'Line Detector', base_url: 'http://localhost:5016', port: 5016, status: 'unknown', category: 'segmentation', description: 'P&ID 라인 검출', icon: '📏', color: '#22c55e', last_check: null },
  // Preprocessing
  { id: 'esrgan', name: 'esrgan', display_name: 'ESRGAN', base_url: 'http://localhost:5010', port: 5010, status: 'unknown', category: 'preprocessing', description: '4x 이미지 업스케일링', icon: '🔍', color: '#f59e0b', last_check: null },
  // Analysis
  { id: 'skinmodel', name: 'skinmodel', display_name: 'SkinModel', base_url: 'http://localhost:5003', port: 5003, status: 'unknown', category: 'analysis', description: '공차 분석 & 제조성 예측', icon: '📊', color: '#8b5cf6', last_check: null },
  { id: 'pid_analyzer', name: 'pid_analyzer', display_name: 'PID Analyzer', base_url: 'http://localhost:5018', port: 5018, status: 'unknown', category: 'analysis', description: 'P&ID 연결 분석, BOM 생성', icon: '🔗', color: '#8b5cf6', last_check: null },
  { id: 'design_checker', name: 'design_checker', display_name: 'Design Checker', base_url: 'http://localhost:5019', port: 5019, status: 'unknown', category: 'analysis', description: 'P&ID 설계 규칙 검증', icon: '✅', color: '#8b5cf6', last_check: null },
  // Knowledge
  { id: 'knowledge', name: 'knowledge', display_name: 'Knowledge', base_url: 'http://localhost:5007', port: 5007, status: 'unknown', category: 'knowledge', description: 'Neo4j + GraphRAG', icon: '🧠', color: '#10b981', last_check: null },
  // AI
  { id: 'vl', name: 'vl', display_name: 'VL (Vision-Language)', base_url: 'http://localhost:5004', port: 5004, status: 'unknown', category: 'ai', description: 'Vision-Language 멀티모달', icon: '🤖', color: '#06b6d4', last_check: null },
];

// localStorage key for deleted APIs
const DELETED_APIS_KEY = 'deleted-api-ids';

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
  const { customAPIs } = useAPIConfigStore();

  // Resource stats state
  const [containerStats, setContainerStats] = useState<Record<string, ContainerStats>>({});
  const [gpuStats, setGpuStats] = useState<GPUStats[]>([]);
  const [gpuAvailable, setGpuAvailable] = useState<boolean>(false);
  const [showResourcePanel, setShowResourcePanel] = useState<boolean>(true);

  // API 리소스 스펙 (스펙 파일에서 동적 로드)
  const [apiResources, setApiResources] = useState<Record<string, APIResourceSpec>>({});

  // Delete API from list (can be restored via "API 자동 검색")
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

  // API ID → Container name mapping
  const apiToContainerMap: Record<string, string> = {
    gateway: 'gateway-api',
    yolo: 'yolo-api',
    yolo_pid: 'yolo-pid-api',
    edocr2: 'edocr2-v2-api',
    paddleocr: 'paddleocr-api',
    tesseract: 'tesseract-api',
    trocr: 'trocr-api',
    ocr_ensemble: 'ocr-ensemble-api',
    surya_ocr: 'surya-ocr-api',
    doctr: 'doctr-api',
    easyocr: 'easyocr-api',
    edgnet: 'edgnet-api',
    line_detector: 'line-detector-api',
    esrgan: 'esrgan-api',
    skinmodel: 'skinmodel-api',
    pid_analyzer: 'pid-analyzer-api',
    design_checker: 'design-checker-api',
    knowledge: 'knowledge-api',
    vl: 'vl-api',
  };

  // API ID → Spec ID mapping (스펙 파일의 ID와 매핑)
  const apiToSpecIdMap: Record<string, string> = {
    yolo: 'yolo',
    yolo_pid: 'yolopid',
    edocr2: 'edocr2',
    paddleocr: 'paddleocr',
    tesseract: 'tesseract',
    trocr: 'trocr',
    ocr_ensemble: 'ocr-ensemble',
    surya_ocr: 'suryaocr',
    doctr: 'doctr',
    easyocr: 'easyocr',
    edgnet: 'edgnet',
    line_detector: 'linedetector',
    esrgan: 'esrgan',
    skinmodel: 'skinmodel',
    pid_analyzer: 'pidanalyzer',
    design_checker: 'designchecker',
    knowledge: 'knowledge',
    vl: 'vl',
  };

  // Get spec ID from API ID
  const getSpecId = (apiId: string): string => apiToSpecIdMap[apiId] || apiId;

  // Category action loading state
  const [categoryActionLoading, setCategoryActionLoading] = useState<string | null>(null);

  // Fetch container and GPU stats
  const fetchResourceStats = useCallback(async () => {
    try {
      // Fetch container stats (includes memory and CPU)
      const containerResponse = await axios.get('http://localhost:8000/api/v1/containers', { timeout: 10000 });
      if (containerResponse.data?.containers) {
        const stats: Record<string, ContainerStats> = {};
        for (const container of containerResponse.data.containers) {
          // Map container name to API ID
          const apiId = Object.entries(apiToContainerMap).find(([, containerName]) => containerName === container.name)?.[0];
          if (apiId) {
            stats[apiId] = {
              name: container.name,
              memory_usage: container.memory_usage,
              cpu_percent: container.cpu_percent,
            };
          }
        }
        setContainerStats(stats);
      }
    } catch (error) {
      console.warn('Failed to fetch container stats:', error);
    }

    try {
      // Fetch GPU stats
      const gpuResponse = await axios.get('http://localhost:8000/api/v1/containers/gpu/stats', { timeout: 5000 });
      if (gpuResponse.data?.available) {
        setGpuAvailable(true);
        setGpuStats(gpuResponse.data.gpus || []);
      } else {
        setGpuAvailable(false);
        setGpuStats([]);
      }
    } catch (error) {
      console.warn('Failed to fetch GPU stats:', error);
      setGpuAvailable(false);
    }

    try {
      // Fetch API resource specs (동적 로드 - 하드코딩 제거)
      const resourcesResponse = await axios.get('http://localhost:8000/api/v1/specs/resources', { timeout: 5000 });
      if (resourcesResponse.data?.resources) {
        setApiResources(resourcesResponse.data.resources);
      }
    } catch (error) {
      console.warn('Failed to fetch API resources:', error);
    }
  }, []);

  // Stop/Start all containers in a category
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
    // Knowledge 카테고리의 경우 neo4j도 함께 관리됨을 알림
    const dependencyNote = category === 'knowledge' ? '\n\n⚠️ Neo4j 데이터베이스도 함께 ' + actionText + '됩니다.' : '';
    if (!confirm(`${category.toUpperCase()} 카테고리의 ${targetAPIs.length}개 API를 ${actionText}하시겠습니까?\n\n${targetAPIs.map(a => a.display_name).join(', ')}${dependencyNote}`)) {
      return;
    }

    setCategoryActionLoading(category);
    let successCount = 0;
    let failCount = 0;
    const failedAPIs: string[] = [];

    // Knowledge 카테고리의 경우 neo4j도 함께 제어 (종속 서비스)
    // neo4j는 knowledge-api보다 먼저 시작하고, 나중에 중지해야 함
    const dependentContainers = category === 'knowledge' ? ['neo4j'] : [];

    // 시작 시: neo4j 먼저 시작
    if (action === 'start') {
      for (const depContainer of dependentContainers) {
        try {
          await axios.post(
            `http://localhost:8000/api/v1/containers/${depContainer}/${action}`,
            {},
            { timeout: 30000 }
          );
          console.log(`Dependent container ${depContainer} ${action}ed`);
        } catch (error) {
          console.warn(`Failed to ${action} dependent container ${depContainer}:`, error);
        }
      }
      // neo4j가 준비될 때까지 잠시 대기
      if (dependentContainers.length > 0) {
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }

    for (const api of targetAPIs) {
      const containerName = apiToContainerMap[api.id];

      // 매핑이 없는 경우
      if (!containerName) {
        console.warn(`No container mapping for API: ${api.id}`);
        failCount++;
        failedAPIs.push(`${api.display_name} (매핑 없음)`);
        continue;
      }

      try {
        const response = await axios.post(
          `http://localhost:8000/api/v1/containers/${containerName}/${action}`,
          {},
          { timeout: 30000 }
        );

        // API 응답의 success 필드 확인
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

    // 중지 시: knowledge-api 중지 후 neo4j 중지
    if (action === 'stop') {
      for (const depContainer of dependentContainers) {
        try {
          await axios.post(
            `http://localhost:8000/api/v1/containers/${depContainer}/${action}`,
            {},
            { timeout: 30000 }
          );
          console.log(`Dependent container ${depContainer} ${action}ed`);
        } catch (error) {
          console.warn(`Failed to ${action} dependent container ${depContainer}:`, error);
        }
      }
    }

    setCategoryActionLoading(null);
    await fetchStatus(true);

    // 결과 알림
    if (successCount > 0 && failCount === 0) {
      // 모두 성공 - 알림 없음 (UI에서 바로 확인 가능)
    } else if (successCount > 0 && failCount > 0) {
      // 일부 성공
      alert(`${actionText} 일부 완료\n\n✓ 성공: ${successCount}개\n✗ 실패: ${failCount}개\n\n실패 목록:\n${failedAPIs.join('\n')}`);
    } else if (successCount === 0 && failCount > 0) {
      // 모두 실패
      alert(`${actionText} 실패\n\n실패 목록:\n${failedAPIs.join('\n')}`);
    }
  };

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
    fetchResourceStats();
    const interval = setInterval(() => {
      fetchStatus();
      fetchResourceStats();
    }, 30000); // 30초마다 자동 갱신
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

  // Filter visible APIs (exclude deleted)
  const visibleApis = apis.filter(api => !deletedApis.has(api.id));
  const healthyAPIs = visibleApis.filter(api => api.status === 'healthy');
  const unhealthyAPIs = visibleApis.filter(api => api.status !== 'healthy');
  const categories = [...new Set(visibleApis.map(api => api.category))];

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

        {/* Resource Usage Panel */}
        <div className="border rounded-lg overflow-hidden">
          <button
            onClick={() => setShowResourcePanel(!showResourcePanel)}
            className="w-full flex items-center justify-between p-3 bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-950 dark:to-indigo-950 hover:opacity-90"
          >
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-purple-600" />
              <span className="font-semibold text-purple-700 dark:text-purple-300">시스템 리소스</span>
              {gpuAvailable && (
                <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 rounded-full">
                  GPU 활성
                </span>
              )}
            </div>
            {showResourcePanel ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>

          {showResourcePanel && (
            <div className="p-3 space-y-3">
              {/* GPU Stats */}
              {gpuAvailable && gpuStats.length > 0 && (
                <div className="space-y-2">
                  {gpuStats.map((gpu) => (
                    <div key={gpu.index} className="p-3 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">🎮</span>
                          <span className="font-medium text-sm">{gpu.name}</span>
                        </div>
                        {gpu.temperature && (
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Thermometer className="h-3 w-3" />
                            <span className={gpu.temperature > 80 ? 'text-red-500' : gpu.temperature > 60 ? 'text-yellow-500' : 'text-green-500'}>
                              {gpu.temperature}°C
                            </span>
                          </div>
                        )}
                      </div>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">VRAM</span>
                          <span className="font-mono">{gpu.memory_used}MB / {gpu.memory_total}MB ({gpu.memory_percent}%)</span>
                        </div>
                        <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all ${
                              gpu.memory_percent > 90 ? 'bg-red-500' :
                              gpu.memory_percent > 70 ? 'bg-yellow-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${gpu.memory_percent}%` }}
                          />
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">GPU 사용률</span>
                          <span className="font-mono">{gpu.utilization}%</span>
                        </div>
                        <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all ${
                              gpu.utilization > 90 ? 'bg-red-500' :
                              gpu.utilization > 70 ? 'bg-yellow-500' : 'bg-blue-500'
                            }`}
                            style={{ width: `${gpu.utilization}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {!gpuAvailable && (
                <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg text-center">
                  <span className="text-sm text-muted-foreground">GPU 없음 (CPU 모드)</span>
                </div>
              )}

              {/* Container Resource Summary */}
              {Object.keys(containerStats).length > 0 && (
                <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <MemoryStick className="h-4 w-4 text-blue-500" />
                    <span className="text-sm font-medium">실행 중인 컨테이너 리소스</span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                    {Object.entries(containerStats)
                      .filter(([, stats]) => stats.memory_usage || stats.cpu_percent)
                      .map(([apiId, stats]) => {
                        const api = apis.find(a => a.id === apiId);
                        return (
                          <div key={apiId} className="p-2 bg-white dark:bg-gray-800 rounded border text-xs">
                            <div className="font-medium truncate">{api?.display_name || apiId}</div>
                            <div className="flex items-center gap-2 mt-1 text-muted-foreground">
                              {stats.memory_usage && (
                                <span className="flex items-center gap-1">
                                  <MemoryStick className="h-3 w-3" />
                                  {stats.memory_usage}
                                </span>
                              )}
                              {stats.cpu_percent !== null && (
                                <span className="flex items-center gap-1">
                                  <Cpu className="h-3 w-3" />
                                  {stats.cpu_percent.toFixed(1)}%
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}
            </div>
          )}
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
            const categoryAPIs = visibleApis.filter(api => api.category === category);
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
                <div className="flex items-center justify-between p-3 bg-muted/30">
                  <button
                    onClick={() => toggleCategory(category)}
                    className="flex items-center gap-2 hover:opacity-70 transition-opacity"
                  >
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
                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    )}
                  </button>

                  {/* Category Actions */}
                  <div className="flex items-center gap-1">
                      {categoryHealthy > 0 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCategoryAction(category, 'stop');
                          }}
                          disabled={categoryActionLoading === category}
                          className="h-7 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                          title={`${categoryLabels[category] || category} 전체 중지`}
                        >
                          {categoryActionLoading === category ? (
                            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Square className="h-3.5 w-3.5" />
                          )}
                          <span className="ml-1 text-xs">Stop All</span>
                        </Button>
                      )}
                      {categoryHealthy < categoryAPIs.length && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCategoryAction(category, 'start');
                          }}
                          disabled={categoryActionLoading === category}
                          className="h-7 px-2 text-green-600 hover:text-green-700 hover:bg-green-50"
                          title={`${categoryLabels[category] || category} 전체 시작`}
                        >
                          {categoryActionLoading === category ? (
                            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Play className="h-3.5 w-3.5" />
                          )}
                          <span className="ml-1 text-xs">Start All</span>
                        </Button>
                      )}
                  </div>
                </div>

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

                        {/* Resource Usage & Estimates */}
                        <div className="mb-2 space-y-1">
                          {/* Current usage if running */}
                          {api.status === 'healthy' && containerStats[api.id] && (
                            <div className="flex items-center gap-2 text-[10px] text-blue-600 dark:text-blue-400">
                              {containerStats[api.id].memory_usage && (
                                <span className="flex items-center gap-0.5">
                                  <MemoryStick className="h-2.5 w-2.5" />
                                  {containerStats[api.id].memory_usage}
                                </span>
                              )}
                              {containerStats[api.id].cpu_percent !== null && (
                                <span className="flex items-center gap-0.5">
                                  <Cpu className="h-2.5 w-2.5" />
                                  {containerStats[api.id].cpu_percent?.toFixed(1)}%
                                </span>
                              )}
                            </div>
                          )}

                          {/* Expected resource estimates - 스펙에서 동적 로드 */}
                          {apiResources[getSpecId(api.id)] && (
                            <div className="space-y-1">
                              <div className="flex flex-wrap gap-1 text-[9px]">
                                {/* GPU 모드 */}
                                {apiResources[getSpecId(api.id)].gpu && (
                                  <span
                                    className={`px-1.5 py-0.5 rounded cursor-help ${
                                      apiResources[getSpecId(api.id)].gpu?.vram === 'N/A'
                                        ? 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
                                        : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                                    }`}
                                    title={apiResources[getSpecId(api.id)].gpu?.recommended || ''}
                                  >
                                    🎮 {apiResources[getSpecId(api.id)].gpu?.vram || '-'}
                                  </span>
                                )}
                                {/* CPU 모드 */}
                                {apiResources[getSpecId(api.id)].cpu && (
                                  <span
                                    className="px-1.5 py-0.5 bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 rounded cursor-help"
                                    title={apiResources[getSpecId(api.id)].cpu?.note || ''}
                                  >
                                    💻 {apiResources[getSpecId(api.id)].cpu?.ram || '?'}/{apiResources[getSpecId(api.id)].cpu?.cores || '?'}c
                                  </span>
                                )}
                              </div>
                              {/* 하이퍼파라미터 영향 */}
                              {apiResources[getSpecId(api.id)].parameterImpact && apiResources[getSpecId(api.id)].parameterImpact!.length > 0 && (
                                <div
                                  className="text-[8px] text-amber-600 dark:text-amber-400 truncate"
                                  title={apiResources[getSpecId(api.id)].parameterImpact!.map(p => `${p.parameter}: ${p.impact} (${p.examples || ''})`).join('\n')}
                                >
                                  ⚠️ {apiResources[getSpecId(api.id)].parameterImpact![0].impact}
                                </div>
                              )}
                            </div>
                          )}
                        </div>

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
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteApi(api.id);
                              }}
                              className="flex items-center gap-0.5 text-muted-foreground hover:text-destructive"
                              title="목록에서 삭제"
                            >
                              <Trash2 className="h-2.5 w-2.5" />
                              삭제
                            </button>
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
