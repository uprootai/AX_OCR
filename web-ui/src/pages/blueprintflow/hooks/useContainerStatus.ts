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
}

export function useContainerStatus({ onExecute }: UseContainerStatusOptions) {
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

      // Fetch container status from Gateway API (lightweight endpoint - no stats)
      const response = await fetch('http://localhost:8000/api/v1/containers/status');
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
    } catch (error) {
      console.error('Failed to check container status:', error);
      return []; // Continue execution if check fails
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
    } catch (error) {
      console.error('Failed to start containers:', error);
      alert('Failed to start containers. Please start them manually from Dashboard.');
      setContainerWarningModal({ isOpen: false, stoppedContainers: [], isStarting: false });
    }
  }, [onExecute]);

  // Handle execute with container check
  const executeWithContainerCheck = useCallback(async (
    nodes: Node[],
    uploadedImage: string | null
  ) => {
    if (nodes.length === 0) {
      alert('Please add at least one node to the workflow');
      return;
    }

    if (!uploadedImage) {
      alert('Please upload an image first');
      return;
    }

    setIsCheckingContainers(true);

    try {
      const stoppedContainers = await checkContainerStatus(nodes);
      if (stoppedContainers.length > 0) {
        setContainerWarningModal({
          isOpen: true,
          stoppedContainers,
          isStarting: false
        });
        return;
      }

      await onExecute();
    } finally {
      setIsCheckingContainers(false);
    }
  }, [checkContainerStatus, onExecute]);

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
