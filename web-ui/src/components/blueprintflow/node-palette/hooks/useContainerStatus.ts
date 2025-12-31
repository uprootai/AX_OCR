/**
 * useContainerStatus Hook
 * 컨테이너 상태 관리 및 폴링
 */

import { useEffect, useState, useCallback } from 'react';
import { NODE_TO_CONTAINER } from '../../../../config/apiRegistry';
import { ALWAYS_ACTIVE_NODE_TYPES, CONTAINER_STATUS_POLL_INTERVAL } from '../constants';

interface ContainerStatusResult {
  stoppedContainers: Set<string>;
  statusFetched: boolean;
  isNodeActive: (nodeType: string) => boolean;
  refreshStatus: () => Promise<void>;
}

/**
 * 컨테이너 상태를 관리하는 훅
 * - 주기적으로 컨테이너 상태를 폴링
 * - 노드 활성화 상태 판단
 */
export function useContainerStatus(): ContainerStatusResult {
  const [stoppedContainers, setStoppedContainers] = useState<Set<string>>(new Set());
  const [statusFetched, setStatusFetched] = useState(false);

  // 컨테이너 상태 가져오기
  const fetchContainerStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/containers');
      const data = await response.json();
      if (data.success && data.containers) {
        const stopped = new Set<string>(
          data.containers
            .filter((c: { status: string }) => c.status !== 'running')
            .map((c: { name: string }) => c.name)
        );
        setStoppedContainers(stopped);
        setStatusFetched(true);
      }
    } catch (error) {
      console.error('Failed to fetch container status:', error);
      setStatusFetched(true);
    }
  }, []);

  // 컨테이너 상태 주기적 갱신
  useEffect(() => {
    fetchContainerStatus();
    const interval = setInterval(fetchContainerStatus, CONTAINER_STATUS_POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchContainerStatus]);

  // 노드가 활성화 상태인지 확인
  const isNodeActive = useCallback(
    (nodeType: string): boolean => {
      // Input, Control 노드는 항상 활성화
      if (ALWAYS_ACTIVE_NODE_TYPES.includes(nodeType)) {
        return true;
      }
      // 상태를 아직 가져오지 않았으면 기본 활성화
      if (!statusFetched) {
        return true;
      }
      const containerName = NODE_TO_CONTAINER[nodeType];
      if (!containerName) return true; // 매핑 없으면 활성화로 간주
      return !stoppedContainers.has(containerName);
    },
    [statusFetched, stoppedContainers]
  );

  return {
    stoppedContainers,
    statusFetched,
    isNodeActive,
    refreshStatus: fetchContainerStatus,
  };
}
