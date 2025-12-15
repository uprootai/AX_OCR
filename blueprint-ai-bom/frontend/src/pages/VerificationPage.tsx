/**
 * Verification Page - 검증 페이지 (Human-in-the-Loop)
 */

import { useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { CheckCircle, XCircle, ArrowRight, Loader2 } from 'lucide-react';
import { useSessionStore } from '../store/sessionStore';
import type { Detection, VerificationStatus } from '../types';

// 전기 패널 부품 클래스별 색상
const CLASS_COLORS: Record<string, string> = {
  // BUZZER
  '10_BUZZER': '#ef4444',
  // HUB
  '11_HUB': '#3b82f6',
  // SMPS
  '13_SWITCHING': '#8b5cf6',
  '14_SWITCHING': '#7c3aed',
  // SWITCH
  '16_DISCONNECTING': '#10b981',
  // OUTLET
  '17_POWER': '#f59e0b',
  // LAMP
  '18_PILOT': '#ec4899',
  // RELAY
  '19_AUXILIARY': '#06b6d4',
  // BREAKER
  '2,3,4,5_CIRCUIT': '#84cc16',
  // PLC CPU
  '20,32_CPU': '#6366f1',
  '21_CPU': '#4f46e5',
  // PLC MODULES
  '22_CM': '#14b8a6',
  '23,37_CM': '#0d9488',
  // GRAPHIC PANEL
  '24,25_GRAPHIC': '#f97316',
  // TERMINAL BLOCK
  '26_TERMINAL': '#a855f7',
  '27_TERMINAL': '#9333ea',
  // PLC I/O
  '28_SM': '#22c55e',
  '29_SM': '#16a34a',
  '30_SM': '#15803d',
  '31_SM': '#166534',
  // BUS INTERFACE
  '34_BUS': '#0ea5e9',
  // VALVE CONTROL
  '35_VALVE': '#e11d48',
  // CONVERTER
  '38_I-I': '#fb923c',
  // SELECTOR
  '39_SELECTOR': '#38bdf8',
  // TRANSFORMER
  '6_TRANSFORMER': '#fbbf24',
  // NOISE FILTER
  '8_NOISE': '#a3e635',
  // EMERGENCY
  '9,9-1_EMERGENCY': '#dc2626',
  default: '#6b7280',
};

export function VerificationPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = searchParams.get('session');

  const {
    currentSession,
    imageData,
    imageSize,
    detections,
    selectedDetectionId,
    isLoading,
    error,
    loadSession,
    verifyDetection,
    approveAll,
    rejectAll,
    selectDetection,
    clearError,
  } = useSessionStore();

  useEffect(() => {
    if (sessionId && !currentSession) {
      loadSession(sessionId);
    }
  }, [sessionId, currentSession, loadSession]);

  const getClassColor = (className: string): string => {
    // 클래스 이름의 접두사로 색상 매칭
    for (const [prefix, color] of Object.entries(CLASS_COLORS)) {
      if (prefix !== 'default' && className.startsWith(prefix)) {
        return color;
      }
    }
    return CLASS_COLORS.default;
  };

  const pendingCount = detections.filter(d => d.verification_status === 'pending').length;
  const approvedCount = detections.filter(d => ['approved', 'modified', 'manual'].includes(d.verification_status)).length;
  const rejectedCount = detections.filter(d => d.verification_status === 'rejected').length;

  if (!sessionId) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">세션 ID가 필요합니다.</p>
        <button onClick={() => navigate('/')} className="mt-4 text-primary-600 hover:text-primary-700">
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
          <h1 className="text-2xl font-bold text-gray-900">검출 검증</h1>
          {currentSession && (
            <p className="text-gray-500 mt-1">{currentSession.filename}</p>
          )}
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={approveAll}
            disabled={isLoading || pendingCount === 0}
            className="flex items-center space-x-2 px-4 py-2 border border-green-500 text-green-600 rounded-lg hover:bg-green-50 disabled:opacity-50"
          >
            <CheckCircle className="w-5 h-5" />
            <span>모두 승인</span>
          </button>
          <button
            onClick={rejectAll}
            disabled={isLoading || pendingCount === 0}
            className="flex items-center space-x-2 px-4 py-2 border border-red-500 text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-50"
          >
            <XCircle className="w-5 h-5" />
            <span>모두 반려</span>
          </button>
          <button
            onClick={() => navigate(`/bom?session=${sessionId}`)}
            disabled={approvedCount === 0}
            className="flex items-center space-x-2 px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            <span>BOM 생성</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <p className="text-sm text-gray-500">전체</p>
          <p className="text-2xl font-bold text-gray-900">{detections.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <p className="text-sm text-gray-500">대기중</p>
          <p className="text-2xl font-bold text-yellow-600">{pendingCount}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <p className="text-sm text-gray-500">승인</p>
          <p className="text-2xl font-bold text-green-600">{approvedCount}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <p className="text-sm text-gray-500">반려</p>
          <p className="text-2xl font-bold text-red-600">{rejectedCount}</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-3 gap-6">
        {/* Image with Bounding Boxes */}
        <div className="col-span-2 bg-white rounded-xl shadow-sm border overflow-hidden">
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
              {/* Bounding Boxes Overlay */}
              {imageSize && (
                <svg
                  className="absolute top-0 left-0 w-full h-full pointer-events-none"
                  viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
                  preserveAspectRatio="xMidYMid meet"
                >
                  {detections.map((detection) => {
                    const color = getClassColor(detection.class_name);
                    const isSelected = detection.id === selectedDetectionId;
                    const bbox = detection.modified_bbox || detection.bbox;

                    return (
                      <g key={detection.id}>
                        <rect
                          x={bbox.x1}
                          y={bbox.y1}
                          width={bbox.x2 - bbox.x1}
                          height={bbox.y2 - bbox.y1}
                          fill="none"
                          stroke={color}
                          strokeWidth={isSelected ? 4 : 2}
                          opacity={detection.verification_status === 'rejected' ? 0.3 : 1}
                        />
                        <rect
                          x={bbox.x1}
                          y={bbox.y1 - 20}
                          width={80}
                          height={20}
                          fill={color}
                        />
                        <text
                          x={bbox.x1 + 4}
                          y={bbox.y1 - 6}
                          fill="white"
                          fontSize="12"
                          fontWeight="bold"
                        >
                          {detection.modified_class_name || detection.class_name}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-96 text-gray-500">
              <p>이미지를 로드하는 중...</p>
            </div>
          )}
        </div>

        {/* Detection List */}
        <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
          <div className="px-4 py-3 border-b bg-gray-50">
            <h3 className="font-semibold text-gray-900">검출 목록</h3>
          </div>
          <div className="overflow-y-auto max-h-[600px]">
            {detections.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <p>검출된 객체가 없습니다.</p>
              </div>
            ) : (
              <ul className="divide-y">
                {detections.map((detection) => (
                  <DetectionItem
                    key={detection.id}
                    detection={detection}
                    isSelected={detection.id === selectedDetectionId}
                    color={getClassColor(detection.class_name)}
                    onSelect={() => selectDetection(detection.id)}
                    onVerify={(status) => verifyDetection(detection.id, status)}
                  />
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

interface DetectionItemProps {
  detection: Detection;
  isSelected: boolean;
  color: string;
  onSelect: () => void;
  onVerify: (status: VerificationStatus) => void;
}

function DetectionItem({ detection, isSelected, color, onSelect, onVerify }: DetectionItemProps) {
  const getStatusIcon = (status: VerificationStatus) => {
    switch (status) {
      case 'approved':
      case 'modified':
      case 'manual':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'rejected':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <div className="w-4 h-4 rounded-full border-2 border-gray-300" />;
    }
  };

  return (
    <li
      className={`px-4 py-3 cursor-pointer transition-colors ${
        isSelected ? 'bg-primary-50' : 'hover:bg-gray-50'
      }`}
      onClick={onSelect}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: color }}
          />
          <div>
            <p className="font-medium text-gray-900">
              {detection.modified_class_name || detection.class_name}
            </p>
            <p className="text-sm text-gray-500">
              신뢰도: {(detection.confidence * 100).toFixed(1)}%
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusIcon(detection.verification_status)}
          {detection.verification_status === 'pending' && (
            <div className="flex space-x-1">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onVerify('approved');
                }}
                className="p-1 rounded hover:bg-green-100 text-green-600"
                title="승인"
              >
                <CheckCircle className="w-5 h-5" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onVerify('rejected');
                }}
                className="p-1 rounded hover:bg-red-100 text-red-600"
                title="반려"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </li>
  );
}
