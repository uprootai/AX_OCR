/**
 * GTManagementModal - GT 라벨 관리 모달
 */

import { useState, useEffect, useRef } from 'react';
import { X, Database, Upload, FileText, Loader2 } from 'lucide-react';
import { projectApi } from '../../../lib/blueprintBomApi';

interface GTManagementModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
}

export function GTManagementModal({
  isOpen,
  onClose,
  projectId,
}: GTManagementModalProps) {
  const [gtFiles, setGtFiles] = useState<string[]>([]);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadGTFiles = async () => {
    setIsLoadingList(true);
    setError(null);
    try {
      const result = await projectApi.listGT(projectId);
      setGtFiles(result.gt_files);
    } catch (err) {
      console.error('Failed to load GT files:', err);
      setError('GT 파일 목록을 불러오는데 실패했습니다.');
    } finally {
      setIsLoadingList(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      setUploadResult(null);
      setError(null);
      loadGTFiles();
    }
  }, [isOpen, projectId]);

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setIsUploading(true);
    setError(null);
    setUploadResult(null);
    try {
      const result = await projectApi.uploadGT(projectId, Array.from(files));
      setUploadResult(
        `${result.uploaded.length}개 업로드 완료` +
        (result.failed.length > 0 ? `, ${result.failed.length}개 실패` : '')
      );
      await loadGTFiles();
    } catch (err) {
      console.error('Failed to upload GT files:', err);
      setError('GT 파일 업로드에 실패했습니다.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-md mx-4">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-5 border-b dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
              <Database className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">GT 관리</h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">Ground Truth 라벨 파일</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {/* 본문 */}
        <div className="p-5 space-y-4">
          {/* 업로드 영역 */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              GT 파일 ({gtFiles.length}개)
            </span>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:opacity-50"
            >
              {isUploading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Upload className="w-3.5 h-3.5" />
              )}
              업로드
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".txt"
              className="hidden"
              onChange={(e) => handleUpload(e.target.files)}
            />
          </div>

          {/* 결과 메시지 */}
          {uploadResult && (
            <div className="p-2.5 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-sm text-green-600 dark:text-green-400">
              {uploadResult}
            </div>
          )}
          {error && (
            <div className="p-2.5 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400">
              {error}
            </div>
          )}

          {/* 파일 목록 */}
          <div className="border dark:border-gray-700 rounded-lg overflow-hidden max-h-64 overflow-y-auto">
            {isLoadingList ? (
              <div className="p-8 flex items-center justify-center">
                <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
              </div>
            ) : gtFiles.length === 0 ? (
              <div className="p-8 text-center">
                <FileText className="w-8 h-8 mx-auto mb-2 text-gray-300 dark:text-gray-600" />
                <p className="text-sm text-gray-500 dark:text-gray-400">GT 파일이 없습니다.</p>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  .txt 파일을 업로드하세요.
                </p>
              </div>
            ) : (
              <div className="divide-y dark:divide-gray-700">
                {gtFiles.map((filename) => (
                  <div
                    key={filename}
                    className="flex items-center gap-3 px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    <FileText className="w-4 h-4 text-gray-400 dark:text-gray-500 shrink-0" />
                    <span className="text-sm text-gray-700 dark:text-gray-300 truncate">
                      {filename}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 푸터 */}
        <div className="p-5 border-t dark:border-gray-700">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 border dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition-colors"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}
