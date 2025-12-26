/**
 * GD&T Handlers Hook
 * GD&T 파싱 관련 핸들러
 */

import { useState, useCallback } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../../../lib/constants';
import logger from '../../../lib/logger';
import type { FeatureControlFrame, DatumFeature, GDTSummary } from '../../../components/GDTEditor';

interface UseGDTHandlersProps {
  sessionId: string | undefined;
  setGdtFcfList: (list: FeatureControlFrame[]) => void;
  setGdtDatums: (datums: DatumFeature[]) => void;
  setGdtSummary: (summary: GDTSummary | null) => void;
}

export function useGDTHandlers({
  sessionId,
  setGdtFcfList,
  setGdtDatums,
  setGdtSummary,
}: UseGDTHandlersProps) {
  const [isParsingGDT, setIsParsingGDT] = useState(false);

  const handleParseGDT = useCallback(async () => {
    if (!sessionId) return;

    setIsParsingGDT(true);
    try {
      const { data } = await axios.post(`${API_BASE_URL}/analysis/gdt/${sessionId}/parse`);
      setGdtFcfList(data.fcf_list || []);
      setGdtDatums(data.datums || []);

      // Summary 조회
      const summaryRes = await axios.get(`${API_BASE_URL}/analysis/gdt/${sessionId}/summary`);
      setGdtSummary(summaryRes.data || null);

      logger.info('GD&T 파싱 완료:', data.total_fcf, 'FCF,', data.total_datums, '데이텀');
    } catch (error) {
      logger.error('GD&T 파싱 실패:', error);
    } finally {
      setIsParsingGDT(false);
    }
  }, [sessionId, setGdtFcfList, setGdtDatums, setGdtSummary]);

  const handleFCFUpdate = useCallback(async (fcfId: string, updates: Partial<FeatureControlFrame>) => {
    if (!sessionId) return;

    try {
      await axios.put(`${API_BASE_URL}/analysis/gdt/${sessionId}/fcf/${fcfId}`, updates);
      // FCF 목록 새로고침
      const { data } = await axios.get(`${API_BASE_URL}/analysis/gdt/${sessionId}`);
      setGdtFcfList(data.fcf_list || []);
      logger.info('FCF 업데이트 완료:', fcfId);
    } catch (error) {
      logger.error('FCF 업데이트 실패:', error);
    }
  }, [sessionId, setGdtFcfList]);

  const handleFCFDelete = useCallback(async (fcfId: string) => {
    if (!sessionId) return;

    try {
      await axios.delete(`${API_BASE_URL}/analysis/gdt/${sessionId}/fcf/${fcfId}`);
      // FCF 목록 새로고침
      const { data } = await axios.get(`${API_BASE_URL}/analysis/gdt/${sessionId}`);
      setGdtFcfList(data.fcf_list || []);

      // Summary 업데이트
      const summaryRes = await axios.get(`${API_BASE_URL}/analysis/gdt/${sessionId}/summary`);
      setGdtSummary(summaryRes.data || null);

      logger.info('FCF 삭제 완료:', fcfId);
    } catch (error) {
      logger.error('FCF 삭제 실패:', error);
    }
  }, [sessionId, setGdtFcfList, setGdtSummary]);

  const handleDatumDelete = useCallback(async (datumId: string) => {
    if (!sessionId) return;

    try {
      await axios.delete(`${API_BASE_URL}/analysis/gdt/${sessionId}/datum/${datumId}`);
      // 데이텀 목록 새로고침
      const { data } = await axios.get(`${API_BASE_URL}/analysis/gdt/${sessionId}`);
      setGdtDatums(data.datums || []);

      // Summary 업데이트
      const summaryRes = await axios.get(`${API_BASE_URL}/analysis/gdt/${sessionId}/summary`);
      setGdtSummary(summaryRes.data || null);

      logger.info('데이텀 삭제 완료:', datumId);
    } catch (error) {
      logger.error('데이텀 삭제 실패:', error);
    }
  }, [sessionId, setGdtDatums, setGdtSummary]);

  return {
    // Handlers
    handleParseGDT,
    handleFCFUpdate,
    handleFCFDelete,
    handleDatumDelete,
    // States
    isParsingGDT,
  };
}
