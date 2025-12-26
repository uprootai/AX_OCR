/**
 * VLMClassificationSection - VLM 분류 결과 섹션
 * Vision-Language Model 기반 도면 분류 결과를 표시
 */

import { DrawingClassifier } from '../../../components/DrawingClassifier';
import logger from '../../../lib/logger';

interface ClassificationData {
  drawing_type: string;
  confidence: number;
  suggested_preset: string;
  provider: string;
}

interface VLMClassificationSectionProps {
  sessionId: string;
  imageBase64: string;
  apiBaseUrl: string;
  showClassifier: boolean;
  classification: ClassificationData | null;
  onClassificationComplete: (result: ClassificationData) => void;
  onPresetApply: (presetName: string) => void;
  onShowClassifierChange: (show: boolean) => void;
}

const CLASSIFICATION_CONFIG: Record<string, { icon: string; label: string }> = {
  mechanical_part: { icon: '⚙️', label: '기계 부품도' },
  pid: { icon: '🔧', label: 'P&ID' },
  assembly: { icon: '🔩', label: '조립도' },
  electrical: { icon: '⚡', label: '전기 회로도' },
  architectural: { icon: '🏗️', label: '건축 도면' },
  unknown: { icon: '❓', label: '분류 불가' },
};

export function VLMClassificationSection({
  sessionId,
  imageBase64,
  apiBaseUrl,
  showClassifier,
  classification,
  onClassificationComplete,
  onPresetApply,
  onShowClassifierChange,
}: VLMClassificationSectionProps) {
  // Show classifier panel
  if (showClassifier) {
    return (
      <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <DrawingClassifier
          sessionId={sessionId}
          imageBase64={imageBase64}
          onClassificationComplete={(result) => {
            onClassificationComplete({
              drawing_type: result.drawing_type,
              confidence: result.confidence,
              suggested_preset: result.suggested_preset,
              provider: result.provider,
            });
            logger.log('Classification complete:', result);
          }}
          onPresetApply={(presetName) => {
            logger.log('Preset applied:', presetName);
            onPresetApply(presetName);
          }}
          apiBaseUrl={apiBaseUrl}
        />
        {classification && (
          <div className="px-4 pb-4 flex justify-end">
            <button
              onClick={() => onShowClassifierChange(false)}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              분류 패널 숨기기
            </button>
          </div>
        )}
      </section>
    );
  }

  // Show summary when classifier is hidden
  if (classification) {
    const config = CLASSIFICATION_CONFIG[classification.drawing_type] || CLASSIFICATION_CONFIG.unknown;
    return (
      <div className="bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-800 rounded-lg p-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{config.icon}</span>
          <div>
            <span className="font-medium text-indigo-800 dark:text-indigo-200">
              {config.label}
            </span>
            <span className="ml-2 text-sm text-indigo-600 dark:text-indigo-400">
              ({(classification.confidence * 100).toFixed(0)}% via {classification.provider})
            </span>
          </div>
        </div>
        <button
          onClick={() => onShowClassifierChange(true)}
          className="text-sm text-indigo-600 hover:text-indigo-800 dark:text-indigo-400"
        >
          다시 분류
        </button>
      </div>
    );
  }

  return null;
}
