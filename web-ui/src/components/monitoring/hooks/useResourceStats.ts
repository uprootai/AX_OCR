/**
 * useResourceStats Hook
 * 컨테이너 및 GPU 리소스 통계 관리
 * fetch API 사용으로 콘솔 에러 없음
 */

import { useState, useCallback } from 'react';
import { API_TO_CONTAINER } from '../../../config/apiRegistry';
import { GATEWAY_URL } from '../../../lib/api';
import type { ContainerStats, GPUStats, APIResourceSpec } from '../types';

// Silent fetch helper (no console errors)
const silentFetch = async <T>(url: string, timeout = 5000): Promise<T | null> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);
    if (response.ok) {
      return await response.json();
    }
    return null;
  } catch {
    clearTimeout(timeoutId);
    return null;
  }
};

export function useResourceStats() {
  const [containerStats, setContainerStats] = useState<Record<string, ContainerStats>>({});
  const [gpuStats, setGpuStats] = useState<GPUStats[]>([]);
  const [gpuAvailable, setGpuAvailable] = useState<boolean>(false);
  const [apiResources, setApiResources] = useState<Record<string, APIResourceSpec>>({});

  const fetchResourceStats = useCallback(async () => {
    // Fetch container stats (includes memory and CPU)
    const containerData = await silentFetch<{ containers: Array<{ name: string; memory_usage: string | null; cpu_percent: number | null }> }>(
      `${GATEWAY_URL}/api/v1/containers`,
      10000
    );
    if (containerData?.containers) {
      const stats: Record<string, ContainerStats> = {};
      for (const container of containerData.containers) {
        const apiId = Object.entries(API_TO_CONTAINER).find(([, containerName]) => containerName === container.name)?.[0];
        if (apiId) {
          stats[apiId] = {
            name: container.name,
            memory_usage: container.memory_usage,
            cpu_percent: container.cpu_percent,
          };
        }
      }
      setContainerStats(stats);
    }

    // Fetch GPU stats
    const gpuData = await silentFetch<{ available: boolean; gpus: GPUStats[] }>(
      `${GATEWAY_URL}/api/v1/containers/gpu/stats`
    );
    if (gpuData?.available) {
      setGpuAvailable(true);
      setGpuStats(gpuData.gpus || []);
    } else {
      setGpuAvailable(false);
      setGpuStats([]);
    }

    // Fetch API resource specs
    const resourcesData = await silentFetch<{ resources: Record<string, APIResourceSpec> }>(
      `${GATEWAY_URL}/api/v1/specs/resources`
    );
    if (resourcesData?.resources) {
      setApiResources(resourcesData.resources);
    }
  }, []);

  return {
    containerStats,
    gpuStats,
    gpuAvailable,
    apiResources,
    fetchResourceStats,
  };
}
