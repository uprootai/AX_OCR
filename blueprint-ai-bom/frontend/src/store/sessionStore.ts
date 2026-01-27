/**
 * Session Store - Zustand 상태 관리
 */

import { create } from 'zustand';
import type {
  Session,
  SessionDetail,
  Detection,
  VerificationStatus,
  BOMData,
  DetectionConfig,
} from '../types';
import { sessionApi, detectionApi, bomApi } from '../lib/api';

// AbortController를 외부에서 관리
let detectionAbortController: AbortController | null = null;

interface SessionState {
  // 현재 세션
  currentSession: SessionDetail | null;
  sessions: Session[];
  isLoading: boolean;
  error: string | null;

  // 검출 관련
  detections: Detection[];
  selectedDetectionId: string | null;

  // BOM 관련
  bomData: BOMData | null;

  // 이미지
  imageData: string | null;
  imageSize: { width: number; height: number } | null;
  currentImageId: string | null;  // 현재 선택된 이미지 ID (다중 이미지 세션용)

  // Actions
  uploadImage: (file: File) => Promise<string>;
  loadSession: (sessionId: string) => Promise<void>;
  loadSessions: (limit?: number) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  loadImage: (sessionId: string, imageId: string) => Promise<void>;  // 특정 이미지 로드

  // Detection actions
  runDetection: (config?: Partial<DetectionConfig>) => Promise<void>;
  cancelDetection: () => void;
  verifyDetection: (detectionId: string, status: VerificationStatus, modifiedClassName?: string) => Promise<void>;
  approveAll: () => Promise<void>;
  rejectAll: () => Promise<void>;
  addManualDetection: (className: string, bbox: { x1: number; y1: number; x2: number; y2: number }) => Promise<void>;
  deleteDetection: (detectionId: string) => Promise<void>;
  selectDetection: (detectionId: string | null) => void;

  // BOM actions
  generateBOM: () => Promise<void>;

  // Utils
  clearError: () => void;
  reset: () => void;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  // Initial state
  currentSession: null,
  sessions: [],
  isLoading: false,
  error: null,
  detections: [],
  selectedDetectionId: null,
  bomData: null,
  imageData: null,
  imageSize: null,
  currentImageId: null,

  // Upload image
  uploadImage: async (file: File) => {
    set({ isLoading: true, error: null });
    try {
      const response = await sessionApi.upload(file);
      await get().loadSession(response.session_id);
      return response.session_id;
    } catch (error) {
      const message = error instanceof Error ? error.message : '업로드 실패';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  // Load session
  loadSession: async (sessionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const session = await sessionApi.get(sessionId, true);
      const imageResponse = await sessionApi.getImage(sessionId);

      set({
        currentSession: session,
        detections: session.detections || [],
        bomData: session.bom_data || null,
        imageData: `data:${imageResponse.mime_type};base64,${imageResponse.image_base64}`,
        imageSize: session.image_width && session.image_height
          ? { width: session.image_width, height: session.image_height }
          : null,
        currentImageId: null,  // 세션 로드 시 이미지 선택 초기화
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : '세션 로드 실패';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  // Load specific image (다중 이미지 세션용)
  loadImage: async (sessionId: string, imageId: string) => {
    set({ isLoading: true, error: null });
    try {
      // 이미지 상세 정보 (검출 결과 포함)
      const imageDetail = await sessionApi.getImageDetail(sessionId, imageId, true);
      // 이미지 데이터 (base64)
      const imageData = await sessionApi.getImageData(sessionId, imageId);

      set({
        detections: imageDetail.detections || [],
        imageData: `data:${imageData.mime_type};base64,${imageData.image_base64}`,
        imageSize: imageData.image_width && imageData.image_height
          ? { width: imageData.image_width, height: imageData.image_height }
          : null,
        currentImageId: imageId,
        isLoading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : '이미지 로드 실패';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  // Load sessions list
  loadSessions: async (limit = 50) => {
    set({ isLoading: true, error: null });
    try {
      const sessions = await sessionApi.list(limit);
      set({ sessions, isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : '목록 로드 실패';
      set({ error: message, isLoading: false });
    }
  },

  // Delete session
  deleteSession: async (sessionId: string) => {
    set({ isLoading: true, error: null });
    try {
      await sessionApi.delete(sessionId);
      set((state) => ({
        sessions: state.sessions.filter((s) => s.session_id !== sessionId),
        currentSession: state.currentSession?.session_id === sessionId ? null : state.currentSession,
        isLoading: false,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : '삭제 실패';
      set({ error: message, isLoading: false });
    }
  },

  // Run detection
  runDetection: async (config?: Partial<DetectionConfig>) => {
    const { currentSession } = get();
    if (!currentSession) return;

    // 이전 요청 취소
    if (detectionAbortController) {
      detectionAbortController.abort();
    }
    detectionAbortController = new AbortController();
    const currentController = detectionAbortController;

    set({ isLoading: true, error: null });
    try {
      const result = await detectionApi.detect(currentSession.session_id, config);

      // 취소된 경우 결과 무시
      if (currentController.signal.aborted) {
        return;
      }

      set({
        detections: result.detections,
        imageSize: { width: result.image_width, height: result.image_height },
        isLoading: false,
      });
      await get().loadSession(currentSession.session_id);
    } catch (error) {
      // 취소된 경우 에러 무시
      if (currentController.signal.aborted) {
        return;
      }
      const message = error instanceof Error ? error.message : '검출 실패';
      set({ error: message, isLoading: false });
    }
  },

  // Cancel detection
  cancelDetection: () => {
    if (detectionAbortController) {
      detectionAbortController.abort();
      detectionAbortController = null;
    }
    set({ isLoading: false, error: null });
  },

  // Verify detection
  verifyDetection: async (detectionId: string, status: VerificationStatus, modifiedClassName?: string) => {
    const { currentSession } = get();
    if (!currentSession) return;

    try {
      await detectionApi.verify(currentSession.session_id, {
        detection_id: detectionId,
        status,
        modified_class_name: modifiedClassName,
      });

      set((state) => ({
        detections: state.detections.map((d) =>
          d.id === detectionId
            ? { ...d, verification_status: status, modified_class_name: modifiedClassName }
            : d
        ),
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : '검증 업데이트 실패';
      set({ error: message });
    }
  },

  // Approve all (manual 제외 - 수작업 라벨은 그대로 유지)
  approveAll: async () => {
    const { currentSession, detections } = get();
    if (!currentSession) return;

    // approved와 manual이 아닌 모든 검출을 승인 대상으로
    const targetDetections = detections.filter(
      (d) => d.verification_status !== 'approved' && d.verification_status !== 'manual'
    );
    if (targetDetections.length === 0) return;

    set({ isLoading: true, error: null });
    try {
      await detectionApi.bulkVerify(
        currentSession.session_id,
        targetDetections.map((d) => ({ detection_id: d.id, status: 'approved' as VerificationStatus }))
      );

      set((state) => ({
        detections: state.detections.map((d) =>
          d.verification_status !== 'approved' && d.verification_status !== 'manual'
            ? { ...d, verification_status: 'approved' as VerificationStatus }
            : d
        ),
        isLoading: false,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : '일괄 승인 실패';
      set({ error: message, isLoading: false });
    }
  },

  // Reject all (manual 제외 - 수작업 라벨은 그대로 유지)
  rejectAll: async () => {
    const { currentSession, detections } = get();
    if (!currentSession) return;

    // rejected와 manual이 아닌 모든 검출을 거부 대상으로
    const targetDetections = detections.filter(
      (d) => d.verification_status !== 'rejected' && d.verification_status !== 'manual'
    );
    if (targetDetections.length === 0) return;

    set({ isLoading: true, error: null });
    try {
      await detectionApi.bulkVerify(
        currentSession.session_id,
        targetDetections.map((d) => ({ detection_id: d.id, status: 'rejected' as VerificationStatus }))
      );

      set((state) => ({
        detections: state.detections.map((d) =>
          d.verification_status !== 'rejected' && d.verification_status !== 'manual'
            ? { ...d, verification_status: 'rejected' as VerificationStatus }
            : d
        ),
        isLoading: false,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : '일괄 반려 실패';
      set({ error: message, isLoading: false });
    }
  },

  // Add manual detection
  addManualDetection: async (className: string, bbox) => {
    const { currentSession } = get();
    if (!currentSession) return;

    set({ isLoading: true, error: null });
    try {
      const { detection } = await detectionApi.addManual(currentSession.session_id, { class_name: className, bbox });
      set((state) => ({
        detections: [...state.detections, detection],
        isLoading: false,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : '수동 검출 추가 실패';
      set({ error: message, isLoading: false });
    }
  },

  // Delete detection
  deleteDetection: async (detectionId: string) => {
    const { currentSession } = get();
    if (!currentSession) return;

    try {
      await detectionApi.deleteDetection(currentSession.session_id, detectionId);
      set((state) => ({
        detections: state.detections.filter((d) => d.id !== detectionId),
        selectedDetectionId: state.selectedDetectionId === detectionId ? null : state.selectedDetectionId,
      }));
    } catch (error) {
      const message = error instanceof Error ? error.message : '검출 삭제 실패';
      set({ error: message });
    }
  },

  // Select detection
  selectDetection: (detectionId: string | null) => {
    set({ selectedDetectionId: detectionId });
  },

  // Generate BOM
  generateBOM: async () => {
    const { currentSession } = get();
    if (!currentSession) return;

    set({ isLoading: true, error: null });
    try {
      const bomData = await bomApi.generate(currentSession.session_id);
      set({ bomData, isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'BOM 생성 실패';
      set({ error: message, isLoading: false });
    }
  },

  // Clear error
  clearError: () => set({ error: null }),

  // Reset store
  reset: () =>
    set({
      currentSession: null,
      detections: [],
      selectedDetectionId: null,
      bomData: null,
      imageData: null,
      imageSize: null,
      currentImageId: null,
      error: null,
    }),
}));
