/**
 * CustomerSessionPage - 세션 기반 워크플로우 페이지
 * Phase 2G: BlueprintFlow에서 배포된 잠긴 세션을 위한 고객용 UI
 *
 * 기능:
 * - 워크플로우 읽기 전용 표시
 * - 이미지 업로드 (다중)
 * - 파라미터 조정 (lock_level이 'parameters'일 때)
 * - 워크플로우 실행
 * - 결과 검토
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import {
  Upload,
  Play,
  Loader2,
  Lock,
  Images,
  CheckCircle,
  Clock,
  FileText,
  AlertCircle,
  RefreshCw,
  ArrowRight,
  Settings,
  Eye,
} from 'lucide-react';
import { sessionApi } from '../../lib/api';
import type { SessionImage, SessionImageProgress } from '../../types';

interface WorkflowNode {
  id: string;
  type: string;
  label?: string;
  parameters?: Record<string, unknown>;
}

interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
}

interface WorkflowDefinition {
  name: string;
  description?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

interface SessionWorkflowData {
  session_id: string;
  workflow_definition: WorkflowDefinition | null;
  workflow_locked: boolean;
  lock_level: 'full' | 'parameters' | 'none';
  allowed_parameters: string[];
  customer_name?: string;
  expires_at?: string;
}

export function CustomerSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [searchParams] = useSearchParams();
  const accessToken = searchParams.get('token') || undefined;

  const [sessionData, setSessionData] = useState<SessionWorkflowData | null>(null);
  const [images, setImages] = useState<SessionImage[]>([]);
  const [progress, setProgress] = useState<SessionImageProgress | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 데이터 로드
  const loadData = useCallback(async () => {
    if (!sessionId) return;
    setIsLoading(true);
    setError(null);

    try {
      // 워크플로우 정보 로드
      const workflowData = await sessionApi.getWorkflow(sessionId, accessToken);
      // API 응답을 SessionWorkflowData 타입으로 변환
      setSessionData(workflowData as unknown as SessionWorkflowData);

      // 이미지 목록 및 진행률 로드
      const [imageList, progressData] = await Promise.all([
        sessionApi.listImages(sessionId),
        sessionApi.getImageProgress(sessionId),
      ]);
      setImages(imageList);
      setProgress(progressData);
    } catch (err) {
      console.error('Failed to load session:', err);
      setError('세션을 불러오는데 실패했습니다. 접근 권한을 확인해주세요.');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, accessToken]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 이미지 업로드
  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0 || !sessionId) return;
    setIsUploading(true);
    setError(null);

    try {
      const result = await sessionApi.bulkUploadImages(
        sessionId,
        Array.from(files)
      );

      if (result.failed_count > 0) {
        setError(`${result.failed_count}개 파일 업로드 실패`);
      }

      await loadData();
    } catch (err) {
      console.error('Failed to upload files:', err);
      setError('파일 업로드에 실패했습니다.');
    } finally {
      setIsUploading(false);
    }
  };

  // 워크플로우 실행
  const handleExecute = async () => {
    if (!sessionId || images.length === 0) return;
    setIsExecuting(true);
    setError(null);

    try {
      const imageIds = images.map((img) => img.image_id);
      await sessionApi.executeWorkflow(sessionId, imageIds, undefined, accessToken);

      // 실행 시작 후 상태 새로고침
      await loadData();
    } catch (err) {
      console.error('Failed to execute workflow:', err);
      setError('워크플로우 실행에 실패했습니다.');
    } finally {
      setIsExecuting(false);
    }
  };

  // 로딩 중
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-500">세션을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  // 세션 없음
  if (!sessionData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p className="text-gray-500">{error || '세션을 찾을 수 없습니다.'}</p>
        </div>
      </div>
    );
  }

  const workflow = sessionData.workflow_definition;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Lock className="w-5 h-5 text-blue-500" />
                <h1 className="text-xl font-bold text-gray-900">
                  {workflow?.name || '워크플로우 세션'}
                </h1>
              </div>
              <span className="px-2 py-1 bg-blue-100 text-blue-600 text-xs rounded-full">
                읽기 전용
              </span>
              {sessionData.customer_name && (
                <span className="text-sm text-gray-500">
                  | {sessionData.customer_name}
                </span>
              )}
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
                이미지 업로드
              </button>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*"
                className="hidden"
                onChange={(e) => handleUpload(e.target.files)}
              />
            </div>
          </div>
        </div>
      </header>

      {/* 워크플로우 시각화 (읽기 전용) */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-2 text-sm text-gray-600 mb-3">
            <Lock className="w-4 h-4" />
            <span>워크플로우는 수정할 수 없습니다.</span>
            {sessionData.lock_level === 'parameters' && (
              <span className="flex items-center gap-1 text-yellow-600 ml-2">
                <Settings className="w-3 h-3" />
                일부 파라미터 조정 가능
              </span>
            )}
          </div>

          {/* 파이프라인 흐름 표시 */}
          {workflow && (
            <div className="flex flex-wrap items-center gap-2">
              {workflow.nodes.map((node, index) => (
                <div key={node.id} className="flex items-center">
                  <div className="px-3 py-1.5 bg-white rounded-lg shadow-sm border border-gray-200">
                    <span className="text-xs font-medium text-gray-700">
                      {node.label || node.type}
                    </span>
                    <span className="ml-1 text-xs text-gray-400">
                      ({node.type})
                    </span>
                  </div>
                  {index < workflow.nodes.length - 1 && (
                    <ArrowRight className="w-4 h-4 text-gray-400 mx-1" />
                  )}
                </div>
              ))}
            </div>
          )}
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

        {/* 만료 정보 */}
        {sessionData.expires_at && (
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-6">
            <Clock className="w-4 h-4" />
            <span>
              만료: {new Date(sessionData.expires_at).toLocaleDateString('ko-KR')}
            </span>
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
              <h2 className="font-semibold text-gray-900">업로드된 이미지</h2>
              <span className="text-sm text-gray-500">({images.length}개)</span>
            </div>
            {images.length > 0 && (
              <button
                onClick={handleExecute}
                disabled={isExecuting}
                className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
              >
                {isExecuting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                워크플로우 실행
              </button>
            )}
          </div>

          {images.length === 0 ? (
            <div className="p-12 text-center">
              <Images className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500">업로드된 이미지가 없습니다.</p>
              <p className="text-sm text-gray-400 mt-1">
                "이미지 업로드" 버튼을 클릭하여 도면을 추가하세요.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 p-4">
              {images.map((image) => (
                <div
                  key={image.image_id}
                  className="group relative aspect-square bg-gray-100 rounded-lg overflow-hidden border-2 border-transparent hover:border-blue-500 transition-all cursor-pointer"
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
                            : image.review_status === 'processed'
                              ? 'bg-blue-100 text-blue-600'
                              : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {image.review_status === 'approved' && '승인'}
                    {image.review_status === 'rejected' && '거부'}
                    {image.review_status === 'modified' && '수정됨'}
                    {image.review_status === 'processed' && '분석완료'}
                    {image.review_status === 'pending' && '대기'}
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
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 도움말 */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mt-6">
          <h3 className="font-medium text-blue-900 mb-2">사용 방법</h3>
          <ol className="text-sm text-blue-700 space-y-1">
            <li>1. "이미지 업로드" 버튼으로 도면 이미지를 업로드합니다.</li>
            <li>2. "워크플로우 실행" 버튼으로 분석을 시작합니다.</li>
            <li>3. 분석이 완료되면 각 이미지를 클릭하여 결과를 검토합니다.</li>
            <li>4. 검출 결과를 승인, 수정, 또는 거부합니다.</li>
          </ol>
        </div>
      </main>
    </div>
  );
}

export default CustomerSessionPage;
