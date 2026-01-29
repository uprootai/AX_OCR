/**
 * GTComparisonSection - Ground Truth 비교 섹션
 * GT 파일 업로드 및 비교 기능 (결과는 DetectionResultsSection에서 표시)
 */

import { useState, useRef, useEffect } from 'react';
import { Upload, BarChart3, FileJson, Trash2, Database, CloudUpload, RefreshCw, CheckCircle, X, FolderOpen } from 'lucide-react';
import { InfoTooltip } from '../../../components/Tooltip';

interface GTMatch {
  detection_idx: number;
  gt_bbox: { x1: number; y1: number; x2: number; y2: number };
  gt_class: string;
  iou: number;
  class_match: boolean;
}

interface FNLabel {
  bbox: { x1: number; y1: number; x2: number; y2: number };
  class_name: string;
}

export interface GTFile {
  filename: string;
  label_file: string;
  size: number;
  source: 'uploaded' | 'reference';
}

interface GTCompareResult {
  gt_count: number;
  tp_matches: GTMatch[];
  fn_labels: FNLabel[];
  metrics: {
    f1_score: number;
    precision: number;
    recall: number;
    tp: number;
    fp: number;
    fn: number;
  };
}

interface GTComparisonSectionProps {
  sessionId: string;
  gtCompareResult: GTCompareResult | null;
  detectionCount: number;
  onUploadGT: (file: File) => Promise<void>;
  onCompare: () => Promise<void>;
  isLoading: boolean;
  apiBaseUrl: string;
  // GT 관리 기능
  gtFiles?: GTFile[];
  onDeleteGT?: (filename: string) => Promise<void>;
  onRefreshGTList?: () => Promise<void>;
  onSelectGT?: (filename: string) => void;
  selectedGT?: string | null;
  // 새로 추가: GT 초기화 콜백
  onClearGT?: () => void;
}

export function GTComparisonSection({
  sessionId: _sessionId,
  gtCompareResult,
  detectionCount,
  onUploadGT,
  onCompare,
  isLoading,
  gtFiles = [],
  onDeleteGT,
  onRefreshGTList,
  onSelectGT,
  selectedGT,
  onClearGT,
}: GTComparisonSectionProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [showGTList, setShowGTList] = useState(false);
  const [deletingFile, setDeletingFile] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // GT 비교 완료 시 파일명 동기화
  useEffect(() => {
    if (gtCompareResult && !uploadedFileName) {
      // gtCompareResult가 있지만 uploadedFileName이 없는 경우
      // 자동 로드된 GT 파일이 있을 수 있음
      if (selectedGT) {
        const gtFile = gtFiles.find(f => f.filename === selectedGT);
        if (gtFile) {
          setUploadedFileName(gtFile.label_file);
        }
      }
    }
  }, [gtCompareResult, selectedGT, gtFiles, uploadedFileName]);

  // GT 비교 완료 여부
  const isComparisonComplete = gtCompareResult !== null;

  // 현재 로드된 GT 파일 정보
  const currentGTFile = gtFiles.find(f => f.filename === selectedGT || f.label_file === uploadedFileName);

  const handleDeleteGT = async (filename: string) => {
    if (!onDeleteGT) return;
    setDeletingFile(filename);
    try {
      await onDeleteGT(filename);
      if (selectedGT === filename) {
        setUploadedFileName(null);
      }
    } finally {
      setDeletingFile(null);
    }
  };

  const handleClearGT = () => {
    setUploadedFileName(null);
    onClearGT?.();
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.name.endsWith('.json') || file.name.endsWith('.xml') || file.name.endsWith('.txt'))) {
      setUploadedFileName(file.name);
      await onUploadGT(file);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFileName(file.name);
      await onUploadGT(file);
    }
  };

  return (
    <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
        <BarChart3 className="w-5 h-5 text-orange-500" />
        GT 비교
        <InfoTooltip
          content="Ground Truth(정답 데이터)와 검출 결과를 비교하여 정밀도, 재현율, F1 스코어를 계산합니다."
          position="right"
        />
      </h2>

      {/* 상태에 따른 UI 분기 */}
      {isComparisonComplete ? (
        /* GT 비교 완료 상태 */
        <div className="space-y-3">
          {/* 로드된 GT 파일 정보 */}
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <div>
                  <p className="text-sm font-medium text-green-700 dark:text-green-300">
                    GT 로드 완료
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1 mt-0.5">
                    <FileJson className="w-3 h-3" />
                    {uploadedFileName || currentGTFile?.label_file || selectedGT || 'GT 파일'}
                    <span className="text-green-500">• {gtCompareResult.gt_count}개 라벨</span>
                  </p>
                </div>
              </div>
              <button
                onClick={handleClearGT}
                className="p-1.5 text-green-600 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                title="GT 초기화"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* 다른 GT 파일 선택 옵션 */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex-1 flex items-center justify-center gap-2 py-2 px-3 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <Upload className="w-4 h-4" />
              다른 GT 업로드
            </button>
            {gtFiles.length > 0 && (
              <button
                onClick={() => setShowGTList(!showGTList)}
                className="flex items-center justify-center gap-2 py-2 px-3 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <FolderOpen className="w-4 h-4" />
                목록 ({gtFiles.length})
              </button>
            )}
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept=".json,.xml,.txt"
            className="hidden"
            onChange={handleFileSelect}
          />

          {/* 안내 메시지 */}
          <p className="text-xs text-center text-gray-500 dark:text-gray-400">
            비교 결과는 위 "AI 검출 결과" 섹션에서 확인하세요
          </p>
        </div>
      ) : isLoading ? (
        /* GT 자동 로딩 중 */
        <div className="flex items-center justify-center gap-2 py-6 text-gray-500 dark:text-gray-400">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span className="text-sm">GT 확인 중...</span>
        </div>
      ) : (
        /* GT 파일 미선택 또는 비교 전 상태 */
        <>
          {/* GT 파일 업로드 영역 */}
          <div
            className={`border-2 border-dashed rounded-lg p-4 mb-4 transition-colors ${
              isDragging
                ? 'border-orange-500 bg-orange-50 dark:bg-orange-900/20'
                : uploadedFileName
                ? 'border-green-300 bg-green-50/50 dark:border-green-700 dark:bg-green-900/10'
                : 'border-gray-300 dark:border-gray-600'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,.xml,.txt"
              className="hidden"
              onChange={handleFileSelect}
            />
            <div className="text-center">
              {uploadedFileName ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-center gap-2 text-green-600 dark:text-green-400">
                    <FileJson className="w-5 h-5" />
                    <span className="font-medium">{uploadedFileName}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setUploadedFileName(null);
                      }}
                      className="p-0.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded"
                      title="선택 취소"
                    >
                      <X className="w-4 h-4 text-gray-400 hover:text-red-500" />
                    </button>
                  </div>
                  <p className="text-xs text-gray-500">
                    아래 버튼을 클릭하여 비교를 실행하세요
                  </p>
                </div>
              ) : (
                <>
                  <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    GT 파일을 드래그하거나{' '}
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="text-orange-600 hover:text-orange-700 font-medium"
                    >
                      클릭하여 선택
                    </button>
                  </p>
                  <p className="text-xs text-gray-500 mt-1">JSON, XML, TXT (YOLO) 형식</p>
                </>
              )}
            </div>
          </div>

          {/* 비교 버튼 */}
          <button
            onClick={onCompare}
            disabled={!uploadedFileName || isLoading || detectionCount === 0}
            className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
              !uploadedFileName || isLoading || detectionCount === 0
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-gray-700'
                : 'bg-orange-500 text-white hover:bg-orange-600'
            }`}
          >
            {isLoading ? '비교 중...' : 'GT 비교 실행'}
          </button>
        </>
      )}

      {/* GT 파일 목록 (비교 완료/미완료 모두에서 표시 가능) */}
      {showGTList && gtFiles.length > 0 && (
        <div className="mt-3 border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
          {/* 목록 헤더 */}
          <div className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-600">
            <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
              사용 가능한 GT 파일
            </span>
            <div className="flex items-center gap-1">
              {onRefreshGTList && (
                <button
                  onClick={onRefreshGTList}
                  className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                  title="목록 새로고침"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              )}
              <button
                onClick={() => setShowGTList(false)}
                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                title="닫기"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* 파일 목록 */}
          <div className="max-h-48 overflow-y-auto">
            {gtFiles.map((file) => (
              <div
                key={file.filename}
                className={`flex items-center justify-between px-3 py-2 border-b border-gray-100 dark:border-gray-700 last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors ${
                  selectedGT === file.filename || uploadedFileName === file.label_file
                    ? 'bg-orange-50 dark:bg-orange-900/20'
                    : ''
                }`}
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  {/* 소스 배지 */}
                  {file.source === 'uploaded' ? (
                    <span
                      className="flex items-center gap-1 px-1.5 py-0.5 text-xs rounded bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400"
                      title="업로드된 파일"
                    >
                      <CloudUpload className="w-3 h-3" />
                    </span>
                  ) : (
                    <span
                      className="flex items-center gap-1 px-1.5 py-0.5 text-xs rounded bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400"
                      title="레퍼런스 파일"
                    >
                      <Database className="w-3 h-3" />
                    </span>
                  )}

                  {/* 파일명 (선택 가능) */}
                  <button
                    onClick={() => {
                      onSelectGT?.(file.filename);
                      setUploadedFileName(file.label_file);
                      setShowGTList(false);
                    }}
                    className="text-sm text-gray-700 dark:text-gray-300 hover:text-orange-600 dark:hover:text-orange-400 truncate text-left"
                    title={`${file.filename} 선택`}
                  >
                    {file.filename}
                  </button>
                </div>

                {/* 삭제 버튼 (업로드된 파일만) */}
                {file.source === 'uploaded' && onDeleteGT && (
                  <button
                    onClick={() => handleDeleteGT(file.filename)}
                    disabled={deletingFile === file.filename}
                    className="p-1 text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors disabled:opacity-50"
                    title="삭제"
                  >
                    {deletingFile === file.filename ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
