/**
 * Home Page - 파일 업로드 및 세션 목록
 */

import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileImage, Clock, CheckCircle, AlertCircle, Trash2 } from 'lucide-react';
import { useSessionStore } from '../store/sessionStore';
import type { Session } from '../types';

export function HomePage() {
  const navigate = useNavigate();
  const { sessions, isLoading, error, loadSessions, uploadImage, deleteSession, clearError } = useSessionStore();
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files?.[0]) {
      try {
        const sessionId = await uploadImage(files[0]);
        navigate(`/detection?session=${sessionId}`);
      } catch {
        // Error handled in store
      }
    }
  }, [uploadImage, navigate]);

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files?.[0]) {
      try {
        const sessionId = await uploadImage(files[0]);
        navigate(`/detection?session=${sessionId}`);
      } catch {
        // Error handled in store
      }
    }
  }, [uploadImage, navigate]);

  const handleSessionClick = (session: Session) => {
    if (session.status === 'uploaded') {
      navigate(`/detection?session=${session.session_id}`);
    } else if (session.status === 'detected' || session.status === 'verifying') {
      navigate(`/verification?session=${session.session_id}`);
    } else if (session.bom_generated) {
      navigate(`/bom?session=${session.session_id}`);
    } else {
      navigate(`/detection?session=${session.session_id}`);
    }
  };

  const getStatusBadge = (session: Session) => {
    const statusConfig: Record<string, { color: string; icon: typeof Clock; text: string }> = {
      uploaded: { color: 'bg-blue-100 text-blue-800', icon: Clock, text: '업로드됨' },
      detecting: { color: 'bg-yellow-100 text-yellow-800', icon: Clock, text: '검출 중' },
      detected: { color: 'bg-green-100 text-green-800', icon: CheckCircle, text: '검출 완료' },
      verifying: { color: 'bg-purple-100 text-purple-800', icon: Clock, text: '검증 중' },
      completed: { color: 'bg-green-100 text-green-800', icon: CheckCircle, text: '완료' },
      error: { color: 'bg-red-100 text-red-800', icon: AlertCircle, text: '오류' },
    };

    const config = statusConfig[session.status] || statusConfig.uploaded;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {config.text}
      </span>
    );
  };

  return (
    <div className="space-y-8">
      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex justify-between items-center">
          <span>{error}</span>
          <button onClick={clearError} className="text-red-500 hover:text-red-700">
            ×
          </button>
        </div>
      )}

      {/* Upload Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">도면 분석 시작</h2>
        <div
          className={`
            relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
            transition-colors
            ${dragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
            }
            ${isLoading ? 'opacity-50 pointer-events-none' : ''}
          `}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input')?.click()}
        >
          <input
            id="file-input"
            type="file"
            accept=".png,.jpg,.jpeg,.pdf"
            className="hidden"
            onChange={handleFileSelect}
            disabled={isLoading}
          />
          <Upload className={`w-16 h-16 mx-auto mb-4 ${dragActive ? 'text-primary-500' : 'text-gray-400'}`} />
          <p className="text-lg font-medium text-gray-700 mb-2">
            {isLoading ? '업로드 중...' : '도면 파일을 드래그하거나 클릭하여 선택'}
          </p>
          <p className="text-sm text-gray-500">PNG, JPG, JPEG, PDF (최대 50MB)</p>
        </div>
      </div>

      {/* Sessions List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">최근 세션</h2>
        </div>

        {sessions.length === 0 ? (
          <div className="p-12 text-center text-gray-500">
            <FileImage className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>아직 분석된 도면이 없습니다.</p>
            <p className="text-sm">위에서 도면을 업로드하여 시작하세요.</p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {sessions.map((session) => (
              <li
                key={session.session_id}
                className="px-6 py-4 hover:bg-gray-50 cursor-pointer flex items-center justify-between"
                onClick={() => handleSessionClick(session)}
              >
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <FileImage className="w-5 h-5 text-gray-500" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{session.filename}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(session.created_at).toLocaleString('ko-KR')}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <p className="text-sm text-gray-600">
                      검출: {session.detection_count}개 / 검증: {session.verified_count}개
                    </p>
                    {getStatusBadge(session)}
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm('이 세션을 삭제하시겠습니까?')) {
                        deleteSession(session.session_id);
                      }
                    }}
                    className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
