import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import {
  ArrowLeft,
  Save,
  RefreshCw,
  Play,
  Square,
  Settings,
  Server,
  Cpu,
  HardDrive,
  FileText,
  ExternalLink,
  AlertCircle,
} from 'lucide-react';
import axios from 'axios';
import { ADMIN_ENDPOINTS } from '../../config/api';

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
}

interface HyperParams {
  [key: string]: number | boolean | string;
}

interface APIConfig {
  enabled: boolean;
  device: 'cpu' | 'cuda';
  memory_limit: string;
  gpu_memory?: string;
  hyperparams: HyperParams;
}

// 하이퍼파라미터 정의
const HYPERPARAM_DEFINITIONS: Record<string, { label: string; type: 'number' | 'boolean' | 'select' | 'text'; min?: number; max?: number; step?: number; options?: { value: string; label: string }[]; description: string }[]> = {
  yolo: [
    { label: '신뢰도 임계값', type: 'number', min: 0, max: 1, step: 0.05, description: '검출 객체의 최소 신뢰도 (0-1)' },
    { label: 'IoU 임계값', type: 'number', min: 0, max: 1, step: 0.05, description: '겹치는 박스 제거 기준' },
    { label: '입력 이미지 크기', type: 'select', options: [{ value: '640', label: '640px (빠름)' }, { value: '1280', label: '1280px (균형)' }, { value: '1920', label: '1920px (정밀)' }], description: 'YOLO 입력 크기' },
    { label: '시각화 생성', type: 'boolean', description: '바운딩 박스 이미지 생성' },
  ],
  edocr2_v1: [
    { label: '치수 추출', type: 'boolean', description: '치수 값, 단위, 공차 정보 추출' },
    { label: 'GD&T 추출', type: 'boolean', description: '기하 공차 기호 인식' },
    { label: '텍스트 추출', type: 'boolean', description: '도면번호, 제목 등 텍스트 블록 추출' },
    { label: '시각화 생성', type: 'boolean', description: 'OCR 결과 시각화 이미지 생성' },
  ],
  edocr2_v2: [
    { label: '치수 추출', type: 'boolean', description: '치수 값, 단위, 공차 정보 추출' },
    { label: 'GD&T 추출', type: 'boolean', description: '기하 공차 기호 인식' },
    { label: '텍스트 추출', type: 'boolean', description: '도면번호, 제목 등 텍스트 블록 추출' },
    { label: '테이블 추출', type: 'boolean', description: '구조화된 표 데이터 추출' },
    { label: '언어 코드', type: 'text', description: 'Tesseract 언어 코드 (eng, kor 등)' },
    { label: '클러스터링 임계값', type: 'number', min: 1, max: 100, step: 1, description: '치수 텍스트 그룹화 거리' },
  ],
  edgnet: [
    { label: '클래스 개수', type: 'number', min: 2, max: 10, step: 1, description: '세그멘테이션 클래스 수' },
    { label: '시각화 생성', type: 'boolean', description: '세그멘테이션 결과 이미지' },
    { label: '그래프 저장', type: 'boolean', description: '노드/엣지 그래프 데이터 저장' },
  ],
  paddleocr: [
    { label: '텍스트 검출 임계값', type: 'number', min: 0, max: 1, step: 0.05, description: '텍스트 검출 감도' },
    { label: '박스 임계값', type: 'number', min: 0, max: 1, step: 0.05, description: '바운딩 박스 신뢰도' },
    { label: '최소 신뢰도', type: 'number', min: 0, max: 1, step: 0.05, description: '인식 결과 필터링' },
    { label: '회전 텍스트 감지', type: 'boolean', description: '텍스트 방향 자동 보정' },
  ],
  surya_ocr: [
    { label: '언어', type: 'select', options: [{ value: 'ko', label: '한국어' }, { value: 'en', label: '영어' }, { value: 'ja', label: '일본어' }, { value: 'zh', label: '중국어' }], description: '인식 언어' },
    { label: '레이아웃 분석', type: 'boolean', description: '문서 레이아웃 분석 활성화' },
    { label: '시각화 생성', type: 'boolean', description: 'OCR 결과 시각화 이미지 생성' },
  ],
  doctr: [
    { label: '텍스트 검출 모델', type: 'select', options: [{ value: 'db_resnet50', label: 'DB ResNet50' }, { value: 'linknet_resnet18', label: 'LinkNet ResNet18' }], description: '텍스트 검출 모델 선택' },
    { label: '인식 모델', type: 'select', options: [{ value: 'crnn_vgg16_bn', label: 'CRNN VGG16' }, { value: 'master', label: 'MASTER' }], description: '텍스트 인식 모델 선택' },
    { label: '시각화 생성', type: 'boolean', description: 'OCR 결과 시각화 이미지 생성' },
  ],
  easyocr: [
    { label: '언어', type: 'select', options: [{ value: 'ko', label: '한국어' }, { value: 'en', label: '영어' }, { value: 'ja', label: '일본어' }, { value: 'ch_sim', label: '중국어 간체' }], description: '인식 언어' },
    { label: '최소 신뢰도', type: 'number', min: 0, max: 1, step: 0.05, description: '최소 인식 신뢰도' },
    { label: '단락 분리', type: 'boolean', description: '텍스트를 단락으로 분리' },
  ],
  skinmodel: [
    { label: '재질', type: 'select', options: [{ value: 'steel', label: '강철' }, { value: 'aluminum', label: '알루미늄' }, { value: 'titanium', label: '티타늄' }, { value: 'plastic', label: '플라스틱' }], description: '부품 재질' },
    { label: '제조 공정', type: 'select', options: [{ value: 'machining', label: '기계 가공' }, { value: 'casting', label: '주조' }, { value: '3d_printing', label: '3D 프린팅' }, { value: 'forging', label: '단조' }], description: '제조 방식' },
    { label: '상관 길이', type: 'number', min: 1, max: 100, step: 0.5, description: '공간적 상관 길이 (mm)' },
  ],
  vl: [
    { label: '모델', type: 'select', options: [{ value: 'qwen-vl', label: 'Qwen-VL' }, { value: 'llava', label: 'LLaVA' }], description: 'Vision-Language 모델 선택' },
    { label: '최대 토큰', type: 'number', min: 100, max: 4096, step: 100, description: '생성 최대 토큰 수' },
    { label: '온도', type: 'number', min: 0, max: 2, step: 0.1, description: '생성 다양성 (높을수록 다양)' },
  ],
};

// 기본 하이퍼파라미터 값
const DEFAULT_HYPERPARAMS: Record<string, HyperParams> = {
  yolo: { conf_threshold: 0.25, iou_threshold: 0.7, imgsz: 1280, visualize: true },
  edocr2_v1: { extract_dimensions: true, extract_gdt: true, extract_text: true, visualize: false },
  edocr2_v2: { extract_dimensions: true, extract_gdt: true, extract_text: true, extract_tables: true, language: 'eng', cluster_threshold: 20 },
  edgnet: { num_classes: 3, visualize: true, save_graph: false },
  paddleocr: { det_db_thresh: 0.3, det_db_box_thresh: 0.5, min_confidence: 0.5, use_angle_cls: true },
  surya_ocr: { language: 'ko', layout_analysis: true, visualize: false },
  doctr: { det_model: 'db_resnet50', reco_model: 'crnn_vgg16_bn', visualize: false },
  easyocr: { language: 'ko', min_confidence: 0.5, paragraph: true },
  skinmodel: { material: 'steel', manufacturing_process: 'machining', correlation_length: 10.0 },
  vl: { model: 'qwen-vl', max_tokens: 1024, temperature: 0.7 },
};

// 기본 API 정의 (APIStatusMonitor와 동일)
const DEFAULT_APIS: APIInfo[] = [
  { id: 'gateway', name: 'gateway', display_name: 'Gateway API', base_url: 'http://localhost:8000', port: 8000, status: 'healthy', category: 'orchestrator', description: 'API Gateway & Orchestrator', icon: '🚀', color: '#6366f1' },
  { id: 'yolo', name: 'yolo', display_name: 'YOLOv11', base_url: 'http://localhost:5005', port: 5005, status: 'unknown', category: 'detection', description: '14가지 도면 심볼 검출', icon: '🎯', color: '#ef4444' },
  { id: 'edocr2_v1', name: 'edocr2_v1', display_name: 'eDOCr v1 (Fast)', base_url: 'http://localhost:5001', port: 5001, status: 'unknown', category: 'ocr', description: '빠른 OCR 처리', icon: '📝', color: '#3b82f6' },
  { id: 'edocr2_v2', name: 'edocr2_v2', display_name: 'eDOCr v2 (Advanced)', base_url: 'http://localhost:5002', port: 5002, status: 'unknown', category: 'ocr', description: '고급 한국어 치수 인식', icon: '📐', color: '#3b82f6' },
  { id: 'paddleocr', name: 'paddleocr', display_name: 'PaddleOCR', base_url: 'http://localhost:5006', port: 5006, status: 'unknown', category: 'ocr', description: '다국어 OCR', icon: '🔤', color: '#3b82f6' },
  { id: 'surya_ocr', name: 'surya_ocr', display_name: 'Surya OCR', base_url: 'http://localhost:5013', port: 5013, status: 'unknown', category: 'ocr', description: '90+ 언어, 레이아웃 분석', icon: '🌞', color: '#3b82f6' },
  { id: 'doctr', name: 'doctr', display_name: 'DocTR', base_url: 'http://localhost:5014', port: 5014, status: 'unknown', category: 'ocr', description: '2단계 파이프라인 OCR', icon: '📑', color: '#3b82f6' },
  { id: 'easyocr', name: 'easyocr', display_name: 'EasyOCR', base_url: 'http://localhost:5015', port: 5015, status: 'unknown', category: 'ocr', description: '80+ 언어, CPU 친화적', icon: '👁️', color: '#3b82f6' },
  { id: 'edgnet', name: 'edgnet', display_name: 'EDGNet', base_url: 'http://localhost:5012', port: 5012, status: 'unknown', category: 'segmentation', description: '엣지 기반 세그멘테이션', icon: '🔲', color: '#22c55e' },
  { id: 'skinmodel', name: 'skinmodel', display_name: 'SkinModel', base_url: 'http://localhost:5003', port: 5003, status: 'unknown', category: 'analysis', description: '공차 분석 & 제조성 예측', icon: '📊', color: '#8b5cf6' },
  { id: 'vl', name: 'vl', display_name: 'VL (Vision-Language)', base_url: 'http://localhost:5004', port: 5004, status: 'unknown', category: 'ai', description: 'Vision-Language 멀티모달', icon: '🤖', color: '#06b6d4' },
];

export default function APIDetail() {
  const { apiId } = useParams<{ apiId: string }>();
  const navigate = useNavigate();
  const [apiInfo, setApiInfo] = useState<APIInfo | null>(null);
  const [config, setConfig] = useState<APIConfig>({
    enabled: true,
    device: 'cpu',
    memory_limit: '2g',
    hyperparams: {},
  });
  const [logs, setLogs] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'settings' | 'logs'>('settings');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dockerAction, setDockerAction] = useState<string | null>(null);

  // API 정보 로드
  const fetchAPIInfo = useCallback(async () => {
    if (!apiId) return;

    try {
      let api: APIInfo | undefined;

      // 1. 먼저 DEFAULT_APIS에서 찾기
      api = DEFAULT_APIS.find((a) => a.id === apiId || a.name === apiId);

      // 2. Gateway Registry에서도 시도 (추가 정보 가져오기)
      try {
        const response = await axios.get('http://localhost:8000/api/v1/registry/list', { timeout: 3000 });
        const registryApis = response.data.apis || [];
        const registryApi = registryApis.find((a: APIInfo) => a.id === apiId || a.name === apiId);

        if (registryApi) {
          // Registry에서 찾은 경우 해당 정보 사용
          api = {
            ...registryApi,
            base_url: registryApi.base_url?.replace(/-(api|api):/, '-api:').replace(/http:\/\/[^:]+:/, 'http://localhost:'),
          };
        }
      } catch {
        // Registry 실패해도 DEFAULT_APIS로 진행
      }

      if (api) {
        setApiInfo(api);

        // 저장된 설정 로드
        const savedConfigs = localStorage.getItem('serviceConfigs');
        const savedHyperParams = localStorage.getItem('hyperParameters');

        let loadedConfig: APIConfig = {
          enabled: api.status === 'healthy' || api.status === 'unknown',
          device: 'cpu',
          memory_limit: '2g',
          hyperparams: DEFAULT_HYPERPARAMS[apiId] || {},
        };

        if (savedConfigs) {
          try {
            const configs = JSON.parse(savedConfigs);
            const saved = configs.find((c: any) => c.name === `${apiId}-api` || c.name === apiId);
            if (saved) {
              loadedConfig = {
                ...loadedConfig,
                enabled: saved.enabled ?? true,
                device: saved.device || 'cpu',
                memory_limit: saved.memory_limit || '2g',
                gpu_memory: saved.gpu_memory,
              };
            }
          } catch (e) {
            console.error('Failed to load saved config:', e);
          }
        }

        if (savedHyperParams) {
          try {
            const hyperParams = JSON.parse(savedHyperParams);
            // 하이퍼파라미터 매핑
            const updatedHyperparams = { ...loadedConfig.hyperparams };
            Object.entries(hyperParams).forEach(([key, value]) => {
              if (key.startsWith(apiId.replace(/_/g, '_'))) {
                const paramName = key.replace(`${apiId}_`, '').replace(`${apiId.replace(/_/g, '')}_`, '');
                updatedHyperparams[paramName] = value as number | boolean | string;
              }
            });
            loadedConfig.hyperparams = updatedHyperparams;
          } catch (e) {
            console.error('Failed to load saved hyperparams:', e);
          }
        }

        setConfig(loadedConfig);
      }
    } catch (error) {
      console.error('Failed to fetch API info:', error);
    } finally {
      setLoading(false);
    }
  }, [apiId]);

  // 로그 로드
  const fetchLogs = async () => {
    if (!apiId) return;

    try {
      const response = await axios.get(ADMIN_ENDPOINTS.logs(apiId));
      setLogs(response.data.logs || '로그가 없습니다.');
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      setLogs('로그를 불러올 수 없습니다.');
    }
  };

  // Docker 제어
  const handleDockerAction = async (action: 'start' | 'stop' | 'restart') => {
    if (!apiId) return;

    const confirmMsg = {
      start: '시작',
      stop: '중지',
      restart: '재시작',
    };

    if (!window.confirm(`${apiInfo?.display_name || apiId} 서비스를 ${confirmMsg[action]}하시겠습니까?`)) {
      return;
    }

    setDockerAction(action);
    try {
      await axios.post(ADMIN_ENDPOINTS.docker(action, apiId));
      alert(`Docker ${action} 성공!`);
      // 상태 새로고침
      setTimeout(fetchAPIInfo, 2000);
    } catch (error: any) {
      alert(`Docker ${action} 실패: ${error.response?.data?.detail || error.message}`);
    } finally {
      setDockerAction(null);
    }
  };

  // 설정 저장
  const handleSave = () => {
    setSaving(true);

    try {
      // serviceConfigs 저장
      const savedConfigs = localStorage.getItem('serviceConfigs');
      const configs = savedConfigs ? JSON.parse(savedConfigs) : [];

      const configIndex = configs.findIndex((c: any) => c.name === `${apiId}-api` || c.name === apiId);
      const newConfig = {
        name: `${apiId}-api`,
        displayName: apiInfo?.display_name || apiId,
        port: apiInfo?.port,
        device: config.device,
        memory_limit: config.memory_limit,
        gpu_memory: config.gpu_memory,
        enabled: config.enabled,
      };

      if (configIndex >= 0) {
        configs[configIndex] = newConfig;
      } else {
        configs.push(newConfig);
      }

      localStorage.setItem('serviceConfigs', JSON.stringify(configs));

      // hyperParameters 저장
      const savedHyperParams = localStorage.getItem('hyperParameters');
      const hyperParams = savedHyperParams ? JSON.parse(savedHyperParams) : {};

      Object.entries(config.hyperparams).forEach(([key, value]) => {
        hyperParams[`${apiId}_${key}`] = value;
      });

      localStorage.setItem('hyperParameters', JSON.stringify(hyperParams));

      alert('설정이 저장되었습니다.');
    } catch (error) {
      console.error('Failed to save config:', error);
      alert('설정 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    fetchAPIInfo();
  }, [fetchAPIInfo]);

  useEffect(() => {
    if (activeTab === 'logs') {
      fetchLogs();
    }
  }, [activeTab, apiId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!apiInfo) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => navigate('/dashboard')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          대시보드로 돌아가기
        </Button>
        <Card>
          <div className="p-8 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">API를 찾을 수 없습니다</h2>
            <p className="text-muted-foreground">ID: {apiId}</p>
          </div>
        </Card>
      </div>
    );
  }

  const hyperparamDefs = HYPERPARAM_DEFINITIONS[apiId || ''] || [];

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-3">
            <span
              className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
              style={{ backgroundColor: apiInfo.color + '20' }}
            >
              {apiInfo.icon}
            </span>
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                {apiInfo.display_name}
                <Badge variant={apiInfo.status === 'healthy' ? 'success' : 'error'}>
                  {apiInfo.status === 'healthy' ? 'Healthy' : 'Unhealthy'}
                </Badge>
              </h1>
              <p className="text-muted-foreground">{apiInfo.description}</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <a
            href={`http://localhost:${apiInfo.port}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
          >
            <ExternalLink className="h-4 w-4" />
            Swagger
          </a>
          <Button onClick={handleSave} disabled={saving}>
            <Save className="h-4 w-4 mr-2" />
            {saving ? '저장 중...' : '저장'}
          </Button>
        </div>
      </div>

      {/* 탭 네비게이션 */}
      <div className="border-b">
        <nav className="flex gap-4">
          {[
            { id: 'settings', label: '설정', icon: Settings },
            { id: 'logs', label: '로그', icon: FileText },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'settings' | 'logs')}
                className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary text-primary font-semibold'
                    : 'border-transparent hover:border-gray-300'
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* 설정 탭 */}
      {activeTab === 'settings' && (
        <div className="grid md:grid-cols-2 gap-6">
          {/* 기본 설정 */}
          <Card>
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Server className="h-5 w-5" />
                서비스 설정
              </h3>

              <div className="space-y-4">
                {/* 포트 */}
                <div>
                  <label className="block text-sm font-medium mb-1">포트</label>
                  <input
                    type="text"
                    value={apiInfo.port}
                    disabled
                    className="w-full px-3 py-2 border rounded bg-muted"
                  />
                </div>

                {/* 연산 장치 */}
                <div>
                  <label className="block text-sm font-medium mb-1">연산 장치</label>
                  <select
                    value={config.device}
                    onChange={(e) => setConfig({ ...config, device: e.target.value as 'cpu' | 'cuda' })}
                    className="w-full px-3 py-2 border rounded bg-background"
                  >
                    <option value="cpu">CPU</option>
                    <option value="cuda">CUDA (GPU)</option>
                  </select>
                </div>

                {/* 메모리 제한 */}
                <div>
                  <label className="block text-sm font-medium mb-1">메모리 제한</label>
                  <input
                    type="text"
                    value={config.memory_limit}
                    onChange={(e) => setConfig({ ...config, memory_limit: e.target.value })}
                    placeholder="예: 4g"
                    className="w-full px-3 py-2 border rounded bg-background"
                  />
                </div>

                {/* GPU 메모리 */}
                {config.device === 'cuda' && (
                  <div>
                    <label className="block text-sm font-medium mb-1">GPU 메모리</label>
                    <input
                      type="text"
                      value={config.gpu_memory || ''}
                      onChange={(e) => setConfig({ ...config, gpu_memory: e.target.value })}
                      placeholder="예: 6g"
                      className="w-full px-3 py-2 border rounded bg-background"
                    />
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Docker 제어 */}
          <Card>
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <HardDrive className="h-5 w-5" />
                Docker 제어
              </h3>

              <div className="space-y-4">
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => handleDockerAction('start')}
                    disabled={dockerAction !== null}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    {dockerAction === 'start' ? '시작 중...' : '시작'}
                  </Button>
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => handleDockerAction('stop')}
                    disabled={dockerAction !== null}
                  >
                    <Square className="h-4 w-4 mr-2" />
                    {dockerAction === 'stop' ? '중지 중...' : '중지'}
                  </Button>
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => handleDockerAction('restart')}
                    disabled={dockerAction !== null}
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    {dockerAction === 'restart' ? '재시작 중...' : '재시작'}
                  </Button>
                </div>

                <div className="p-3 bg-muted/50 rounded text-sm">
                  <p className="text-muted-foreground">
                    컨테이너: <code className="bg-muted px-1 rounded">{apiId}-api</code>
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* 하이퍼파라미터 */}
          {hyperparamDefs.length > 0 && (
            <Card className="md:col-span-2">
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Cpu className="h-5 w-5" />
                  하이퍼파라미터
                </h3>

                <div className="grid md:grid-cols-3 gap-4">
                  {hyperparamDefs.map((param, idx) => {
                    const key = Object.keys(config.hyperparams)[idx] || `param_${idx}`;
                    const value = Object.values(config.hyperparams)[idx];

                    return (
                      <div key={idx}>
                        <label className="block text-sm font-medium mb-1" title={param.description}>
                          {param.label}
                        </label>
                        {param.type === 'boolean' ? (
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={value as boolean}
                              onChange={(e) => {
                                const newHyperparams = { ...config.hyperparams };
                                newHyperparams[key] = e.target.checked;
                                setConfig({ ...config, hyperparams: newHyperparams });
                              }}
                              className="w-4 h-4"
                            />
                            <span className="text-sm text-muted-foreground">{param.description}</span>
                          </label>
                        ) : param.type === 'select' ? (
                          <select
                            value={value as string}
                            onChange={(e) => {
                              const newHyperparams = { ...config.hyperparams };
                              newHyperparams[key] = e.target.value;
                              setConfig({ ...config, hyperparams: newHyperparams });
                            }}
                            className="w-full px-3 py-2 border rounded bg-background"
                          >
                            {param.options?.map((opt) => (
                              <option key={opt.value} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <input
                            type={param.type}
                            value={value as string | number}
                            min={param.min}
                            max={param.max}
                            step={param.step}
                            onChange={(e) => {
                              const newHyperparams = { ...config.hyperparams };
                              newHyperparams[key] = param.type === 'number' ? parseFloat(e.target.value) : e.target.value;
                              setConfig({ ...config, hyperparams: newHyperparams });
                            }}
                            className="w-full px-3 py-2 border rounded bg-background"
                          />
                        )}
                        <p className="text-xs text-muted-foreground mt-1">{param.description}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* 로그 탭 */}
      {activeTab === 'logs' && (
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">서비스 로그</h3>
              <Button variant="outline" size="sm" onClick={fetchLogs}>
                <RefreshCw className="h-4 w-4 mr-2" />
                새로고침
              </Button>
            </div>
            <div className="bg-black text-green-400 p-4 rounded font-mono text-sm h-96 overflow-auto">
              <pre>{logs || '로그를 불러오는 중...'}</pre>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
