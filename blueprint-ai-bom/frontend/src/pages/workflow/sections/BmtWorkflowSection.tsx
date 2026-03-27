/**
 * BMT Workflow Section — Human-in-the-Loop 도면 검증
 * Step 1: 크롭 뷰어 (Min-Content 뷰 분리 결과)
 * Step 2: TAG 확인/수정 (크롭별 OCR 결과 Review)
 * Step 3: BOM 매칭 판정 (불일치 확인)
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Loader2, CheckCircle2, XCircle, AlertTriangle, Trash2,
  ChevronLeft, ChevronRight, Tag, FileSpreadsheet, BarChart3, Layout
} from 'lucide-react';
import logger from '../../../lib/logger';
import { ZoomableImage } from '../../../components/ZoomableImage';

// === Types ===

interface BmtCrop {
  name: string;
  bbox: number[];
  tags: string[];
}

interface CropTag {
  id: string;
  tag: string;
  x: number;
  y: number;
  crop: string;
  pl_code: string;
  bom_status: string;
  review_status: string;
}

interface BmtDetail {
  tag: string;
  pl_code: string;
  status: string;
  review_status?: string;
  review_notes?: string;
}

interface BmtSummary {
  total_tags: number;
  matched: number;
  mismatched: number;
  unmapped: number;
  mismatch_tags: string[];
  unmapped_tags: string[];
}

interface OcrEngine {
  name: string;
  recall: number;
  detected: number;
  total: number;
}

interface BmtData {
  pipeline_version: string;
  tag_count: number;
  tags: string[];
  details: BmtDetail[];
  crops: BmtCrop[];
  summary: BmtSummary;
  ocr_benchmark?: { engines: OcrEngine[]; ensemble: { recall: number; detected: number; total: number; method: string } };
}

interface ReviewProgress {
  reviewed: number;
  total: number;
  percent: number;
}

interface Props {
  sessionId: string;
  apiBaseUrl: string;
}

// 크롭 이름 → OCR 오버레이 이미지 매핑
const CROP_IMAGE_MAP: Record<string, string> = {
  'BOTTOM VIEW': '/bom/bmt-visuals/e11-ocr-bottom_view.png',
  'FRONT VIEW': '/bom/bmt-visuals/e11-ocr-front_view.png',
  'TOP VIEW': '/bom/bmt-visuals/e11-ocr-top_view.png',
  'RIGHT VIEW': '/bom/bmt-visuals/e11-ocr-right_view.png',
  "'A'VIEW": '/bom/bmt-visuals/e11-ocr-aview.png',
  '3D+LOWER': '/bom/bmt-visuals/e11-ocr-3d_view.png',
  '3D LEFT': '/bom/bmt-visuals/e11-ocr-3d_left.png',
  '3D RIGHT': '/bom/bmt-visuals/e11-ocr-3d_right.png',
  'TABLES': '/bom/bmt-visuals/e11-ocr-tables.png',
};

// === Component ===

export function BmtWorkflowSection({ sessionId, apiBaseUrl }: Props) {
  const [data, setData] = useState<BmtData | null>(null);
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState(0); // 0=overview, 1=crops, 2=tag-review, 3=bom-review
  const [selectedCrop, setSelectedCrop] = useState(0);
  const [cropTags, setCropTags] = useState<CropTag[]>([]);
  const [cropLoading, setCropLoading] = useState(false);
  const [tagProgress, setTagProgress] = useState<ReviewProgress>({ reviewed: 0, total: 0, percent: 0 });
  const [bomProgress, setBomProgress] = useState<ReviewProgress>({ reviewed: 0, total: 0, percent: 0 });
  const [filter, setFilter] = useState<'all' | 'match' | 'mismatch' | 'unmapped'>('all');
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState<{ step: number; message: string } | null>(null);

  // Load BMT data
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiBaseUrl}/sessions/${sessionId}`);
      if (!res.ok) throw new Error(`${res.status}`);
      const session = await res.json();
      const bmt = session.metadata?.bmt_results;
      if (bmt) setData(bmt);

      // Progress
      const sumRes = await fetch(`${apiBaseUrl}/bmt/${sessionId}/summary`);
      if (sumRes.ok) {
        const sum = await sumRes.json();
        setTagProgress(sum.tag_review_progress);
        setBomProgress(sum.bom_review_progress);
      }
    } catch (err) {
      logger.error('BMT data load failed:', err);
    } finally {
      setLoading(false);
    }
  }, [sessionId, apiBaseUrl]);

  useEffect(() => { loadData(); }, [loadData]);

  // Run pipeline
  const runPipeline = useCallback(async () => {
    setPipelineRunning(true);
    setPipelineStatus({ step: 1, message: '뷰 라벨 검출 중...' });
    try {
      const res = await fetch(`${apiBaseUrl}/bmt/${sessionId}/run-pipeline`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
      if (!res.ok) throw new Error(`${res.status}`);
      // Poll status
      for (let i = 0; i < 60; i++) {
        await new Promise(r => setTimeout(r, 2000));
        const statusRes = await fetch(`${apiBaseUrl}/bmt/${sessionId}/pipeline-status`);
        if (statusRes.ok) {
          const status = await statusRes.json();
          setPipelineStatus({ step: status.step || 0, message: status.message || '' });
          if (status.status === 'completed') { await loadData(); setPipelineRunning(false); setPipelineStatus(null); return; }
          if (status.status === 'error') { setPipelineRunning(false); setPipelineStatus({ step: 0, message: `오류: ${status.message}` }); return; }
        }
      }
      setPipelineRunning(false);
      setPipelineStatus({ step: 0, message: '타임아웃' });
    } catch (err) {
      logger.error('Pipeline run failed:', err);
      setPipelineRunning(false);
      setPipelineStatus({ step: 0, message: '파이프라인 실행 실패' });
    }
  }, [sessionId, apiBaseUrl, loadData]);

  // Load crop tags
  const loadCropTags = useCallback(async (cropIdx: number) => {
    setCropLoading(true);
    try {
      const res = await fetch(`${apiBaseUrl}/bmt/${sessionId}/crops/${cropIdx}/tags`);
      if (res.ok) {
        const result = await res.json();
        setCropTags(result.tags || []);
      }
    } catch (err) {
      logger.error('Crop tags load failed:', err);
    } finally {
      setCropLoading(false);
    }
  }, [sessionId, apiBaseUrl]);

  useEffect(() => {
    if (step === 2 && data) loadCropTags(selectedCrop);
  }, [step, selectedCrop, data, loadCropTags]);

  // TAG review action
  const reviewTag = async (tagId: string, status: string) => {
    try {
      await fetch(`${apiBaseUrl}/bmt/${sessionId}/tags/${tagId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review_status: status }),
      });
      setCropTags(prev => prev.map(t => t.id === tagId ? { ...t, review_status: status } : t));
      setTagProgress(prev => ({ ...prev, reviewed: prev.reviewed + 1, percent: Math.round((prev.reviewed + 1) / prev.total * 100) }));
    } catch (err) {
      logger.error('Tag review failed:', err);
    }
  };

  // BOM review action
  const reviewBom = async (tag: string, status: string) => {
    try {
      await fetch(`${apiBaseUrl}/bmt/${sessionId}/bom-match/${tag}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review_status: status }),
      });
      setData(prev => prev ? {
        ...prev,
        details: prev.details.map(d => d.tag === tag ? { ...d, review_status: status } : d),
      } : prev);
      setBomProgress(prev => ({ ...prev, reviewed: prev.reviewed + 1, percent: Math.round((prev.reviewed + 1) / prev.total * 100) }));
    } catch (err) {
      logger.error('BOM review failed:', err);
    }
  };

  if (loading) return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border p-8 flex items-center gap-3 text-gray-500">
      <Loader2 className="w-5 h-5 animate-spin" /> BMT 데이터 로드 중...
    </div>
  );

  if (!data) return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
        <h2 className="text-lg font-bold text-white">BMT 도면-BOM 교차검증</h2>
        <p className="text-blue-100 text-sm">GAR 배치도 TAG 추출 + BOM 누락 확인</p>
      </div>
      <div className="p-8 text-center">
        {pipelineRunning ? (
          <div>
            <Loader2 className="w-10 h-10 mx-auto mb-3 text-blue-500 animate-spin" />
            <p className="font-bold text-gray-700 mb-2">파이프라인 실행 중... ({pipelineStatus?.step || 0}/6)</p>
            <p className="text-sm text-gray-500">{pipelineStatus?.message}</p>
            <div className="w-64 mx-auto mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${((pipelineStatus?.step || 0) / 6) * 100}%` }} />
            </div>
          </div>
        ) : (
          <div>
            <Tag className="w-10 h-10 mx-auto mb-3 text-gray-400" />
            <p className="text-gray-500 mb-4">아직 BMT 파이프라인 결과가 없습니다.</p>
            <button onClick={runPipeline} className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 inline-flex items-center gap-2">
              <BarChart3 className="w-5 h-5" /> 파이프라인 실행
            </button>
            {pipelineStatus?.message && (
              <p className="text-sm text-red-500 mt-3">{pipelineStatus.message}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );

  const tagCrops = data.crops.filter(c => c.tags.length > 0);

  const statusIcon = (s: string) => {
    if (s === 'match') return <CheckCircle2 className="w-4 h-4 text-green-600" />;
    if (s === 'mismatch') return <XCircle className="w-4 h-4 text-red-600" />;
    return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
  };

  const reviewBadge = (s: string) => {
    if (s === 'approved') return <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">승인</span>;
    if (s === 'confirmed') return <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">확인</span>;
    if (s === 'deleted') return <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded line-through">삭제</span>;
    if (s === 'false_positive') return <span className="text-xs bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded">정상</span>;
    return <span className="text-xs bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded">대기</span>;
  };

  const filteredDetails = data.details.filter(d => filter === 'all' ? true : d.status === filter);

  // Step navigation
  const steps = [
    { label: '개요', icon: BarChart3 },
    { label: '크롭 뷰', icon: Layout },
    { label: 'TAG 확인', icon: Tag },
    { label: 'BOM 매칭', icon: FileSpreadsheet },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border overflow-hidden">
      {/* 헤더 */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
        <h2 className="text-lg font-bold text-white">BMT 도면-BOM 교차검증</h2>
        <p className="text-blue-100 text-sm">{data.pipeline_version} · {data.tag_count}개 TAG · {data.summary.matched}건 매칭 · {data.summary.mismatched}건 불일치</p>
      </div>

      {/* 스텝 네비게이션 */}
      <div className="flex border-b border-gray-200 dark:border-gray-700">
        {steps.map((s, i) => (
          <button
            key={i}
            onClick={() => setStep(i)}
            className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors ${
              step === i ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50 dark:bg-blue-900/20' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <s.icon className="w-4 h-4" />
            {s.label}
            {i === 2 && tagProgress.total > 0 && (
              <span className="text-xs bg-blue-100 text-blue-600 px-1.5 rounded-full">{tagProgress.percent}%</span>
            )}
            {i === 3 && bomProgress.total > 0 && (
              <span className="text-xs bg-blue-100 text-blue-600 px-1.5 rounded-full">{bomProgress.percent}%</span>
            )}
          </button>
        ))}
      </div>

      {/* Step 0: 개요 */}
      {step === 0 && (
        <div className="p-6">
          {/* 요약 카드 */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold">{data.summary.total_tags}</div>
              <div className="text-sm text-gray-500">TAG 검출</div>
            </div>
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-green-600">{data.summary.matched}</div>
              <div className="text-sm text-green-600">✅ BOM 매칭</div>
            </div>
            <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-red-600">{data.summary.mismatched}</div>
              <div className="text-sm text-red-600">❌ 불일치</div>
            </div>
            <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-yellow-600">{data.summary.unmapped}</div>
              <div className="text-sm text-yellow-600">❓ 미매핑</div>
            </div>
          </div>

          {/* 시각화 이미지 */}
          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className="border rounded-lg overflow-hidden">
              <div className="bg-gray-100 dark:bg-gray-700 px-3 py-1.5 text-xs font-bold">Min-Content 뷰 분리</div>
              <ZoomableImage src="/bom/bmt-visuals/e11-mincontent-final.png" alt="뷰 분리" initialZoom={100} compact />
            </div>
            <div className="border rounded-lg overflow-hidden">
              <div className="bg-gray-100 dark:bg-gray-700 px-3 py-1.5 text-xs font-bold">TAG 검출 (24/24)</div>
              <ZoomableImage src="/bom/bmt-visuals/e11-100percent-overlay.png" alt="TAG 오버레이" initialZoom={100} compact />
            </div>
          </div>

          {/* OCR 벤치마크 */}
          {data.ocr_benchmark && (
            <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-4">
              <h3 className="font-bold text-sm mb-3">📊 OCR 벤치마크 ({data.ocr_benchmark.engines.length}개 엔진)</h3>
              {data.ocr_benchmark.engines.map((eng, i) => (
                <div key={i} className="flex items-center gap-2 mb-1">
                  <span className="w-20 text-xs text-right text-gray-500">{eng.name}</span>
                  <div className="flex-1 h-4 bg-gray-200 dark:bg-gray-600 rounded overflow-hidden">
                    <div className={`h-full rounded ${eng.recall > 50 ? 'bg-green-500' : eng.recall > 0 ? 'bg-blue-500' : 'bg-red-300'}`} style={{ width: `${Math.max(eng.recall, 1)}%` }} />
                  </div>
                  <span className="w-14 text-xs font-bold text-right">{eng.recall}%</span>
                </div>
              ))}
              <div className="flex items-center gap-2 mt-2 pt-2 border-t">
                <span className="w-20 text-xs font-bold text-right">앙상블</span>
                <div className="flex-1 h-4 bg-gray-200 rounded overflow-hidden">
                  <div className="h-full rounded bg-gradient-to-r from-green-500 to-blue-500" style={{ width: '100%' }} />
                </div>
                <span className="w-14 text-xs font-bold text-green-600 text-right">100%</span>
              </div>
            </div>
          )}

          <button onClick={() => setStep(1)} className="mt-4 w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700">
            크롭 확인 시작 →
          </button>
        </div>
      )}

      {/* Step 1: 크롭 뷰 */}
      {step === 1 && (
        <div className="p-6">
          <h3 className="font-bold mb-4">📐 Min-Content 뷰 분리 — {data.crops.length}개 크롭</h3>
          <div className="grid grid-cols-3 gap-3">
            {data.crops.map((crop, i) => (
              <button
                key={i}
                onClick={() => { setSelectedCrop(i); setStep(2); }}
                className={`border-2 rounded-lg p-3 text-left transition-all hover:shadow-md ${
                  crop.tags.length > 0 ? 'border-green-300 bg-green-50 hover:border-green-500' : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="font-bold text-sm">{crop.name}</div>
                <div className="text-xs text-gray-500 mt-1">({crop.bbox[0]},{crop.bbox[1]}) → ({crop.bbox[2]},{crop.bbox[3]})</div>
                {crop.tags.length > 0 ? (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {crop.tags.map(tag => (
                      <span key={tag} className="bg-green-100 text-green-700 text-xs px-1.5 py-0.5 rounded font-mono">{tag}</span>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-gray-400 mt-2">TAG 없음</div>
                )}
              </button>
            ))}
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={() => setStep(0)} className="px-4 py-2 border rounded-lg text-sm">← 개요</button>
            <button onClick={() => { setSelectedCrop(tagCrops.length > 0 ? data.crops.indexOf(tagCrops[0]) : 0); setStep(2); }} className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium">TAG 확인 시작 →</button>
          </div>
        </div>
      )}

      {/* Step 2: TAG 확인 */}
      {step === 2 && (
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold">🏷️ TAG 확인 — {data.crops[selectedCrop]?.name}</h3>
            <div className="flex items-center gap-2">
              <button
                onClick={() => { const prev = selectedCrop > 0 ? selectedCrop - 1 : data.crops.length - 1; setSelectedCrop(prev); }}
                className="p-1.5 border rounded hover:bg-gray-100"
              ><ChevronLeft className="w-4 h-4" /></button>
              <span className="text-sm text-gray-500">{selectedCrop + 1} / {data.crops.length}</span>
              <button
                onClick={() => { const next = (selectedCrop + 1) % data.crops.length; setSelectedCrop(next); }}
                className="p-1.5 border rounded hover:bg-gray-100"
              ><ChevronRight className="w-4 h-4" /></button>
            </div>
          </div>

          {/* 크롭 선택 탭 */}
          <div className="flex gap-1 mb-4 overflow-x-auto">
            {data.crops.map((c, i) => (
              <button
                key={i}
                onClick={() => setSelectedCrop(i)}
                className={`px-2 py-1 text-xs rounded whitespace-nowrap ${
                  i === selectedCrop ? 'bg-blue-600 text-white' : c.tags.length > 0 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'
                }`}
              >
                {c.name} {c.tags.length > 0 && `(${c.tags.length})`}
              </button>
            ))}
          </div>

          {/* 크롭 이미지 */}
          {(() => {
            const cropName = data.crops[selectedCrop]?.name || '';
            const imgUrl = CROP_IMAGE_MAP[cropName];
            return imgUrl ? (
              <div className="mb-4">
                <ZoomableImage src={imgUrl} alt={`${cropName} OCR 결과`} initialZoom={100} maxZoom={300} compact />
              </div>
            ) : null;
          })()}

          {/* TAG 목록 */}
          {cropLoading ? (
            <div className="flex items-center gap-2 text-gray-500 py-8 justify-center">
              <Loader2 className="w-4 h-4 animate-spin" /> TAG 로드 중...
            </div>
          ) : cropTags.length === 0 ? (
            <div className="text-center py-8 text-gray-400">이 크롭에 검출된 TAG가 없습니다.</div>
          ) : (
            <div className="space-y-2">
              {cropTags.map((t) => (
                <div key={t.id} className={`flex items-center gap-3 p-3 rounded-lg border ${
                  t.review_status === 'approved' ? 'bg-green-50 border-green-200' :
                  t.review_status === 'deleted' ? 'bg-red-50 border-red-200 opacity-50' :
                  'bg-white border-gray-200'
                }`}>
                  {statusIcon(t.bom_status)}
                  <span className="font-mono font-bold text-sm w-16">{t.tag}</span>
                  <span className="text-xs text-gray-500 flex-1 font-mono">{t.pl_code || '—'}</span>
                  {reviewBadge(t.review_status)}
                  <div className="flex gap-1">
                    <button onClick={() => reviewTag(t.id, 'approved')} className="p-1 text-green-600 hover:bg-green-100 rounded" title="승인">
                      <CheckCircle2 className="w-4 h-4" />
                    </button>
                    <button onClick={() => reviewTag(t.id, 'deleted')} className="p-1 text-red-600 hover:bg-red-100 rounded" title="삭제">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="flex gap-2 mt-4">
            <button onClick={() => setStep(1)} className="px-4 py-2 border rounded-lg text-sm">← 크롭</button>
            <button onClick={() => setStep(3)} className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium">BOM 매칭 확인 →</button>
          </div>
        </div>
      )}

      {/* Step 3: BOM 매칭 */}
      {step === 3 && (
        <div className="p-6">
          <h3 className="font-bold mb-4">📊 BOM 매칭 결과</h3>

          {/* 불일치 하이라이트 */}
          {data.summary.mismatched > 0 && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <h4 className="font-bold text-red-700 mb-2">❌ 불일치 {data.summary.mismatched}건 — 확인 필요</h4>
              {data.details.filter(d => d.status === 'mismatch').map(d => (
                <div key={d.tag} className="flex items-center gap-3 text-sm mb-2">
                  <span className="font-mono font-bold text-red-700 w-12">{d.tag}</span>
                  <span className="text-gray-600 flex-1">
                    <code className="bg-red-100 px-1 rounded">{d.pl_code || '(없음)'}</code>
                    <span className="mx-2">→ ERP에서 미발견</span>
                  </span>
                  {reviewBadge(d.review_status || 'pending')}
                  <div className="flex gap-1">
                    <button onClick={() => reviewBom(d.tag, 'confirmed')} className="text-xs px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700">실제 오류</button>
                    <button onClick={() => reviewBom(d.tag, 'false_positive')} className="text-xs px-2 py-1 bg-gray-200 rounded hover:bg-gray-300">정상 차이</button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 필터 */}
          <div className="flex gap-2 mb-3">
            {(['all', 'match', 'mismatch', 'unmapped'] as const).map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium ${filter === f ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                {f === 'all' ? `전체 (${data.details.length})` : f === 'match' ? `매칭 (${data.summary.matched})` : f === 'mismatch' ? `불일치 (${data.summary.mismatched})` : `미매핑 (${data.summary.unmapped})`}
              </button>
            ))}
          </div>

          {/* 테이블 */}
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b-2">
                <th className="text-left py-2 px-3 w-12">상태</th>
                <th className="text-left py-2 px-3 w-16">TAG</th>
                <th className="text-left py-2 px-3">Part List 품목코드</th>
                <th className="text-left py-2 px-3 w-16">결과</th>
                <th className="text-left py-2 px-3 w-16">판정</th>
              </tr>
            </thead>
            <tbody>
              {filteredDetails.map((d, i) => (
                <tr key={i} className={`border-b ${d.status === 'match' ? 'bg-green-50' : d.status === 'mismatch' ? 'bg-red-50' : 'bg-yellow-50'}`}>
                  <td className="py-2 px-3">{statusIcon(d.status)}</td>
                  <td className="py-2 px-3 font-mono font-bold">{d.tag}</td>
                  <td className="py-2 px-3 font-mono text-xs text-gray-600">{d.pl_code || '—'}</td>
                  <td className="py-2 px-3"><span className={`text-xs px-1.5 py-0.5 rounded-full ${d.status === 'match' ? 'bg-green-100 text-green-700' : d.status === 'mismatch' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>{d.status === 'match' ? '매칭' : d.status === 'mismatch' ? '불일치' : '미매핑'}</span></td>
                  <td className="py-2 px-3">{reviewBadge(d.review_status || 'pending')}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="flex gap-2 mt-4">
            <button onClick={() => setStep(2)} className="px-4 py-2 border rounded-lg text-sm">← TAG 확인</button>
            <a href={`${apiBaseUrl}/bmt/${sessionId}/report`} download className="flex-1 py-2 bg-green-600 text-white rounded-lg text-sm font-medium text-center hover:bg-green-700 flex items-center justify-center gap-2">
              <FileSpreadsheet className="w-4 h-4" /> Excel 리포트 다운로드
            </a>
          </div>
        </div>
      )}

      {/* 하단 */}
      <div className="px-6 py-3 border-t text-xs text-gray-400 flex items-center justify-between">
        <span>{data.pipeline_version} · Min-Content · 하드코딩 0</span>
        <span>TAG 확인: {tagProgress.percent}% | BOM 판정: {bomProgress.percent}%</span>
      </div>
    </div>
  );
}
