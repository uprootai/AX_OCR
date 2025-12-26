/**
 * Long-term Roadmap Features Section
 * 장기 로드맵 4개 기능 UI 섹션
 * - 도면 영역 세분화
 * - 주석/노트 추출
 * - 리비전 비교
 * - VLM 자동 분류
 */

import { Loader2, RefreshCw } from 'lucide-react';
import { InfoTooltip } from '../../../components/Tooltip';
import type { SectionVisibility } from '../types/workflow';
import type {
  DrawingRegion,
  ExtractedNote,
  RevisionChange,
  VLMClassificationResult,
} from '../../../lib/api';

interface Session {
  session_id: string;
  filename?: string;
}

interface LongTermSectionProps {
  currentSession: Session | null;
  imageData: string | null;
  visibility: SectionVisibility;
  sessions: Session[];

  // 도면 영역 세분화
  drawingRegions: DrawingRegion[];
  isSegmentingRegions: boolean;
  selectedRegionId: string | null;
  onSelectRegion: (id: string | null) => void;
  onSegmentRegions: () => void;

  // 주석/노트 추출
  extractedNotes: ExtractedNote[];
  isExtractingNotes: boolean;
  selectedNoteId: string | null;
  onSelectNote: (id: string | null) => void;
  onExtractNotes: () => void;

  // 리비전 비교
  revisionChanges: RevisionChange[];
  isComparingRevisions: boolean;
  comparisonSessionId: string;
  onComparisonSessionChange: (id: string) => void;
  onCompareRevisions: () => void;

  // VLM 자동 분류
  vlmClassification: VLMClassificationResult | null;
  isVlmClassifying: boolean;
  onVlmClassify: () => void;
}

export function LongTermSection({
  currentSession,
  imageData,
  visibility,
  sessions,
  drawingRegions,
  isSegmentingRegions,
  selectedRegionId,
  onSelectRegion,
  onSegmentRegions,
  extractedNotes,
  isExtractingNotes,
  selectedNoteId,
  onSelectNote,
  onExtractNotes,
  revisionChanges,
  isComparingRevisions,
  comparisonSessionId,
  onComparisonSessionChange,
  onCompareRevisions,
  vlmClassification,
  isVlmClassifying,
  onVlmClassify,
}: LongTermSectionProps) {
  if (!currentSession || !imageData) return null;

  return (
    <>
      {/* 1. 도면 영역 세분화 */}
      {visibility.drawingRegionSegmentation && (
        <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              🗺️ 도면 영역 세분화
              <InfoTooltip content="SAM/U-Net 모델을 사용하여 도면의 뷰 영역(정면도, 측면도, 단면도, 상세도, 표제란 등)을 자동으로 구분합니다." position="right" />
              {drawingRegions.length > 0 && (
                <span className="px-2 py-0.5 text-xs font-normal bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 rounded-full">
                  {drawingRegions.length}개 영역
                </span>
              )}
            </h2>
            <button
              onClick={onSegmentRegions}
              disabled={isSegmentingRegions}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSegmentingRegions ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  분석 중...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  영역 분석
                </>
              )}
            </button>
          </div>

          {drawingRegions.length > 0 ? (
            <div className="space-y-4">
              <div className="grid grid-cols-5 gap-3">
                {['front', 'side', 'section', 'detail', 'title_block'].map((type) => {
                  const count = drawingRegions.filter(r => r.view_type === type).length;
                  return (
                    <div key={type} className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-3 text-center">
                      <p className="text-lg font-bold text-indigo-600">{count}</p>
                      <p className="text-xs text-gray-500 capitalize">{type.replace('_', ' ')}</p>
                    </div>
                  );
                })}
              </div>

              <div className="space-y-2 max-h-64 overflow-y-auto">
                {drawingRegions.map((region) => (
                  <div
                    key={region.id}
                    onClick={() => onSelectRegion(selectedRegionId === region.id ? null : region.id)}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedRegionId === region.id
                        ? 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-300'
                        : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 hover:border-indigo-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium capitalize">{region.view_type.replace('_', ' ')}</span>
                      <span className="text-xs text-gray-500">{(region.confidence * 100).toFixed(0)}%</span>
                    </div>
                    {region.label && <p className="text-sm text-gray-500 mt-1">{region.label}</p>}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🗺️</div>
              <p>영역 분석을 실행하여 도면 뷰를 자동 구분하세요</p>
              <p className="text-sm text-gray-400 mt-1">정면도, 측면도, 단면도, 상세도 등을 자동 검출</p>
            </div>
          )}
        </section>
      )}

      {/* 2. 주석/노트 추출 */}
      {visibility.notesExtraction && (
        <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              📋 주석/노트 추출
              <InfoTooltip content="OCR과 LLM을 활용하여 도면의 주석, 노트, 재료 정보, 열처리 조건 등을 자동으로 추출하고 분류합니다." position="right" />
              {extractedNotes.length > 0 && (
                <span className="px-2 py-0.5 text-xs font-normal bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300 rounded-full">
                  {extractedNotes.length}개 노트
                </span>
              )}
            </h2>
            <button
              onClick={onExtractNotes}
              disabled={isExtractingNotes}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isExtractingNotes ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  추출 중...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  노트 추출
                </>
              )}
            </button>
          </div>

          {extractedNotes.length > 0 ? (
            <div className="space-y-4">
              <div className="grid grid-cols-4 gap-3">
                {['material', 'tolerance', 'surface_finish', 'general'].map((cat) => {
                  const count = extractedNotes.filter(n => n.category === cat).length;
                  const colors: Record<string, string> = {
                    material: 'bg-blue-50 text-blue-600',
                    tolerance: 'bg-green-50 text-green-600',
                    surface_finish: 'bg-orange-50 text-orange-600',
                    general: 'bg-gray-50 text-gray-600',
                  };
                  return (
                    <div key={cat} className={`${colors[cat] || 'bg-gray-50 text-gray-600'} dark:bg-opacity-20 rounded-lg p-3 text-center`}>
                      <p className="text-lg font-bold">{count}</p>
                      <p className="text-xs capitalize">{cat.replace('_', ' ')}</p>
                    </div>
                  );
                })}
              </div>

              <div className="space-y-2 max-h-64 overflow-y-auto">
                {extractedNotes.map((note) => (
                  <div
                    key={note.id}
                    onClick={() => onSelectNote(selectedNoteId === note.id ? null : note.id)}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedNoteId === note.id
                        ? 'bg-teal-50 dark:bg-teal-900/20 border-teal-300'
                        : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 hover:border-teal-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className={`px-2 py-0.5 text-xs rounded-full ${
                        note.category === 'material' ? 'bg-blue-100 text-blue-700' :
                        note.category === 'tolerance' ? 'bg-green-100 text-green-700' :
                        note.category === 'surface_finish' ? 'bg-orange-100 text-orange-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {note.category.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-gray-500">{(note.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-sm">{note.text}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">📋</div>
              <p>노트 추출을 실행하여 주석 정보를 추출하세요</p>
              <p className="text-sm text-gray-400 mt-1">재료, 공차, 가공 방법, 일반 주석 자동 분류</p>
            </div>
          )}
        </section>
      )}

      {/* 3. 리비전 비교 */}
      {visibility.revisionComparison && (
        <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              🔄 리비전 비교
              <InfoTooltip content="SIFT/ORB 특징점 매칭을 사용하여 두 도면 버전 간의 변경점을 감지합니다." position="right" />
              {revisionChanges.length > 0 && (
                <span className="px-2 py-0.5 text-xs font-normal bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300 rounded-full">
                  {revisionChanges.length}개 변경
                </span>
              )}
            </h2>
            <div className="flex items-center gap-2">
              <select
                value={comparisonSessionId}
                onChange={(e) => onComparisonSessionChange(e.target.value)}
                className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
              >
                <option value="">비교할 세션 선택...</option>
                {sessions.filter(s => s.session_id !== currentSession.session_id).map(s => (
                  <option key={s.session_id} value={s.session_id}>
                    {s.filename || s.session_id.slice(0, 8)}
                  </option>
                ))}
              </select>
              <button
                onClick={onCompareRevisions}
                disabled={isComparingRevisions || !comparisonSessionId}
                className="flex items-center gap-2 px-4 py-2 text-sm bg-violet-600 text-white rounded-lg hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isComparingRevisions ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    비교 중...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    비교 실행
                  </>
                )}
              </button>
            </div>
          </div>

          {revisionChanges.length > 0 ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3">
                {['added', 'modified', 'deleted'].map((type) => {
                  const count = revisionChanges.filter(c => c.change_type === type).length;
                  const colors: Record<string, string> = {
                    added: 'bg-green-50 text-green-600',
                    modified: 'bg-yellow-50 text-yellow-600',
                    deleted: 'bg-red-50 text-red-600',
                  };
                  const icons: Record<string, string> = { added: '+', modified: '~', deleted: '-' };
                  return (
                    <div key={type} className={`${colors[type]} dark:bg-opacity-20 rounded-lg p-3 text-center`}>
                      <p className="text-lg font-bold">{icons[type]}{count}</p>
                      <p className="text-xs capitalize">{type}</p>
                    </div>
                  );
                })}
              </div>

              <div className="space-y-2 max-h-64 overflow-y-auto">
                {revisionChanges.map((change, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-lg border ${
                      change.change_type === 'added' ? 'bg-green-50 dark:bg-green-900/20 border-green-200' :
                      change.change_type === 'modified' ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200' :
                      'bg-red-50 dark:bg-red-900/20 border-red-200'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 text-xs rounded-full ${
                        change.change_type === 'added' ? 'bg-green-200 text-green-800' :
                        change.change_type === 'modified' ? 'bg-yellow-200 text-yellow-800' :
                        'bg-red-200 text-red-800'
                      }`}>
                        {change.change_type}
                      </span>
                      <span className="text-xs text-gray-500">{change.category}</span>
                    </div>
                    {change.description && <p className="text-sm">{change.description}</p>}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🔄</div>
              <p>비교할 세션을 선택하고 리비전 비교를 실행하세요</p>
              <p className="text-sm text-gray-400 mt-1">추가, 수정, 삭제된 요소를 자동 감지</p>
            </div>
          )}
        </section>
      )}

      {/* 4. VLM 자동 분류 */}
      {visibility.vlmAutoClassification && (
        <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              🤖 VLM 자동 분류
              <InfoTooltip content="Vision-Language Model을 사용하여 도면의 타입, 산업분야, 복잡도를 자동으로 분류합니다." position="right" />
              {vlmClassification && (
                <span className="px-2 py-0.5 text-xs font-normal bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 rounded-full">
                  {vlmClassification.drawing_type}
                </span>
              )}
            </h2>
            <button
              onClick={onVlmClassify}
              disabled={isVlmClassifying}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isVlmClassifying ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  분류 중...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  VLM 분류
                </>
              )}
            </button>
          </div>

          {vlmClassification ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 text-center">
                  <p className="text-xs text-gray-500 mb-1">도면 타입</p>
                  <p className="text-lg font-bold text-purple-600">{vlmClassification.drawing_type}</p>
                  <p className="text-xs text-gray-400">{(vlmClassification.drawing_type_confidence * 100).toFixed(0)}%</p>
                </div>
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center">
                  <p className="text-xs text-gray-500 mb-1">산업분야</p>
                  <p className="text-lg font-bold text-blue-600">{vlmClassification.industry_domain}</p>
                  <p className="text-xs text-gray-400">{(vlmClassification.industry_confidence * 100).toFixed(0)}%</p>
                </div>
                <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center">
                  <p className="text-xs text-gray-500 mb-1">복잡도</p>
                  <p className="text-lg font-bold text-green-600">{vlmClassification.complexity}</p>
                </div>
              </div>

              {vlmClassification.recommended_features && vlmClassification.recommended_features.length > 0 && (
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <p className="text-sm font-medium mb-2">추천 기능:</p>
                  <div className="flex flex-wrap gap-2">
                    {vlmClassification.recommended_features.map((feature, idx) => (
                      <span key={idx} className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full">
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {vlmClassification.analysis_summary && (
                <p className="text-sm text-gray-600 dark:text-gray-400 italic">
                  💡 {vlmClassification.analysis_summary}
                </p>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🤖</div>
              <p>VLM 분류를 실행하여 도면을 자동 분석하세요</p>
              <p className="text-sm text-gray-400 mt-1">도면 타입, 산업분야, 복잡도 및 추천 기능 제공</p>
            </div>
          )}
        </section>
      )}
    </>
  );
}
