import { useEffect, useState } from 'react';
import { Card, CardContent } from './Card';
import { CheckCircle, Circle, Loader2, AlertCircle, Clock } from 'lucide-react';

interface ProgressUpdate {
  timestamp: string;
  step: string;
  status: 'started' | 'running' | 'completed' | 'error';
  message: string;
  data?: Record<string, any>;
}

interface PipelineProgressProps {
  jobId: string;
  pipelineMode?: 'hybrid' | 'speed';
  onComplete?: (data: any) => void;
  onError?: (error: string) => void;
}

// 메인 단계만 표시
const mainSteps: Array<{ id: string; label: string; subSteps: string[]; parallel?: boolean }> = [
  { id: 'initialize', label: '📋 초기화', subSteps: [] },
  { id: 'yolo', label: '🎯 YOLO 검출', subSteps: [] },
  { id: 'ocr', label: '📝 OCR 분석', subSteps: [], parallel: true },
  { id: 'edgnet', label: '🎨 EDGNet 분석', subSteps: [], parallel: true },
  { id: 'ensemble', label: '🔀 결과 병합', subSteps: [] },
  { id: 'tolerance', label: '📐 공차 예측', subSteps: [] },
  { id: 'complete', label: '✅ 완료', subSteps: [] }
];

export default function PipelineProgress({ jobId, pipelineMode, onComplete, onError }: PipelineProgressProps) {
  const [updates, setUpdates] = useState<ProgressUpdate[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [startTime] = useState(Date.now());
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!jobId) return;

    let eventSource: EventSource | null = null;
    let intervalId: number;

    const connectSSE = () => {
      const url = `http://localhost:8000/api/v1/progress/${jobId}`;
      eventSource = new EventSource(url);

      eventSource.onopen = () => {
        setIsConnected(true);
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.status === 'done') {
            eventSource?.close();
            if (onComplete) {
              const lastUpdate = updates[updates.length - 1];
              onComplete(lastUpdate?.data || {});
            }
            return;
          }

          if (data.status === 'timeout') {
            eventSource?.close();
            if (onError) {
              onError('진행 상황 추적 시간 초과');
            }
            return;
          }

          setUpdates((prev) => [...prev, data]);
        } catch (error) {
          console.error('[SSE] Parse error:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('[SSE] Connection error:', error);
        setIsConnected(false);
        eventSource?.close();
        if (onError) {
          onError('진행 상황 연결 오류');
        }
      };
    };

    connectSSE();

    intervalId = setInterval(() => {
      setElapsed(Date.now() - startTime);
    }, 100);

    return () => {
      eventSource?.close();
      clearInterval(intervalId);
    };
  }, [jobId, onComplete, onError, startTime]);

  // 메인 단계의 상태 계산
  const getMainStepStatus = (step: typeof mainSteps[0]): 'pending' | 'running' | 'completed' | 'error' => {
    const allSteps = [step.id, ...step.subSteps];

    // 에러가 있는지 확인
    const hasError = updates.some(u => allSteps.includes(u.step) && u.status === 'error');
    if (hasError) return 'error';

    // 모든 하위 단계가 완료되었는지 확인
    const allCompleted = allSteps.every(s => {
      const update = updates.find(u => u.step === s);
      return update && update.status === 'completed';
    });
    if (allCompleted) return 'completed';

    // 하나라도 실행 중인지 확인
    const anyRunning = allSteps.some(s => {
      const update = updates.find(u => u.step === s);
      return update && (update.status === 'running' || update.status === 'started');
    });
    if (anyRunning) return 'running';

    // 하나라도 시작되었는지 확인
    const anyStarted = allSteps.some(s => updates.some(u => u.step === s));
    if (anyStarted) return 'running';

    return 'pending';
  };

  // 메인 단계의 상세 정보 가져오기
  const getMainStepDetails = (step: typeof mainSteps[0]) => {
    const allSteps = [step.id, ...step.subSteps];
    const relevantUpdates = updates.filter(u => allSteps.includes(u.step));

    if (relevantUpdates.length === 0) return null;

    // 가장 최근 업데이트
    const latestUpdate = relevantUpdates[relevantUpdates.length - 1];

    return {
      message: latestUpdate.message,
      data: latestUpdate.data
    };
  };

  const getStepIcon = (status: 'pending' | 'running' | 'completed' | 'error') => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'running':
        return <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />;
      case 'error':
        return <AlertCircle className="w-6 h-6 text-red-500" />;
      default:
        return <Circle className="w-6 h-6 text-gray-300" />;
    }
  };

  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const deciseconds = Math.floor((ms % 1000) / 100);
    return `${seconds}.${deciseconds}s`;
  };

  // Use prop first, fallback to SSE data if not provided
  const displayMode = pipelineMode || updates.find((u) => u.step === 'initialize')?.data?.pipeline_mode;
  const isPipelineComplete = updates.some((u) => u.step === 'complete' && u.status === 'completed');

  // 현재 진행 중인 단계 찾기 (완료되지 않았을 때만)
  const currentStepIndex = !isPipelineComplete ? mainSteps.findIndex(step => getMainStepStatus(step) === 'running') : -1;
  const currentStep = currentStepIndex >= 0 ? mainSteps[currentStepIndex] : null;

  return (
    <Card className="mt-4">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold">파이프라인 진행 상황</h3>
            <p className="text-sm text-muted-foreground">
              {displayMode === 'hybrid' ? '🔵 하이브리드 모드' : '🟢 속도 우선 모드'}
              {' · '}
              <Clock className="inline w-4 h-4" /> {formatTime(elapsed)}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isConnected && !isPipelineComplete && (
              <div className="flex items-center gap-2 text-sm text-blue-600">
                <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
                실시간 업데이트 중
              </div>
            )}
            {isPipelineComplete && (
              <div className="flex items-center gap-2 text-sm text-green-600">
                <CheckCircle className="w-4 h-4" />
                완료
              </div>
            )}
          </div>
        </div>

        {/* 현재 진행 단계 하이라이트 */}
        {currentStep && (
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-950 border-2 border-blue-300 dark:border-blue-700 rounded-lg">
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
              <div>
                <p className="font-semibold text-blue-900 dark:text-blue-100">
                  현재 진행 중: {currentStep.label}
                </p>
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  {getMainStepDetails(currentStep)?.message}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 단계별 프로그레스 바 */}
        <div className="mb-6">
          <div className="flex items-start justify-between">
            {mainSteps.map((step, index) => {
              const status = getMainStepStatus(step);
              const isActive = status === 'running';
              const isComplete = status === 'completed';
              const isParallel = step.parallel;
              // const prevStep = index > 0 ? mainSteps[index - 1] : null;
              const nextStep = index < mainSteps.length - 1 ? mainSteps[index + 1] : null;

              return (
                <div key={step.id} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-1">
                    {/* 아이콘 */}
                    <div className={`
                      w-10 h-10 rounded-full flex items-center justify-center
                      ${isComplete ? 'bg-green-100 dark:bg-green-900' : ''}
                      ${isActive ? 'bg-blue-100 dark:bg-blue-900' : ''}
                      ${status === 'pending' ? 'bg-gray-100 dark:bg-gray-800' : ''}
                      ${isParallel ? 'ring-2 ring-blue-300 ring-offset-2' : ''}
                    `}>
                      {getStepIcon(status)}
                    </div>

                    {/* 라벨 */}
                    <p className={`
                      text-xs mt-2 text-center
                      ${isActive ? 'font-bold text-blue-600' : ''}
                      ${isComplete ? 'text-green-600' : ''}
                      ${status === 'pending' ? 'text-gray-400' : ''}
                    `}>
                      {step.label.replace(/^[^\s]+\s/, '')}
                    </p>

                    {/* 병렬 표시 */}
                    {isParallel && (
                      <p className="text-[10px] text-blue-500 mt-0.5">동시 실행</p>
                    )}
                  </div>

                  {/* 연결선 */}
                  {index < mainSteps.length - 1 && !nextStep?.parallel && (
                    <div className={`
                      h-1 w-full mx-2
                      ${isComplete ? 'bg-green-300' : 'bg-gray-200'}
                    `} />
                  )}

                  {/* 병렬 단계 사이는 연결선 없음 */}
                  {nextStep?.parallel && (
                    <div className="w-4" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* 상세 정보 */}
        <div className="space-y-2">
          {mainSteps.map((step) => {
            const status = getMainStepStatus(step);
            const details = getMainStepDetails(step);

            if (status === 'pending') return null;

            return (
              <div
                key={step.id}
                className={`
                  flex items-start gap-3 p-3 rounded-lg transition-all
                  ${status === 'running' ? 'bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800' : ''}
                  ${status === 'completed' ? 'bg-gray-50 dark:bg-gray-900' : ''}
                  ${status === 'error' ? 'bg-red-50 dark:bg-red-950' : ''}
                `}
              >
                <div className="flex-shrink-0 mt-0.5">
                  {getStepIcon(status)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-sm">
                      {step.label}
                    </p>
                    {details?.data?.processing_time && (
                      <span className="text-xs text-muted-foreground">
                        {details.data.processing_time.toFixed(2)}s
                      </span>
                    )}
                  </div>
                  {details && (
                    <p className="text-sm text-muted-foreground mt-1">
                      {details.message}
                    </p>
                  )}
                  {details?.data && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {details.data.detection_count !== undefined && (
                        <span className="text-xs bg-white dark:bg-gray-800 px-2 py-1 rounded">
                          검출: {details.data.detection_count}
                        </span>
                      )}
                      {details.data.dimensions_count !== undefined && (
                        <span className="text-xs bg-white dark:bg-gray-800 px-2 py-1 rounded">
                          치수: {details.data.dimensions_count}
                        </span>
                      )}
                      {details.data.components_count !== undefined && (
                        <span className="text-xs bg-white dark:bg-gray-800 px-2 py-1 rounded">
                          컴포넌트: {details.data.components_count}
                        </span>
                      )}
                      {details.data.dimension_count !== undefined && (
                        <span className="text-xs bg-white dark:bg-gray-800 px-2 py-1 rounded">
                          업스케일: {details.data.dimension_count}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* 완료 요약 */}
        {isPipelineComplete && (
          <div className="mt-6 p-4 bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-950 dark:to-blue-950 rounded-lg border border-green-200 dark:border-green-800">
            <h4 className="font-semibold text-sm mb-2 text-green-900 dark:text-green-100">
              ✅ 파이프라인 완료
            </h4>
            <p className="text-sm text-green-800 dark:text-green-200">
              총 처리 시간: {formatTime(elapsed)}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
