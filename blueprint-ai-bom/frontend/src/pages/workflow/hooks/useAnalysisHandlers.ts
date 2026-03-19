/**
 * Analysis Handlers Hook
 * 분석 실행 관련 핸들러
 */

import { useState, useCallback } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../../../lib/constants';
import { analysisApi } from '../../../lib/api';
import logger from '../../../lib/logger';
import type { ConnectivityResult } from '../../../lib/api';

interface AnalysisOptionsData {
  enable_symbol_detection: boolean;
  enable_dimension_ocr: boolean;
  enable_line_detection: boolean;
  enable_text_extraction: boolean;
  ocr_engine: string;
  confidence_threshold: number;
  symbol_model_type: string;
  preset: string | null;
  // Detectron2 옵션
  detection_backend: 'yolo' | 'detectron2';
  return_masks: boolean;
  return_polygons: boolean;
}

interface LineData {
  id: string;
  start: { x: number; y: number };
  end: { x: number; y: number };
  length: number;
  angle: number;
  line_type: string;
  line_style: string;
  color?: string;
  confidence: number;
  thickness?: number;
}

interface IntersectionData {
  id: string;
  point: { x: number; y: number };
  line_ids: string[];
  intersection_type?: string;
}

// Use generic types for flexibility with external types
interface DimensionLike {
  verification_status?: string;
  [key: string]: unknown;
}

interface DimensionStatsLike {
  pending: number;
  approved: number;
  rejected: number;
  modified: number;
  manual: number;
}

interface RelationStatisticsLike {
  total: number;
  by_method: Record<string, number>;
  by_confidence: { high: number; medium: number; low: number };
  linked_count: number;
  unlinked_count: number;
}

interface UseAnalysisHandlersProps {
  sessionId: string | undefined;
  selectedImageId?: string | null;
  setIsAnalyzing: (value: boolean) => void;
  setAnalysisOptions: (options: AnalysisOptionsData) => void;
  setLines: (lines: LineData[]) => void;
  setIntersections: (intersections: IntersectionData[]) => void;
  setConnectivity: (result: ConnectivityResult | null) => void;
  loadSession: (sessionId: string) => Promise<void>;
  loadImage?: (sessionId: string, imageId: string) => Promise<void>;
  // Dimension handling (optional for backward compatibility)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  setDimensions?: (dimensions: any[]) => void;
  setDimensionStats?: (stats: DimensionStatsLike | null) => void;
  // Relation handling (optional for backward compatibility)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  setRelations?: (relations: any[]) => void;
  setRelationStats?: (stats: RelationStatisticsLike | null) => void;
}

export function useAnalysisHandlers({
  sessionId,
  selectedImageId,
  setIsAnalyzing,
  setAnalysisOptions,
  setLines,
  setIntersections,
  setConnectivity,
  loadSession,
  loadImage,
  setDimensions,
  setDimensionStats,
  setRelations,
  setRelationStats,
}: UseAnalysisHandlersProps) {
  const [isRunningLineDetection, setIsRunningLineDetection] = useState(false);
  const [isAnalyzingConnectivity, setIsAnalyzingConnectivity] = useState(false);

  // 선택된 이미지가 서브이미지인지 판단
  const isSubImage = selectedImageId && selectedImageId !== 'main';

  const handleRunAnalysis = useCallback(async () => {
    if (!sessionId) return null;

    setIsAnalyzing(true);
    try {
      // 서브이미지가 선택되면 이미지별 분석 API 호출
      const url = isSubImage
        ? `${API_BASE_URL}/analysis/run/${sessionId}/image/${selectedImageId}`
        : `${API_BASE_URL}/analysis/run/${sessionId}`;

      const { data } = await axios.post(url);
      logger.info(isSubImage ? `서브이미지 분석 완료 (${selectedImageId}):` : '분석 완료:', data);

      if (isSubImage && selectedImageId) {
        // 서브이미지: loadImage로 해당 이미지 데이터 + 검출 결과 반영
        if (loadImage) {
          await loadImage(sessionId, selectedImageId);
        }

        // 치수 OCR 결과 (서브이미지 분석 응답에서 직접 적용)
        if (data.dimensions && data.dimensions.length > 0 && setDimensions && setDimensionStats) {
          setDimensions(data.dimensions);
          const stats: DimensionStatsLike = { pending: 0, approved: 0, rejected: 0, modified: 0, manual: 0 };
          data.dimensions.forEach((d: DimensionLike) => {
            const status = d.verification_status || 'pending';
            if (status in stats) stats[status as keyof DimensionStatsLike]++;
          });
          setDimensionStats(stats);
        }

        // 분석 결과 요약 알림
        const dimCount = data.dimension_count ?? data.dimensions?.length ?? 0;
        const detCount = data.detection_count ?? data.detections?.length ?? 0;
        const parts = [];
        if (dimCount > 0) parts.push(`치수 ${dimCount}개`);
        if (detCount > 0) parts.push(`검출 ${detCount}개`);
        if (data.od) parts.push(`OD: ${data.od}`);
        if (data.id) parts.push(`ID: ${data.id}`);
        if (data.width) parts.push(`W: ${data.width}`);
        alert(parts.length > 0
          ? `서브이미지 분석 완료: ${parts.join(', ')}`
          : '서브이미지 분석 완료: 검출된 치수/심볼이 없습니다.'
        );
      } else {
        // 메인 이미지: 기존 로직
        // 심볼 검출 결과는 기존 detections로 처리
        if (data.detections && data.detections.length > 0) {
          await loadSession(sessionId);
        }

        // 치수 OCR 결과
        if (data.dimensions && setDimensions && setDimensionStats) {
          setDimensions(data.dimensions);
          const stats: DimensionStatsLike = { pending: 0, approved: 0, rejected: 0, modified: 0, manual: 0 };
          data.dimensions.forEach((d: DimensionLike) => {
            const status = d.verification_status || 'pending';
            if (status in stats) stats[status as keyof DimensionStatsLike]++;
          });
          setDimensionStats(stats);
        }

        // Phase 2: 관계 추출 결과
        if (data.relations && setRelations && setRelationStats) {
          setRelations(data.relations);
          try {
            const statsRes = await axios.get(`${API_BASE_URL}/relations/${sessionId}/statistics`);
            setRelationStats(statsRes.data || null);
          } catch {
            setRelationStats({
              total: data.relations.length,
              by_method: {},
              by_confidence: { high: 0, medium: 0, low: 0 },
              linked_count: 0,
              unlinked_count: data.relations.length,
            });
          }
          logger.info(`관계 추출 완료: ${data.relations.length}개`);
        }
      }

      return data;
    } catch (error) {
      logger.error('분석 실행 실패:', error);
      return null;
    } finally {
      setIsAnalyzing(false);
    }
  }, [sessionId, selectedImageId, isSubImage, setIsAnalyzing, loadSession, loadImage, setDimensions, setDimensionStats, setRelations, setRelationStats]);

  const handleAnalysisOptionsChange = useCallback((options: AnalysisOptionsData) => {
    setAnalysisOptions(options);
    logger.debug('분석 옵션 변경:', options);
  }, [setAnalysisOptions]);

  const handleRunLineDetection = useCallback(async () => {
    if (!sessionId) return;

    setIsRunningLineDetection(true);
    try {
      const { data } = await axios.post(`${API_BASE_URL}/analysis/lines/${sessionId}`);
      setLines(data.lines || []);
      setIntersections(data.intersections || []);
      logger.info('선 검출 완료:', data.lines?.length, '개');
    } catch (error) {
      logger.error('선 검출 실패:', error);
    } finally {
      setIsRunningLineDetection(false);
    }
  }, [sessionId, setLines, setIntersections]);

  const handleLinkDimensionsToSymbols = useCallback(async () => {
    if (!sessionId) return;

    try {
      const { data } = await axios.post(`${API_BASE_URL}/analysis/lines/${sessionId}/link-dimensions`);
      logger.info('치수-심볼 연결 완료:', data);
      return data;
    } catch (error) {
      logger.error('치수-심볼 연결 실패:', error);
      return null;
    }
  }, [sessionId]);

  const handleAnalyzeConnectivity = useCallback(async () => {
    if (!sessionId) return;

    setIsAnalyzingConnectivity(true);
    try {
      const result = await analysisApi.analyzeConnectivity(sessionId);
      setConnectivity(result.connectivity_graph);
      logger.info('연결성 분석 완료:', result.connectivity_graph.statistics);
    } catch (error) {
      logger.error('연결성 분석 실패:', error);
    } finally {
      setIsAnalyzingConnectivity(false);
    }
  }, [sessionId, setConnectivity]);

  const handleFindPath = useCallback(async (startId: string, endId: string) => {
    if (!sessionId) return null;

    try {
      const result = await analysisApi.findPath(sessionId, startId, endId);
      logger.info('경로 찾기 결과:', result);
      return result;
    } catch (error) {
      logger.error('경로 찾기 실패:', error);
      return null;
    }
  }, [sessionId]);

  return {
    // Handlers
    handleRunAnalysis,
    handleAnalysisOptionsChange,
    handleRunLineDetection,
    handleLinkDimensionsToSymbols,
    handleAnalyzeConnectivity,
    handleFindPath,
    // States
    isRunningLineDetection,
    isAnalyzingConnectivity,
  };
}
