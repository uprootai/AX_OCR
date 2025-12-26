/**
 * Mid-term Roadmap Features Hook
 * 중기 로드맵 기능 상태 및 핸들러
 * - 용접 기호 파싱
 * - 표면 거칠기 파싱
 * - 수량 추출
 * - 벌룬 매칭
 */

import { useState, useCallback } from 'react';
import { analysisApi } from '../../../lib/api';
import logger from '../../../lib/logger';
import type {
  WeldingParsingResult,
  SurfaceRoughnessResult,
  QuantityExtractionResult,
  BalloonMatchingResult,
} from '../../../lib/api';

interface UseMidTermFeaturesResult {
  // 용접 기호 파싱
  weldingResult: WeldingParsingResult | null;
  isParsingWelding: boolean;
  selectedWeldingId: string | null;
  setSelectedWeldingId: (id: string | null) => void;
  handleParseWelding: (sessionId: string) => Promise<void>;

  // 표면 거칠기 파싱
  roughnessResult: SurfaceRoughnessResult | null;
  isParsingRoughness: boolean;
  selectedRoughnessId: string | null;
  setSelectedRoughnessId: (id: string | null) => void;
  handleParseRoughness: (sessionId: string) => Promise<void>;

  // 수량 추출
  quantityResult: QuantityExtractionResult | null;
  isExtractingQuantity: boolean;
  selectedQuantityId: string | null;
  setSelectedQuantityId: (id: string | null) => void;
  handleExtractQuantity: (sessionId: string) => Promise<void>;

  // 벌룬 매칭
  balloonResult: BalloonMatchingResult | null;
  isMatchingBalloons: boolean;
  selectedBalloonId: string | null;
  setSelectedBalloonId: (id: string | null) => void;
  handleMatchBalloons: (sessionId: string) => Promise<void>;
  handleLinkBalloon: (sessionId: string, balloonId: string, symbolId: string) => Promise<void>;
}

export function useMidTermFeatures(): UseMidTermFeaturesResult {
  // 1. 용접 기호 파싱
  const [weldingResult, setWeldingResult] = useState<WeldingParsingResult | null>(null);
  const [isParsingWelding, setIsParsingWelding] = useState(false);
  const [selectedWeldingId, setSelectedWeldingId] = useState<string | null>(null);

  // 2. 표면 거칠기 파싱
  const [roughnessResult, setRoughnessResult] = useState<SurfaceRoughnessResult | null>(null);
  const [isParsingRoughness, setIsParsingRoughness] = useState(false);
  const [selectedRoughnessId, setSelectedRoughnessId] = useState<string | null>(null);

  // 3. 수량 추출
  const [quantityResult, setQuantityResult] = useState<QuantityExtractionResult | null>(null);
  const [isExtractingQuantity, setIsExtractingQuantity] = useState(false);
  const [selectedQuantityId, setSelectedQuantityId] = useState<string | null>(null);

  // 4. 벌룬 매칭
  const [balloonResult, setBalloonResult] = useState<BalloonMatchingResult | null>(null);
  const [isMatchingBalloons, setIsMatchingBalloons] = useState(false);
  const [selectedBalloonId, setSelectedBalloonId] = useState<string | null>(null);

  // 핸들러: 용접 기호 파싱
  const handleParseWelding = useCallback(async (sessionId: string) => {
    if (!sessionId) return;
    setIsParsingWelding(true);
    try {
      const result = await analysisApi.parseWeldingSymbols(sessionId);
      setWeldingResult(result);
      logger.log(`🔩 용접 기호 파싱 완료: ${result.total_count}개`);
    } catch (err) {
      logger.error('Welding symbol parsing failed:', err);
    } finally {
      setIsParsingWelding(false);
    }
  }, []);

  // 핸들러: 표면 거칠기 파싱
  const handleParseRoughness = useCallback(async (sessionId: string) => {
    if (!sessionId) return;
    setIsParsingRoughness(true);
    try {
      const result = await analysisApi.parseSurfaceRoughness(sessionId);
      setRoughnessResult(result);
      logger.log(`🪨 표면 거칠기 파싱 완료: ${result.total_count}개`);
    } catch (err) {
      logger.error('Surface roughness parsing failed:', err);
    } finally {
      setIsParsingRoughness(false);
    }
  }, []);

  // 핸들러: 수량 추출
  const handleExtractQuantity = useCallback(async (sessionId: string) => {
    if (!sessionId) return;
    setIsExtractingQuantity(true);
    try {
      const result = await analysisApi.extractQuantities(sessionId);
      setQuantityResult(result);
      logger.log(`🔢 수량 추출 완료: ${result.total_items}개 항목, 총 ${result.total_quantity}개`);
    } catch (err) {
      logger.error('Quantity extraction failed:', err);
    } finally {
      setIsExtractingQuantity(false);
    }
  }, []);

  // 핸들러: 벌룬 매칭
  const handleMatchBalloons = useCallback(async (sessionId: string) => {
    if (!sessionId) return;
    setIsMatchingBalloons(true);
    try {
      const result = await analysisApi.matchBalloons(sessionId);
      setBalloonResult(result);
      logger.log(`🎈 벌룬 매칭 완료: ${result.matched_count}/${result.total_balloons}개 매칭됨 (${result.match_rate.toFixed(1)}%)`);
    } catch (err) {
      logger.error('Balloon matching failed:', err);
    } finally {
      setIsMatchingBalloons(false);
    }
  }, []);

  // 핸들러: 벌룬-심볼 수동 연결
  const handleLinkBalloon = useCallback(async (sessionId: string, balloonId: string, symbolId: string) => {
    if (!sessionId) return;
    try {
      const result = await analysisApi.linkBalloonToSymbol(sessionId, balloonId, symbolId);
      // 결과 업데이트
      if (balloonResult) {
        const updated = balloonResult.balloons.map(b =>
          b.id === balloonId ? result.balloon : b
        );
        setBalloonResult({
          ...balloonResult,
          balloons: updated,
          matched_count: updated.filter(b => b.matched_symbol_id).length,
          unmatched_count: updated.filter(b => !b.matched_symbol_id).length,
          match_rate: (updated.filter(b => b.matched_symbol_id).length / updated.length) * 100,
        });
      }
      logger.log(`🎈 벌룬 ${balloonId} → 심볼 ${symbolId} 연결됨`);
    } catch (err) {
      logger.error('Balloon link failed:', err);
    }
  }, [balloonResult]);

  return {
    // 용접 기호 파싱
    weldingResult,
    isParsingWelding,
    selectedWeldingId,
    setSelectedWeldingId,
    handleParseWelding,

    // 표면 거칠기 파싱
    roughnessResult,
    isParsingRoughness,
    selectedRoughnessId,
    setSelectedRoughnessId,
    handleParseRoughness,

    // 수량 추출
    quantityResult,
    isExtractingQuantity,
    selectedQuantityId,
    setSelectedQuantityId,
    handleExtractQuantity,

    // 벌룬 매칭
    balloonResult,
    isMatchingBalloons,
    selectedBalloonId,
    setSelectedBalloonId,
    handleMatchBalloons,
    handleLinkBalloon,
  };
}
