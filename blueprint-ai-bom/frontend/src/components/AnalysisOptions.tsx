/**
 * AnalysisOptions - 분석 옵션 선택 컴포넌트
 *
 * 도면 분석 시 어떤 기능을 활성화할지 선택:
 * - 프리셋 선택 (기계부품도, 전력설비, P&ID, 조립도)
 * - 개별 옵션 토글
 */

import { useState, useEffect } from 'react';
import axios from 'axios';
import logger from '../lib/logger';
import { API_BASE_URL } from '../lib/constants';
import {
  Settings,
  Zap,
  Ruler,
  GitBranch,
  FileText,
  ChevronDown,
  ChevronUp,
  Check,
  Cpu,
  Layers,
} from 'lucide-react';

interface AnalysisOptionsData {
  enable_symbol_detection: boolean;
  enable_dimension_ocr: boolean;
  enable_line_detection: boolean;
  enable_text_extraction: boolean;
  ocr_engine: string;
  confidence_threshold: number;
  symbol_model_type: string;
  preset: string | null;
  // Detectron2 옵션
  detection_backend: 'yolo' | 'detectron2';
  return_masks: boolean;
  return_polygons: boolean;
}

interface Preset {
  id: string;
  name: string;
  description: string;
  icon: string;
}

interface AnalysisOptionsProps {
  sessionId: string;
  onOptionsChange?: (options: AnalysisOptionsData) => void;
  onRunAnalysis?: () => void;
  compact?: boolean;
}

export function AnalysisOptions({
  sessionId,
  onOptionsChange,
  onRunAnalysis,
  compact = false,
}: AnalysisOptionsProps) {
  const [options, setOptions] = useState<AnalysisOptionsData>({
    enable_symbol_detection: true,
    enable_dimension_ocr: false,
    enable_line_detection: false,
    enable_text_extraction: false,
    ocr_engine: 'edocr2',
    confidence_threshold: 0.5,
    symbol_model_type: 'panasia',
    preset: 'electrical',
    // Detectron2 옵션 기본값
    detection_backend: 'yolo',
    return_masks: false,
    return_polygons: true,
  });

  const [presets, setPresets] = useState<Preset[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string | null>('electrical');
  const [isExpanded, setIsExpanded] = useState(!compact);
  const [isLoading, setIsLoading] = useState(false);

  // 프리셋 목록 로드
  useEffect(() => {
    const loadPresets = async () => {
      try {
        const { data } = await axios.get(`${API_BASE_URL}/analysis/presets`);
        setPresets(data.presets || []);
      } catch (error) {
        logger.error('Failed to load presets:', error);
        // 기본 프리셋 사용
        setPresets([
          { id: 'electrical', name: '전력 설비 단선도', description: '전기 심볼 검출', icon: '⚡' },
          { id: 'mechanical_part', name: '기계 부품도', description: '치수 OCR 중심', icon: '⚙️' },
          { id: 'pid', name: 'P&ID 배관도', description: '심볼 + 연결선', icon: '🔧' },
          { id: 'assembly', name: '조립도', description: '심볼 + 치수', icon: '🔩' },
        ]);
      }
    };

    loadPresets();
  }, []);

  // 세션 옵션 로드
  useEffect(() => {
    const loadOptions = async () => {
      if (!sessionId) return;

      try {
        const { data } = await axios.get(`${API_BASE_URL}/analysis/options/${sessionId}`);
        setOptions(data);
        setSelectedPreset(data.preset);
      } catch (error) {
        logger.error('Failed to load options:', error);
      }
    };

    loadOptions();
  }, [sessionId]);

  // 프리셋 적용
  const applyPreset = async (presetId: string) => {
    if (!sessionId) return;

    setIsLoading(true);
    try {
      const { data } = await axios.post(
        `${API_BASE_URL}/analysis/options/${sessionId}/preset/${presetId}`
      );
      setOptions(data);
      setSelectedPreset(presetId);
      onOptionsChange?.(data);
    } catch (error) {
      logger.error('Failed to apply preset:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 개별 옵션 변경
  const updateOption = async (key: keyof AnalysisOptionsData, value: boolean | string | number) => {
    if (!sessionId) return;

    const newOptions = { ...options, [key]: value };
    setOptions(newOptions);
    setSelectedPreset(null); // 프리셋 해제

    try {
      await axios.put(`${API_BASE_URL}/analysis/options/${sessionId}`, {
        [key]: value,
      });
      onOptionsChange?.(newOptions);
    } catch (error) {
      logger.error('Failed to update option:', error);
    }
  };

  // Compact 모드: 프리셋 버튼만 표시
  if (compact && !isExpanded) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="w-4 h-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">분석 옵션</span>
            {selectedPreset && (
              <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded">
                {presets.find((p) => p.id === selectedPreset)?.name || selectedPreset}
              </span>
            )}
          </div>
          <button
            onClick={() => setIsExpanded(true)}
            className="text-gray-500 hover:text-gray-700"
          >
            <ChevronDown className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* 헤더 */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gray-50">
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">분석 옵션</h3>
        </div>
        {compact && (
          <button
            onClick={() => setIsExpanded(false)}
            className="text-gray-500 hover:text-gray-700"
          >
            <ChevronUp className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* 프리셋 선택 */}
      <div className="p-4 border-b border-gray-200">
        <p className="text-sm text-gray-600 mb-3">도면 유형 선택</p>
        <div className="grid grid-cols-2 gap-2">
          {presets.map((preset) => (
            <button
              key={preset.id}
              onClick={() => applyPreset(preset.id)}
              disabled={isLoading}
              className={`
                flex items-center gap-2 p-3 rounded-lg border-2 transition-all text-left
                ${
                  selectedPreset === preset.id
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-200 hover:border-gray-300 text-gray-700'
                }
                ${isLoading ? 'opacity-50 cursor-wait' : ''}
              `}
            >
              <span className="text-lg">{preset.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{preset.name}</div>
                <div className="text-xs text-gray-500 truncate">{preset.description}</div>
              </div>
              {selectedPreset === preset.id && (
                <Check className="w-4 h-4 text-primary-600 flex-shrink-0" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 상세 옵션 */}
      <div className="p-4 space-y-4">
        <p className="text-sm text-gray-600">활성화된 분석</p>

        {/* 심볼 검출 */}
        <label className="flex items-center justify-between cursor-pointer">
          <div className="flex items-center gap-3">
            <Zap className="w-4 h-4 text-yellow-500" />
            <span className="text-sm text-gray-700">심볼 검출 (YOLO)</span>
          </div>
          <input
            type="checkbox"
            checked={options.enable_symbol_detection}
            onChange={(e) => updateOption('enable_symbol_detection', e.target.checked)}
            className="w-4 h-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
          />
        </label>

        {/* 치수 OCR */}
        <label className="flex items-center justify-between cursor-pointer">
          <div className="flex items-center gap-3">
            <Ruler className="w-4 h-4 text-blue-500" />
            <span className="text-sm text-gray-700">치수 OCR (eDOCr2)</span>
          </div>
          <input
            type="checkbox"
            checked={options.enable_dimension_ocr}
            onChange={(e) => updateOption('enable_dimension_ocr', e.target.checked)}
            className="w-4 h-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500"
          />
        </label>

        {/* 선 검출 */}
        <label className="flex items-center justify-between cursor-pointer">
          <div className="flex items-center gap-3">
            <GitBranch className="w-4 h-4 text-green-500" />
            <span className="text-sm text-gray-700">선 검출</span>
            <span className="text-xs text-gray-400">(준비중)</span>
          </div>
          <input
            type="checkbox"
            checked={options.enable_line_detection}
            onChange={(e) => updateOption('enable_line_detection', e.target.checked)}
            disabled
            className="w-4 h-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500 disabled:opacity-50"
          />
        </label>

        {/* 텍스트 추출 */}
        <label className="flex items-center justify-between cursor-pointer">
          <div className="flex items-center gap-3">
            <FileText className="w-4 h-4 text-purple-500" />
            <span className="text-sm text-gray-700">텍스트 블록 추출</span>
            <span className="text-xs text-gray-400">(준비중)</span>
          </div>
          <input
            type="checkbox"
            checked={options.enable_text_extraction}
            onChange={(e) => updateOption('enable_text_extraction', e.target.checked)}
            disabled
            className="w-4 h-4 text-primary-600 rounded border-gray-300 focus:ring-primary-500 disabled:opacity-50"
          />
        </label>

        {/* 신뢰도 임계값 */}
        <div className="pt-2 border-t border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-700">신뢰도 임계값</span>
            <span className="text-sm font-medium text-gray-900">
              {(options.confidence_threshold * 100).toFixed(0)}%
            </span>
          </div>
          <input
            type="range"
            min="0.1"
            max="0.9"
            step="0.05"
            value={options.confidence_threshold}
            onChange={(e) => updateOption('confidence_threshold', parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
          />
        </div>

        {/* 검출 백엔드 선택 */}
        <div className="pt-4 border-t border-gray-100">
          <div className="flex items-center gap-2 mb-3">
            <Cpu className="w-4 h-4 text-indigo-500" />
            <span className="text-sm font-medium text-gray-700">검출 백엔드</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => updateOption('detection_backend', 'yolo')}
              className={`
                flex flex-col items-center p-3 rounded-lg border-2 transition-all
                ${
                  options.detection_backend === 'yolo'
                    ? 'border-yellow-500 bg-yellow-50 text-yellow-700'
                    : 'border-gray-200 hover:border-gray-300 text-gray-600'
                }
              `}
            >
              <Zap className="w-5 h-5 mb-1" />
              <span className="text-sm font-medium">YOLO</span>
              <span className="text-xs text-gray-500">빠른 검출</span>
            </button>
            <button
              onClick={() => updateOption('detection_backend', 'detectron2')}
              className={`
                flex flex-col items-center p-3 rounded-lg border-2 transition-all
                ${
                  options.detection_backend === 'detectron2'
                    ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                    : 'border-gray-200 hover:border-gray-300 text-gray-600'
                }
              `}
            >
              <Layers className="w-5 h-5 mb-1" />
              <span className="text-sm font-medium">Detectron2</span>
              <span className="text-xs text-gray-500">마스킹 포함</span>
            </button>
          </div>

          {/* Detectron2 옵션 (선택 시에만 표시) */}
          {options.detection_backend === 'detectron2' && (
            <div className="mt-3 p-3 bg-indigo-50 rounded-lg space-y-2">
              <label className="flex items-center justify-between cursor-pointer">
                <span className="text-sm text-indigo-700">마스크 반환 (RLE)</span>
                <input
                  type="checkbox"
                  checked={options.return_masks}
                  onChange={(e) => updateOption('return_masks', e.target.checked)}
                  className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                />
              </label>
              <label className="flex items-center justify-between cursor-pointer">
                <span className="text-sm text-indigo-700">폴리곤 반환 (SVG용)</span>
                <input
                  type="checkbox"
                  checked={options.return_polygons}
                  onChange={(e) => updateOption('return_polygons', e.target.checked)}
                  className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                />
              </label>
              <p className="text-xs text-indigo-500 mt-2">
                ⚠️ Detectron2는 처리 시간이 더 오래 걸립니다 (~5초)
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 분석 실행 버튼 */}
      {onRunAnalysis && (
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onRunAnalysis}
            disabled={isLoading}
            className="w-full py-2 px-4 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? '분석 중...' : '분석 실행'}
          </button>
        </div>
      )}
    </div>
  );
}

export default AnalysisOptions;
