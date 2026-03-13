/**
 * APIStatusMonitor — local types
 */

// Toast 알림 타입
export interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

// 로딩 오버레이 타입
export interface LoadingState {
  isLoading: boolean;
  action: 'stop' | 'start' | null;
  target: string; // API 이름 또는 카테고리
  progress: { current: number; total: number } | null;
}
