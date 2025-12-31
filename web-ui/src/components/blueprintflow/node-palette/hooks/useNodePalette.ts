/**
 * useNodePalette Hook
 * 노드 팔레트 상태 관리
 */

import { useEffect, useState, useMemo } from 'react';
import { useAPIConfigStore } from '../../../../store/apiConfigStore';
import { baseNodeConfigs } from '../constants';
import type { NodeConfig } from '../types';

interface NodePaletteState {
  allNodeConfigs: NodeConfig[];
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
  showImageModal: boolean;
  setShowImageModal: (show: boolean) => void;
  // 카테고리별 노드
  inputNodes: NodeConfig[];
  bomNodes: NodeConfig[];
  detectionNodes: NodeConfig[];
  ocrNodes: NodeConfig[];
  segmentationNodes: NodeConfig[];
  preprocessingNodes: NodeConfig[];
  analysisNodes: NodeConfig[];
  knowledgeNodes: NodeConfig[];
  aiNodes: NodeConfig[];
  controlNodes: NodeConfig[];
}

/**
 * 노드 팔레트 상태를 관리하는 훅
 * - 기본 노드 + 커스텀 노드 병합
 * - 카테고리별 노드 필터링
 * - 접힘 상태 및 이미지 모달 관리
 */
export function useNodePalette(): NodePaletteState {
  const { customAPIs } = useAPIConfigStore();
  const [allNodeConfigs, setAllNodeConfigs] = useState<NodeConfig[]>(baseNodeConfigs);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showImageModal, setShowImageModal] = useState(false);

  // 커스텀 API를 노드 설정에 병합
  useEffect(() => {
    // 기본 노드 타입 집합
    const baseTypes = new Set(baseNodeConfigs.map((n) => n.type));

    // 커스텀 API를 NodeConfig로 변환 (기본 노드와 중복되지 않는 것만)
    const customNodeConfigs: NodeConfig[] = customAPIs
      .filter((api) => api.enabled && !baseTypes.has(api.id))
      .map((api) => ({
        type: api.id,
        label: api.displayName,
        description: api.description,
        icon: api.icon, // 이모지 문자열
        color: api.color,
        category: api.category,
      }));

    // 기본 노드 + 커스텀 노드 병합 (중복 제거됨)
    setAllNodeConfigs([...baseNodeConfigs, ...customNodeConfigs]);
  }, [customAPIs]);

  // 카테고리별 노드 필터링
  const inputNodes = useMemo(
    () => allNodeConfigs.filter((n) => n.category === 'input'),
    [allNodeConfigs]
  );
  const bomNodes = useMemo(
    () => allNodeConfigs.filter((n) => n.category === 'bom'),
    [allNodeConfigs]
  );
  const detectionNodes = useMemo(
    () => allNodeConfigs.filter((n) => n.category === 'detection'),
    [allNodeConfigs]
  );
  const ocrNodes = useMemo(
    () => allNodeConfigs.filter((n) => n.category === 'ocr'),
    [allNodeConfigs]
  );
  const segmentationNodes = useMemo(
    () => allNodeConfigs.filter((n) => n.category === 'segmentation'),
    [allNodeConfigs]
  );
  const preprocessingNodes = useMemo(
    () => allNodeConfigs.filter((n) => n.category === 'preprocessing'),
    [allNodeConfigs]
  );
  const analysisNodes = useMemo(
    () => allNodeConfigs.filter((n) => n.category === 'analysis'),
    [allNodeConfigs]
  );
  const knowledgeNodes = useMemo(
    () => allNodeConfigs.filter((n) => n.category === 'knowledge'),
    [allNodeConfigs]
  );
  const aiNodes = useMemo(
    () => allNodeConfigs.filter((n) => n.category === 'ai'),
    [allNodeConfigs]
  );
  const controlNodes = useMemo(
    () => allNodeConfigs.filter((n) => n.category === 'control'),
    [allNodeConfigs]
  );

  return {
    allNodeConfigs,
    isCollapsed,
    setIsCollapsed,
    showImageModal,
    setShowImageModal,
    inputNodes,
    bomNodes,
    detectionNodes,
    ocrNodes,
    segmentationNodes,
    preprocessingNodes,
    analysisNodes,
    knowledgeNodes,
    aiNodes,
    controlNodes,
  };
}
