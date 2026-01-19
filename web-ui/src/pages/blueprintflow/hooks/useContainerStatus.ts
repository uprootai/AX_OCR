/**
 * useContainerStatus Hook
 * 컨테이너 상태 확인 및 시작 로직
 */

import { useState, useCallback } from 'react';
import { NODE_TO_CONTAINER, CONTROL_NODES } from '../../../config/apiRegistry';
import type { ContainerWarningModalState } from '../types';
import type { Node } from 'reactflow';

interface UseContainerStatusOptions {
  onExecute: () => Promise<void>;
  onShowToast?: (message: string, type: 'success' | 'error' | 'warning' | 'info') => void;
}

export function useContainerStatus({ onExecute, onShowToast }: UseContainerStatusOptions) {
  const [isCheckingContainers, setIsCheckingContainers] = useState(false);
  const [containerWarningModal, setContainerWarningModal] = useState<ContainerWarningModalState>({
    isOpen: false,
    stoppedContainers: [],
    isStarting: false
  });

  // Check container status before execution
  const checkContainerStatus = useCallback(async (nodes: Node[]): Promise<string[]> => {
    try {
      // Get unique node types that need containers
      const nodeTypes = [...new Set(nodes.map(n => n.type).filter(Boolean))] as string[];
      const containerNodes = nodeTypes.filter(t => !CONTROL_NODES.includes(t));

      if (containerNodes.length === 0) return [];

      // Fetch container status from Gateway API with timeout (5초)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      try {
        const response = await fetch('http://localhost:8000/api/v1/containers/status', {
          signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (!response.ok) throw new Error('Failed to fetch container status');

        const data = await response.json();
        const containers = data.containers || [];

        // Check which required containers are not running
        const stoppedContainers: string[] = [];
        containerNodes.forEach(nodeType => {
          const containerName = NODE_TO_CONTAINER[nodeType];
          if (containerName) {
            const container = containers.find((c: { name: string }) => c.name === containerName);
            if (!container || container.status !== 'running') {
              stoppedContainers.push(containerName);
            }
          }
        });

        return stoppedContainers;
      } catch (fetchError) {
        clearTimeout(timeoutId);
        throw fetchError;
      }
    } catch {
      // 컨테이너 상태 확인 실패 시 조용히 실행 계속 (타임아웃 포함)
      return [];
    }
  }, []);

  // Start stopped containers
  const startContainers = useCallback(async (containerNames: string[]) => {
    setContainerWarningModal(prev => ({ ...prev, isStarting: true }));
    try {
      for (const name of containerNames) {
        await fetch(`http://localhost:8000/api/v1/containers/${name}/start`, {
          method: 'POST'
        });
      }
      // Wait for containers to be ready
      await new Promise(resolve => setTimeout(resolve, 3000));
      setContainerWarningModal({ isOpen: false, stoppedContainers: [], isStarting: false });
      // Execute workflow after starting containers
      await onExecute();
    } catch {
      onShowToast?.('✗ 컨테이너 시작 실패. Dashboard에서 수동으로 시작해주세요.', 'error');
      setContainerWarningModal({ isOpen: false, stoppedContainers: [], isStarting: false });
    }
  }, [onExecute, onShowToast]);

  // Handle execute with container check
  const executeWithContainerCheck = useCallback(async (
    nodes: Node[],
    uploadedImage: string | null
  ) => {
    if (nodes.length === 0) {
      onShowToast?.('⚠️ 워크플로우에 노드를 추가해주세요', 'warning');
      return;
    }

    if (!uploadedImage) {
      onShowToast?.('⚠️ 이미지를 먼저 업로드해주세요', 'warning');
      return;
    }

    setIsCheckingContainers(true);

    try {
      const stoppedContainers = await checkContainerStatus(nodes);
      if (stoppedContainers.length > 0) {
        // 모달 열기 전에 체크 상태 리셋 (모달이 열리면 버튼이 정상 상태로 돌아가야 함)
        setIsCheckingContainers(false);
        setContainerWarningModal({
          isOpen: true,
          stoppedContainers,
          isStarting: false
        });
        return;
      }

      // 컨테이너 확인 완료 - 실행 시작 전에 상태 리셋
      // (onExecute는 SSE 스트리밍으로 오래 걸릴 수 있어 먼저 리셋)
      setIsCheckingContainers(false);

      // 워크플로우 실행 (비동기, 완료를 기다리지 않음)
      onExecute().catch(error => {
        const errorMsg = error instanceof Error ? error.message : '알 수 없는 오류';
        onShowToast?.(`✗ 워크플로우 실행 실패: ${errorMsg}`, 'error');
      });
    } catch {
      setIsCheckingContainers(false);
    }
  }, [checkContainerStatus, onExecute, onShowToast]);

  const closeWarningModal = useCallback(() => {
    setContainerWarningModal({ isOpen: false, stoppedContainers: [], isStarting: false });
  }, []);

  return {
    isCheckingContainers,
    containerWarningModal,
    executeWithContainerCheck,
    startContainers,
    closeWarningModal,
  };
}
