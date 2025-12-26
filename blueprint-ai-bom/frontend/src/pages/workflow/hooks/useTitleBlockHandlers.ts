/**
 * Title Block Handlers Hook
 * 표제란 OCR 추출/수정 핸들러
 */

import { useState, useCallback } from 'react';
import { analysisApi } from '../../../lib/api';
import logger from '../../../lib/logger';
import type { TitleBlockData } from '../../../lib/api';

interface UseTitleBlockHandlersProps {
  sessionId: string | undefined;
  setTitleBlockData: (data: TitleBlockData | null) => void;
  editingTitleBlock: Partial<TitleBlockData> | null;
  setEditingTitleBlock: (data: Partial<TitleBlockData> | null) => void;
}

export function useTitleBlockHandlers({
  sessionId,
  setTitleBlockData,
  editingTitleBlock,
  setEditingTitleBlock,
}: UseTitleBlockHandlersProps) {
  const [isExtractingTitleBlock, setIsExtractingTitleBlock] = useState(false);
  const [isUpdatingTitleBlock, setIsUpdatingTitleBlock] = useState(false);

  const handleExtractTitleBlock = useCallback(async () => {
    if (!sessionId) return;

    setIsExtractingTitleBlock(true);
    try {
      const result = await analysisApi.extractTitleBlock(sessionId);
      if (result.title_block) {
        setTitleBlockData(result.title_block);
        logger.info('표제란 OCR 완료');
      } else {
        logger.warn('표제란을 찾을 수 없습니다');
      }
    } catch (err) {
      logger.error('Title block extraction failed:', err);
    } finally {
      setIsExtractingTitleBlock(false);
    }
  }, [sessionId, setTitleBlockData]);

  const handleUpdateTitleBlock = useCallback(async () => {
    if (!sessionId || !editingTitleBlock) return;

    setIsUpdatingTitleBlock(true);
    try {
      const result = await analysisApi.updateTitleBlock(sessionId, editingTitleBlock);
      setTitleBlockData(result.title_block);
      setEditingTitleBlock(null);
      logger.info('표제란 정보 수정 완료');
    } catch (err) {
      logger.error('Title block update failed:', err);
    } finally {
      setIsUpdatingTitleBlock(false);
    }
  }, [sessionId, editingTitleBlock, setTitleBlockData, setEditingTitleBlock]);

  const handleCancelEditTitleBlock = useCallback(() => {
    setEditingTitleBlock(null);
  }, [setEditingTitleBlock]);

  const handleStartEditTitleBlock = useCallback((data: TitleBlockData) => {
    setEditingTitleBlock({ ...data });
  }, [setEditingTitleBlock]);

  return {
    // Handlers
    handleExtractTitleBlock,
    handleUpdateTitleBlock,
    handleCancelEditTitleBlock,
    handleStartEditTitleBlock,
    // States
    isExtractingTitleBlock,
    isUpdatingTitleBlock,
  };
}
