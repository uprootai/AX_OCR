/**
 * PIDWorkflowSection - P&ID 검출 전용 워크플로우
 *
 * web-ui 네이티브 구현 (다크모드 지원)
 */

import { useRef, useState, useEffect } from 'react';
import {
  Upload,
  FileText,
  CheckCircle,
  Clock,
  ExternalLink,
  Loader2,
  AlertCircle,
  Search,
  ImageIcon,
  Unlink,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { projectApi, type ProjectDetail } from '../../../lib/blueprintBomApi';
import { Tooltip } from '../../../components/ui/Tooltip';

interface PIDWorkflowSectionProps {
  projectId: string;
  project: ProjectDetail;
  onRefresh: () => void;
  onUnlinkSession?: (sessionId: string) => Promise<void>;
  unlinkingSessionId?: string | null;
}

const PAGE_SIZE = 10;

export function PIDWorkflowSection({
  projectId,
  project,
  onRefresh,
  onUnlinkSession,
  unlinkingSessionId,
}: PIDWorkflowSectionProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const sessions = project.sessions ?? [];
  const totalPages = Math.max(1, Math.ceil(sessions.length / PAGE_SIZE));
  const pagedSessions = sessions.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const [thumbnails, setThumbnails] = useState<Record<string, string>>({});

  // 페이지 범위 보정
  useEffect(() => {
    if (page >= totalPages) setPage(Math.max(0, totalPages - 1));
  }, [page, totalPages]);

  useEffect(() => {
    pagedSessions.forEach((session) => {
      if (thumbnails[session.session_id]) return;
      fetch(projectApi.getSessionImageUrl(session.session_id))
        .then((res) => res.json())
        .then((data) => {
          if (data.image_base64 && data.mime_type) {
            setThumbnails((prev) => ({
              ...prev,
              [session.session_id]: `data:${data.mime_type};base64,${data.image_base64}`,
            }));
          }
        })
        .catch(() => {});
    });
  }, [pagedSessions]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setIsUploading(true);
    setError(null);
    try {
      await projectApi.batchUpload(projectId, Array.from(files));
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : '업로드에 실패했습니다.');
    } finally {
      setIsUploading(false);
    }
  };

  const statusIcon = (status: string) => {
    if (status === 'completed') return <CheckCircle className="w-4 h-4 text-green-500 dark:text-green-400" />;
    if (status === 'error') return <AlertCircle className="w-4 h-4 text-red-500 dark:text-red-400" />;
    return <Clock className="w-4 h-4 text-yellow-500 dark:text-yellow-400" />;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 mb-6">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Search className="w-5 h-5 text-cyan-500 dark:text-cyan-400" />
          <Tooltip content="P&ID 도면을 업로드하면 YOLO로 심볼을 자동 검출하고, 사람이 검증한 뒤 GT 비교·BOM 생성까지 수행하는 워크플로우입니다." position="bottom">
            <h2 className="font-semibold text-gray-900 dark:text-white">P&ID 검출 워크플로우</h2>
          </Tooltip>
          <Tooltip content="현재 프로젝트에 연결된 P&ID 분석 세션 수입니다" position="bottom">
            <span className="px-1.5 py-0.5 text-[10px] font-medium rounded bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300">
              {sessions.length}개 세션
            </span>
          </Tooltip>
        </div>
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*,.pdf"
            className="hidden"
            onChange={(e) => handleUpload(e.target.files)}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="flex items-center gap-2 px-3 py-1.5 bg-cyan-500 dark:bg-cyan-600 text-white text-sm rounded-lg hover:bg-cyan-600 dark:hover:bg-cyan-700 transition-colors disabled:opacity-50"
          >
            {isUploading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Upload className="w-4 h-4" />
            )}
            도면 업로드
          </button>
        </div>
      </div>

      <div className="px-4 pt-3 pb-1">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          P&ID 도면 이미지를 업로드하면 세션이 생성됩니다. 각 세션의 <strong className="text-gray-700 dark:text-gray-300">"세션 열기"</strong>를 클릭하면
          검출 결과 확인, 심볼 검증, GT 비교 등을 수행할 수 있습니다.
        </p>
      </div>

      {error && (
        <div className="mx-4 mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      <div className="p-4">
        {sessions.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-12 h-12 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-3">
              <FileText className="w-6 h-6 text-gray-400 dark:text-gray-500" />
            </div>
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              위의 "도면 업로드" 버튼으로 P&ID 도면 이미지(JPG, PNG)를 업로드하세요.
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-2">
              {pagedSessions.map((session) => (
                <a
                  key={session.session_id}
                  href={`http://localhost:3000/workflow?session=${session.session_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-600 hover:bg-cyan-50 dark:hover:bg-cyan-900/20 hover:border-cyan-300 dark:hover:border-cyan-700 transition-colors group cursor-pointer"
                >
                  <div className="w-14 h-14 rounded-lg border border-gray-200 dark:border-gray-600 overflow-hidden shrink-0 bg-gray-50 dark:bg-gray-700 flex items-center justify-center">
                    {thumbnails[session.session_id] ? (
                      <img
                        src={thumbnails[session.session_id]}
                        alt={session.filename}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <ImageIcon className="w-5 h-5 text-gray-300 dark:text-gray-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {statusIcon(session.status)}
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate group-hover:text-cyan-700 dark:group-hover:text-cyan-300">
                        {session.filename}
                      </p>
                    </div>
                    <Tooltip content={`YOLO가 검출한 심볼 ${session.detection_count}개 중 사람이 검증한 ${session.verified_count}개`} position="bottom">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                        검출 {session.detection_count}개 · 검증 {session.verified_count}개
                      </p>
                    </Tooltip>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    session.status === 'completed'
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                      : session.status === 'error'
                        ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'
                        : 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-600 dark:text-cyan-400'
                  }`}>
                    {session.status}
                  </span>
                  <span className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-100 dark:bg-cyan-900/30 text-cyan-600 dark:text-cyan-400 text-xs font-medium rounded-lg group-hover:bg-cyan-200 dark:group-hover:bg-cyan-800/40 transition-colors">
                    <ExternalLink className="w-3.5 h-3.5" />
                    세션 열기
                  </span>
                  {onUnlinkSession && (
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        onUnlinkSession(session.session_id);
                      }}
                      disabled={unlinkingSessionId === session.session_id}
                      className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                      title="프로젝트에서 분리"
                    >
                      {unlinkingSessionId === session.session_id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Unlink className="w-4 h-4" />
                      )}
                    </button>
                  )}
                </a>
              ))}
            </div>

            {/* 페이지네이션 */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-30"
                >
                  <ChevronLeft className="w-4 h-4" />
                  이전
                </button>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {page + 1} / {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-30"
                >
                  다음
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
