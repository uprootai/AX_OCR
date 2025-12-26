/**
 * Long-term Roadmap Features Hook
 * 장기 로드맵 기능 상태 및 핸들러
 * - 도면 영역 세분화
 * - 주석/노트 추출
 * - 리비전 비교
 * - VLM 자동 분류
 */

import { useState, useCallback } from 'react';
import { longtermApi } from '../../../lib/api';
import logger from '../../../lib/logger';
import type {
  DrawingRegion,
  ExtractedNote,
  RevisionChange,
  VLMClassificationResult,
} from '../../../lib/api';

interface UseLongTermFeaturesResult {
  // 도면 영역 세분화
  drawingRegions: DrawingRegion[];
  isSegmentingRegions: boolean;
  selectedRegionId: string | null;
  setSelectedRegionId: (id: string | null) => void;
  handleSegmentRegions: (sessionId: string) => Promise<void>;

  // 주석/노트 추출
  extractedNotes: ExtractedNote[];
  isExtractingNotes: boolean;
  selectedNoteId: string | null;
  setSelectedNoteId: (id: string | null) => void;
  handleExtractNotes: (sessionId: string) => Promise<void>;

  // 리비전 비교
  revisionChanges: RevisionChange[];
  isComparingRevisions: boolean;
  comparisonSessionId: string;
  setComparisonSessionId: (id: string) => void;
  handleCompareRevisions: (sessionId: string, compareToSessionId: string) => Promise<void>;

  // VLM 자동 분류
  vlmClassification: VLMClassificationResult | null;
  isVlmClassifying: boolean;
  handleVlmClassify: (sessionId: string) => Promise<void>;
}

export function useLongTermFeatures(): UseLongTermFeaturesResult {
  // 1. 도면 영역 세분화
  const [drawingRegions, setDrawingRegions] = useState<DrawingRegion[]>([]);
  const [isSegmentingRegions, setIsSegmentingRegions] = useState(false);
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null);

  // 2. 주석/노트 추출
  const [extractedNotes, setExtractedNotes] = useState<ExtractedNote[]>([]);
  const [isExtractingNotes, setIsExtractingNotes] = useState(false);
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null);

  // 3. 리비전 비교
  const [revisionChanges, setRevisionChanges] = useState<RevisionChange[]>([]);
  const [isComparingRevisions, setIsComparingRevisions] = useState(false);
  const [comparisonSessionId, setComparisonSessionId] = useState<string>('');

  // 4. VLM 자동 분류
  const [vlmClassification, setVlmClassification] = useState<VLMClassificationResult | null>(null);
  const [isVlmClassifying, setIsVlmClassifying] = useState(false);

  // 핸들러: 도면 영역 세분화
  const handleSegmentRegions = useCallback(async (sessionId: string) => {
    if (!sessionId) return;
    setIsSegmentingRegions(true);
    try {
      const result = await longtermApi.segmentDrawingRegions(sessionId);
      setDrawingRegions(result.regions);
      logger.log(`🗺️ 도면 영역 세분화 완료: ${result.total_regions}개 영역 검출`);
    } catch (err) {
      logger.error('Region segmentation failed:', err);
    } finally {
      setIsSegmentingRegions(false);
    }
  }, []);

  // 핸들러: 주석/노트 추출
  const handleExtractNotes = useCallback(async (sessionId: string) => {
    if (!sessionId) return;
    setIsExtractingNotes(true);
    try {
      const result = await longtermApi.extractNotes(sessionId);
      setExtractedNotes(result.notes);
      logger.log(`📋 주석/노트 추출 완료: ${result.total_notes}개 추출`);
    } catch (err) {
      logger.error('Notes extraction failed:', err);
    } finally {
      setIsExtractingNotes(false);
    }
  }, []);

  // 핸들러: 리비전 비교
  const handleCompareRevisions = useCallback(async (sessionId: string, compareToSessionId: string) => {
    if (!sessionId || !compareToSessionId) return;
    setIsComparingRevisions(true);
    try {
      const result = await longtermApi.compareRevisions(sessionId, compareToSessionId);
      setRevisionChanges(result.changes);
      logger.log(`🔄 리비전 비교 완료: ${result.total_changes}개 변경점 감지`);
    } catch (err) {
      logger.error('Revision comparison failed:', err);
    } finally {
      setIsComparingRevisions(false);
    }
  }, []);

  // 핸들러: VLM 자동 분류
  const handleVlmClassify = useCallback(async (sessionId: string) => {
    if (!sessionId) return;
    setIsVlmClassifying(true);
    try {
      const result = await longtermApi.vlmClassify(sessionId);
      setVlmClassification(result);
      logger.log(`🤖 VLM 분류 완료: ${result.drawing_type} (${(result.drawing_type_confidence * 100).toFixed(1)}%)`);
    } catch (err) {
      logger.error('VLM classification failed:', err);
    } finally {
      setIsVlmClassifying(false);
    }
  }, []);

  return {
    // 도면 영역 세분화
    drawingRegions,
    isSegmentingRegions,
    selectedRegionId,
    setSelectedRegionId,
    handleSegmentRegions,

    // 주석/노트 추출
    extractedNotes,
    isExtractingNotes,
    selectedNoteId,
    setSelectedNoteId,
    handleExtractNotes,

    // 리비전 비교
    revisionChanges,
    isComparingRevisions,
    comparisonSessionId,
    setComparisonSessionId,
    handleCompareRevisions,

    // VLM 자동 분류
    vlmClassification,
    isVlmClassifying,
    handleVlmClassify,
  };
}
