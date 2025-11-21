import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAPIConfigStore } from '../../store/apiConfigStore';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Settings as SettingsIcon, Save, RefreshCw, AlertCircle, Download, Upload } from 'lucide-react';
import { useToast } from '../../hooks/useToast';

interface ModelConfig {
  name: string;
  displayName: string;
  description: string;
  icon: string;
  port: number;
  enabled: boolean;
  device: 'cpu' | 'cuda';
  memory_limit: string;
  gpu_memory?: string;
  hyperparams: {
    [key: string]: number | boolean | string;
  };
}

// Hyperparameter mapping schema for automatic serialization/deserialization
const HYPERPARAM_SCHEMA: Record<string, Record<string, string>> = {
  'yolo-api': {
    'conf_threshold': 'yolo_conf_threshold',
    'iou_threshold': 'yolo_iou_threshold',
    'imgsz': 'yolo_imgsz',
    'visualize': 'yolo_visualize'
  },
  'edocr2-api-v2': {
    'extract_dimensions': 'edocr_extract_dimensions',
    'extract_gdt': 'edocr_extract_gdt',
    'extract_text': 'edocr_extract_text',
    'extract_tables': 'edocr_extract_tables',
    'visualize': 'edocr_visualize',
    'language': 'edocr_language',
    'cluster_threshold': 'edocr_cluster_threshold'
  },
  'edgnet-api': {
    'num_classes': 'edgnet_num_classes',
    'visualize': 'edgnet_visualize',
    'save_graph': 'edgnet_save_graph'
  },
  'paddleocr-api': {
    'det_db_thresh': 'paddle_det_db_thresh',
    'det_db_box_thresh': 'paddle_det_db_box_thresh',
    'min_confidence': 'paddle_min_confidence',
    'use_angle_cls': 'paddle_use_angle_cls'
  },
  'skinmodel-api': {
    'material': 'skin_material',
    'manufacturing_process': 'skin_manufacturing_process',
    'correlation_length': 'skin_correlation_length'
  }
};

const defaultModels: ModelConfig[] = [
  {
    name: 'gateway-api',
    displayName: 'Gateway API',
    description: '파이프라인 오케스트레이션 및 요청 라우팅',
    icon: '🔀',
    port: 8000,
    enabled: true,
    device: 'cpu',
    memory_limit: '2g',
    hyperparams: {}
  },
  {
    name: 'yolo-api',
    displayName: 'YOLOv11 Detection',
    description: '도면 객체 검출 (치수, 테이블, 텍스트 영역)',
    icon: '🎯',
    port: 5005,
    enabled: true,
    device: 'cuda',
    memory_limit: '4g',
    gpu_memory: '4g',
    hyperparams: {
      conf_threshold: 0.25,
      iou_threshold: 0.7,
      imgsz: 1280,
      visualize: true
    }
  },
  {
    name: 'edocr2-api-v2',
    displayName: 'eDOCr2 V2 OCR',
    description: '도면 텍스트 및 치수 인식 (VL 모델 지원)',
    icon: '📝',
    port: 5002,
    enabled: true,
    device: 'cuda',
    memory_limit: '4g',
    gpu_memory: '6g',
    hyperparams: {
      extract_dimensions: true,
      extract_gdt: true,
      extract_text: true,
      extract_tables: true,
      visualize: false,
      language: 'eng',
      cluster_threshold: 20
    }
  },
  {
    name: 'paddleocr-api',
    displayName: 'PaddleOCR',
    description: '다국어 OCR (중국어, 일본어, 한국어 특화)',
    icon: '🌏',
    port: 5006,
    enabled: true,
    device: 'cpu',
    memory_limit: '2g',
    hyperparams: {
      det_db_thresh: 0.3,
      det_db_box_thresh: 0.5,
      use_angle_cls: true,
      min_confidence: 0.5
    }
  },
  {
    name: 'edgnet-api',
    displayName: 'EDGNet Segmentation',
    description: '도면 세그멘테이션 (윤곽선, 텍스트, 치수 영역 분리)',
    icon: '🎨',
    port: 5012,
    enabled: true,
    device: 'cuda',
    memory_limit: '4g',
    gpu_memory: '4g',
    hyperparams: {
      num_classes: 3,
      visualize: true,
      save_graph: false
    }
  },
  {
    name: 'skinmodel-api',
    displayName: 'Skin Model Tolerance',
    description: '제조 공차 예측 및 가공 가능성 분석',
    icon: '📐',
    port: 5003,
    enabled: true,
    device: 'cpu',
    memory_limit: '2g',
    hyperparams: {
      material: 'steel',
      manufacturing_process: 'machining',
      correlation_length: 10.0
    }
  }
];

export default function Settings() {
  const { t } = useTranslation();
  const { customAPIs } = useAPIConfigStore();
  const [models, setModels] = useState<ModelConfig[]>(defaultModels);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);
  const { success, error, ToastContainer } = useToast();

  // 커스텀 API를 models 배열에 병합
  useEffect(() => {
    const customModels: ModelConfig[] = customAPIs
      .filter((api) => api.enabled)
      .map((api) => ({
        name: api.id,
        displayName: api.displayName,
        description: api.description,
        icon: api.icon,
        port: api.port,
        enabled: true,
        device: 'cpu',
        memory_limit: '2g',
        hyperparams: {},
      }));

    // 기본 모델 + 커스텀 모델 병합
    setModels([...defaultModels, ...customModels]);
  }, [customAPIs]);

  useEffect(() => {
    // Load service configs
    const savedConfigs = localStorage.getItem('serviceConfigs');
    if (savedConfigs) {
      try {
        const configs = JSON.parse(savedConfigs);
        setModels(prevModels => prevModels.map(model => {
          const savedConfig = configs.find((c: any) => c.name === model.name);
          if (savedConfig) {
            return {
              ...model,
              enabled: savedConfig.enabled ?? model.enabled,
              device: savedConfig.device ?? model.device,
              memory_limit: savedConfig.memory_limit ?? model.memory_limit,
              gpu_memory: savedConfig.gpu_memory ?? model.gpu_memory
            };
          }
          return model;
        }));
      } catch (e) {
        console.error('Failed to load saved configs:', e);
      }
    }

    // Load hyperparameters using schema
    const savedHyperParams = localStorage.getItem('hyperParameters');
    if (savedHyperParams) {
      try {
        const hyperParams = JSON.parse(savedHyperParams);
        setModels(prevModels => prevModels.map(model => {
          const updatedHyperparams = { ...model.hyperparams };
          const schema = HYPERPARAM_SCHEMA[model.name];

          // Use schema to automatically map saved hyperparameters
          if (schema) {
            Object.entries(schema).forEach(([localKey, savedKey]) => {
              if (hyperParams[savedKey] !== undefined) {
                updatedHyperparams[localKey] = hyperParams[savedKey];
              }
            });
          }

          return { ...model, hyperparams: updatedHyperparams };
        }));
      } catch (e) {
        console.error('Failed to load saved hyperparameters:', e);
      }
    }
  }, []);

  // Validation helper functions
  const validateMemoryFormat = (value: string): boolean => {
    // Valid formats: "1g", "2g", "10g", etc. (number followed by 'g')
    return /^\d+g$/i.test(value);
  };

  const validatePortNumber = (port: number): boolean => {
    return port >= 1024 && port <= 65535;
  };

  const handleSave = () => {
    // Validate hyperparameters before saving
    const validationErrors: string[] = [];

    models.forEach(model => {
      // Validate port number
      if (!validatePortNumber(model.port)) {
        validationErrors.push(`[${model.displayName}] 포트 번호는 1024~65535 범위여야 합니다 (현재: ${model.port})`);
      }

      // Validate memory_limit format
      if (!validateMemoryFormat(model.memory_limit)) {
        validationErrors.push(`[${model.displayName}] 메모리 제한 형식이 올바르지 않습니다. 예: "2g", "4g" (현재: ${model.memory_limit})`);
      }

      // Validate GPU memory format if GPU is used
      if (model.device === 'cuda' && model.gpu_memory) {
        if (!validateMemoryFormat(model.gpu_memory)) {
          validationErrors.push(`[${model.displayName}] GPU 메모리 형식이 올바르지 않습니다. 예: "4g", "6g" (현재: ${model.gpu_memory})`);
        }

        // Check GPU memory is reasonable (1-24GB)
        const gpuMemoryGB = parseInt(model.gpu_memory);
        if (gpuMemoryGB < 1 || gpuMemoryGB > 24) {
          validationErrors.push(`[${model.displayName}] GPU 메모리는 1~24GB 범위를 권장합니다 (현재: ${gpuMemoryGB}g)`);
        }
      }

      // Check memory limit is reasonable (1-32GB)
      const memoryLimitGB = parseInt(model.memory_limit);
      if (memoryLimitGB < 1 || memoryLimitGB > 32) {
        validationErrors.push(`[${model.displayName}] 메모리 제한은 1~32GB 범위를 권장합니다 (현재: ${memoryLimitGB}g)`);
      }

      // Validate hyperparameters
      if (model.name === 'yolo-api') {
        const { conf_threshold, iou_threshold, imgsz } = model.hyperparams;
        const confVal = Number(conf_threshold);
        const iouVal = Number(iou_threshold);
        const imgszVal = Number(imgsz);

        if (isNaN(confVal) || confVal < 0 || confVal > 1) {
          validationErrors.push(`[${model.displayName}] 신뢰도 임계값은 0~1 범위여야 합니다 (현재: ${confVal})`);
        }
        if (isNaN(iouVal) || iouVal < 0 || iouVal > 1) {
          validationErrors.push(`[${model.displayName}] IoU 임계값은 0~1 범위여야 합니다 (현재: ${iouVal})`);
        }
        if (isNaN(imgszVal) || imgszVal < 320 || imgszVal > 2560) {
          validationErrors.push(`[${model.displayName}] 이미지 크기는 320~2560 범위를 권장합니다 (현재: ${imgszVal})`);
        }
      } else if (model.name === 'edocr2-api-v2') {
        const { cluster_threshold } = model.hyperparams;
        const clusterVal = Number(cluster_threshold);
        if (isNaN(clusterVal) || clusterVal < 1 || clusterVal > 100) {
          validationErrors.push(`[${model.displayName}] 클러스터링 임계값은 1~100 범위여야 합니다 (현재: ${clusterVal})`);
        }
      } else if (model.name === 'edgnet-api') {
        const { num_classes } = model.hyperparams;
        const numClassesVal = Number(num_classes);
        if (isNaN(numClassesVal) || numClassesVal < 2 || numClassesVal > 10) {
          validationErrors.push(`[${model.displayName}] 클래스 개수는 2~10 범위여야 합니다 (현재: ${numClassesVal})`);
        }
      } else if (model.name === 'paddleocr-api') {
        const { det_db_thresh, det_db_box_thresh, min_confidence } = model.hyperparams;
        const detThreshVal = Number(det_db_thresh);
        const boxThreshVal = Number(det_db_box_thresh);
        const minConfVal = Number(min_confidence);

        if (isNaN(detThreshVal) || detThreshVal < 0 || detThreshVal > 1) {
          validationErrors.push(`[${model.displayName}] 텍스트 검출 임계값은 0~1 범위여야 합니다 (현재: ${detThreshVal})`);
        }
        if (isNaN(boxThreshVal) || boxThreshVal < 0 || boxThreshVal > 1) {
          validationErrors.push(`[${model.displayName}] 박스 임계값은 0~1 범위여야 합니다 (현재: ${boxThreshVal})`);
        }
        if (isNaN(minConfVal) || minConfVal < 0 || minConfVal > 1) {
          validationErrors.push(`[${model.displayName}] 최소 신뢰도는 0~1 범위여야 합니다 (현재: ${minConfVal})`);
        }
      } else if (model.name === 'skinmodel-api') {
        const { correlation_length } = model.hyperparams;
        const corrLenVal = Number(correlation_length);
        if (isNaN(corrLenVal) || corrLenVal < 1 || corrLenVal > 100) {
          validationErrors.push(`[${model.displayName}] 상관 길이는 1~100 범위여야 합니다 (현재: ${corrLenVal})`);
        }
      }
    });

    // Show validation errors if any
    if (validationErrors.length > 0) {
      const errorMessage = `설정 검증 실패\n\n다음 항목을 수정해주세요:\n\n${validationErrors.map((err, idx) => `${idx + 1}. ${err}`).join('\n')}`;
      error(errorMessage, 5000);
      return;
    }

    setLoading(true);

    // Save service configs
    const serviceConfigs = models.map(model => ({
      name: model.name,
      displayName: model.displayName,
      port: model.port,
      device: model.device,
      memory_limit: model.memory_limit,
      gpu_memory: model.gpu_memory,
      enabled: model.enabled
    }));
    localStorage.setItem('serviceConfigs', JSON.stringify(serviceConfigs));

    // Save hyperparameters using schema
    const hyperParameters: any = {};
    models.forEach(model => {
      const schema = HYPERPARAM_SCHEMA[model.name];
      if (schema) {
        Object.entries(schema).forEach(([localKey, savedKey]) => {
          if (model.hyperparams[localKey] !== undefined) {
            hyperParameters[savedKey] = model.hyperparams[localKey];
          }
        });
      }
    });
    localStorage.setItem('hyperParameters', JSON.stringify(hyperParameters));

    setTimeout(() => {
      setLoading(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    }, 500);
  };

  const handleReset = () => {
    if (confirm('모든 설정을 기본값으로 되돌리시겠습니까?')) {
      setModels(defaultModels);
      localStorage.removeItem('serviceConfigs');
      localStorage.removeItem('hyperParameters');
    }
  };

  const handleExport = () => {
    try {
      const exportData = {
        version: '1.0.0',
        exportDate: new Date().toISOString(),
        serviceConfigs: localStorage.getItem('serviceConfigs'),
        hyperParameters: localStorage.getItem('hyperParameters'),
      };

      const dataStr = JSON.stringify(exportData, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);

      const link = document.createElement('a');
      link.href = url;
      link.download = `ax-settings-backup-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      success(t('settings.backupSuccess'));
    } catch (err) {
      console.error('백업 실패:', err);
      error(t('settings.backupFailed'));
    }
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';

    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const importData = JSON.parse(event.target?.result as string);

          // Version validation
          if (!importData.version) {
            throw new Error('유효하지 않은 백업 파일입니다. 버전 정보가 없습니다.');
          }

          // Structure validation
          if (!importData.serviceConfigs && !importData.hyperParameters) {
            throw new Error('백업 파일에 설정 데이터가 없습니다.');
          }

          // Validate serviceConfigs format if present
          if (importData.serviceConfigs) {
            const configs = JSON.parse(importData.serviceConfigs);
            if (!Array.isArray(configs)) {
              throw new Error('서비스 설정 형식이 올바르지 않습니다.');
            }

            // Validate each service config
            const validationErrors: string[] = [];
            configs.forEach((config: any) => {
              if (!config.name || !config.displayName) {
                validationErrors.push('서비스 설정에 필수 필드가 누락되었습니다.');
                return;
              }

              // Validate memory format
              if (config.memory_limit && !validateMemoryFormat(config.memory_limit)) {
                validationErrors.push(`${config.displayName}: 메모리 형식 오류 (${config.memory_limit})`);
              }

              // Validate GPU memory format
              if (config.gpu_memory && !validateMemoryFormat(config.gpu_memory)) {
                validationErrors.push(`${config.displayName}: GPU 메모리 형식 오류 (${config.gpu_memory})`);
              }

              // Validate port
              if (config.port && !validatePortNumber(config.port)) {
                validationErrors.push(`${config.displayName}: 포트 번호 오류 (${config.port})`);
              }
            });

            if (validationErrors.length > 0) {
              throw new Error(`백업 파일 검증 실패:\n\n${validationErrors.join('\n')}`);
            }
          }

          // Validate hyperParameters format if present
          if (importData.hyperParameters) {
            const hyperParams = JSON.parse(importData.hyperParameters);
            if (typeof hyperParams !== 'object') {
              throw new Error('하이퍼파라미터 형식이 올바르지 않습니다.');
            }
          }

          // Confirmation dialog
          const confirmMsg = `백업 파일을 복원하시겠습니까?\n\n` +
            `백업 날짜: ${new Date(importData.exportDate).toLocaleString()}\n` +
            `버전: ${importData.version}\n\n` +
            `⚠️ 현재 설정은 덮어씌워집니다.`;

          if (!confirm(confirmMsg)) return;

          // Restore to localStorage
          if (importData.serviceConfigs) {
            localStorage.setItem('serviceConfigs', importData.serviceConfigs);
          }
          if (importData.hyperParameters) {
            localStorage.setItem('hyperParameters', importData.hyperParameters);
          }

          // Reload page to apply settings
          success(t('settings.restoreSuccess'));
          setTimeout(() => window.location.reload(), 1000);
        } catch (err) {
          console.error('복원 실패:', err);
          const errorMsg = err instanceof Error ? err.message : 'Unknown error';
          error(`${t('settings.restoreFailed')}\n\n${errorMsg}`, 5000);
        }
      };

      reader.readAsText(file);
    };

    input.click();
  };

  const updateModel = (index: number, updates: Partial<ModelConfig>) => {
    const newModels = [...models];
    newModels[index] = { ...newModels[index], ...updates };
    setModels(newModels);
  };

  const updateHyperparam = (modelIndex: number, param: string, value: any) => {
    const newModels = [...models];
    newModels[modelIndex].hyperparams[param] = value;
    setModels(newModels);
  };

  const getModelTip = (modelName: string) => {
    const tips: { [key: string]: string } = {
      'yolo-api': 'GPU 사용 시 약 10배 빠른 성능',
      'edocr2-api-v2': '대량 OCR 처리 시 GPU 권장',
      'paddleocr-api': '중국어/일본어 OCR 특화, CPU로도 충분한 성능',
      'edgnet-api': 'GPU 필수 (CPU 모드는 매우 느림)',
      'skinmodel-api': '가벼운 수치 계산, CPU로 충분',
      'gateway-api': '요청 라우팅만 담당, CPU로 충분'
    };
    return tips[modelName] || '';
  };

  return (
    <>
      <ToastContainer />
      <div className="p-6 space-y-6">
        {/* 헤더 */}
        <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <SettingsIcon className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-3xl font-bold">{t('settings.title')}</h1>
            <p className="text-muted-foreground">{t('settings.subtitle')}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {saved && <span className="text-sm text-green-600">✓ {t('settings.saved')}</span>}
          <Button variant="outline" size="sm" onClick={handleImport} title={t('settings.restore')}>
            <Upload className="w-4 h-4 mr-2" />
            {t('settings.restore')}
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport} title={t('settings.backup')}>
            <Download className="w-4 h-4 mr-2" />
            {t('settings.backup')}
          </Button>
          <Button variant="outline" size="sm" onClick={handleReset}>
            <RefreshCw className="w-4 h-4 mr-2" />
            {t('settings.reset')}
          </Button>
          <Button size="sm" onClick={handleSave} disabled={loading}>
            <Save className="w-4 h-4 mr-2" />
            {loading ? t('settings.saving') : t('common.save')}
          </Button>
        </div>
      </div>

      {/* 경고 메시지 */}
      <div className="p-4 bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800 rounded-lg">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-yellow-800 dark:text-yellow-200">
            {t('settings.warning')}
          </p>
        </div>
      </div>

      {/* 동적 API 시스템 안내 */}
      <div className="p-4 bg-cyan-50 dark:bg-cyan-950 border border-cyan-200 dark:border-cyan-800 rounded-lg">
        <div className="flex items-start gap-3">
          <span className="text-2xl flex-shrink-0">➕</span>
          <div className="flex-1">
            <h3 className="font-semibold text-cyan-900 dark:text-cyan-100 mb-2">
              동적 API 추가 시스템
            </h3>
            <p className="text-sm text-cyan-800 dark:text-cyan-200 mb-3">
              Dashboard에서 "API 추가" 버튼을 통해 새로운 API를 추가하면,
              이 Settings 페이지에 자동으로 설정 패널이 생성됩니다.
              코드 수정 없이 즉시 사용 가능합니다.
            </p>
            <div className="space-y-2 text-xs text-cyan-700 dark:text-cyan-300">
              <div className="flex items-start gap-2">
                <span className="text-cyan-500">•</span>
                <span>
                  <strong>자동 반영:</strong> Dashboard(헬스체크), Settings(이 페이지), BlueprintFlow(노드 팔레트)에 즉시 반영
                </span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-cyan-500">•</span>
                <span>
                  <strong>위치 무관:</strong> Docker 위치 상관없이 HTTP로 통신 가능하면 사용 가능
                  (localhost, 원격 서버, 클라우드 모두 OK)
                </span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-cyan-500">•</span>
                <span>
                  <strong>요구사항:</strong> API는 <code className="bg-cyan-100 dark:bg-cyan-900 px-1 py-0.5 rounded">/api/v1/health</code> 엔드포인트 필요
                </span>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-cyan-500">•</span>
                <span>
                  <strong>상세 가이드:</strong> Docs → 동적 API 추가 가이드 참고
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 모델별 통합 설정 카드 */}
      <div className="space-y-4">
        {models.map((model, index) => (
          <Card key={model.name}>
            <div className="p-6 space-y-4">
              {/* 모델 헤더 */}
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <span className="text-3xl">{model.icon}</span>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-semibold">{model.displayName}</h3>
                      {model.enabled ? (
                        <Badge variant="success">활성화</Badge>
                      ) : (
                        <Badge variant="secondary">비활성화</Badge>
                      )}
                      {model.device === 'cuda' && (
                        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300">
                          🎮 GPU
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">{model.description}</p>
                    {getModelTip(model.name) && (
                      <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                        💡 {getModelTip(model.name)}
                      </p>
                    )}
                  </div>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <span className="text-sm">활성화</span>
                  <input
                    type="checkbox"
                    checked={model.enabled}
                    onChange={(e) => updateModel(index, { enabled: e.target.checked })}
                    className="w-4 h-4 cursor-pointer"
                  />
                </label>
              </div>

              {/* 기본 설정 */}
              <div className="grid grid-cols-4 gap-3">
                <div>
                  <label className="block text-xs font-medium mb-1">포트</label>
                  <input
                    type="number"
                    value={model.port}
                    disabled
                    className="w-full px-2 py-1 text-sm border rounded bg-muted"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium mb-1">연산 장치</label>
                  <select
                    value={model.device}
                    onChange={(e) => updateModel(index, { device: e.target.value as 'cpu' | 'cuda' })}
                    disabled={!model.enabled}
                    className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                  >
                    <option value="cpu">CPU</option>
                    <option value="cuda">CUDA (GPU)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium mb-1">메모리 제한</label>
                  <input
                    type="text"
                    value={model.memory_limit}
                    onChange={(e) => updateModel(index, { memory_limit: e.target.value })}
                    disabled={!model.enabled}
                    placeholder="예: 4g"
                    className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                  />
                </div>

                {model.device === 'cuda' && (
                  <div>
                    <label className="block text-xs font-medium mb-1">GPU 메모리</label>
                    <input
                      type="text"
                      value={model.gpu_memory || ''}
                      onChange={(e) => updateModel(index, { gpu_memory: e.target.value })}
                      disabled={!model.enabled}
                      placeholder="예: 6g"
                      className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                    />
                  </div>
                )}
              </div>

              {/* 하이퍼파라미터 */}
              {Object.keys(model.hyperparams).length > 0 && (
                <div className="border-t pt-4 mt-4">
                  <h4 className="text-sm font-semibold mb-3">하이퍼파라미터</h4>
                  <div className="grid grid-cols-3 gap-4">
                    {/* YOLO 하이퍼파라미터 */}
                    {model.name === 'yolo-api' && (
                      <>
                        <div>
                          <label className="block text-xs font-medium mb-1" title="검출된 객체의 최소 신뢰도. 이 값보다 낮은 신뢰도의 객체는 필터링됩니다.">
                            신뢰도 임계값 (Confidence) ⓘ
                          </label>
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.05"
                            value={model.hyperparams.conf_threshold as number}
                            onChange={(e) => updateHyperparam(index, 'conf_threshold', parseFloat(e.target.value))}
                            disabled={!model.enabled}
                            className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                            title="검출 객체의 최소 신뢰도 (0-1). 높을수록 정확하지만 검출 수가 줄어듭니다."
                          />
                          <p className="text-xs text-muted-foreground mt-1">기본값: 0.25</p>
                        </div>

                        <div>
                          <label className="block text-xs font-medium mb-1" title="Non-Maximum Suppression IoU 임계값. 겹치는 박스를 제거할 때 사용합니다.">
                            IoU 임계값 (NMS) ⓘ
                          </label>
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.05"
                            value={model.hyperparams.iou_threshold as number}
                            onChange={(e) => updateHyperparam(index, 'iou_threshold', parseFloat(e.target.value))}
                            disabled={!model.enabled}
                            className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                            title="겹치는 검출 박스를 제거하는 기준 (0-1). 높을수록 더 많은 박스가 유지됩니다."
                          />
                          <p className="text-xs text-muted-foreground mt-1">기본값: 0.7</p>
                        </div>

                        <div>
                          <label className="block text-xs font-medium mb-1" title="YOLO 모델의 입력 이미지 크기. 클수록 정밀하지만 느립니다.">
                            입력 이미지 크기 ⓘ
                          </label>
                          <select
                            value={model.hyperparams.imgsz as number}
                            onChange={(e) => updateHyperparam(index, 'imgsz', parseInt(e.target.value))}
                            disabled={!model.enabled}
                            className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                            title="YOLO 입력 크기. 640px(빠름), 1280px(균형), 1920px(정밀)"
                          >
                            <option value="640">640px (빠름)</option>
                            <option value="1280">1280px (균형)</option>
                            <option value="1920">1920px (정밀)</option>
                          </select>
                          <p className="text-xs text-muted-foreground mt-1">기본값: 1280px</p>
                        </div>

                        <div>
                          <label className="flex items-center gap-2 cursor-pointer" title="검출 결과에 바운딩 박스를 그린 이미지를 생성합니다.">
                            <input
                              type="checkbox"
                              checked={model.hyperparams.visualize as boolean}
                              onChange={(e) => updateHyperparam(index, 'visualize', e.target.checked)}
                              disabled={!model.enabled}
                              className="w-4 h-4 cursor-pointer disabled:opacity-50"
                            />
                            <span className="text-sm">시각화 이미지 생성 ⓘ</span>
                          </label>
                          <p className="text-xs text-muted-foreground mt-1">
                            검출 결과를 바운딩 박스로 표시한 이미지 생성
                          </p>
                        </div>
                      </>
                    )}

                    {/* EDGNet 하이퍼파라미터 */}
                    {model.name === 'edgnet-api' && (
                      <>
                        <div>
                          <label className="block text-xs font-medium mb-1" title="세그멘테이션 클래스 개수를 지정합니다. 2: 윤곽선/텍스트, 3: 윤곽선/텍스트/치수">
                            클래스 개수 ⓘ
                          </label>
                          <input
                            type="number"
                            min="2"
                            max="10"
                            step="1"
                            value={model.hyperparams.num_classes as number}
                            onChange={(e) => updateHyperparam(index, 'num_classes', parseInt(e.target.value))}
                            disabled={!model.enabled}
                            className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                            title="세그멘테이션 클래스 개수 (2 또는 3 권장). 2클래스: 윤곽선과 텍스트, 3클래스: 윤곽선/텍스트/치수 영역"
                          />
                          <p className="text-xs text-muted-foreground mt-1">기본값: 3</p>
                        </div>

                        <div className="col-span-2">
                          <label className="flex items-center gap-2 cursor-pointer" title="세그멘테이션 결과를 시각화한 이미지를 생성합니다.">
                            <input
                              type="checkbox"
                              checked={model.hyperparams.visualize as boolean}
                              onChange={(e) => updateHyperparam(index, 'visualize', e.target.checked)}
                              disabled={!model.enabled}
                              className="w-4 h-4 cursor-pointer disabled:opacity-50"
                            />
                            <span className="text-sm">시각화 생성 ⓘ</span>
                          </label>
                          <p className="text-xs text-muted-foreground mt-1">
                            세그멘테이션 결과를 색상으로 표시한 이미지 생성
                          </p>
                        </div>

                        <div className="col-span-3">
                          <label className="flex items-center gap-2 cursor-pointer" title="세그멘테이션 그래프 데이터를 파일로 저장합니다.">
                            <input
                              type="checkbox"
                              checked={model.hyperparams.save_graph as boolean}
                              onChange={(e) => updateHyperparam(index, 'save_graph', e.target.checked)}
                              disabled={!model.enabled}
                              className="w-4 h-4 cursor-pointer disabled:opacity-50"
                            />
                            <span className="text-sm">그래프 저장 ⓘ</span>
                          </label>
                          <p className="text-xs text-muted-foreground mt-1">
                            노드와 엣지 정보를 포함한 그래프 데이터 저장 (디버깅용)
                          </p>
                        </div>
                      </>
                    )}

                    {/* eDOCr2 하이퍼파라미터 */}
                    {model.name === 'edocr2-api-v2' && (
                      <>
                        <div className="col-span-3">
                          <label className="flex items-center gap-2 cursor-pointer" title="도면에서 치수 정보를 추출합니다.">
                            <input
                              type="checkbox"
                              checked={model.hyperparams.extract_dimensions as boolean}
                              onChange={(e) => updateHyperparam(index, 'extract_dimensions', e.target.checked)}
                              disabled={!model.enabled}
                              className="w-4 h-4 cursor-pointer disabled:opacity-50"
                            />
                            <span className="text-sm">치수 정보 추출 ⓘ</span>
                          </label>
                          <p className="text-xs text-muted-foreground mt-1">
                            치수 값, 단위, 공차 정보 추출
                          </p>
                        </div>

                        <div className="col-span-3">
                          <label className="flex items-center gap-2 cursor-pointer" title="기하 공차 (GD&T) 기호와 정보를 추출합니다.">
                            <input
                              type="checkbox"
                              checked={model.hyperparams.extract_gdt as boolean}
                              onChange={(e) => updateHyperparam(index, 'extract_gdt', e.target.checked)}
                              disabled={!model.enabled}
                              className="w-4 h-4 cursor-pointer disabled:opacity-50"
                            />
                            <span className="text-sm">GD&T 정보 추출 ⓘ</span>
                          </label>
                          <p className="text-xs text-muted-foreground mt-1">
                            형상 공차, 자세 공차 등 GD&T 기호 인식
                          </p>
                        </div>

                        <div className="col-span-3">
                          <label className="flex items-center gap-2 cursor-pointer" title="도면의 텍스트 블록 (제목, 부품번호, 재질 등)을 추출합니다.">
                            <input
                              type="checkbox"
                              checked={model.hyperparams.extract_text as boolean}
                              onChange={(e) => updateHyperparam(index, 'extract_text', e.target.checked)}
                              disabled={!model.enabled}
                              className="w-4 h-4 cursor-pointer disabled:opacity-50"
                            />
                            <span className="text-sm">텍스트 정보 추출 ⓘ</span>
                          </label>
                          <p className="text-xs text-muted-foreground mt-1">
                            도면번호, 제목, 재질, 주석 등 텍스트 블록 추출
                          </p>
                        </div>

                        <div className="col-span-3">
                          <label className="flex items-center gap-2 cursor-pointer" title="도면 내 표(table) 정보를 추출합니다 (V2 전용 기능).">
                            <input
                              type="checkbox"
                              checked={model.hyperparams.extract_tables as boolean}
                              onChange={(e) => updateHyperparam(index, 'extract_tables', e.target.checked)}
                              disabled={!model.enabled}
                              className="w-4 h-4 cursor-pointer disabled:opacity-50"
                            />
                            <span className="text-sm">테이블 정보 추출 ⓘ</span>
                          </label>
                          <p className="text-xs text-muted-foreground mt-1">
                            구조화된 표 데이터 추출 (V2 전용)
                          </p>
                        </div>

                        <div className="col-span-3">
                          <label className="flex items-center gap-2 cursor-pointer" title="OCR 결과를 시각화한 이미지를 생성합니다.">
                            <input
                              type="checkbox"
                              checked={model.hyperparams.visualize as boolean}
                              onChange={(e) => updateHyperparam(index, 'visualize', e.target.checked)}
                              disabled={!model.enabled}
                              className="w-4 h-4 cursor-pointer disabled:opacity-50"
                            />
                            <span className="text-sm">시각화 생성 ⓘ</span>
                          </label>
                          <p className="text-xs text-muted-foreground mt-1">
                            인식된 텍스트와 치수를 원본 이미지에 표시
                          </p>
                        </div>

                        <div>
                          <label className="block text-xs font-medium mb-1" title="Tesseract OCR에서 사용할 언어 코드를 지정합니다.">
                            언어 코드 ⓘ
                          </label>
                          <input
                            type="text"
                            value={model.hyperparams.language as string}
                            onChange={(e) => updateHyperparam(index, 'language', e.target.value)}
                            disabled={!model.enabled}
                            className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                            title="Tesseract 언어 코드 (eng, kor, jpn 등)"
                            placeholder="eng"
                          />
                          <p className="text-xs text-muted-foreground mt-1">기본값: eng</p>
                        </div>

                        <div>
                          <label className="block text-xs font-medium mb-1" title="치수 텍스트를 그룹화할 때 사용하는 거리 임계값입니다.">
                            클러스터링 임계값 ⓘ
                          </label>
                          <input
                            type="number"
                            min="1"
                            max="100"
                            step="1"
                            value={model.hyperparams.cluster_threshold as number}
                            onChange={(e) => updateHyperparam(index, 'cluster_threshold', parseInt(e.target.value))}
                            disabled={!model.enabled}
                            className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                            title="치수 텍스트 클러스터링 거리 임계값 (픽셀). 낮을수록 엄격하게 그룹화됩니다."
                          />
                          <p className="text-xs text-muted-foreground mt-1">기본값: 20 (픽셀)</p>
                        </div>
                      </>
                    )}

                    {/* PaddleOCR 하이퍼파라미터 */}
                    {model.name === 'paddleocr-api' && (
                      <>
                        <div>
                          <label className="block text-xs font-medium mb-1" title="텍스트 영역을 검출하기 위한 임계값입니다.">
                            텍스트 검출 임계값 ⓘ
                          </label>
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.05"
                            value={model.hyperparams.det_db_thresh as number}
                            onChange={(e) => updateHyperparam(index, 'det_db_thresh', parseFloat(e.target.value))}
                            disabled={!model.enabled}
                            className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                            title="텍스트 검출 감도 (0-1). 낮을수록 더 많은 텍스트를 검출하지만 오검출 가능성 증가."
                          />
                          <p className="text-xs text-muted-foreground mt-1">기본값: 0.3 (낮을수록 많이 검출)</p>
                        </div>

                        <div>
                          <label className="block text-xs font-medium mb-1" title="검출된 텍스트 박스의 정확도 임계값입니다.">
                            박스 임계값 ⓘ
                          </label>
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.05"
                            value={model.hyperparams.det_db_box_thresh as number}
                            onChange={(e) => updateHyperparam(index, 'det_db_box_thresh', parseFloat(e.target.value))}
                            disabled={!model.enabled}
                            className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                            title="바운딩 박스 신뢰도 임계값 (0-1). 높을수록 정확한 박스만 반환."
                          />
                          <p className="text-xs text-muted-foreground mt-1">기본값: 0.5 (정확한 박스만)</p>
                        </div>

                        <div>
                          <label className="block text-xs font-medium mb-1" title="OCR 결과에서 필터링할 최소 신뢰도입니다.">
                            최소 신뢰도 ⓘ
                          </label>
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.05"
                            value={model.hyperparams.min_confidence as number}
                            onChange={(e) => updateHyperparam(index, 'min_confidence', parseFloat(e.target.value))}
                            disabled={!model.enabled}
                            className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                            title="인식된 텍스트의 최소 신뢰도 (0-1). 이 값 이하의 결과는 필터링됩니다."
                          />
                          <p className="text-xs text-muted-foreground mt-1">기본값: 0.5 (결과 필터링)</p>
                        </div>

                        <div className="col-span-3">
                          <label className="flex items-center gap-2 cursor-pointer" title="회전된 텍스트를 자동으로 감지하고 보정합니다.">
                            <input
                              type="checkbox"
                              checked={model.hyperparams.use_angle_cls as boolean}
                              onChange={(e) => updateHyperparam(index, 'use_angle_cls', e.target.checked)}
                              disabled={!model.enabled}
                              className="w-4 h-4 cursor-pointer disabled:opacity-50"
                            />
                            <span className="text-sm">회전된 텍스트 감지 ⓘ</span>
                          </label>
                          <p className="text-xs text-muted-foreground mt-1">
                            텍스트 방향 자동 감지 및 회전 보정
                          </p>
                        </div>
                      </>
                    )}

                    {/* Skin Model 하이퍼파라미터 */}
                    {model.name === 'skinmodel-api' && (
                      <>
                        <div>
                          <label className="block text-xs font-medium mb-1" title="부품의 재질을 지정합니다.">
                            재질 (Material) ⓘ
                          </label>
                          <select
                            value={model.hyperparams.material as string}
                            onChange={(e) => updateHyperparam(index, 'material', e.target.value)}
                            disabled={!model.enabled}
                            className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                            title="부품 재질. 재질에 따라 제조 공차 예측이 달라집니다."
                          >
                            <option value="steel">강철 (Steel)</option>
                            <option value="aluminum">알루미늄 (Aluminum)</option>
                            <option value="titanium">티타늄 (Titanium)</option>
                            <option value="plastic">플라스틱 (Plastic)</option>
                            <option value="composite">복합재 (Composite)</option>
                          </select>
                          <p className="text-xs text-muted-foreground mt-1">기본값: steel</p>
                        </div>

                        <div>
                          <label className="block text-xs font-medium mb-1" title="제조 공정 방식을 지정합니다.">
                            제조 공정 ⓘ
                          </label>
                          <select
                            value={model.hyperparams.manufacturing_process as string}
                            onChange={(e) => updateHyperparam(index, 'manufacturing_process', e.target.value)}
                            disabled={!model.enabled}
                            className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                            title="제조 방식. 공정에 따라 달성 가능한 공차가 달라집니다."
                          >
                            <option value="machining">기계 가공 (Machining)</option>
                            <option value="casting">주조 (Casting)</option>
                            <option value="3d_printing">3D 프린팅</option>
                            <option value="forging">단조 (Forging)</option>
                            <option value="sheet_metal">판금 (Sheet Metal)</option>
                          </select>
                          <p className="text-xs text-muted-foreground mt-1">기본값: machining</p>
                        </div>

                        <div>
                          <label className="block text-xs font-medium mb-1" title="Random Field 모델의 공간 상관 길이를 지정합니다.">
                            상관 길이 ⓘ
                          </label>
                          <input
                            type="number"
                            min="1"
                            max="100"
                            step="0.5"
                            value={model.hyperparams.correlation_length as number}
                            onChange={(e) => updateHyperparam(index, 'correlation_length', parseFloat(e.target.value))}
                            disabled={!model.enabled}
                            className="w-full px-2 py-1 text-sm border rounded bg-background disabled:opacity-50"
                            title="제조 공정의 공간적 상관 길이 (mm). 값이 클수록 인접 영역의 오차가 유사합니다."
                          />
                          <p className="text-xs text-muted-foreground mt-1">기본값: 10.0 (mm)</p>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
    </>
  );
}
