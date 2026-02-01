/**
 * Dimension Handlers Hook
 * 치수 검증/편집/삭제 관련 핸들러
 */

import { useState, useCallback } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../../../lib/constants';
import logger from '../../../lib/logger';

interface Dimension {
  id: string;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  value: string;
  raw_text: string;
  unit: string | null;
  tolerance: string | null;
  dimension_type: string;
  confidence: number;
  verification_status: 'pending' | 'approved' | 'rejected' | 'modified' | 'manual';
  modified_value: string | null;
  linked_to: string | null;
}

interface DimensionStats {
  pending: number;
  approved: number;
  rejected: number;
  modified: number;
  manual: number;
}

interface UseDimensionHandlersProps {
  sessionId: string | undefined;
  setDimensions: (dimensions: Dimension[] | ((prev: Dimension[]) => Dimension[])) => void;
  setDimensionStats: (stats: DimensionStats | null) => void;
}

export function useDimensionHandlers({
  sessionId,
  setDimensions,
  setDimensionStats,
}: UseDimensionHandlersProps) {
  const [isLoading, setIsLoading] = useState(false);

  const loadDimensions = useCallback(async (sid: string) => {
    try {
      const { data } = await axios.get(`${API_BASE_URL}/analysis/dimensions/${sid}`);
      setDimensions(data.dimensions || []);
      setDimensionStats(data.stats || null);
    } catch (err) {
      logger.error('Failed to load dimensions:', err);
    }
  }, [setDimensions, setDimensionStats]);

  const handleDimensionVerify = useCallback(async (id: string, status: 'approved' | 'rejected') => {
    if (!sessionId) return;

    try {
      await axios.put(`${API_BASE_URL}/analysis/dimensions/${sessionId}/${id}`, {
        verification_status: status
      });

      // 로컬 상태 업데이트
      setDimensions((prev: Dimension[]) => prev.map(d =>
        d.id === id ? { ...d, verification_status: status } : d
      ));

      // 통계 업데이트
      await loadDimensions(sessionId);
    } catch (err) {
      logger.error('Dimension verification failed:', err);
    }
  }, [sessionId, setDimensions, loadDimensions]);

  const handleDimensionEdit = useCallback(async (id: string, newValue: string) => {
    if (!sessionId) return;

    try {
      await axios.put(`${API_BASE_URL}/analysis/dimensions/${sessionId}/${id}`, {
        modified_value: newValue,
        verification_status: 'modified'
      });

      // 로컬 상태 업데이트
      setDimensions((prev: Dimension[]) => prev.map(d =>
        d.id === id ? { ...d, modified_value: newValue, verification_status: 'modified' } : d
      ));
    } catch (err) {
      logger.error('Dimension edit failed:', err);
    }
  }, [sessionId, setDimensions]);

  const handleDimensionDelete = useCallback(async (id: string) => {
    if (!sessionId) return;

    try {
      await axios.delete(`${API_BASE_URL}/analysis/dimensions/${sessionId}/${id}`);

      // 로컬 상태 업데이트
      setDimensions((prev: Dimension[]) => prev.filter(d => d.id !== id));

      // 통계 업데이트
      await loadDimensions(sessionId);
    } catch (err) {
      logger.error('Dimension delete failed:', err);
    }
  }, [sessionId, setDimensions, loadDimensions]);

  const handleAddManualDimension = useCallback(async (
    value: string,
    box: { x1: number; y1: number; x2: number; y2: number }
  ) => {
    if (!sessionId) return;
    try {
      await axios.post(
        `${API_BASE_URL}/analysis/dimensions/${sessionId}/manual`,
        null,
        { params: { value, x1: box.x1, y1: box.y1, x2: box.x2, y2: box.y2 } }
      );
      await loadDimensions(sessionId);
    } catch (err) {
      logger.error('Manual dimension add failed:', err);
    }
  }, [sessionId, loadDimensions]);

  const handleAutoApprove = useCallback(async () => {
    if (!sessionId) return;
    setIsLoading(true);
    try {
      await axios.post(
        `${API_BASE_URL}/verification/auto-approve/${sessionId}?item_type=dimension`
      );
      await loadDimensions(sessionId);
    } catch (err) {
      logger.error('Auto-approve failed:', err);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, loadDimensions]);

  const handleBulkApproveDimensions = useCallback(async (ids: string[]) => {
    if (!sessionId) return;

    setIsLoading(true);
    try {
      await axios.put(`${API_BASE_URL}/analysis/dimensions/${sessionId}/verify/bulk`, {
        updates: ids.map(id => ({ dimension_id: id, status: 'approved' }))
      });

      // 로컬 상태 업데이트
      setDimensions((prev: Dimension[]) => prev.map(d =>
        ids.includes(d.id) ? { ...d, verification_status: 'approved' } : d
      ));

      // 통계 업데이트
      await loadDimensions(sessionId);
    } catch (err) {
      logger.error('Bulk approve failed:', err);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, setDimensions, loadDimensions]);

  return {
    // Handlers
    loadDimensions,
    handleDimensionVerify,
    handleDimensionEdit,
    handleDimensionDelete,
    handleAddManualDimension,
    handleAutoApprove,
    handleBulkApproveDimensions,
    // States
    isLoading,
  };
}
