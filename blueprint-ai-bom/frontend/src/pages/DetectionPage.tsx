/**
 * Detection Page - 검출 실행 페이지
 */

import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Play, Settings, ArrowRight, Loader2 } from 'lucide-react';
import { useSessionStore } from '../store/sessionStore';
import type { DetectionConfig } from '../types';

export function DetectionPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = searchParams.get('session');

  const {
    currentSession,
    imageData,
    detections,
    isLoading,
    error,
    loadSession,
    runDetection,
    clearError,
  } = useSessionStore();

  const [config, setConfig] = useState<Partial<DetectionConfig>>({
    confidence: 0.4,  // Streamlit과 동일
    iou_threshold: 0.5,  // Streamlit과 동일
    model_id: 'yolo_v11n',
  });

  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId);
    }
  }, [sessionId, loadSession]);

  const handleDetect = async () => {
    await runDetection(config);
    if (detections.length > 0) {
      navigate(`/verification?session=${sessionId}`);
    }
  };

  if (!sessionId) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">세션 ID가 필요합니다.</p>
        <button
          onClick={() => navigate('/')}
          className="mt-4 text-primary-600 hover:text-primary-700"
        >
          홈으로 돌아가기
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex justify-between items-center">
          <span>{error}</span>
          <button onClick={clearError} className="text-red-500 hover:text-red-700">×</button>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">객체 검출</h1>
          {currentSession && (
            <p className="text-gray-500 mt-1">{currentSession.filename}</p>
          )}
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <Settings className="w-5 h-5" />
            <span>설정</span>
          </button>
          <button
            onClick={handleDetect}
            disabled={isLoading || !imageData}
            className="flex items-center space-x-2 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Play className="w-5 h-5" />
            )}
            <span>{isLoading ? '검출 중...' : '검출 시작'}</span>
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">검출 설정</h3>
          <div className="grid grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                신뢰도 임계값: {config.confidence}
              </label>
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.05"
                value={config.confidence}
                onChange={(e) => setConfig({ ...config, confidence: parseFloat(e.target.value) })}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                IOU 임계값: {config.iou_threshold}
              </label>
              <input
                type="range"
                min="0.1"
                max="0.9"
                step="0.05"
                value={config.iou_threshold}
                onChange={(e) => setConfig({ ...config, iou_threshold: parseFloat(e.target.value) })}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">모델</label>
              <select
                value={config.model_id}
                onChange={(e) => setConfig({ ...config, model_id: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value="yolo_v11n">YOLO v11 Nano</option>
                <option value="yolo_v11s">YOLO v11 Small</option>
                <option value="yolo_v11m">YOLO v11 Medium</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Image Preview */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {isLoading && !imageData ? (
          <div className="flex items-center justify-center h-96">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
          </div>
        ) : imageData ? (
          <div className="relative">
            <img
              src={imageData}
              alt="도면"
              className="w-full max-h-[600px] object-contain bg-gray-100"
            />
            {detections.length > 0 && (
              <div className="absolute bottom-4 right-4 bg-white px-4 py-2 rounded-lg shadow-lg">
                <span className="font-semibold text-primary-600">{detections.length}개</span>
                <span className="text-gray-600"> 객체 검출됨</span>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-96 text-gray-500">
            <p>이미지를 로드하는 중...</p>
          </div>
        )}
      </div>

      {/* Next Step */}
      {detections.length > 0 && (
        <div className="flex justify-end">
          <button
            onClick={() => navigate(`/verification?session=${sessionId}`)}
            className="flex items-center space-x-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <span>검증 단계로 이동</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      )}
    </div>
  );
}
