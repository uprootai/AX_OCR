/**
 * GlobalLoadingOverlay — API stop/start 전역 로딩 오버레이
 */

import { Loader2, StopCircle, PlayCircle } from 'lucide-react';
import type { LoadingState } from './types';

interface GlobalLoadingOverlayProps {
  globalLoading: LoadingState;
}

export function GlobalLoadingOverlay({ globalLoading }: GlobalLoadingOverlayProps) {
  if (!globalLoading.isLoading) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl p-8 max-w-sm w-full mx-4">
        <div className="flex flex-col items-center gap-4">
          {/* 스피너 */}
          <div className="relative">
            <Loader2 className="h-12 w-12 text-primary animate-spin" />
            {globalLoading.action === 'stop' ? (
              <StopCircle className="h-5 w-5 text-red-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
            ) : (
              <PlayCircle className="h-5 w-5 text-green-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
            )}
          </div>

          {/* 제목 */}
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {globalLoading.action === 'stop' ? 'API 중지 중...' : 'API 시작 중...'}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {globalLoading.target}
            </p>
          </div>

          {/* 진행 바 */}
          {globalLoading.progress && (
            <div className="w-full">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>진행률</span>
                <span>{globalLoading.progress.current} / {globalLoading.progress.total}</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    globalLoading.action === 'stop' ? 'bg-red-500' : 'bg-green-500'
                  }`}
                  style={{
                    width: `${(globalLoading.progress.current / globalLoading.progress.total) * 100}%`
                  }}
                />
              </div>
            </div>
          )}

          <p className="text-xs text-gray-400 dark:text-gray-500">
            잠시만 기다려주세요...
          </p>
        </div>
      </div>
    </div>
  );
}
