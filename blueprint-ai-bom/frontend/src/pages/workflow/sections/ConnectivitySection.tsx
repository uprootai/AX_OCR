/**
 * Connectivity Section
 * P&ID 연결성 분석 섹션 컴포넌트
 */

import { Loader2, RefreshCw } from 'lucide-react';
import { InfoTooltip } from '../../../components/Tooltip';
import { ConnectivityDiagram } from '../../../components/ConnectivityDiagram';
import type { ConnectivityResult } from '../../../lib/api';
import type { Detection } from '../../../types';

interface ConnectivitySectionProps {
  imageData: string;
  imageSize: { width: number; height: number };
  detections: Detection[];
  connectivityData: ConnectivityResult | null;
  selectedSymbolId: string | null;
  setSelectedSymbolId: (id: string | null) => void;
  highlightPath: string[] | null;
  setHighlightPath: (path: string[] | null) => void;
  isAnalyzingConnectivity: boolean;
  onAnalyzeConnectivity: () => void;
  onFindPath: (startId: string, endId: string) => void;
}

export function ConnectivitySection({
  imageData,
  imageSize,
  detections,
  connectivityData,
  selectedSymbolId,
  setSelectedSymbolId,
  highlightPath,
  setHighlightPath,
  isAnalyzingConnectivity,
  onAnalyzeConnectivity,
  onFindPath,
}: ConnectivitySectionProps) {
  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          🔗 P&ID 연결성
          <InfoTooltip content="P&ID 도면에서 심볼 간 연결 관계를 분석합니다. 선 검출 결과를 기반으로 배관, 밸브, 기기 간의 연결을 추적합니다." position="right" />
          {connectivityData && (
            <span className="px-2 py-0.5 text-xs font-normal bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300 rounded-full">
              {connectivityData.statistics.total_connections}개 연결
            </span>
          )}
        </h2>
        <button
          onClick={onAnalyzeConnectivity}
          disabled={isAnalyzingConnectivity || detections.length === 0}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-rose-600 text-white rounded-lg hover:bg-rose-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isAnalyzingConnectivity ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              분석 중...
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4" />
              연결성 분석
            </>
          )}
        </button>
      </div>

      {/* 연결성 다이어그램 */}
      {connectivityData ? (
        <div className="relative border rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700" style={{ height: 400 }}>
          <img
            src={imageData}
            alt="P&ID with connectivity"
            className="w-full h-full object-contain"
          />
          <div className="absolute inset-0">
            <ConnectivityDiagram
              data={connectivityData}
              detections={detections}
              imageSize={imageSize}
              containerSize={{ width: 600, height: 400 }}
              selectedSymbolId={selectedSymbolId}
              highlightPath={highlightPath}
              onSymbolClick={(id) => {
                if (selectedSymbolId && selectedSymbolId !== id) {
                  // 두 심볼 선택 시 경로 찾기
                  onFindPath(selectedSymbolId, id);
                }
                setSelectedSymbolId(id);
              }}
              onSymbolHover={() => {}}
              showLabels={true}
              showOrphans={true}
            />
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <div className="w-12 h-12 mx-auto mb-2 text-gray-300 flex items-center justify-center">
            <svg className="w-full h-full" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <p>연결성 분석을 실행하여 심볼 간 연결을 분석하세요</p>
          <p className="text-sm text-gray-400 mt-1">
            {detections.length === 0
              ? '먼저 심볼 검출을 실행하세요'
              : `${detections.length}개 심볼 검출됨 - 분석 가능`}
          </p>
        </div>
      )}

      {/* 연결 통계 요약 */}
      {connectivityData && (
        <div className="mt-4 grid grid-cols-4 gap-4 text-center">
          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {connectivityData.statistics.total_symbols}
            </div>
            <div className="text-xs text-gray-500">전체 심볼</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-rose-600 dark:text-rose-400">
              {connectivityData.statistics.total_connections}
            </div>
            <div className="text-xs text-gray-500">연결 수</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {(connectivityData.statistics.connectivity_ratio * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-gray-500">연결률</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-3">
            <div className="text-2xl font-bold text-amber-600 dark:text-amber-400">
              {connectivityData.statistics.orphan_count}
            </div>
            <div className="text-xs text-gray-500">고립 심볼</div>
          </div>
        </div>
      )}

      {/* 선택된 심볼 정보 / 경로 찾기 안내 */}
      {selectedSymbolId && connectivityData && (
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm">
          <span className="font-medium text-blue-700 dark:text-blue-300">
            💡 다른 심볼을 클릭하면 두 심볼 간 연결 경로를 찾습니다.
          </span>
          {highlightPath && highlightPath.length > 1 && (
            <div className="mt-2 text-blue-600 dark:text-blue-400">
              경로: {highlightPath.map((id, i) => (
                <span key={id}>
                  {connectivityData.nodes[id]?.class_name || id}
                  {i < highlightPath.length - 1 && ' → '}
                </span>
              ))}
            </div>
          )}
          <button
            onClick={() => { setSelectedSymbolId(null); setHighlightPath(null); }}
            className="mt-2 text-xs text-blue-500 hover:underline"
          >
            선택 해제
          </button>
        </div>
      )}
    </section>
  );
}
