/**
 * API Status Monitor Types
 * 모니터링 관련 타입 정의
 */

export interface APIInfo {
  id: string;
  name: string;
  display_name: string;
  base_url: string;
  port: number;
  status: 'healthy' | 'unhealthy' | 'unknown';
  category: string;
  description: string;
  icon: string;
  color: string;
  last_check: string | null;
}

// Container stats from Docker
export interface ContainerStats {
  name: string;
  memory_usage: string | null;
  cpu_percent: number | null;
}

// GPU stats from nvidia-smi
export interface GPUStats {
  index: number;
  name: string;
  memory_used: number;
  memory_total: number;
  memory_percent: number;
  utilization: number;
  temperature: number | null;
}

// API별 리소스 정보 타입 (스펙에서 동적으로 로드)
export interface APIResourceSpec {
  gpu?: {
    vram?: string;
    minVram?: number;
    recommended?: string;
  };
  cpu?: {
    ram?: string;
    minRam?: number;
    cores?: number;
    note?: string;
  };
  parameterImpact?: Array<{
    parameter: string;
    impact: string;
    examples?: string;
  }>;
}

// Category labels
export const CATEGORY_LABELS: Record<string, string> = {
  orchestrator: 'Orchestrator',
  detection: 'Detection',
  ocr: 'OCR',
  segmentation: 'Segmentation',
  preprocessing: 'Preprocessing',
  analysis: 'Analysis',
  knowledge: 'Knowledge',
  ai: 'AI',
};

// Category order for sorting
export const CATEGORY_ORDER = [
  'orchestrator',
  'detection',
  'ocr',
  'segmentation',
  'preprocessing',
  'analysis',
  'knowledge',
  'ai',
];
