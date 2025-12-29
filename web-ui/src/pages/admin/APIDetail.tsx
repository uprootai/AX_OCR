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
  Key,
  Eye,
  EyeOff,
  Check,
  X,
  Loader2,
} from 'lucide-react';
import axios from 'axios';
import { ADMIN_ENDPOINTS } from '../../config/api';
import { getHyperparamDefinitions, getDefaultHyperparams, type HyperparamDefinition } from '../../utils/specToHyperparams';
import { YOLOModelManager } from '../../components/admin/YOLOModelManager';
// 중복 제거: constants.ts에서 공통 정의 import
import { DEFAULT_APIS } from '../../components/monitoring/constants';
import type { APIInfo } from '../../components/monitoring/types';
import { apiKeyApi, type AllAPIKeySettings, type ProviderSettings } from '../../lib/api';

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

interface GPUInfo {
  name: string;
  total_mb: number;
  used_mb: number;
  free_mb: number;
  utilization: number;
}

interface ContainerStatus {
  service: string;
  container_name: string;
  running: boolean;
  gpu_enabled: boolean;
  gpu_count: number;
  memory_limit: string | null;
}

// 하이퍼파라미터 정의
const HYPERPARAM_DEFINITIONS: Record<string, { key?: string; label: string; type: 'number' | 'boolean' | 'select' | 'text'; min?: number; max?: number; step?: number; options?: { value: string; label: string }[]; description: string }[]> = {
  yolo: [
    { label: '신뢰도 임계값', type: 'number', min: 0, max: 1, step: 0.05, description: '검출 객체의 최소 신뢰도 (0-1)' },
    { label: 'IoU 임계값', type: 'number', min: 0, max: 1, step: 0.05, description: '겹치는 박스 제거 기준' },
    { label: '입력 이미지 크기', type: 'select', options: [{ value: '640', label: '640px (빠름)' }, { value: '1280', label: '1280px (균형)' }, { value: '1920', label: '1920px (정밀)' }], description: 'YOLO 입력 크기' },
    { label: '모델 타입', type: 'select', options: [{ value: 'engineering', label: '기계도면 (14종)' }, { value: 'bom_detector', label: '전력설비 (27종)' }, { value: 'pid_class_aware', label: 'P&ID 분류 (32종)' }, { value: 'pid_class_agnostic', label: 'P&ID 위치만' }], description: 'YOLO 모델 선택' },
    { label: 'SAHI 슬라이싱', type: 'boolean', description: 'SAHI 슬라이싱 (P&ID 모델은 자동 활성화)' },
    { label: '슬라이스 크기', type: 'select', options: [{ value: '256', label: '256px (최정밀)' }, { value: '512', label: '512px (균형)' }, { value: '768', label: '768px' }, { value: '1024', label: '1024px (빠름)' }], description: 'SAHI 슬라이스 크기' },
    { label: '시각화 생성', type: 'boolean', description: '바운딩 박스 이미지 생성' },
  ],
  edocr2: [
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
  line_detector: [
    { key: 'method', label: '검출 방법', type: 'select', options: [{ value: 'lsd', label: 'LSD (정밀)' }, { value: 'hough', label: 'Hough (빠름)' }, { value: 'combined', label: 'Combined (최고 정확도)' }], description: '라인 검출 알고리즘' },
    { key: 'min_length', label: '최소 라인 길이', type: 'number', min: 0, max: 500, step: 10, description: '최소 라인 픽셀 길이 (0=필터링 안함)' },
    { key: 'max_lines', label: '최대 라인 수', type: 'number', min: 0, max: 5000, step: 100, description: '최대 라인 수 제한 (0=제한 없음)' },
    { key: 'merge_threshold', label: '병합 거리', type: 'number', min: 5, max: 50, step: 5, description: '동일선상 라인 병합 거리 (픽셀)' },
    { key: 'classify_types', label: '타입 분류', type: 'boolean', description: '배관 vs 신호선 분류' },
    { key: 'classify_colors', label: '색상 분류', type: 'boolean', description: '색상 기반 라인 분류' },
    { key: 'classify_styles', label: '스타일 분류', type: 'boolean', description: '실선/점선/일점쇄선 분류' },
    { key: 'detect_intersections', label: '교차점 검출', type: 'boolean', description: '라인 교차점 검출' },
    { key: 'detect_regions', label: '📦 영역 검출', type: 'boolean', description: '점선 박스 영역 검출 (SIGNAL FOR BWMS 등)' },
    { key: 'region_line_styles', label: '영역 라인 스타일', type: 'text', description: '영역 검출에 사용할 스타일 (쉼표 구분)' },
    { key: 'min_region_area', label: '최소 영역 크기', type: 'number', min: 1000, max: 100000, step: 1000, description: '최소 영역 크기 (픽셀²)' },
    { key: 'visualize', label: '시각화 생성', type: 'boolean', description: '라인 시각화 이미지 생성' },
    { key: 'visualize_regions', label: '영역 시각화', type: 'boolean', description: '검출된 영역 시각화 포함' },
  ],
  paddleocr: [
    { label: '텍스트 검출 임계값', type: 'number', min: 0, max: 1, step: 0.05, description: '텍스트 검출 감도' },
    { label: '박스 임계값', type: 'number', min: 0, max: 1, step: 0.05, description: '바운딩 박스 신뢰도' },
    { label: '최소 신뢰도', type: 'number', min: 0, max: 1, step: 0.05, description: '인식 결과 필터링' },
    { label: '회전 텍스트 감지', type: 'boolean', description: '텍스트 방향 자동 보정' },
  ],
  tesseract: [
    { label: '언어', type: 'select', options: [{ value: 'kor', label: '한국어' }, { value: 'eng', label: '영어' }, { value: 'kor+eng', label: '한영 혼합' }], description: '인식 언어' },
    { label: 'PSM 모드', type: 'select', options: [{ value: '3', label: '자동 페이지 분할' }, { value: '6', label: '단일 블록' }, { value: '11', label: '희소 텍스트' }], description: '페이지 분할 모드' },
    { label: '시각화 생성', type: 'boolean', description: 'OCR 결과 시각화 이미지 생성' },
  ],
  trocr: [
    { label: '모델 크기', type: 'select', options: [{ value: 'base', label: 'Base (빠름)' }, { value: 'large', label: 'Large (정밀)' }], description: 'TrOCR 모델 크기' },
    { label: '최대 길이', type: 'number', min: 16, max: 128, step: 8, description: '최대 토큰 길이' },
    { label: '시각화 생성', type: 'boolean', description: 'OCR 결과 시각화 이미지 생성' },
  ],
  ocr_ensemble: [
    { label: '엔진 선택', type: 'select', options: [{ value: 'all', label: '전체 엔진' }, { value: 'fast', label: '빠른 엔진만' }, { value: 'accurate', label: '정밀 엔진만' }], description: '사용할 OCR 엔진 조합' },
    { label: '투표 방식', type: 'select', options: [{ value: 'weighted', label: '가중 투표' }, { value: 'majority', label: '다수결' }], description: '앙상블 투표 방식' },
    { label: '시각화 생성', type: 'boolean', description: 'OCR 결과 시각화 이미지 생성' },
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
  esrgan: [
    { label: '업스케일 배율', type: 'select', options: [{ value: '2', label: '2x' }, { value: '4', label: '4x' }], description: '이미지 업스케일 배율' },
    { label: '타일 크기', type: 'number', min: 128, max: 512, step: 64, description: '처리 타일 크기 (VRAM 절약)' },
  ],
  skinmodel: [
    { label: '재질', type: 'select', options: [{ value: 'steel', label: '강철' }, { value: 'aluminum', label: '알루미늄' }, { value: 'titanium', label: '티타늄' }, { value: 'plastic', label: '플라스틱' }], description: '부품 재질' },
    { label: '제조 공정', type: 'select', options: [{ value: 'machining', label: '기계 가공' }, { value: 'casting', label: '주조' }, { value: '3d_printing', label: '3D 프린팅' }, { value: 'forging', label: '단조' }], description: '제조 방식' },
    { label: '상관 길이', type: 'number', min: 1, max: 100, step: 0.5, description: '공간적 상관 길이 (mm)' },
  ],
  pid_analyzer: [
    { label: '연결 거리', type: 'number', min: 10, max: 100, step: 5, description: '심볼-라인 연결 거리 임계값 (px)' },
    { label: 'BOM 생성', type: 'boolean', description: 'Bill of Materials 생성' },
    { label: '시각화 생성', type: 'boolean', description: '연결 분석 시각화' },
  ],
  design_checker: [
    { label: '규칙셋', type: 'select', options: [{ value: 'standard', label: '표준 규칙' }, { value: 'strict', label: '엄격 규칙' }, { value: 'custom', label: '사용자 정의' }], description: '적용할 설계 규칙셋' },
    { label: '경고 포함', type: 'boolean', description: '경고 수준 이슈도 보고' },
  ],
  knowledge: [
    { label: '검색 모드', type: 'select', options: [{ value: 'hybrid', label: '하이브리드 (벡터+그래프)' }, { value: 'vector', label: '벡터 검색만' }, { value: 'graph', label: '그래프 검색만' }], description: 'GraphRAG 검색 모드' },
    { label: '검색 깊이', type: 'number', min: 1, max: 5, step: 1, description: '그래프 탐색 깊이' },
    { label: 'Top K', type: 'number', min: 3, max: 20, step: 1, description: '반환할 결과 수' },
  ],
  vl: [
    {
      key: 'model',
      label: '모델',
      type: 'select',
      options: [
        // Local models (항상 표시)
        { value: 'qwen-vl', label: 'Qwen-VL (Local)' },
        { value: 'llava', label: 'LLaVA (Local)' },
        // 외부 API 모델은 동적으로 추가됨 (getEnhancedHyperparamDefs에서 처리)
      ],
      description: 'Vision-Language 모델 선택'
    },
    { key: 'max_tokens', label: '최대 토큰', type: 'number', min: 100, max: 4096, step: 100, description: '생성 최대 토큰 수' },
    { key: 'temperature', label: '온도', type: 'number', min: 0, max: 2, step: 0.1, description: '생성 다양성 (높을수록 다양)' },
  ],
  blueprint_ai_bom: [
    { key: 'symbol_detection', label: '심볼 검출', type: 'boolean', description: 'YOLO 기반 심볼 검출' },
    { key: 'dimension_ocr', label: '치수 OCR', type: 'boolean', description: 'eDOCr2 기반 치수 인식' },
    { key: 'gdt_parsing', label: 'GD&T 파싱', type: 'boolean', description: '기하공차/데이텀 파싱' },
    { key: 'human_in_the_loop', label: 'Human-in-the-Loop', type: 'boolean', description: '수동 검증 큐 활성화' },
    { key: 'confidence_threshold', label: '신뢰도 임계값', type: 'number', min: 0.5, max: 1, step: 0.05, description: '자동 승인 신뢰도 임계값' },
  ],
};

// 기본 하이퍼파라미터 값
const DEFAULT_HYPERPARAMS: Record<string, HyperParams> = {
  yolo: { conf_threshold: 0.25, iou_threshold: 0.7, imgsz: '1280', model_type: 'engineering', use_sahi: false, slice_size: '512', visualize: true },
  edocr2: { extract_dimensions: true, extract_gdt: true, extract_text: true, extract_tables: true, language: 'eng', cluster_threshold: 20 },
  edgnet: { num_classes: 3, visualize: true, save_graph: false },
  line_detector: { method: 'combined', min_length: 0, max_lines: 0, merge_threshold: 10, classify_types: true, classify_colors: true, classify_styles: true, detect_intersections: true, detect_regions: false, region_line_styles: 'dashed,dash_dot', min_region_area: 5000, visualize: true, visualize_regions: true },
  paddleocr: { det_db_thresh: 0.3, det_db_box_thresh: 0.5, min_confidence: 0.5, use_angle_cls: true },
  tesseract: { language: 'kor+eng', psm: '3', visualize: false },
  trocr: { model_size: 'base', max_length: 64, visualize: false },
  ocr_ensemble: { engines: 'all', voting: 'weighted', visualize: false },
  surya_ocr: { language: 'ko', layout_analysis: true, visualize: false },
  doctr: { det_model: 'db_resnet50', reco_model: 'crnn_vgg16_bn', visualize: false },
  easyocr: { language: 'ko', min_confidence: 0.5, paragraph: true },
  esrgan: { scale: '4', tile_size: 256 },
  skinmodel: { material: 'steel', manufacturing_process: 'machining', correlation_length: 10.0 },
  pid_analyzer: { connection_distance: 30, generate_bom: true, visualize: true },
  design_checker: { ruleset: 'standard', include_warnings: true },
  knowledge: { search_mode: 'hybrid', search_depth: 2, top_k: 10 },
  vl: { model: 'qwen-vl', max_tokens: 1024, temperature: 0.7 },
  blueprint_ai_bom: { symbol_detection: true, dimension_ocr: true, gdt_parsing: true, human_in_the_loop: true, confidence_threshold: 0.8 },
};

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
  // Dynamic hyperparameter definitions from API spec
  const [dynamicHyperparamDefs, setDynamicHyperparamDefs] = useState<HyperparamDefinition[]>([]);
  // GPU information for memory guidance
  const [gpuInfo, setGpuInfo] = useState<GPUInfo | null>(null);
  // Actual container status from Docker
  const [containerStatus, setContainerStatus] = useState<ContainerStatus | null>(null);
  // API Key management
  const [apiKeySettings, setApiKeySettings] = useState<AllAPIKeySettings | null>(null);
  const [apiKeyInputs, setApiKeyInputs] = useState<Record<string, string>>({});
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({});
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({});
  const [savingApiKey, setSavingApiKey] = useState<string | null>(null);
  // APIs that require external API keys
  const API_KEY_REQUIRED_APIS = ['vl', 'ocr_ensemble', 'blueprint_ai_bom', 'blueprint-ai-bom'];

  // VL API 모델 선택에 외부 API 모델 동적 추가
  const getEnhancedHyperparamDefs = useCallback((baseDefs: typeof HYPERPARAM_DEFINITIONS[string], apiIdParam: string) => {
    // VL API가 아니면 그대로 반환
    if (!apiIdParam.includes('vl')) return baseDefs;
    if (!apiKeySettings) return baseDefs;

    // 모델 선택 필드 찾기
    const modelFieldIndex = baseDefs.findIndex(def => def.key === 'model' || def.label === '모델');
    if (modelFieldIndex === -1) return baseDefs;

    const modelField = baseDefs[modelFieldIndex];
    if (modelField.type !== 'select' || !modelField.options) return baseDefs;

    // 기존 옵션 복사
    const enhancedOptions = [...modelField.options];

    // API Key가 설정된 Provider의 모델 추가
    const providers = ['openai', 'anthropic', 'google'] as const;
    providers.forEach(provider => {
      const settings = apiKeySettings[provider];
      if (settings?.has_key && settings.models) {
        settings.models.forEach(model => {
          const providerLabel = {
            openai: 'OpenAI',
            anthropic: 'Anthropic',
            google: 'Google'
          }[provider];

          // 중복 체크
          if (!enhancedOptions.some(opt => opt.value === model.id)) {
            enhancedOptions.push({
              value: model.id,
              label: `${model.name} (${providerLabel})${model.recommended ? ' ⭐' : ''}`
            });
          }
        });
      }
    });

    // 새로운 정의 반환
    const newDefs = [...baseDefs];
    newDefs[modelFieldIndex] = {
      ...modelField,
      options: enhancedOptions
    };
    return newDefs;
  }, [apiKeySettings]);

  // API 정보 로드
  const fetchAPIInfo = useCallback(async () => {
    if (!apiId) return;

    // URL에서 하이픈으로 접근해도 언더스코어 ID와 매칭되도록 정규화
    const normalizedId = apiId.replace(/-/g, '_');

    try {
      let api: APIInfo | undefined;

      // 1. 먼저 DEFAULT_APIS에서 찾기 (원본 ID와 정규화된 ID 모두 시도)
      api = DEFAULT_APIS.find((a) => a.id === apiId || a.name === apiId || a.id === normalizedId || a.name === normalizedId);

      // 2. Gateway Registry에서도 시도 (추가 정보 가져오기)
      try {
        const response = await axios.get('http://localhost:8000/api/v1/registry/list', { timeout: 3000 });
        const registryApis = response.data.apis || [];
        const registryApi = registryApis.find((a: APIInfo) => a.id === apiId || a.name === apiId || a.id === normalizedId || a.name === normalizedId);

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

        // 정규화된 ID로 하이퍼파라미터 찾기 (URL 하이픈 → 언더스코어)
        const effectiveApiId = api.id;
        let loadedConfig: APIConfig = {
          enabled: api.status === 'healthy' || api.status === 'unknown',
          device: 'cpu',
          memory_limit: '2g',
          hyperparams: DEFAULT_HYPERPARAMS[effectiveApiId] || DEFAULT_HYPERPARAMS[normalizedId] || {},
        };

        if (savedConfigs) {
          try {
            const configs = JSON.parse(savedConfigs);
            const saved = configs.find((c: { name: string; enabled?: boolean; device?: string; memory_limit?: string; gpu_memory?: string }) => c.name === `${apiId}-api` || c.name === apiId);
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
  const fetchLogs = useCallback(async () => {
    if (!apiId) return;

    try {
      const response = await axios.get(ADMIN_ENDPOINTS.logs(apiId));
      setLogs(response.data.logs || '로그가 없습니다.');
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      setLogs('로그를 불러올 수 없습니다.');
    }
  }, [apiId]);

  // GPU 정보 로드
  const fetchGPUInfo = useCallback(async () => {
    try {
      const response = await axios.get(ADMIN_ENDPOINTS.status, { timeout: 5000 });
      const gpu = response.data.gpu;
      if (gpu && gpu.available && gpu.device_name) {
        setGpuInfo({
          name: gpu.device_name,
          total_mb: gpu.total_memory,
          used_mb: gpu.used_memory,
          free_mb: gpu.free_memory,
          utilization: gpu.utilization,
        });
      }
    } catch (error) {
      console.warn('Failed to fetch GPU info:', error);
    }
  }, []);

  // 컨테이너 실제 상태 로드
  const fetchContainerStatus = useCallback(async () => {
    if (!apiId) return;
    try {
      const response = await axios.get(
        `${ADMIN_ENDPOINTS.status.replace('/status', '')}/container/status/${apiId}`,
        { timeout: 5000 }
      );
      setContainerStatus(response.data);
      // 실제 컨테이너 상태로 UI 초기화
      if (response.data) {
        setConfig(prev => ({
          ...prev,
          device: response.data.gpu_enabled ? 'cuda' : 'cpu',
        }));
      }
    } catch (error) {
      console.warn('Failed to fetch container status:', error);
    }
  }, [apiId]);

  // API Key 설정 로드
  const fetchApiKeySettings = useCallback(async () => {
    try {
      const settings = await apiKeyApi.getAllSettings();
      setApiKeySettings(settings);
    } catch (error) {
      console.warn('Failed to fetch API key settings:', error);
    }
  }, []);

  // API Key 저장
  const handleSaveApiKey = async (provider: string) => {
    const apiKey = apiKeyInputs[provider];
    if (!apiKey) return;

    setSavingApiKey(provider);
    try {
      await apiKeyApi.setAPIKey({ provider, api_key: apiKey });
      setApiKeyInputs(prev => ({ ...prev, [provider]: '' }));
      await fetchApiKeySettings();
      setTestResults(prev => ({ ...prev, [provider]: { success: true, message: '저장 완료' } }));
    } catch (error) {
      console.error('Failed to save API key:', error);
      setTestResults(prev => ({ ...prev, [provider]: { success: false, message: '저장 실패' } }));
    } finally {
      setSavingApiKey(null);
    }
  };

  // API Key 삭제
  const handleDeleteApiKey = async (provider: string) => {
    if (!confirm(`${provider} API Key를 삭제하시겠습니까?`)) return;

    try {
      await apiKeyApi.deleteAPIKey(provider);
      await fetchApiKeySettings();
      setTestResults(prev => {
        const newResults = { ...prev };
        delete newResults[provider];
        return newResults;
      });
    } catch (error) {
      console.error('Failed to delete API key:', error);
    }
  };

  // 연결 테스트
  const handleTestConnection = async (provider: string) => {
    setTestingProvider(provider);
    try {
      const result = await apiKeyApi.testConnection(provider, apiKeyInputs[provider] || undefined);
      setTestResults(prev => ({
        ...prev,
        [provider]: {
          success: result.success,
          message: result.message || result.error || ''
        }
      }));
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        [provider]: { success: false, message: '테스트 실패' }
      }));
    } finally {
      setTestingProvider(null);
    }
  };

  // 모델 선택
  const handleModelChange = async (provider: string, model: string) => {
    try {
      await apiKeyApi.setModel(provider, model);
      await fetchApiKeySettings();
    } catch (error) {
      console.error('Failed to set model:', error);
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
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      alert(`Docker ${action} 실패: ${errorMessage}`);
    } finally {
      setDockerAction(null);
    }
  };

  // 설정 저장
  const handleSave = async () => {
    setSaving(true);

    try {
      // serviceConfigs 저장
      const savedConfigs = localStorage.getItem('serviceConfigs');
      const configs = savedConfigs ? JSON.parse(savedConfigs) : [];

      const configIndex = configs.findIndex((c: { name: string }) => c.name === `${apiId}-api` || c.name === apiId);
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

      // GPU/메모리 설정 변경 시 컨테이너 재생성
      const applyContainerConfig = window.confirm(
        `설정을 저장하고 컨테이너에 적용하시겠습니까?\n\n` +
        `• 연산 장치: ${config.device.toUpperCase()}\n` +
        `• GPU 메모리: ${config.gpu_memory || '제한 없음'}\n\n` +
        `컨테이너가 재생성되며 5-10초 정도 소요됩니다.`
      );

      if (applyContainerConfig) {
        try {
          const response = await axios.post(
            `${ADMIN_ENDPOINTS.status.replace('/status', '')}/container/configure/${apiId}`,
            {
              device: config.device,
              memory_limit: config.memory_limit,
              gpu_memory: config.gpu_memory,
            }
          );

          if (response.data.success) {
            alert(`✅ 설정이 저장되고 컨테이너가 재생성되었습니다.\n\n${response.data.message}`);
            // 상태 새로고침
            setTimeout(fetchContainerStatus, 2000);
          } else {
            alert(`⚠️ 설정은 저장되었지만 컨테이너 재생성에 실패했습니다.\n\n${response.data.message}`);
          }
        } catch (configError) {
          const errorMessage = configError instanceof Error ? configError.message : 'Unknown error';
          alert(`⚠️ 설정은 저장되었지만 컨테이너 재생성에 실패했습니다.\n\n${errorMessage}`);
        }
      } else {
        alert('설정이 저장되었습니다. (컨테이너 미적용)');
      }
    } catch (error) {
      console.error('Failed to save config:', error);
      alert('설정 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    fetchAPIInfo();
    fetchContainerStatus();
    // API Key 설정이 필요한 API인 경우 로드
    if (apiId && API_KEY_REQUIRED_APIS.some(id => apiId.includes(id) || id.includes(apiId.replace(/-/g, '_')))) {
      fetchApiKeySettings();
    }
  }, [fetchAPIInfo, fetchContainerStatus, fetchApiKeySettings, apiId]);

  // Fetch GPU info when device is set to cuda
  useEffect(() => {
    if (config.device === 'cuda') {
      fetchGPUInfo();
    }
  }, [config.device, fetchGPUInfo]);

  // Load dynamic hyperparameter definitions from API spec
  useEffect(() => {
    if (!apiId) return;

    const loadSpecParams = async () => {
      try {
        const [defs, defaults] = await Promise.all([
          getHyperparamDefinitions(apiId),
          getDefaultHyperparams(apiId),
        ]);

        if (defs.length > 0) {
          setDynamicHyperparamDefs(defs);
          // Update config with spec defaults if no saved values
          setConfig(prev => ({
            ...prev,
            hyperparams: {
              ...(defaults as HyperParams),
              ...prev.hyperparams, // Saved values take precedence
            },
          }));
        }
      } catch (error) {
        console.warn('Failed to load spec parameters, using fallback:', error);
      }
    };

    loadSpecParams();
  }, [apiId]);

  useEffect(() => {
    if (activeTab === 'logs') {
      fetchLogs();
    }
  }, [activeTab, fetchLogs]);

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

  // Use dynamic definitions from spec, fallback to hardcoded
  // Normalize apiId for fallback lookup (hyphens to underscores)
  const normalizedApiId = apiId?.replace(/-/g, '_') || '';
  const baseHyperparamDefs = dynamicHyperparamDefs.length > 0
    ? dynamicHyperparamDefs.map(def => ({
        label: def.label,
        type: def.type,
        min: def.min,
        max: def.max,
        step: def.step,
        options: def.options,
        description: def.description,
        key: def.key,
      }))
    : (HYPERPARAM_DEFINITIONS[normalizedApiId] || HYPERPARAM_DEFINITIONS[apiId || ''] || []);

  // VL API인 경우 외부 API 모델 동적 추가
  const hyperparamDefs = getEnhancedHyperparamDefs(baseHyperparamDefs, apiId || '');

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

              {/* 현재 컨테이너 상태 */}
              {containerStatus && (
                <div className="mb-4 p-3 bg-muted/50 rounded border">
                  <div className="text-sm font-medium mb-2">현재 컨테이너 상태</div>
                  <div className="flex items-center gap-4 text-sm">
                    <span className={`flex items-center gap-1 ${containerStatus.running ? 'text-green-600' : 'text-red-500'}`}>
                      <span className={`w-2 h-2 rounded-full ${containerStatus.running ? 'bg-green-500' : 'bg-red-500'}`} />
                      {containerStatus.running ? '실행 중' : '중지됨'}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${containerStatus.gpu_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {containerStatus.gpu_enabled ? 'GPU' : 'CPU'}
                    </span>
                    {containerStatus.memory_limit && (
                      <span className="text-muted-foreground">
                        메모리: {containerStatus.memory_limit}
                      </span>
                    )}
                  </div>
                </div>
              )}

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
                    <label className="block text-sm font-medium mb-1">GPU 메모리 제한</label>
                    <input
                      type="text"
                      value={config.gpu_memory || ''}
                      onChange={(e) => setConfig({ ...config, gpu_memory: e.target.value })}
                      placeholder="예: 6g"
                      className="w-full px-3 py-2 border rounded bg-background"
                    />
                    {/* GPU 정보 표시 */}
                    {gpuInfo && (
                      <div className="mt-2 p-3 bg-muted/50 rounded border text-sm">
                        <div className="font-medium text-primary mb-2">🖥️ {gpuInfo.name}</div>
                        <div className="grid grid-cols-3 gap-2 text-center">
                          <div>
                            <div className="text-xs text-muted-foreground">전체</div>
                            <div className="font-semibold">{(gpuInfo.total_mb / 1024).toFixed(1)}GB</div>
                          </div>
                          <div>
                            <div className="text-xs text-muted-foreground">사용 중</div>
                            <div className="font-semibold text-orange-500">{(gpuInfo.used_mb / 1024).toFixed(1)}GB</div>
                          </div>
                          <div>
                            <div className="text-xs text-muted-foreground">사용 가능</div>
                            <div className="font-semibold text-green-500">{(gpuInfo.free_mb / 1024).toFixed(1)}GB</div>
                          </div>
                        </div>
                        <div className="mt-2 text-xs text-muted-foreground">
                          GPU 사용률: {gpuInfo.utilization}% |
                          권장: {Math.floor(gpuInfo.free_mb / 1024 * 0.8)}GB 이하
                        </div>
                        {/* Progress bar */}
                        <div className="mt-2 h-2 bg-gray-200 rounded overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500"
                            style={{ width: `${(gpuInfo.used_mb / gpuInfo.total_mb) * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                    {!gpuInfo && (
                      <p className="text-xs text-muted-foreground mt-1">
                        GPU 정보를 로드할 수 없습니다
                      </p>
                    )}
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

          {/* API Key 설정 (외부 API 필요한 서비스만 표시) */}
          {apiKeySettings && API_KEY_REQUIRED_APIS.some(id => apiId?.includes(id) || id.includes(apiId?.replace(/-/g, '_') || '')) && (
            <Card className="md:col-span-2">
              <div className="p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Key className="h-5 w-5" />
                  외부 AI API 설정
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  이 서비스는 외부 AI API를 사용합니다. API Key를 설정하면 해당 서비스를 이용할 수 있습니다.
                </p>

                <div className="grid md:grid-cols-2 gap-4">
                  {(['openai', 'anthropic', 'google', 'local'] as const).map((provider) => {
                    const settings = apiKeySettings[provider] as ProviderSettings;
                    const providerLabels: Record<string, { name: string; color: string; icon: string }> = {
                      openai: { name: 'OpenAI', color: 'bg-green-500', icon: '🤖' },
                      anthropic: { name: 'Anthropic', color: 'bg-orange-500', icon: '🧠' },
                      google: { name: 'Google AI', color: 'bg-blue-500', icon: '🔷' },
                      local: { name: 'Local VL', color: 'bg-purple-500', icon: '🏠' },
                    };
                    const label = providerLabels[provider];
                    const testResult = testResults[provider];

                    return (
                      <div key={provider} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <span className="text-xl">{label.icon}</span>
                            <span className="font-medium">{label.name}</span>
                          </div>
                          {settings.has_key && (
                            <Badge variant="success" className="text-xs">
                              {settings.source === 'environment' ? '환경변수' : '설정됨'}
                            </Badge>
                          )}
                        </div>

                        {/* 현재 설정된 키 표시 */}
                        {settings.has_key && settings.masked_key && (
                          <div className="mb-3 p-2 bg-muted/50 rounded text-sm flex items-center justify-between">
                            <span className="font-mono">{settings.masked_key}</span>
                            {settings.source === 'dashboard' && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteApiKey(provider)}
                                className="h-6 px-2 text-red-500 hover:text-red-600"
                              >
                                <X className="h-3 w-3" />
                              </Button>
                            )}
                          </div>
                        )}

                        {/* API Key 입력 */}
                        {provider !== 'local' && (
                          <div className="mb-3">
                            <div className="relative">
                              <input
                                type={showApiKeys[provider] ? 'text' : 'password'}
                                value={apiKeyInputs[provider] || ''}
                                onChange={(e) => setApiKeyInputs(prev => ({ ...prev, [provider]: e.target.value }))}
                                placeholder={settings.has_key ? '새 키로 덮어쓰기' : 'API Key 입력'}
                                className="w-full px-3 py-2 pr-10 border rounded bg-background text-sm font-mono"
                              />
                              <button
                                type="button"
                                onClick={() => setShowApiKeys(prev => ({ ...prev, [provider]: !prev[provider] }))}
                                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                              >
                                {showApiKeys[provider] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                              </button>
                            </div>
                          </div>
                        )}

                        {/* 모델 선택 */}
                        {settings.models && settings.models.length > 0 && (
                          <div className="mb-3">
                            <label className="block text-xs text-muted-foreground mb-1">모델</label>
                            <select
                              value={settings.model || ''}
                              onChange={(e) => handleModelChange(provider, e.target.value)}
                              className="w-full px-3 py-2 border rounded bg-background text-sm"
                            >
                              {settings.models.map((model) => (
                                <option key={model.id} value={model.id}>
                                  {model.name} ({model.cost}){model.recommended ? ' ⭐' : ''}
                                </option>
                              ))}
                            </select>
                          </div>
                        )}

                        {/* 테스트 결과 */}
                        {testResult && (
                          <div className={`mb-3 p-2 rounded text-sm flex items-center gap-2 ${testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                            {testResult.success ? <Check className="h-4 w-4" /> : <X className="h-4 w-4" />}
                            {testResult.message}
                          </div>
                        )}

                        {/* 액션 버튼 */}
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleTestConnection(provider)}
                            disabled={testingProvider === provider}
                            className="flex-1"
                          >
                            {testingProvider === provider ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              '테스트'
                            )}
                          </Button>
                          {provider !== 'local' && apiKeyInputs[provider] && (
                            <Button
                              size="sm"
                              onClick={() => handleSaveApiKey(provider)}
                              disabled={savingApiKey === provider}
                              className="flex-1"
                            >
                              {savingApiKey === provider ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                '저장'
                              )}
                            </Button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </Card>
          )}

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
                    // Use param.key if available (dynamic), otherwise fallback to index-based key
                    const paramKey = (param as { key?: string }).key || Object.keys(config.hyperparams)[idx] || `param_${idx}`;
                    const value = (param as { key?: string }).key
                      ? config.hyperparams[paramKey]
                      : Object.values(config.hyperparams)[idx];

                    return (
                      <div key={paramKey}>
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
                                newHyperparams[paramKey] = e.target.checked;
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
                              newHyperparams[paramKey] = e.target.value;
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
                              newHyperparams[paramKey] = param.type === 'number' ? parseFloat(e.target.value) : e.target.value;
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

      {/* YOLO 모델 관리 (yolo API만 표시) */}
      {activeTab === 'settings' && apiInfo?.id === 'yolo' && (
        <div className="mt-6">
          <YOLOModelManager apiBaseUrl={apiInfo.base_url} />
        </div>
      )}
    </div>
  );
}
