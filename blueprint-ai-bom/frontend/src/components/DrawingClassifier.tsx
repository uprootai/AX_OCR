/**
 * DrawingClassifier - VLM 기반 도면 자동 분류 컴포넌트
 *
 * Vision-Language Model을 사용하여 도면 타입을 자동으로 분류하고
 * 적합한 분석 프리셋을 추천합니다.
 */

import { useState, useCallback } from 'react';
import logger from '../lib/logger';
import { API_BASE_URL } from '../lib/constants';
import {
  Brain,
  Wand2,
  AlertCircle,
  Loader2,
  Settings,
  Layers,
  Eye,
  ChevronRight,
  Sparkles,
} from 'lucide-react';

// 도면 타입 정의
type DrawingType = 'mechanical_part' | 'pid' | 'assembly' | 'electrical' | 'architectural' | 'unknown';

// 영역 타입 정의
type RegionType = 'title_block' | 'main_view' | 'bom_table' | 'notes' | 'detail_view' | 'section_view' | 'dimension_area';

interface DetectedRegion {
  region_type: RegionType;
  bbox: number[];
  confidence: number;
  description?: string;
}

interface ClassificationResult {
  drawing_type: DrawingType;
  confidence: number;
  suggested_preset: string;
  regions: DetectedRegion[];
  analysis_notes: string;
  provider: string;
}

interface PresetConfig {
  name: string;
  description: string;
  nodes: string[];
  yolo_confidence?: number;
  ocr_engine?: string;
  enable_tolerance_analysis?: boolean;
  enable_connectivity?: boolean;
  enable_bom?: boolean;
}

interface DrawingClassifierProps {
  sessionId: string;
  imageBase64?: string;
  onClassificationComplete?: (result: ClassificationResult, preset: PresetConfig) => void;
  onPresetApply?: (presetName: string) => void;
  apiBaseUrl?: string;
}

// 도면 타입별 UI 설정
const DRAWING_TYPE_CONFIG: Record<DrawingType, {
  label: string;
  icon: string;
  color: string;
  bgColor: string;
  description: string;
}> = {
  mechanical_part: {
    label: '기계 부품도',
    icon: '⚙️',
    color: 'text-blue-700',
    bgColor: 'bg-blue-50 border-blue-200',
    description: '치수, 공차, 표면처리 정보가 있는 단일 부품 도면'
  },
  pid: {
    label: 'P&ID (배관계장도)',
    icon: '🔧',
    color: 'text-purple-700',
    bgColor: 'bg-purple-50 border-purple-200',
    description: '파이프, 밸브, 계기류 심볼이 있는 배관 시스템 도면'
  },
  assembly: {
    label: '조립도',
    icon: '🔩',
    color: 'text-green-700',
    bgColor: 'bg-green-50 border-green-200',
    description: '여러 부품이 조립된 상태를 보여주는 도면'
  },
  electrical: {
    label: '전기 회로도',
    icon: '⚡',
    color: 'text-yellow-700',
    bgColor: 'bg-yellow-50 border-yellow-200',
    description: '전기 배선, 회로 심볼이 있는 도면'
  },
  architectural: {
    label: '건축 도면',
    icon: '🏗️',
    color: 'text-orange-700',
    bgColor: 'bg-orange-50 border-orange-200',
    description: '평면도, 입면도, 단면도 등 건축 관련 도면'
  },
  unknown: {
    label: '분류 불가',
    icon: '❓',
    color: 'text-gray-700',
    bgColor: 'bg-gray-50 border-gray-200',
    description: '자동 분류할 수 없는 도면 (수동 선택 필요)'
  }
};

// 영역 타입별 UI 설정
const REGION_TYPE_CONFIG: Record<RegionType, {
  label: string;
  color: string;
}> = {
  title_block: { label: '표제란', color: 'bg-blue-500' },
  main_view: { label: '메인 뷰', color: 'bg-green-500' },
  bom_table: { label: 'BOM 테이블', color: 'bg-purple-500' },
  notes: { label: '주석', color: 'bg-yellow-500' },
  detail_view: { label: '상세도', color: 'bg-orange-500' },
  section_view: { label: '단면도', color: 'bg-red-500' },
  dimension_area: { label: '치수 영역', color: 'bg-cyan-500' }
};

export function DrawingClassifier({
  sessionId,
  imageBase64,
  onClassificationComplete,
  onPresetApply,
  apiBaseUrl = API_BASE_URL
}: DrawingClassifierProps) {
  const [classification, setClassification] = useState<ClassificationResult | null>(null);
  const [preset, setPreset] = useState<PresetConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [provider, setProvider] = useState<string>('local');
  const [showRegions, setShowRegions] = useState(false);

  // 분류 실행
  const handleClassify = useCallback(async () => {
    if (!imageBase64 && !sessionId) {
      setError('이미지 또는 세션 ID가 필요합니다');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/classification/classify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          image_base64: imageBase64,
          provider: provider
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '분류 실패');
      }

      const data = await response.json();
      setClassification(data.classification);
      setPreset(data.preset);

      onClassificationComplete?.(data.classification, data.preset);
    } catch (err) {
      setError(err instanceof Error ? err.message : '분류 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  }, [sessionId, imageBase64, provider, apiBaseUrl, onClassificationComplete]);

  // 프리셋 적용
  const handleApplyPreset = useCallback(async () => {
    if (!classification?.suggested_preset) return;

    try {
      const response = await fetch(
        `${apiBaseUrl}/classification/apply-preset/${sessionId}?preset_name=${classification.suggested_preset}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error('프리셋 적용 실패');
      }

      onPresetApply?.(classification.suggested_preset);
    } catch (err) {
      logger.error('Preset apply error:', err);
    }
  }, [sessionId, classification, apiBaseUrl, onPresetApply]);

  // 수동 도면 타입 선택
  const handleManualSelect = useCallback(async (drawingType: DrawingType) => {
    // 간단한 매핑
    const presetMap: Record<DrawingType, string> = {
      mechanical_part: 'dimension_extraction',
      pid: 'pid_analysis',
      assembly: 'assembly_analysis',
      electrical: 'electrical_analysis',
      architectural: 'architectural_analysis',
      unknown: 'general'
    };

    const presetName = presetMap[drawingType];

    const result: ClassificationResult = {
      drawing_type: drawingType,
      confidence: 1.0,
      suggested_preset: presetName,
      regions: [],
      analysis_notes: '수동 선택됨',
      provider: 'manual'
    };

    setClassification(result);

    // 세션에 drawing_type 저장
    try {
      await fetch(`${apiBaseUrl}/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          drawing_type: drawingType,
          drawing_type_source: 'manual'
        })
      });
    } catch (err) {
      logger.error('Failed to save drawing_type to session:', err);
    }

    // 분석 프리셋 자동 적용 (심볼 검출 ON/OFF, 치수 OCR ON/OFF 등)
    const analysisPresetMap: Record<string, string> = {
      mechanical_part: 'mechanical_part',
      electrical: 'electrical',
      pid: 'pid',
      assembly: 'assembly',
    };
    const analysisPreset = analysisPresetMap[drawingType];
    if (analysisPreset) {
      try {
        await fetch(`${apiBaseUrl}/analysis/options/${sessionId}/preset/${analysisPreset}`, {
          method: 'POST'
        });
        logger.log('Analysis preset applied:', analysisPreset);
      } catch (err) {
        logger.error('Failed to apply analysis preset:', err);
      }
    }

    // 수동 선택 시에도 프리셋 자동 적용 (세션의 features 설정)
    try {
      const response = await fetch(
        `${apiBaseUrl}/classification/apply-preset/${sessionId}?preset_name=${presetName}`,
        { method: 'POST' }
      );
      if (response.ok) {
        const data = await response.json();
        logger.log('Manual preset applied:', presetName, data);
        onPresetApply?.(presetName);
      }
    } catch (err) {
      logger.error('Failed to apply preset:', err);
    }

    onClassificationComplete?.(result, { name: presetName, description: '', nodes: [] } as PresetConfig);
  }, [sessionId, apiBaseUrl, onClassificationComplete, onPresetApply]);

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* 헤더 */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-purple-50">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <Brain className="w-5 h-5 text-indigo-500" />
            VLM 도면 분류
            <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full">
              Phase 4
            </span>
          </h3>

          {!classification && (
            <div className="flex items-center gap-2">
              {/* 프로바이더 선택 */}
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="local">Local VL</option>
                <option value="openai">OpenAI GPT-4o</option>
                <option value="anthropic">Claude Vision</option>
              </select>

              <button
                onClick={handleClassify}
                disabled={loading || (!imageBase64 && !sessionId)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    분류 중...
                  </>
                ) : (
                  <>
                    <Wand2 className="w-4 h-4" />
                    자동 분류
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 에러 표시 */}
      {error && (
        <div className="p-3 bg-red-50 border-b border-red-200 flex items-center gap-2 text-red-700">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* 분류 결과 */}
      {classification ? (
        <div className="p-4">
          {/* 도면 타입 */}
          <div className={`p-4 rounded-lg border ${DRAWING_TYPE_CONFIG[classification.drawing_type].bgColor}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-3xl">
                  {DRAWING_TYPE_CONFIG[classification.drawing_type].icon}
                </span>
                <div>
                  <div className={`font-semibold ${DRAWING_TYPE_CONFIG[classification.drawing_type].color}`}>
                    {DRAWING_TYPE_CONFIG[classification.drawing_type].label}
                  </div>
                  <div className="text-sm text-gray-600">
                    {DRAWING_TYPE_CONFIG[classification.drawing_type].description}
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900">
                  {(classification.confidence * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-gray-500">
                  via {classification.provider}
                </div>
              </div>
            </div>

            {/* 분석 노트 */}
            {classification.analysis_notes && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="text-sm text-gray-600">
                  <Eye className="w-4 h-4 inline mr-1" />
                  {classification.analysis_notes}
                </div>
              </div>
            )}
          </div>

          {/* 추천 프리셋 */}
          {preset && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-green-600" />
                  <div>
                    <div className="font-medium text-green-800">{preset.name}</div>
                    <div className="text-xs text-green-600">{preset.description}</div>
                  </div>
                </div>
                <button
                  onClick={handleApplyPreset}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm bg-green-500 text-white rounded-lg hover:bg-green-600"
                >
                  <Settings className="w-4 h-4" />
                  프리셋 적용
                </button>
              </div>

              {/* 노드 목록 */}
              <div className="mt-2 flex flex-wrap gap-1">
                {preset.nodes.map((node) => (
                  <span
                    key={node}
                    className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded"
                  >
                    {node}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 검출된 영역 */}
          {classification.regions.length > 0 && (
            <div className="mt-4">
              <button
                onClick={() => setShowRegions(!showRegions)}
                className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
              >
                <Layers className="w-4 h-4" />
                검출된 영역 ({classification.regions.length}개)
                <ChevronRight className={`w-4 h-4 transition-transform ${showRegions ? 'rotate-90' : ''}`} />
              </button>

              {showRegions && (
                <div className="mt-2 space-y-2">
                  {classification.regions.map((region, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 p-2 bg-gray-50 rounded text-sm"
                    >
                      <span className={`w-2 h-2 rounded-full ${REGION_TYPE_CONFIG[region.region_type].color}`} />
                      <span className="font-medium">
                        {REGION_TYPE_CONFIG[region.region_type].label}
                      </span>
                      <span className="text-gray-400">
                        ({(region.confidence * 100).toFixed(0)}%)
                      </span>
                      {region.description && (
                        <span className="text-gray-500 text-xs">{region.description}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 다시 분류 버튼 */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <button
              onClick={() => {
                setClassification(null);
                setPreset(null);
              }}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              다시 분류하기
            </button>
          </div>
        </div>
      ) : (
        /* 수동 선택 UI */
        <div className="p-4">
          <div className="text-sm text-gray-500 mb-3">
            또는 도면 타입을 직접 선택하세요:
          </div>
          <div className="grid grid-cols-2 gap-2">
            {(Object.keys(DRAWING_TYPE_CONFIG) as DrawingType[])
              .filter(type => type !== 'unknown')
              .map((type) => (
                <button
                  key={type}
                  onClick={() => handleManualSelect(type)}
                  className={`p-3 rounded-lg border text-left hover:shadow-md transition-shadow ${DRAWING_TYPE_CONFIG[type].bgColor}`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{DRAWING_TYPE_CONFIG[type].icon}</span>
                    <span className={`font-medium text-sm ${DRAWING_TYPE_CONFIG[type].color}`}>
                      {DRAWING_TYPE_CONFIG[type].label}
                    </span>
                  </div>
                </button>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default DrawingClassifier;
