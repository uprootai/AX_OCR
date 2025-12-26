/**
 * Mid-term Roadmap Features Section
 * 중기 로드맵 4개 기능 UI 섹션
 * - 용접 기호 파싱
 * - 표면 거칠기 파싱
 * - 수량 추출
 * - 벌룬 매칭
 */

import { Loader2, RefreshCw, Check, AlertCircle } from 'lucide-react';
import { InfoTooltip } from '../../../components/Tooltip';
import type { SectionVisibility } from '../types/workflow';
import type {
  WeldingParsingResult,
  SurfaceRoughnessResult,
  QuantityExtractionResult,
  BalloonMatchingResult,
} from '../../../lib/api';

interface Detection {
  id: string;
  class_name: string;
}

interface MidTermSectionProps {
  sessionId: string | undefined;
  imageData: string | null;
  visibility: SectionVisibility;
  detections: Detection[];

  // 용접 기호
  weldingResult: WeldingParsingResult | null;
  isParsingWelding: boolean;
  selectedWeldingId: string | null;
  onSelectWelding: (id: string | null) => void;
  onParseWelding: () => void;

  // 표면 거칠기
  roughnessResult: SurfaceRoughnessResult | null;
  isParsingRoughness: boolean;
  selectedRoughnessId: string | null;
  onSelectRoughness: (id: string | null) => void;
  onParseRoughness: () => void;

  // 수량 추출
  quantityResult: QuantityExtractionResult | null;
  isExtractingQuantity: boolean;
  selectedQuantityId: string | null;
  onSelectQuantity: (id: string | null) => void;
  onExtractQuantity: () => void;

  // 벌룬 매칭
  balloonResult: BalloonMatchingResult | null;
  isMatchingBalloons: boolean;
  selectedBalloonId: string | null;
  onSelectBalloon: (id: string | null) => void;
  onMatchBalloons: () => void;
  onLinkBalloon: (balloonId: string, symbolId: string) => void;
}

export function MidTermSection({
  sessionId,
  imageData,
  visibility,
  detections,
  weldingResult,
  isParsingWelding,
  selectedWeldingId,
  onSelectWelding,
  onParseWelding,
  roughnessResult,
  isParsingRoughness,
  selectedRoughnessId,
  onSelectRoughness,
  onParseRoughness,
  quantityResult,
  isExtractingQuantity,
  selectedQuantityId,
  onSelectQuantity,
  onExtractQuantity,
  balloonResult,
  isMatchingBalloons,
  selectedBalloonId,
  onSelectBalloon,
  onMatchBalloons,
  onLinkBalloon,
}: MidTermSectionProps) {
  if (!sessionId || !imageData) return null;

  return (
    <>
      {/* 1. 용접 기호 파싱 */}
      {visibility.weldingSymbolParsing && (
        <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              🔩 용접 기호
              <InfoTooltip content="도면에서 용접 기호를 감지하고 ISO 2553/AWS A2.4 표준에 따라 파싱합니다." position="right" />
              {weldingResult && (
                <span className="px-2 py-0.5 text-xs font-normal bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300 rounded-full">
                  {weldingResult.total_count}개
                </span>
              )}
            </h2>
            <button
              onClick={onParseWelding}
              disabled={isParsingWelding}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isParsingWelding ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  파싱 중...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  용접 파싱
                </>
              )}
            </button>
          </div>

          {weldingResult && weldingResult.welding_symbols.length > 0 ? (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {weldingResult.welding_symbols.map((symbol) => (
                <div
                  key={symbol.id}
                  onClick={() => onSelectWelding(selectedWeldingId === symbol.id ? null : symbol.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedWeldingId === symbol.id
                      ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-300'
                      : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 hover:border-amber-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{symbol.welding_type}</span>
                    <span className="text-xs text-gray-500">{(symbol.confidence * 100).toFixed(0)}%</span>
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    {symbol.size && <span className="mr-2">크기: {symbol.size}</span>}
                    {symbol.process && <span>공정: {symbol.process}</span>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🔩</div>
              <p>용접 파싱을 실행하여 용접 기호를 분석하세요</p>
            </div>
          )}
        </section>
      )}

      {/* 2. 표면 거칠기 */}
      {visibility.surfaceRoughnessParsing && (
        <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              🪨 표면 거칠기
              <InfoTooltip content="도면에서 표면 거칠기 기호(Ra, Rz, Rmax)를 검출하고 가공 방법을 분류합니다." position="right" />
              {roughnessResult && (
                <span className="px-2 py-0.5 text-xs font-normal bg-stone-100 text-stone-700 dark:bg-stone-900/30 dark:text-stone-300 rounded-full">
                  {roughnessResult.total_count}개
                </span>
              )}
            </h2>
            <button
              onClick={onParseRoughness}
              disabled={isParsingRoughness}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-stone-600 text-white rounded-lg hover:bg-stone-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isParsingRoughness ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  파싱 중...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  거칠기 파싱
                </>
              )}
            </button>
          </div>

          {roughnessResult && roughnessResult.roughness_symbols.length > 0 ? (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {roughnessResult.roughness_symbols.map((symbol) => (
                <div
                  key={symbol.id}
                  onClick={() => onSelectRoughness(selectedRoughnessId === symbol.id ? null : symbol.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedRoughnessId === symbol.id
                      ? 'bg-stone-50 dark:bg-stone-900/20 border-stone-300'
                      : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 hover:border-stone-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{symbol.roughness_type}: {symbol.value}</span>
                    <span className="text-xs text-gray-500">{(symbol.confidence * 100).toFixed(0)}%</span>
                  </div>
                  {symbol.machining_method && (
                    <p className="text-sm text-gray-500 mt-1">가공: {symbol.machining_method}</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🪨</div>
              <p>표면 거칠기 파싱을 실행하여 거칠기 정보를 추출하세요</p>
            </div>
          )}
        </section>
      )}

      {/* 3. 수량 추출 */}
      {visibility.quantityExtraction && (
        <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              🔢 수량 추출
              <InfoTooltip content="도면에서 부품 수량 정보를 추출합니다. QTY, 수량, EA 등의 패턴을 인식합니다." position="right" />
              {quantityResult && (
                <>
                  <span className="px-2 py-0.5 text-xs font-normal bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300 rounded-full">
                    {quantityResult.total_items}개 항목
                  </span>
                  <span className="px-2 py-0.5 text-xs font-normal bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 rounded-full">
                    총 {quantityResult.total_quantity}개
                  </span>
                </>
              )}
            </h2>
            <button
              onClick={onExtractQuantity}
              disabled={isExtractingQuantity}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isExtractingQuantity ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  추출 중...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  수량 추출
                </>
              )}
            </button>
          </div>

          {quantityResult && quantityResult.quantities.length > 0 ? (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {quantityResult.quantities.map((item) => (
                <div
                  key={item.id}
                  onClick={() => onSelectQuantity(selectedQuantityId === item.id ? null : item.id)}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedQuantityId === item.id
                      ? 'bg-cyan-50 dark:bg-cyan-900/20 border-cyan-300'
                      : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 hover:border-cyan-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl font-bold text-cyan-600">{item.quantity}</span>
                      {item.unit && <span className="text-sm text-gray-500">{item.unit}</span>}
                    </div>
                    <span className="text-xs px-2 py-1 bg-cyan-100 text-cyan-700 rounded">
                      {(item.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {item.part_number && <span className="mr-2">부품번호: {item.part_number}</span>}
                    {item.balloon_number && <span>벌룬: {item.balloon_number}</span>}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🔢</div>
              <p>수량 추출을 실행하여 부품 수량을 파악하세요</p>
            </div>
          )}
        </section>
      )}

      {/* 4. 벌룬 매칭 */}
      {visibility.balloonMatching && (
        <section className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              🎈 벌룬 매칭
              <InfoTooltip content="벌룬 번호를 검출하고 해당 심볼과 자동으로 매칭합니다." position="right" />
              {balloonResult && (
                <>
                  <span className="px-2 py-0.5 text-xs font-normal bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300 rounded-full">
                    {balloonResult.total_balloons}개
                  </span>
                  <span className="px-2 py-0.5 text-xs font-normal bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300 rounded-full">
                    {balloonResult.match_rate.toFixed(0)}% 매칭
                  </span>
                </>
              )}
            </h2>
            <button
              onClick={onMatchBalloons}
              disabled={isMatchingBalloons || detections.length === 0}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-pink-600 text-white rounded-lg hover:bg-pink-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isMatchingBalloons ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  매칭 중...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  벌룬 매칭
                </>
              )}
            </button>
          </div>

          {balloonResult && balloonResult.balloons.length > 0 ? (
            <div className="space-y-4">
              <div className="grid grid-cols-4 gap-3">
                <div className="bg-pink-50 dark:bg-pink-900/20 rounded-lg p-3 text-center">
                  <p className="text-lg font-bold text-pink-600">{balloonResult.total_balloons}</p>
                  <p className="text-xs text-gray-500">전체</p>
                </div>
                <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
                  <p className="text-lg font-bold text-green-600">{balloonResult.matched_count}</p>
                  <p className="text-xs text-gray-500">매칭됨</p>
                </div>
                <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 text-center">
                  <p className="text-lg font-bold text-yellow-600">{balloonResult.unmatched_count}</p>
                  <p className="text-xs text-gray-500">미매칭</p>
                </div>
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
                  <p className="text-lg font-bold text-blue-600">{balloonResult.match_rate.toFixed(0)}%</p>
                  <p className="text-xs text-gray-500">매칭률</p>
                </div>
              </div>

              <div className="space-y-2 max-h-64 overflow-y-auto">
                {balloonResult.balloons.map((balloon) => (
                  <div
                    key={balloon.id}
                    onClick={() => onSelectBalloon(selectedBalloonId === balloon.id ? null : balloon.id)}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedBalloonId === balloon.id
                        ? 'bg-pink-50 dark:bg-pink-900/20 border-pink-300'
                        : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 hover:border-pink-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="w-8 h-8 rounded-full bg-pink-100 dark:bg-pink-900/30 flex items-center justify-center text-lg font-bold text-pink-600">
                          {balloon.number}
                        </span>
                        <div>
                          {balloon.matched_symbol_id ? (
                            <span className="text-green-600 font-medium flex items-center gap-1">
                              <Check className="w-4 h-4" />
                              {balloon.matched_symbol_class || balloon.matched_symbol_id}
                            </span>
                          ) : (
                            <span className="text-yellow-600 font-medium flex items-center gap-1">
                              <AlertCircle className="w-4 h-4" />
                              미매칭
                            </span>
                          )}
                        </div>
                      </div>
                      <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
                        {balloon.shape}
                      </span>
                    </div>

                    {/* 수동 연결 UI */}
                    {selectedBalloonId === balloon.id && !balloon.matched_symbol_id && detections.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                        <p className="text-sm text-gray-600 mb-2">수동 연결:</p>
                        <div className="flex flex-wrap gap-1">
                          {detections.slice(0, 10).map((d) => (
                            <button
                              key={d.id}
                              onClick={(e) => {
                                e.stopPropagation();
                                onLinkBalloon(balloon.id, d.id);
                              }}
                              className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                            >
                              {d.class_name}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">🎈</div>
              <p>벌룬 매칭을 실행하여 부품 번호를 연결하세요</p>
              <p className="text-sm text-gray-400 mt-1">
                {detections.length === 0
                  ? '먼저 심볼 검출을 실행하세요'
                  : `${detections.length}개 심볼 검출됨 - 매칭 가능`}
              </p>
            </div>
          )}
        </section>
      )}
    </>
  );
}
