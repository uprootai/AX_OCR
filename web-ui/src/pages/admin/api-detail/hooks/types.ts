/**
 * Type definitions for useAPIDetail hook
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
  action: 'stop' | 'start' | 'restart' | 'save' | 'delete' | null;
  target: string;
}

export interface HyperParams {
  [key: string]: number | boolean | string;
}

export interface APIConfig {
  enabled: boolean;
  device: 'cpu' | 'cuda';
  memory_limit: string;
  gpu_memory?: string;
  hyperparams: HyperParams;
}

export interface GPUInfo {
  name: string;
  total_mb: number;
  used_mb: number;
  free_mb: number;
  utilization: number;
}

export interface ContainerStatus {
  service: string;
  container_name: string;
  running: boolean;
  gpu_enabled: boolean;
  gpu_count: number;
  memory_limit: string | null;
}

export interface TestResult {
  success: boolean;
  message: string;
}

// APIs that require external API keys
export const API_KEY_REQUIRED_APIS = ['vl', 'ocr_ensemble', 'blueprint_ai_bom', 'blueprint-ai-bom'];
