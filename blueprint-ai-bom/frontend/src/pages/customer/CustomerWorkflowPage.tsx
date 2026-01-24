/**
 * CustomerWorkflowPage - 고객용 워크플로우 페이지
 * Phase 2F: 제한된 권한의 고객용 UI
 * - 워크플로우 읽기 전용 표시
 * - 이미지 업로드 가능
 * - 분석 실행 가능
 * - 워크플로우/모델/파라미터 수정 불가
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  FolderOpen,
  Upload,
  Eye,
  RefreshCw,
  Loader2,
  Lock,
  Images,
  CheckCircle,
  Clock,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { projectApi, sessionApi, type ProjectDetail, type SessionImage, type SessionImageProgress } from '../../lib/api';

export function CustomerWorkflowPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [images, setImages] = useState<SessionImage[]>([]);
  const [progress, setProgress] = useState<SessionImageProgress | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 프로젝트 및 데이터 로드
  const loadData = useCallback(async () => {
    if (!projectId) return;
    setIsLoading(true);
    setError(null);
    try {
      const projectData = await projectApi.get(projectId);
      setProject(projectData);

      // 첫 번째 세션의 이미지 목록 로드 (간단한 구현)
      if (projectData.sessions.length > 0) {
        const sessionId = projectData.sessions[0].session_id;
        const [imageList, progressData] = await Promise.all([
          sessionApi.listImages(sessionId),
          sessionApi.getImageProgress(sessionId),
        ]);
        setImages(imageList);
        setProgress(progressData);
      }
    } catch (err) {
      console.error('Failed to load project:', err);
      setError('프로젝트를 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 이미지 업로드
  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0 || !project) return;
    setIsUploading(true);
    setError(null);
    try {
      // 각 파일을 개별 세션으로 업로드
      for (const file of Array.from(files)) {
        await sessionApi.upload(file);
      }
      await loadData();
    } catch (err) {
      console.error('Failed to upload files:', err);
      setError('파일 업로드에 실패했습니다.');
    } finally {
      setIsUploading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500">{error || '프로젝트를 찾을 수 없습니다.'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <FolderOpen className="w-6 h-6 text-blue-500" />
                <div>
                  <h1 className="text-xl font-bold text-gray-900">{project.name}</h1>
                  <p className="text-xs text-gray-500">{project.customer}</p>
                </div>
              </div>
              <span className="px-2 py-1 bg-blue-100 text-blue-600 text-xs rounded-full flex items-center gap-1">
                <Lock className="w-3 h-3" />
                고객 전용
              </span>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={loadData}
                disabled={isLoading}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <RefreshCw className={`w-5 h-5 text-gray-500 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
              >
                {isUploading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4" />
                )}
                도면 업로드
              </button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*,.pdf"
                className="hidden"
                onChange={(e) => handleUpload(e.target.files)}
              />
            </div>
          </div>
        </div>
      </header>

      {/* 워크플로우 정보 (읽기 전용) */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Lock className="w-4 h-4" />
            <span>워크플로우 설정은 관리자만 수정할 수 있습니다.</span>
            {project.default_template_name && (
              <span className="text-blue-600 font-medium">
                템플릿: {project.default_template_name}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* 메인 컨텐츠 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* 에러 메시지 */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 mb-6">
            {error}
          </div>
        )}

        {/* 진행률 */}
        {progress && progress.total_images > 0 && (
          <div className="bg-white rounded-xl border p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-900">검토 진행률</h2>
              <span className="text-lg font-bold text-blue-600">
                {progress.progress_percent.toFixed(1)}%
              </span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden flex">
              {progress.approved_count > 0 && (
                <div
                  className="h-full bg-green-500"
                  style={{ width: `${(progress.approved_count / progress.total_images) * 100}%` }}
                />
              )}
              {progress.modified_count > 0 && (
                <div
                  className="h-full bg-yellow-500"
                  style={{ width: `${(progress.modified_count / progress.total_images) * 100}%` }}
                />
              )}
              {progress.rejected_count > 0 && (
                <div
                  className="h-full bg-red-500"
                  style={{ width: `${(progress.rejected_count / progress.total_images) * 100}%` }}
                />
              )}
            </div>
            <div className="flex gap-4 mt-3 text-xs">
              <span className="flex items-center gap-1 text-green-600">
                <CheckCircle className="w-3 h-3" />
                승인 {progress.approved_count}
              </span>
              <span className="flex items-center gap-1 text-yellow-600">
                수정됨 {progress.modified_count}
              </span>
              <span className="flex items-center gap-1 text-gray-500">
                <Clock className="w-3 h-3" />
                대기 {progress.pending_count}
              </span>
            </div>
          </div>
        )}

        {/* 이미지 그리드 */}
        <div className="bg-white rounded-xl border">
          <div className="p-4 border-b flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Images className="w-5 h-5 text-gray-400" />
              <h2 className="font-semibold text-gray-900">도면 목록</h2>
              <span className="text-sm text-gray-500">({images.length}개)</span>
            </div>
          </div>

          {images.length === 0 ? (
            <div className="p-12 text-center">
              <Images className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500">업로드된 도면이 없습니다.</p>
              <p className="text-sm text-gray-400 mt-1">
                "도면 업로드" 버튼을 클릭하여 도면을 추가하세요.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 p-4">
              {images.map((image) => (
                <Link
                  key={image.image_id}
                  to={`/customer/${projectId}/review/${image.image_id}`}
                  className="group relative aspect-square bg-gray-100 rounded-lg overflow-hidden border-2 border-transparent hover:border-blue-500 transition-all"
                >
                  {image.thumbnail_base64 ? (
                    <img
                      src={`data:image/jpeg;base64,${image.thumbnail_base64}`}
                      alt={image.filename}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      <FileText className="w-8 h-8" />
                    </div>
                  )}

                  {/* 상태 배지 */}
                  <div
                    className={`absolute top-2 left-2 px-2 py-0.5 rounded-full text-xs font-medium ${
                      image.review_status === 'approved'
                        ? 'bg-green-100 text-green-600'
                        : image.review_status === 'rejected'
                          ? 'bg-red-100 text-red-600'
                          : image.review_status === 'modified'
                            ? 'bg-yellow-100 text-yellow-600'
                            : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {image.review_status}
                  </div>

                  {/* 검출 수 */}
                  {image.detection_count > 0 && (
                    <div className="absolute top-2 right-2 bg-black/60 text-white px-2 py-0.5 rounded-full text-xs">
                      {image.detection_count}
                    </div>
                  )}

                  {/* 호버 오버레이 */}
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                    <div className="flex items-center gap-1 text-white text-sm font-medium">
                      <Eye className="w-4 h-4" />
                      검토하기
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* 세션 목록 */}
        {project.sessions.length > 0 && (
          <div className="bg-white rounded-xl border mt-6">
            <div className="p-4 border-b">
              <h2 className="font-semibold text-gray-900">세션 이력</h2>
            </div>
            <div className="divide-y">
              {project.sessions.map((session) => (
                <div
                  key={session.session_id}
                  className="flex items-center gap-4 p-4"
                >
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">
                      {session.filename}
                    </p>
                    <p className="text-sm text-gray-500">
                      검출: {session.detection_count}개 | 검증: {session.verified_count}개
                    </p>
                  </div>
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      session.status === 'completed'
                        ? 'bg-green-100 text-green-600'
                        : 'bg-blue-100 text-blue-600'
                    }`}
                  >
                    {session.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default CustomerWorkflowPage;
