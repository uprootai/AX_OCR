/**
 * BOMWorkflowSection - 5단계 BOM 워크플로우 위저드
 * BOM 업로드 → 계층 트리 → 도면 매칭 → 세션 생성 → 견적 현황
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Upload,
  GitBranch,
  Link2,
  PlusCircle,
  BarChart3,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import {
  projectApi,
  type ProjectDetail,
  type BOMHierarchyResponse,
  type DrawingMatchResult,
  type SessionBatchCreateResponse,
} from '../../../lib/api';
import { BOMHierarchyTree } from './BOMHierarchyTree';
import { DrawingMatchTable } from './DrawingMatchTable';
import { QuotationDashboard } from './QuotationDashboard';

interface BOMWorkflowSectionProps {
  projectId: string;
  project: ProjectDetail;
  onRefresh: () => void;
}

const STEPS = [
  { label: 'BOM 업로드', icon: Upload },
  { label: 'BOM 계층', icon: GitBranch },
  { label: '도면 매칭', icon: Link2 },
  { label: '세션 생성', icon: PlusCircle },
  { label: '견적 현황', icon: BarChart3 },
];

function detectInitialStep(project: ProjectDetail): number {
  // 세션이 이미 연결된 BOM 항목이 있으면 → Step 4
  const hasSessions = (project.sessions ?? []).length > 0 && project.bom_item_count > 0;
  if (hasSessions) return 4;

  // bom_source가 있으면 BOM이 이미 업로드됨
  if (project.bom_source) return 1;

  return 0;
}

export function BOMWorkflowSection({
  projectId,
  project,
  onRefresh,
}: BOMWorkflowSectionProps) {
  const [currentStep, setCurrentStep] = useState(() => detectInitialStep(project));
  const [bomData, setBomData] = useState<BOMHierarchyResponse | null>(null);
  const [_matchResult, setMatchResult] = useState<DrawingMatchResult | null>(null);
  const [sessionResult, setSessionResult] = useState<SessionBatchCreateResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bomFileRef = useRef<HTMLInputElement>(null);

  // Step 3 state
  const [templateName, setTemplateName] = useState('');
  const [onlyMatched, setOnlyMatched] = useState(true);

  // BOM 계층 데이터 로드
  const loadBOMData = useCallback(async () => {
    if (!project.bom_source) return;
    setIsLoading(true);
    try {
      const data = await projectApi.getBOMHierarchy(projectId);
      setBomData(data);
    } catch {
      // BOM 데이터가 없을 수 있음 - 무시
    } finally {
      setIsLoading(false);
    }
  }, [projectId, project.bom_source]);

  useEffect(() => {
    if (project.bom_source) {
      loadBOMData();
    }
  }, [loadBOMData, project.bom_source]);

  // BOM PDF 업로드
  const handleBOMUpload = async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await projectApi.importBOM(projectId, file);
      setBomData(data);
      onRefresh();
      setCurrentStep(1);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'BOM 파일 업로드에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 도면 매칭 완료 핸들러
  const handleMatchComplete = (result: DrawingMatchResult) => {
    setMatchResult(result);
  };

  // 세션 일괄 생성
  const handleCreateSessions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await projectApi.createSessions(
        projectId,
        templateName || undefined,
        onlyMatched
      );
      setSessionResult(data);
      onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : '세션 생성에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 다음/이전 단계 조건
  const canGoNext = (): boolean => {
    switch (currentStep) {
      case 0: return !!bomData;
      case 1: return !!bomData;
      case 2: return true; // 매칭은 선택사항
      case 3: return true;
      default: return false;
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border dark:border-gray-700 mb-6">
      {/* 스테퍼 */}
      <div className="p-4 border-b dark:border-gray-700">
        <div className="flex items-center justify-between">
          {STEPS.map((step, idx) => {
            const Icon = step.icon;
            const isCompleted = idx < currentStep;
            const isActive = idx === currentStep;
            return (
              <div key={idx} className="flex items-center">
                <button
                  onClick={() => {
                    // 완료된 단계 또는 현재 단계만 클릭 가능
                    if (idx <= currentStep || (bomData && idx <= 4)) {
                      setCurrentStep(idx);
                    }
                  }}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-500 text-white'
                      : isCompleted
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-sm font-medium hidden sm:inline">{step.label}</span>
                </button>
                {idx < STEPS.length - 1 && (
                  <div
                    className={`w-8 h-0.5 mx-1 ${
                      idx < currentStep ? 'bg-green-400' : 'bg-gray-200 dark:bg-gray-600'
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="mx-4 mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* 단계별 콘텐츠 */}
      <div className="p-4">
        {/* Step 0: BOM 업로드 */}
        {currentStep === 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">BOM PDF 업로드</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              BOM(Bill of Materials) PDF 파일을 업로드하면 계층 구조를 자동으로 파싱합니다.
            </p>
            <div className="flex items-center gap-3">
              <input
                ref={bomFileRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleBOMUpload(file);
                }}
              />
              <button
                onClick={() => bomFileRef.current?.click()}
                disabled={isLoading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4" />
                )}
                BOM PDF 선택
              </button>
            </div>
            {bomData && (
              <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-sm text-green-700 dark:text-green-400 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                파싱 완료: 전체 {bomData.total_items}개 (ASSY {bomData.assembly_count}, SUB{' '}
                {bomData.subassembly_count}, PART {bomData.part_count})
              </div>
            )}
          </div>
        )}

        {/* Step 1: BOM 계층 트리 */}
        {currentStep === 1 && bomData && (
          <BOMHierarchyTree bomData={bomData} />
        )}
        {currentStep === 1 && !bomData && (
          <div className="text-center py-8 text-gray-400 dark:text-gray-500">
            {isLoading ? (
              <Loader2 className="w-8 h-8 mx-auto animate-spin" />
            ) : (
              <p>BOM 데이터를 로드할 수 없습니다. Step 0에서 BOM을 업로드하세요.</p>
            )}
          </div>
        )}

        {/* Step 2: 도면 매칭 */}
        {currentStep === 2 && bomData && (
          <DrawingMatchTable
            projectId={projectId}
            bomItems={bomData.items}
            drawingFolder={project.drawing_folder}
            onMatchComplete={handleMatchComplete}
          />
        )}
        {currentStep === 2 && !bomData && (
          <div className="text-center py-8 text-gray-400 dark:text-gray-500">
            BOM 데이터가 필요합니다.
          </div>
        )}

        {/* Step 3: 세션 일괄 생성 */}
        {currentStep === 3 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">세션 일괄 생성</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              BOM의 견적 대상 항목에 대해 BlueprintFlow 세션을 일괄 생성합니다.
            </p>

            <div className="space-y-4 max-w-md">
              <div>
                <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">
                  템플릿 이름 (선택)
                </label>
                <input
                  type="text"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  placeholder="예: bearing-analysis"
                  className="w-full px-3 py-2 border dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-300"
                />
              </div>

              <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={onlyMatched}
                  onChange={(e) => setOnlyMatched(e.target.checked)}
                  className="rounded"
                />
                매칭된 도면만 세션 생성
              </label>

              <button
                onClick={handleCreateSessions}
                disabled={isLoading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <PlusCircle className="w-4 h-4" />
                )}
                세션 생성
              </button>
            </div>

            {sessionResult && (
              <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border dark:border-gray-600">
                <h4 className="font-medium text-gray-900 dark:text-white mb-2">생성 결과</h4>
                <div className="flex items-center gap-4 text-sm">
                  <span className="flex items-center gap-1 text-green-600 dark:text-green-400">
                    <CheckCircle className="w-4 h-4" />
                    생성: {sessionResult.created_count}개
                  </span>
                  <span className="text-gray-500 dark:text-gray-400">
                    건너뜀: {sessionResult.skipped_count}개
                  </span>
                  {sessionResult.failed_count > 0 && (
                    <span className="text-red-600 dark:text-red-400">
                      실패: {sessionResult.failed_count}개
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">{sessionResult.message}</p>
              </div>
            )}
          </div>
        )}

        {/* Step 4: 견적 현황 */}
        {currentStep === 4 && bomData && (
          <QuotationDashboard
            projectId={projectId}
            project={project}
            bomItems={bomData.items}
          />
        )}
        {currentStep === 4 && !bomData && (
          <div className="text-center py-8 text-gray-400 dark:text-gray-500">
            {isLoading ? (
              <Loader2 className="w-8 h-8 mx-auto animate-spin" />
            ) : (
              <p>BOM 데이터가 필요합니다.</p>
            )}
          </div>
        )}
      </div>

      {/* 네비게이션 */}
      <div className="p-4 border-t dark:border-gray-700 flex items-center justify-between">
        <button
          onClick={() => setCurrentStep((s) => Math.max(0, s - 1))}
          disabled={currentStep === 0}
          className="flex items-center gap-1 px-4 py-2 border dark:border-gray-600 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-30"
        >
          <ChevronLeft className="w-4 h-4" />
          이전
        </button>
        <span className="text-sm text-gray-400 dark:text-gray-500">
          {currentStep + 1} / {STEPS.length}
        </span>
        <button
          onClick={() => setCurrentStep((s) => Math.min(STEPS.length - 1, s + 1))}
          disabled={currentStep === STEPS.length - 1 || !canGoNext()}
          className="flex items-center gap-1 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors disabled:opacity-30"
        >
          다음
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
