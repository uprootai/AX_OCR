/**
 * useLayerToggle Hook
 *
 * 시각화 컴포넌트에서 레이어 표시/숨김을 관리하는 공통 훅
 * PIDOverlayViewer, YOLOVisualization 등에서 사용
 */

import { useState, useCallback, useMemo } from 'react';
import { Layers, GitBranch, Type, Square, Box, Eye, EyeOff } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

// ============ Types ============

export interface LayerConfig {
  /** 레이어 표시 라벨 */
  label: string;
  /** 레이어 색상 */
  color: string;
  /** 아이콘 (lucide-react) */
  icon?: LucideIcon;
  /** 기본 표시 여부 */
  defaultVisible?: boolean;
}

export interface LayerState {
  /** 레이어 표시 여부 */
  visible: boolean;
  /** 레이어 투명도 (0-1) */
  opacity: number;
}

export interface UseLayerToggleOptions<T extends string> {
  /** 레이어 설정 */
  layers: Record<T, LayerConfig>;
  /** 초기 표시 상태 (기본: 모두 true) */
  initialVisibility?: Partial<Record<T, boolean>>;
  /** 라벨 표시 여부 초기값 */
  initialShowLabels?: boolean;
}

export interface UseLayerToggleResult<T extends string> {
  /** 각 레이어의 표시 상태 */
  visibility: Record<T, boolean>;
  /** 레이어 토글 함수 */
  toggleLayer: (layer: T) => void;
  /** 특정 레이어 상태 설정 */
  setLayerVisible: (layer: T, visible: boolean) => void;
  /** 모든 레이어 표시 */
  showAllLayers: () => void;
  /** 모든 레이어 숨김 */
  hideAllLayers: () => void;
  /** 라벨 표시 여부 */
  showLabels: boolean;
  /** 라벨 표시 토글 */
  toggleLabels: () => void;
  /** 레이어 설정 (UI 렌더링용) */
  layerConfigs: Array<{ key: T; config: LayerConfig; visible: boolean }>;
  /** 표시된 레이어 개수 */
  visibleCount: number;
  /** 전체 레이어 개수 */
  totalCount: number;
}

// ============ Default Layer Configs ============

/** PID 관련 레이어 기본 설정 */
export const PID_LAYER_CONFIG = {
  symbols: { label: '심볼', color: '#ff7800', icon: Layers, defaultVisible: true },
  lines: { label: '라인', color: '#3b82f6', icon: GitBranch, defaultVisible: true },
  texts: { label: '텍스트', color: '#ffa500', icon: Type, defaultVisible: true },
  regions: { label: '영역', color: '#00ffff', icon: Square, defaultVisible: true },
} as const;

/** YOLO Detection 레이어 기본 설정 */
export const DETECTION_LAYER_CONFIG = {
  detections: { label: '검출', color: '#3b82f6', icon: Box, defaultVisible: true },
  labels: { label: '라벨', color: '#10b981', icon: Type, defaultVisible: true },
} as const;

/** OCR 레이어 기본 설정 */
export const OCR_LAYER_CONFIG = {
  dimensions: { label: '치수', color: '#FFA500', icon: Type, defaultVisible: true },
  texts: { label: '텍스트', color: '#00CED1', icon: Type, defaultVisible: true },
  gdts: { label: 'GD&T', color: '#9370DB', icon: Square, defaultVisible: true },
} as const;

// ============ Hook Implementation ============

/**
 * 레이어 토글 훅
 */
export function useLayerToggle<T extends string>({
  layers,
  initialVisibility = {},
  initialShowLabels = true,
}: UseLayerToggleOptions<T>): UseLayerToggleResult<T> {
  // 초기 visibility 상태 생성
  const getInitialVisibility = useCallback((): Record<T, boolean> => {
    const result = {} as Record<T, boolean>;
    for (const key of Object.keys(layers) as T[]) {
      result[key] = initialVisibility[key] ?? layers[key].defaultVisible ?? true;
    }
    return result;
  }, [layers, initialVisibility]);

  const [visibility, setVisibility] = useState<Record<T, boolean>>(getInitialVisibility);
  const [showLabels, setShowLabels] = useState(initialShowLabels);

  // 레이어 토글
  const toggleLayer = useCallback((layer: T) => {
    setVisibility((prev) => ({
      ...prev,
      [layer]: !prev[layer],
    }));
  }, []);

  // 특정 레이어 상태 설정
  const setLayerVisible = useCallback((layer: T, visible: boolean) => {
    setVisibility((prev) => ({
      ...prev,
      [layer]: visible,
    }));
  }, []);

  // 모든 레이어 표시
  const showAllLayers = useCallback(() => {
    const allVisible = {} as Record<T, boolean>;
    for (const key of Object.keys(layers) as T[]) {
      allVisible[key] = true;
    }
    setVisibility(allVisible);
  }, [layers]);

  // 모든 레이어 숨김
  const hideAllLayers = useCallback(() => {
    const allHidden = {} as Record<T, boolean>;
    for (const key of Object.keys(layers) as T[]) {
      allHidden[key] = false;
    }
    setVisibility(allHidden);
  }, [layers]);

  // 라벨 토글
  const toggleLabels = useCallback(() => {
    setShowLabels((prev) => !prev);
  }, []);

  // 레이어 설정 배열 (UI 렌더링용)
  const layerConfigs = useMemo(() => {
    return (Object.keys(layers) as T[]).map((key) => ({
      key,
      config: layers[key],
      visible: visibility[key],
    }));
  }, [layers, visibility]);

  // 통계
  const visibleCount = useMemo(() => {
    return Object.values(visibility).filter(Boolean).length;
  }, [visibility]);

  const totalCount = Object.keys(layers).length;

  return {
    visibility,
    toggleLayer,
    setLayerVisible,
    showAllLayers,
    hideAllLayers,
    showLabels,
    toggleLabels,
    layerConfigs,
    visibleCount,
    totalCount,
  };
}

// ============ UI Component Helpers ============

/**
 * 레이어 토글 버튼 컴포넌트용 props 생성
 */
export function getLayerToggleButtonProps<T extends string>(
  layer: { key: T; config: LayerConfig; visible: boolean },
  toggleLayer: (key: T) => void
) {
  const Icon = layer.visible ? Eye : EyeOff;
  const LayerIcon = layer.config.icon || Layers;

  return {
    onClick: () => toggleLayer(layer.key),
    title: `${layer.config.label} ${layer.visible ? '숨기기' : '표시'}`,
    className: layer.visible ? 'opacity-100' : 'opacity-50',
    style: { borderColor: layer.config.color },
    icon: LayerIcon,
    statusIcon: Icon,
    label: layer.config.label,
    color: layer.config.color,
    visible: layer.visible,
  };
}

export default useLayerToggle;
