/**
 * ActiveFeaturesSection - 활성화된 기능 + 분석 실행
 * 빌더에서 설정한 기능 목록 표시 + 분석 실행 버튼
 *
 * 2025-12-26: SSOT 리팩토링 - features 정의를 config/features에서 import
 */

import { Loader2, Play } from 'lucide-react';
import { FEATURE_BADGE_CONFIG } from '../../../config/features';

interface ActiveFeaturesSectionProps {
  features: string[];
  onRunAnalysis?: () => void;
  isLoading?: boolean;
  sessionStatus?: string;
  selectedImageId?: string | null;
  imageAnalyzed?: boolean;
}

export function ActiveFeaturesSection({ features, onRunAnalysis, isLoading, sessionStatus, selectedImageId, imageAnalyzed }: ActiveFeaturesSectionProps) {
  const isSubImage = selectedImageId && selectedImageId !== 'main';
  // 서브이미지 선택 시: 해당 이미지의 분석 여부로 판단
  // 메인 이미지/미선택 시: 세션 status로 판단
  const isAnalyzed = isSubImage
    ? (imageAnalyzed ?? false)
    : (sessionStatus === 'verified' || sessionStatus === 'completed' || sessionStatus === 'detected');

  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
          활성화된 기능
        </h2>
        {onRunAnalysis && (
          <button
            onClick={onRunAnalysis}
            disabled={isLoading}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              isLoading
                ? 'bg-gray-200 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
                : isAnalyzed
                  ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-700 hover:bg-green-100'
                  : 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm'
            }`}
          >
            {isLoading ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> 분석 중...</>
            ) : isAnalyzed ? (
              <><Play className="w-4 h-4" /> 재분석</>
            ) : (
              <><Play className="w-4 h-4" /> 분석 실행</>
            )}
          </button>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        {features.map(feature => {
          const config = FEATURE_BADGE_CONFIG[feature];
          if (!config) return null;
          return (
            <span
              key={feature}
              className={`px-3 py-1.5 ${config.bgClass} ${config.textClass} rounded-full text-sm flex items-center gap-1`}
            >
              {config.icon} {config.label}
            </span>
          );
        })}
      </div>
    </section>
  );
}
