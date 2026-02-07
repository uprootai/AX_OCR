/**
 * PIDWorkflowSection - P&ID 검출 전용 워크플로우
 * 세션 기반 심볼 검출 + GT 비교 요약
 */

import { useRef, useState } from 'react';
import {
  Upload,
  FileText,
  CheckCircle,
  Clock,
  ExternalLink,
  Loader2,
  AlertCircle,
  Search,
} from 'lucide-react';
import { projectApi, type ProjectDetail } from '../../../lib/api';

interface PIDWorkflowSectionProps {
  projectId: string;
  project: ProjectDetail;
  onRefresh: () => void;
}

export function PIDWorkflowSection({
  projectId,
  project,
  onRefresh,
}: PIDWorkflowSectionProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const sessions = project.sessions ?? [];

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
    if (status === 'completed') return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (status === 'error') return <AlertCircle className="w-4 h-4 text-red-500" />;
    return <Clock className="w-4 h-4 text-yellow-500" />;
  };

  return (
    <div className="bg-white rounded-xl border mb-6">
      <div className="p-4 border-b flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Search className="w-5 h-5 text-cyan-500" />
          <h2 className="font-semibold text-gray-900">P&ID 검출 워크플로우</h2>
          <span className="px-1.5 py-0.5 text-[10px] font-medium rounded bg-cyan-100 text-cyan-700">
            {sessions.length}개 세션
          </span>
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
            className="flex items-center gap-2 px-3 py-1.5 bg-cyan-500 text-white text-sm rounded-lg hover:bg-cyan-600 transition-colors disabled:opacity-50"
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

      {error && (
        <div className="mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-sm text-red-600">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      <div className="p-4">
        {sessions.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="w-10 h-10 mx-auto mb-3 text-gray-300" />
            <p className="text-gray-500 text-sm">P&ID 도면을 업로드하여 검출을 시작하세요.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {sessions.map((session) => (
              <a
                key={session.session_id}
                href={`http://localhost:5173/workflow?session=${session.session_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 p-3 rounded-lg border hover:bg-gray-50 transition-colors group"
              >
                {statusIcon(session.status)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {session.filename}
                  </p>
                  <p className="text-xs text-gray-500">
                    검출 {session.detection_count}개 · 검증 {session.verified_count}개
                  </p>
                </div>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  session.status === 'completed'
                    ? 'bg-green-100 text-green-600'
                    : session.status === 'error'
                      ? 'bg-red-100 text-red-600'
                      : 'bg-cyan-100 text-cyan-600'
                }`}>
                  {session.status}
                </span>
                <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-cyan-500" />
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
