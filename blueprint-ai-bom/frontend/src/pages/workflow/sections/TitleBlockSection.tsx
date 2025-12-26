/**
 * Title Block Section
 * 표제란 OCR 섹션 컴포넌트
 */

import { Loader2, RefreshCw } from 'lucide-react';
import { InfoTooltip } from '../../../components/Tooltip';
import type { TitleBlockData } from '../../../lib/api';

interface TitleBlockSectionProps {
  titleBlockData: TitleBlockData | null;
  editingTitleBlock: TitleBlockData | null;
  setEditingTitleBlock: (data: TitleBlockData | null) => void;
  isExtractingTitleBlock: boolean;
  onExtractTitleBlock: () => void;
  onUpdateTitleBlock: () => void;
}

export function TitleBlockSection({
  titleBlockData,
  editingTitleBlock,
  setEditingTitleBlock,
  isExtractingTitleBlock,
  onExtractTitleBlock,
  onUpdateTitleBlock,
}: TitleBlockSectionProps) {
  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          📝 표제란 OCR
          <InfoTooltip content="도면 표제란에서 도면번호, 리비전, 날짜, 스케일 등 메타데이터를 자동으로 추출합니다." position="right" />
          {titleBlockData?.drawing_number && (
            <span className="px-2 py-0.5 text-xs font-normal bg-slate-100 text-slate-700 dark:bg-slate-900/30 dark:text-slate-300 rounded-full">
              {titleBlockData.drawing_number}
            </span>
          )}
        </h2>
        <div className="flex items-center gap-2">
          {titleBlockData && !editingTitleBlock && (
            <button
              onClick={() => setEditingTitleBlock(titleBlockData)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600 dark:text-slate-400 border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
            >
              ✏️ 수정
            </button>
          )}
          <button
            onClick={onExtractTitleBlock}
            disabled={isExtractingTitleBlock}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-slate-600 text-white rounded-lg hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isExtractingTitleBlock ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                추출 중...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                표제란 추출
              </>
            )}
          </button>
        </div>
      </div>

      {/* 표제란 정보 표시 */}
      {titleBlockData ? (
        <div className="space-y-4">
          {/* 편집 모드 */}
          {editingTitleBlock ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">도면번호</label>
                  <input
                    type="text"
                    value={editingTitleBlock.drawing_number || ''}
                    onChange={(e) => setEditingTitleBlock({ ...editingTitleBlock, drawing_number: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">리비전</label>
                  <input
                    type="text"
                    value={editingTitleBlock.revision || ''}
                    onChange={(e) => setEditingTitleBlock({ ...editingTitleBlock, revision: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">도면 제목</label>
                  <input
                    type="text"
                    value={editingTitleBlock.drawing_title || ''}
                    onChange={(e) => setEditingTitleBlock({ ...editingTitleBlock, drawing_title: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">날짜</label>
                  <input
                    type="text"
                    value={editingTitleBlock.date || ''}
                    onChange={(e) => setEditingTitleBlock({ ...editingTitleBlock, date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">스케일</label>
                  <input
                    type="text"
                    value={editingTitleBlock.scale || ''}
                    onChange={(e) => setEditingTitleBlock({ ...editingTitleBlock, scale: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">회사</label>
                  <input
                    type="text"
                    value={editingTitleBlock.company || ''}
                    onChange={(e) => setEditingTitleBlock({ ...editingTitleBlock, company: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={onUpdateTitleBlock}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                >
                  ✓ 저장
                </button>
                <button
                  onClick={() => setEditingTitleBlock(null)}
                  className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-400 text-sm"
                >
                  취소
                </button>
              </div>
            </div>
          ) : (
            /* 읽기 모드 */
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {titleBlockData.drawing_number && (
                <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                  <div className="text-xs text-slate-500 mb-1">도면번호</div>
                  <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.drawing_number}</div>
                </div>
              )}
              {titleBlockData.revision && (
                <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                  <div className="text-xs text-slate-500 mb-1">리비전</div>
                  <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.revision}</div>
                </div>
              )}
              {titleBlockData.drawing_title && (
                <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3 col-span-2">
                  <div className="text-xs text-slate-500 mb-1">도면 제목</div>
                  <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.drawing_title}</div>
                </div>
              )}
              {titleBlockData.date && (
                <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                  <div className="text-xs text-slate-500 mb-1">날짜</div>
                  <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.date}</div>
                </div>
              )}
              {titleBlockData.scale && (
                <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                  <div className="text-xs text-slate-500 mb-1">스케일</div>
                  <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.scale}</div>
                </div>
              )}
              {titleBlockData.material && (
                <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                  <div className="text-xs text-slate-500 mb-1">재료</div>
                  <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.material}</div>
                </div>
              )}
              {titleBlockData.company && (
                <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                  <div className="text-xs text-slate-500 mb-1">회사</div>
                  <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.company}</div>
                </div>
              )}
              {titleBlockData.drawn_by && (
                <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                  <div className="text-xs text-slate-500 mb-1">작성자</div>
                  <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.drawn_by}</div>
                </div>
              )}
              {titleBlockData.checked_by && (
                <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                  <div className="text-xs text-slate-500 mb-1">검토자</div>
                  <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.checked_by}</div>
                </div>
              )}
              {titleBlockData.approved_by && (
                <div className="bg-slate-50 dark:bg-slate-900/30 rounded-lg p-3">
                  <div className="text-xs text-slate-500 mb-1">승인자</div>
                  <div className="font-semibold text-slate-800 dark:text-slate-200">{titleBlockData.approved_by}</div>
                </div>
              )}
            </div>
          )}

          {/* 원본 텍스트 표시 (디버깅용) */}
          {titleBlockData.raw_text && (
            <details className="mt-4">
              <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                📄 원본 텍스트 보기
              </summary>
              <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-900 rounded-lg text-xs overflow-x-auto whitespace-pre-wrap">
                {titleBlockData.raw_text}
              </pre>
            </details>
          )}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <div className="w-12 h-12 mx-auto mb-2 text-gray-300 flex items-center justify-center text-4xl">
            📝
          </div>
          <p>표제란 추출을 실행하여 도면 메타데이터를 가져오세요</p>
          <p className="text-sm text-gray-400 mt-1">
            도면번호, 리비전, 날짜, 스케일 등의 정보를 자동으로 인식합니다
          </p>
        </div>
      )}
    </section>
  );
}
