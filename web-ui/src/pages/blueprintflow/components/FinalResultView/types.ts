/**
 * FinalResultView — shared types
 */

// Toast 알림 타입
export interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}
