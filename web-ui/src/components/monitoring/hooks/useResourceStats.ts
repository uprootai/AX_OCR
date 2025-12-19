/**
 * useResourceStats Hook
 * 컨테이너 및 GPU 리소스 통계 관리
 */

import { useState, useCallback } from 'react';
import axios from 'axios';
import { API_TO_CONTAINER } from '../../../config/apiRegistry';
import type { ContainerStats, GPUStats, APIResourceSpec } from '../types';

export function useResourceStats() {
  const [containerStats, setContainerStats] = useState<Record<string, ContainerStats>>({});
  const [gpuStats, setGpuStats] = useState<GPUStats[]>([]);
  const [gpuAvailable, setGpuAvailable] = useState<boolean>(false);
  const [apiResources, setApiResources] = useState<Record<string, APIResourceSpec>>({});

  const fetchResourceStats = useCallback(async () => {
    try {
      // Fetch container stats (includes memory and CPU)
      const containerResponse = await axios.get('http://localhost:8000/api/v1/containers', { timeout: 10000 });
      if (containerResponse.data?.containers) {
        const stats: Record<string, ContainerStats> = {};
        for (const container of containerResponse.data.containers) {
          // Map container name to API ID
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
    } catch (error) {
      console.warn('Failed to fetch container stats:', error);
    }

    try {
      // Fetch GPU stats
      const gpuResponse = await axios.get('http://localhost:8000/api/v1/containers/gpu/stats', { timeout: 5000 });
      if (gpuResponse.data?.available) {
        setGpuAvailable(true);
        setGpuStats(gpuResponse.data.gpus || []);
      } else {
        setGpuAvailable(false);
        setGpuStats([]);
      }
    } catch (error) {
      console.warn('Failed to fetch GPU stats:', error);
      setGpuAvailable(false);
    }

    try {
      // Fetch API resource specs (동적 로드)
      const resourcesResponse = await axios.get('http://localhost:8000/api/v1/specs/resources', { timeout: 5000 });
      if (resourcesResponse.data?.resources) {
        setApiResources(resourcesResponse.data.resources);
      }
    } catch (error) {
      console.warn('Failed to fetch API resources:', error);
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
