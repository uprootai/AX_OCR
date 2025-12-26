/**
 * GDT Section
 * GD&T 기하공차 분석 섹션 컴포넌트
 */

import { Loader2, RefreshCw } from 'lucide-react';
import { InfoTooltip } from '../../../components/Tooltip';
import GDTEditor from '../../../components/GDTEditor';
import type { FeatureControlFrame, DatumFeature, GDTSummary } from '../../../components/GDTEditor';

interface GDTSectionProps {
  sessionId: string;
  imageData: string;
  imageSize: { width: number; height: number };
  fcfList: FeatureControlFrame[];
  gdtDatums: DatumFeature[];
  gdtSummary: GDTSummary | null;
  showGDT: boolean;
  setShowGDT: (show: boolean) => void;
  selectedFCFId: string | null;
  setSelectedFCFId: (id: string | null) => void;
  selectedDatumId: string | null;
  setSelectedDatumId: (id: string | null) => void;
  isParsingGDT: boolean;
  onParseGDT: () => void;
  onFCFUpdate: (fcfId: string, updates: Partial<FeatureControlFrame>) => void;
  onFCFDelete: (fcfId: string) => void;
  onDatumDelete: (datumId: string) => void;
}

export function GDTSection({
  sessionId,
  imageData,
  imageSize,
  fcfList,
  gdtDatums,
  gdtSummary,
  showGDT,
  setShowGDT,
  selectedFCFId,
  setSelectedFCFId,
  selectedDatumId,
  setSelectedDatumId,
  isParsingGDT,
  onParseGDT,
  onFCFUpdate,
  onFCFDelete,
  onDatumDelete,
}: GDTSectionProps) {
  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          &#128208; GD&T 기하공차
          <InfoTooltip content="기하 공차 (Geometric Dimensioning and Tolerancing): 직진도, 평면도, 위치도 등 14가지 기하 특성을 파싱합니다." position="right" />
          {fcfList.length > 0 && (
            <span className="px-2 py-0.5 text-xs font-normal bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 rounded-full">
              FCF {fcfList.length}개
            </span>
          )}
          {gdtDatums.length > 0 && (
            <span className="px-2 py-0.5 text-xs font-normal bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300 rounded-full">
              데이텀 {gdtDatums.length}개
            </span>
          )}
        </h2>
        <div className="flex items-center gap-2">
          {/* 토글 버튼 */}
          <button
            onClick={() => setShowGDT(!showGDT)}
            className={`px-3 py-1.5 text-xs rounded-lg transition-colors ${
              showGDT
                ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
            }`}
          >
            {showGDT ? 'GD&T 표시' : 'GD&T 숨김'}
          </button>
          {/* 파싱 버튼 */}
          <button
            onClick={onParseGDT}
            disabled={isParsingGDT}
            className="flex items-center gap-2 px-3 py-1.5 text-xs bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
          >
            {isParsingGDT ? (
              <>
                <Loader2 className="w-3 h-3 animate-spin" />
                파싱 중...
              </>
            ) : (
              <>
                <RefreshCw className="w-3 h-3" />
                GD&T 파싱
              </>
            )}
          </button>
        </div>
      </div>

      {/* GD&T 요약 통계 */}
      {gdtSummary && (fcfList.length > 0 || gdtDatums.length > 0) && (
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 text-center">
            <p className="text-lg font-bold text-purple-600">{gdtSummary.total_fcf}</p>
            <p className="text-xs text-gray-500">FCF</p>
          </div>
          <div className="bg-amber-50 dark:bg-amber-900/20 rounded-lg p-3 text-center">
            <p className="text-lg font-bold text-amber-600">{gdtSummary.total_datums}</p>
            <p className="text-xs text-gray-500">데이텀</p>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
            <p className="text-lg font-bold text-green-600">{gdtSummary.verified_fcf}</p>
            <p className="text-xs text-gray-500">검증됨</p>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 text-center">
            <p className="text-lg font-bold text-yellow-600">{gdtSummary.pending_fcf}</p>
            <p className="text-xs text-gray-500">대기중</p>
          </div>
        </div>
      )}

      {/* GD&T 에디터 */}
      {showGDT && (fcfList.length > 0 || gdtDatums.length > 0) && (
        <div className="relative border rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700" style={{ height: 400 }}>
          <img
            src={imageData}
            alt="Blueprint with GD&T"
            className="w-full h-full object-contain"
          />
          <GDTEditor
            sessionId={sessionId}
            fcfList={fcfList}
            datums={gdtDatums}
            imageSize={imageSize}
            containerSize={{ width: 600, height: 400 }}
            selectedFCFId={selectedFCFId}
            selectedDatumId={selectedDatumId}
            onFCFSelect={setSelectedFCFId}
            onDatumSelect={setSelectedDatumId}
            onFCFUpdate={onFCFUpdate}
            onFCFDelete={onFCFDelete}
            onDatumDelete={onDatumDelete}
            onParse={onParseGDT}
            isProcessing={isParsingGDT}
            showLabels={true}
          />
        </div>
      )}

      {/* 빈 상태 */}
      {fcfList.length === 0 && gdtDatums.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">&#128208;</div>
          <p>GD&T 파싱을 실행하여 기하공차를 분석하세요</p>
          <p className="text-sm text-gray-400 mt-1">직진도, 평면도, 위치도 등 14가지 기하 특성을 검출합니다</p>
        </div>
      )}
    </section>
  );
}
