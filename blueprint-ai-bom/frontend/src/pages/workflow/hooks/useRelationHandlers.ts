/**
 * Relation Handlers Hook
 * 치수-객체 관계 추출/연결/삭제 핸들러
 */

import { useState, useCallback } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../../../lib/constants';
import logger from '../../../lib/logger';
import type { DimensionRelation, RelationStatistics } from '../../../types';

interface UseRelationHandlersProps {
  sessionId: string | undefined;
  setRelations: (relations: DimensionRelation[]) => void;
  setRelationStats: (stats: RelationStatistics | null) => void;
}

export function useRelationHandlers({
  sessionId,
  setRelations,
  setRelationStats,
}: UseRelationHandlersProps) {
  const [isExtractingRelations, setIsExtractingRelations] = useState(false);

  const loadRelations = useCallback(async (sid: string) => {
    try {
      const { data } = await axios.get(`${API_BASE_URL}/relations/${sid}`);
      setRelations(data.relations || []);
      const statsRes = await axios.get(`${API_BASE_URL}/relations/${sid}/statistics`);
      setRelationStats(statsRes.data || null);
    } catch (err) {
      logger.error('Failed to load relations:', err);
      setRelations([]);
      setRelationStats(null);
    }
  }, [setRelations, setRelationStats]);

  const handleExtractRelations = useCallback(async () => {
    if (!sessionId) return;

    setIsExtractingRelations(true);
    try {
      const { data } = await axios.post(`${API_BASE_URL}/relations/extract/${sessionId}?use_lines=true`);
      setRelations(data.relations || []);
      setRelationStats(data.statistics || null);
      logger.info('관계 추출 완료:', data.relations?.length, '개');
    } catch (err) {
      logger.error('Relation extraction failed:', err);
    } finally {
      setIsExtractingRelations(false);
    }
  }, [sessionId, setRelations, setRelationStats]);

  const handleManualLink = useCallback(async (dimensionId: string, targetId: string) => {
    if (!sessionId) return;

    try {
      await axios.post(`${API_BASE_URL}/relations/${sessionId}/link/${dimensionId}/${targetId}`);
      logger.info('수동 연결 완료:', dimensionId, '→', targetId);

      // 관계 목록 다시 로드
      await loadRelations(sessionId);
    } catch (err) {
      logger.error('Manual link failed:', err);
    }
  }, [sessionId, loadRelations]);

  const handleDeleteRelation = useCallback(async (relationId: string) => {
    if (!sessionId) return;

    try {
      await axios.delete(`${API_BASE_URL}/relations/${sessionId}/${relationId}`);
      logger.info('관계 삭제 완료:', relationId);

      // 관계 목록 다시 로드
      await loadRelations(sessionId);
    } catch (err) {
      logger.error('Delete relation failed:', err);
    }
  }, [sessionId, loadRelations]);

  return {
    // Handlers
    loadRelations,
    handleExtractRelations,
    handleManualLink,
    handleDeleteRelation,
    // States
    isExtractingRelations,
  };
}
