import { type Project, type ProjectDetail as BOMProjectDetail } from '../../../lib/blueprintBomApi';

// Toast 알림 타입
export interface ToastState {
  show: boolean;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
}

// 프로젝트 세션 타입
export type ProjectWithSessions = {
  project: Project;
  sessions: BOMProjectDetail['sessions'];
};
