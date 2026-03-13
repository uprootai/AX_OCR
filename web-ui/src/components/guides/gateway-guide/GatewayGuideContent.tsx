import { Badge } from '../../ui/Badge';
import Mermaid from '../../ui/Mermaid';
import { systemDiagram, hybridPipelineDiagram, speedPipelineDiagram } from './diagrams';

type PipelineMode = 'hybrid' | 'speed';

interface GatewayGuideContentProps {
  selectedPipeline: PipelineMode;
  onSelectPipeline: (mode: PipelineMode) => void;
}

export function GatewayGuideContent({ selectedPipeline, onSelectPipeline }: GatewayGuideContentProps) {
  return (
    <div className="space-y-6">
      {/* 📊 시스템 아키텍처 */}
      <div>
        <h3 className="text-lg font-semibold mb-3">📊 시스템 아키텍처</h3>
        <Mermaid chart={systemDiagram} />
      </div>

      {/* 📋 추가 옵션별 파이프라인 영향 */}
      <div className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950 dark:to-orange-950 p-6 rounded-lg border-2 border-amber-200 dark:border-amber-800">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          📋 추가 옵션별 파이프라인 영향
        </h3>
        <p className="text-sm text-muted-foreground mb-4">
          체크박스 선택에 따라 파이프라인이 동적으로 변경됩니다
        </p>

        <div className="grid md:grid-cols-2 gap-4 mb-4">
          <div className="bg-white dark:bg-gray-900 p-4 rounded-lg border">
            <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
              ✅ OCR 실행
              <Badge variant="outline" className="text-xs">eDOCr v2</Badge>
            </h4>
            <p className="text-xs text-muted-foreground">
              ❌ 비활성화 시: OCR 단계 전체 건너뜀<br/>
              ✅ 활성화 시: eDOCr v2로 치수 텍스트 추출 (92% 정확도)
            </p>
          </div>

          <div className="bg-white dark:bg-gray-900 p-4 rounded-lg border">
            <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
              ✅ 세그멘테이션 실행
              <Badge variant="outline" className="text-xs">EDGNet</Badge>
            </h4>
            <p className="text-xs text-muted-foreground">
              ❌ 비활성화 시: 구조 분석 없이 YOLO + OCR만 수행<br/>
              ✅ 활성화 시: GraphSAGE 기반 레이어 분류 (90.82% 정확도)
            </p>
          </div>

          <div className="bg-white dark:bg-gray-900 p-4 rounded-lg border">
            <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
              ✅ 공차 분석 실행
              <Badge variant="outline" className="text-xs">Skin Model</Badge>
            </h4>
            <p className="text-xs text-muted-foreground">
              ❌ 비활성화 시: 치수 추출까지만 수행<br/>
              ✅ 활성화 시: 제조 가능성 및 공차 예측 추가
            </p>
          </div>

          <div className="bg-white dark:bg-gray-900 p-4 rounded-lg border">
            <h4 className="font-semibold text-sm mb-2 flex items-center gap-2">
              ✅ 시각화
              <Badge variant="outline" className="text-xs">이미지 생성</Badge>
            </h4>
            <p className="text-xs text-muted-foreground">
              ❌ 비활성화 시: JSON 데이터만 반환<br/>
              ✅ 활성화 시: 바운딩 박스 overlay 이미지 생성 (처리 시간 +0.5초)
            </p>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 p-4 rounded-lg border">
          <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
            🎯 고급 OCR 전략
            <Badge variant="success" className="text-xs">재현율 향상</Badge>
          </h4>

          <div className="space-y-3">
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-purple-500 text-white rounded-full flex items-center justify-center text-xs font-bold">1</div>
              <div className="flex-1">
                <p className="text-sm font-medium mb-1">🎯 YOLO Crop OCR</p>
                <p className="text-xs text-muted-foreground">
                  YOLO가 검출한 각 치수 영역을 개별 크롭하여 PaddleOCR로 텍스트 추출<br/>
                  <strong>효과:</strong> 재현율 76.7% → 93.3% (+16.7%p), 처리 시간 +2.1%
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">2</div>
              <div className="flex-1">
                <p className="text-sm font-medium mb-1">🚀 앙상블 전략 (YOLO Crop + eDOCr v2)</p>
                <p className="text-xs text-muted-foreground">
                  두 방식의 결과를 신뢰도 기반 가중치 융합 (중복 제거 + 누락 보완)<br/>
                  <strong>효과:</strong> 정밀도 60% → 93% (+33%p), 예상 F1 Score 95%+<br/>
                  <strong>조건:</strong> YOLO Crop OCR이 먼저 활성화되어야 함
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 🚀 파이프라인 모드 비교 */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950 p-6 rounded-lg border-2 border-blue-200 dark:border-blue-800">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          🚀 파이프라인 모드 비교
        </h3>
        <p className="text-sm text-muted-foreground mb-4">
          목적에 맞게 최적화된 두 가지 처리 전략을 선택할 수 있습니다
        </p>

        <div className="flex gap-3 mb-6">
          <button
            onClick={() => onSelectPipeline('hybrid')}
            className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all ${
              selectedPipeline === 'hybrid'
                ? 'border-blue-500 bg-blue-500 text-white shadow-lg'
                : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
            }`}
          >
            <div className="font-semibold mb-1">⚖️ 하이브리드 파이프라인</div>
            <div className="text-xs opacity-90">
              정확도 ~95% | 처리시간 40-50초
            </div>
          </button>
          <button
            onClick={() => onSelectPipeline('speed')}
            className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all ${
              selectedPipeline === 'speed'
                ? 'border-green-500 bg-green-500 text-white shadow-lg'
                : 'border-gray-300 dark:border-gray-600 hover:border-green-400'
            }`}
          >
            <div className="font-semibold mb-1">⚡ 속도 우선 파이프라인</div>
            <div className="text-xs opacity-90">
              정확도 ~93% | 처리시간 35-45초
            </div>
          </button>
        </div>

        <div className="bg-white dark:bg-gray-900 p-4 rounded-lg">
          <Mermaid
            chart={selectedPipeline === 'hybrid' ? hybridPipelineDiagram : speedPipelineDiagram}
          />
        </div>

        {selectedPipeline === 'hybrid' ? (
          <div className="mt-4 grid md:grid-cols-2 gap-3">
            <div className="bg-blue-50 dark:bg-blue-900/30 p-3 rounded-lg">
              <h5 className="font-semibold text-sm mb-2">✅ 장점</h5>
              <ul className="text-xs space-y-1 text-muted-foreground">
                <li>• YOLO로 정확한 위치 검출 (mAP50 80.4%)</li>
                <li>• Upscaling으로 작은 텍스트도 인식</li>
                <li>• eDOCr v2 정밀 OCR (92% 정확도)</li>
                <li>• EDGNet으로 구조적 검증</li>
                <li>• 앙상블로 최고 정확도 달성</li>
              </ul>
            </div>
            <div className="bg-orange-50 dark:bg-orange-900/30 p-3 rounded-lg">
              <h5 className="font-semibold text-sm mb-2">💡 추천 상황</h5>
              <ul className="text-xs space-y-1 text-muted-foreground">
                <li>• 고정밀도가 필요한 중요 도면</li>
                <li>• 복잡한 치수 정보가 많은 도면</li>
                <li>• 작은 폰트 크기의 치수 표기</li>
                <li>• 최종 견적서 생성 시</li>
              </ul>
            </div>
          </div>
        ) : (
          <div className="mt-4 grid md:grid-cols-2 gap-3">
            <div className="bg-green-50 dark:bg-green-900/30 p-3 rounded-lg">
              <h5 className="font-semibold text-sm mb-2">✅ 장점</h5>
              <ul className="text-xs space-y-1 text-muted-foreground">
                <li>• 3-way 병렬 처리로 최고 속도</li>
                <li>• Confidence 기반 스마트 병합</li>
                <li>• YOLO + eDOCr + EDGNet 동시 활용</li>
                <li>• 리소스 효율적</li>
                <li>• 실시간 피드백 가능</li>
              </ul>
            </div>
            <div className="bg-orange-50 dark:bg-orange-900/30 p-3 rounded-lg">
              <h5 className="font-semibold text-sm mb-2">💡 추천 상황</h5>
              <ul className="text-xs space-y-1 text-muted-foreground">
                <li>• 대량의 도면을 빠르게 처리</li>
                <li>• 실시간 프리뷰가 필요한 경우</li>
                <li>• 표준화된 도면 형식</li>
                <li>• 초기 검토 및 분석 단계</li>
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* 🎯 주요 기능 */}
      <div>
        <h3 className="text-lg font-semibold mb-3">🎯 주요 기능</h3>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-card p-4 rounded-lg border">
            <h4 className="font-semibold mb-2">🔗 API 오케스트레이션</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• 12개 API 통합 관리</li>
              <li>• 병렬 처리로 속도 최적화</li>
              <li>• 자동 에러 핸들링</li>
              <li>• 결과 데이터 검증</li>
            </ul>
          </div>

          <div className="bg-card p-4 rounded-lg border">
            <h4 className="font-semibold mb-2">📄 견적서 생성</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• 자동 비용 산정</li>
              <li>• PDF 견적서 생성</li>
              <li>• QC 체크리스트 포함</li>
              <li>• 가공 공정 명세</li>
            </ul>
          </div>

          <div className="bg-card p-4 rounded-lg border">
            <h4 className="font-semibold mb-2">⚡ 성능 최적화</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• 비동기 병렬 처리</li>
              <li>• 캐싱 메커니즘</li>
              <li>• 로드 밸런싱</li>
              <li>• 타임아웃 관리</li>
            </ul>
          </div>

          <div className="bg-card p-4 rounded-lg border">
            <h4 className="font-semibold mb-2">📊 모니터링</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• 실시간 헬스체크</li>
              <li>• 성능 메트릭 수집</li>
              <li>• 에러 로깅</li>
              <li>• API 상태 추적</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 📝 엔드포인트 */}
      <div>
        <h3 className="text-lg font-semibold mb-3">📝 주요 엔드포인트</h3>
        <div className="space-y-3">
          <div className="bg-muted p-3 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="default">POST</Badge>
              <code className="text-sm">/api/v1/process</code>
            </div>
            <p className="text-sm text-muted-foreground">
              전체 파이프라인 실행 (OCR + 세그멘테이션 + 공차 예측)
            </p>
          </div>

          <div className="bg-muted p-3 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="default">POST</Badge>
              <code className="text-sm">/api/v1/generate_quote</code>
            </div>
            <p className="text-sm text-muted-foreground">
              견적서 자동 생성 (분석 + 비용 산정 + PDF)
            </p>
          </div>

          <div className="bg-muted p-3 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="success">GET</Badge>
              <code className="text-sm">/api/v1/health</code>
            </div>
            <p className="text-sm text-muted-foreground">
              모든 서비스의 헬스 상태 확인
            </p>
          </div>

          <div className="bg-muted p-3 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="success">GET</Badge>
              <code className="text-sm">/api/v1/download_quote/{'{'} quote_number{'}'}</code>
            </div>
            <p className="text-sm text-muted-foreground">
              생성된 견적서 PDF 다운로드
            </p>
          </div>
        </div>
      </div>

      {/* 📝 사용 방법 */}
      <div>
        <h3 className="text-lg font-semibold mb-3">📝 사용 방법</h3>
        <div className="space-y-3">
          {[
            { step: 1, title: '도면 업로드', desc: '공학 도면 파일을 업로드 (이미지 또는 PDF)' },
            { step: 2, title: '처리 옵션 선택', desc: 'OCR, 세그멘테이션, 공차 예측 중 필요한 기능 선택' },
            { step: 3, title: '자동 처리', desc: 'Gateway가 모든 API를 병렬로 호출하여 결과 통합' },
            { step: 4, title: '결과 확인', desc: '통합된 분석 결과와 견적서 확인 및 다운로드' },
          ].map(({ step, title, desc }) => (
            <div key={step} className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold">
                {step}
              </div>
              <div>
                <h4 className="font-semibold">{title}</h4>
                <p className="text-sm text-muted-foreground">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ⚡ 성능 지표 */}
      <div>
        <h3 className="text-lg font-semibold mb-3">⚡ 성능 지표</h3>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-950 dark:to-cyan-950 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mb-1">
              ~40-50초
            </div>
            <div className="text-sm text-muted-foreground">
              전체 파이프라인 처리 시간<br/>
              (병렬 처리로 최적화)
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400 mb-1">
              99.9%
            </div>
            <div className="text-sm text-muted-foreground">
              시스템 가용성<br/>
              (헬스체크 기반)
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950 dark:to-pink-950 p-4 rounded-lg">
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400 mb-1">
              12개
            </div>
            <div className="text-sm text-muted-foreground">
              통합 API 서비스<br/>
              (핵심 6 + 확장 5 + 지식 1)
            </div>
          </div>
        </div>
      </div>

      {/* 💡 팁 */}
      <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg">
        <h4 className="font-semibold mb-2 text-blue-900 dark:text-blue-100">
          💡 최적의 결과를 위한 팁
        </h4>
        <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
          <li>• 모든 API가 healthy 상태인지 먼저 확인</li>
          <li>• 대용량 파일은 처리 시간이 더 소요될 수 있음</li>
          <li>• 에러 발생 시 개별 API 테스트로 원인 파악</li>
          <li>• 견적서는 quote_number로 나중에도 다운로드 가능</li>
        </ul>
      </div>
    </div>
  );
}
