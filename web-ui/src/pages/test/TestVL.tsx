import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { FileUploadSection } from '../../components/upload/FileUploadSection';
import JSONViewer from '../../components/debug/JSONViewer';
import RequestInspector from '../../components/debug/RequestInspector';
import RequestTimeline from '../../components/debug/RequestTimeline';
import ErrorPanel from '../../components/debug/ErrorPanel';
import { vlApi } from '../../lib/api';
import { useMonitoringStore } from '../../store/monitoringStore';
import { Loader2, Play, Brain, ListChecks, Info } from 'lucide-react';
import type { RequestTrace } from '../../types/api';

type VLFunction = 'extractInfoBlock' | 'extractDimensions' | 'inferManufacturingProcess' | 'generateQCChecklist';

export default function TestVL() {
  const [file, setFile] = useState<File | null>(null);
  const [selectedFunction, setSelectedFunction] = useState<VLFunction>('extractInfoBlock');
  const [model, setModel] = useState('claude-3-5-sonnet-20241022');
  const [queryFields, setQueryFields] = useState(['name', 'part number', 'material', 'scale', 'weight']);
  const [result, setResult] = useState<any>(null);
  const [selectedTrace, setSelectedTrace] = useState<RequestTrace | null>(null);

  const { traces, addTrace } = useMonitoringStore();
  const vlTraces = traces.filter((t) => t.endpoint.includes('vl') || t.endpoint.includes('/extract') || t.endpoint.includes('/infer') || t.endpoint.includes('/generate'));

  const mutation = useMutation({
    mutationFn: async (params: { file: File; func: VLFunction }) => {
      const startTime = Date.now();
      const traceId = `vl-${Date.now()}`;

      try {
        let response;
        let endpoint = '';

        switch (params.func) {
          case 'extractInfoBlock':
            endpoint = '/api/v1/extract_info_block';
            response = await vlApi.extractInfoBlock(params.file, { query_fields: queryFields, model });
            break;
          case 'extractDimensions':
            endpoint = '/api/v1/extract_dimensions';
            response = await vlApi.extractDimensions(params.file, model);
            break;
          case 'inferManufacturingProcess':
            endpoint = '/api/v1/infer_manufacturing_process';
            response = await vlApi.inferManufacturingProcess(params.file, model);
            break;
          case 'generateQCChecklist':
            endpoint = '/api/v1/generate_qc_checklist';
            response = await vlApi.generateQCChecklist(params.file, model);
            break;
        }

        const duration = Date.now() - startTime;

        const trace: RequestTrace = {
          id: traceId,
          timestamp: new Date(),
          endpoint,
          method: 'POST',
          status: 200,
          duration,
          request: { file: params.file.name, func: params.func, model },
          response,
        };

        addTrace(trace);
        setSelectedTrace(trace);
        return response;
      } catch (error: any) {
        const duration = Date.now() - startTime;

        const trace: RequestTrace = {
          id: traceId,
          timestamp: new Date(),
          endpoint: `/api/v1/${params.func}`,
          method: 'POST',
          status: error.response?.status || 0,
          duration,
          request: { file: params.file.name, func: params.func },
          response: error.response?.data || null,
          error: {
            status: error.response?.status || 0,
            code: error.response?.status?.toString() || 'NETWORK_ERROR',
            message: error.response?.data?.detail || error.message,
            details: error.response?.data,
          },
        };

        addTrace(trace);
        setSelectedTrace(trace);
        throw error;
      }
    },
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const handleSubmit = () => {
    if (file) {
      mutation.mutate({ file, func: selectedFunction });
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
              <Brain className="w-8 h-8 text-purple-600" />
              Vision Language Model API
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              Claude 3.5 Sonnet 멀티모달 LLM으로 도면 분석 (Information Block, 치수, 공정, QC)
            </p>
          </div>
        </div>

        <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-purple-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                🧠 VL 모델 기능
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                <div>
                  <p className="font-medium text-purple-900 dark:text-purple-100">📋 Information Block 추출</p>
                  <p className="text-gray-700 dark:text-gray-300 ml-4">부품명, 재질, 스케일 등</p>
                </div>
                <div>
                  <p className="font-medium text-blue-900 dark:text-blue-100">📐 치수 추출</p>
                  <p className="text-gray-700 dark:text-gray-300 ml-4">모든 치수 텍스트 인식</p>
                </div>
                <div>
                  <p className="font-medium text-green-900 dark:text-green-100">🏭 제조 공정 추론</p>
                  <p className="text-gray-700 dark:text-gray-300 ml-4">가공 순서 자동 생성</p>
                </div>
                <div>
                  <p className="font-medium text-orange-900 dark:text-orange-100">✓ QC 체크리스트</p>
                  <p className="text-gray-700 dark:text-gray-300 ml-4">품질 검사 항목 생성</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>1. 파일 업로드</CardTitle>
            </CardHeader>
            <CardContent>
              <FileUploadSection
                onFileSelect={setFile}
                currentFile={file}
                accept={{
                  'image/*': ['.png', '.jpg', '.jpeg'],
                  'application/pdf': ['.pdf']
                }}
                maxSize={10 * 1024 * 1024}
                disabled={mutation.isPending}
                showSamples={true}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>2. VL 기능 선택</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">기능</label>
                <select
                  value={selectedFunction}
                  onChange={(e) => setSelectedFunction(e.target.value as VLFunction)}
                  className="w-full px-3 py-2 border rounded-md bg-background"
                  disabled={mutation.isPending}
                >
                  <option value="extractInfoBlock">📋 Information Block 추출</option>
                  <option value="extractDimensions">📐 치수 추출</option>
                  <option value="inferManufacturingProcess">🏭 제조 공정 추론</option>
                  <option value="generateQCChecklist">✓ QC 체크리스트 생성</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">모델</label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md bg-background"
                  disabled={mutation.isPending}
                >
                  <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet (권장)</option>
                  <option value="gpt-4o">GPT-4o</option>
                </select>
              </div>

              {selectedFunction === 'extractInfoBlock' && (
                <div>
                  <label className="block text-sm font-medium mb-2">추출할 정보 필드</label>
                  <div className="space-y-2">
                    {['name', 'part number', 'material', 'scale', 'weight', 'drawing number'].map((field) => (
                      <label key={field} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={queryFields.includes(field)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setQueryFields([...queryFields, field]);
                            } else {
                              setQueryFields(queryFields.filter(f => f !== field));
                            }
                          }}
                          disabled={mutation.isPending}
                        />
                        <span className="text-sm">{field}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              <Button
                onClick={handleSubmit}
                disabled={!file || mutation.isPending}
                className="w-full"
              >
                {mutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    처리 중...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    분석 시작
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {mutation.error && <ErrorPanel error={mutation.error as any} />}

          {result && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ListChecks className="w-5 h-5" />
                  분석 결과
                  <Badge variant="outline">{result.processing_time?.toFixed(2)}s</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <JSONViewer data={result} />
              </CardContent>
            </Card>
          )}

          {selectedTrace && (
            <RequestInspector trace={selectedTrace} />
          )}

          {vlTraces.length > 0 && (
            <RequestTimeline
              traces={vlTraces}
              onSelectTrace={setSelectedTrace}
            />
          )}
        </div>
      </div>
    </div>
  );
}
