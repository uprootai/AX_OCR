import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import JSONViewer from '../../components/debug/JSONViewer';
import RequestInspector from '../../components/debug/RequestInspector';
import RequestTimeline from '../../components/debug/RequestTimeline';
import ErrorPanel from '../../components/debug/ErrorPanel';
import SkinmodelGuide from '../../components/guides/SkinmodelGuide';
import { skinmodelApi } from '../../lib/api';
import { useMonitoringStore } from '../../store/monitoringStore';
import { Loader2, Play, Target, Plus, Trash2, BookOpen } from 'lucide-react';
import type { ToleranceResult, RequestTrace } from '../../types/api';

interface Dimension {
  type: string;
  value: number;
  tolerance?: number;
  unit: string;
}

export default function TestSkinmodel() {
  const [showGuide, setShowGuide] = useState(true);
  const [dimensions, setDimensions] = useState<Dimension[]>([
    { type: 'diameter', value: 50, tolerance: 0.1, unit: 'mm' },
  ]);
  const [material, setMaterial] = useState({
    name: 'Steel',
    youngs_modulus: 200,
    poisson_ratio: 0.3,
    density: 7850,
  });
  const [manufacturingProcess, setManufacturingProcess] = useState('milling');
  const [correlationLength, setCorrelationLength] = useState(0.5);

  const [result, setResult] = useState<ToleranceResult | null>(null);
  const [selectedTrace, setSelectedTrace] = useState<RequestTrace | null>(null);

  const { traces, addTrace } = useMonitoringStore();
  const skinmodelTraces = traces.filter((t) => t.endpoint.includes('tolerance') || t.endpoint.includes('skinmodel'));

  const mutation = useMutation({
    mutationFn: async () => {
      const startTime = Date.now();
      const traceId = `skinmodel-${Date.now()}`;

      const requestData = {
        dimensions: dimensions.map(d => ({
          type: d.type,
          value: d.value,
          tolerance: d.tolerance,
          unit: d.unit,
        })),
        material: {
          name: material.name,
          youngs_modulus: material.youngs_modulus,
          poisson_ratio: material.poisson_ratio,
          density: material.density,
        },
        manufacturing_process: manufacturingProcess,
        correlation_length: correlationLength,
      };

      try {
        const response = await skinmodelApi.tolerance(requestData);
        const duration = Date.now() - startTime;

        const trace: RequestTrace = {
          id: traceId,
          timestamp: new Date(),
          endpoint: '/api/v1/tolerance',
          method: 'POST',
          status: 200,
          duration,
          request: requestData,
          response,
        };

        addTrace(trace);
        setSelectedTrace(trace);
        return response.data;
      } catch (error: any) {
        const duration = Date.now() - startTime;

        const trace: RequestTrace = {
          id: traceId,
          timestamp: new Date(),
          endpoint: '/api/v1/tolerance',
          method: 'POST',
          status: error.response?.status || 0,
          duration,
          request: requestData,
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

  const handleTest = () => {
    setResult(null);
    mutation.mutate();
  };

  const addDimension = () => {
    setDimensions([...dimensions, { type: 'length', value: 10, tolerance: 0.05, unit: 'mm' }]);
  };

  const removeDimension = (index: number) => {
    setDimensions(dimensions.filter((_, i) => i !== index));
  };

  const updateDimension = (index: number, field: keyof Dimension, value: any) => {
    const newDimensions = [...dimensions];
    newDimensions[index] = { ...newDimensions[index], [field]: value };
    setDimensions(newDimensions);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Easy':
        return 'success';
      case 'Medium':
        return 'warning';
      case 'Hard':
        return 'error';
      default:
        return 'default';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'Low':
        return 'success';
      case 'Medium':
        return 'warning';
      case 'High':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <Target className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold">Skin Model API Test</h1>
          </div>
          <Button
            variant={showGuide ? 'default' : 'outline'}
            onClick={() => setShowGuide(!showGuide)}
          >
            <BookOpen className="w-4 h-4 mr-2" />
            {showGuide ? '가이드 숨기기' : '가이드 보기'}
          </Button>
        </div>
        <p className="text-muted-foreground">
          공차 예측 및 제조 가능성 분석을 수행합니다.
        </p>
      </div>

      {/* Usage Guide */}
      {showGuide && <SkinmodelGuide />}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Left Column: Test Configuration */}
        <div className="space-y-6">
          {/* Dimensions Input */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>1. Dimensions</CardTitle>
                <Button variant="outline" size="sm" onClick={addDimension}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {dimensions.map((dim, idx) => (
                <div key={idx} className="p-3 border rounded space-y-2">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">Dimension {idx + 1}</span>
                    {dimensions.length > 1 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeDimension(idx)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs text-muted-foreground">Type</label>
                      <input
                        type="text"
                        value={dim.type}
                        onChange={(e) => updateDimension(idx, 'type', e.target.value)}
                        className="w-full px-2 py-1 text-sm border rounded"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">Unit</label>
                      <input
                        type="text"
                        value={dim.unit}
                        onChange={(e) => updateDimension(idx, 'unit', e.target.value)}
                        className="w-full px-2 py-1 text-sm border rounded"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">Value</label>
                      <input
                        type="number"
                        value={dim.value}
                        onChange={(e) => updateDimension(idx, 'value', parseFloat(e.target.value))}
                        className="w-full px-2 py-1 text-sm border rounded"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-muted-foreground">Tolerance</label>
                      <input
                        type="number"
                        step="0.01"
                        value={dim.tolerance || 0}
                        onChange={(e) => updateDimension(idx, 'tolerance', parseFloat(e.target.value))}
                        className="w-full px-2 py-1 text-sm border rounded"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Material Properties */}
          <Card>
            <CardHeader>
              <CardTitle>2. Material Properties</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <label className="text-sm font-medium">Material Name</label>
                <input
                  type="text"
                  value={material.name}
                  onChange={(e) => setMaterial({ ...material, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded mt-1"
                />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-xs text-muted-foreground">Young's Modulus (GPa)</label>
                  <input
                    type="number"
                    value={material.youngs_modulus}
                    onChange={(e) => setMaterial({ ...material, youngs_modulus: parseFloat(e.target.value) })}
                    className="w-full px-2 py-1 text-sm border rounded mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground">Poisson Ratio</label>
                  <input
                    type="number"
                    step="0.01"
                    value={material.poisson_ratio}
                    onChange={(e) => setMaterial({ ...material, poisson_ratio: parseFloat(e.target.value) })}
                    className="w-full px-2 py-1 text-sm border rounded mt-1"
                  />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground">Density (kg/m³)</label>
                  <input
                    type="number"
                    value={material.density}
                    onChange={(e) => setMaterial({ ...material, density: parseFloat(e.target.value) })}
                    className="w-full px-2 py-1 text-sm border rounded mt-1"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Process Parameters */}
          <Card>
            <CardHeader>
              <CardTitle>3. Process Parameters</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <label className="text-sm font-medium">Manufacturing Process</label>
                <select
                  value={manufacturingProcess}
                  onChange={(e) => setManufacturingProcess(e.target.value)}
                  className="w-full px-3 py-2 border rounded mt-1"
                >
                  <option value="milling">Milling</option>
                  <option value="turning">Turning</option>
                  <option value="grinding">Grinding</option>
                  <option value="casting">Casting</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">Correlation Length</label>
                <input
                  type="number"
                  step="0.1"
                  value={correlationLength}
                  onChange={(e) => setCorrelationLength(parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border rounded mt-1"
                />
              </div>
            </CardContent>
          </Card>

          {/* Execute */}
          <Card>
            <CardHeader>
              <CardTitle>4. Run Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <Button
                onClick={handleTest}
                disabled={dimensions.length === 0 || mutation.isPending}
                className="w-full"
                size="lg"
              >
                {mutation.isPending ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5 mr-2" />
                    공차 분석 실행
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Request Timeline */}
          {skinmodelTraces.length > 0 && (
            <RequestTimeline
              traces={skinmodelTraces}
              onSelectTrace={setSelectedTrace}
              maxItems={10}
            />
          )}
        </div>

        {/* Right Column: Results */}
        <div className="space-y-6">
          {/* Error */}
          {mutation.isError && (
            <ErrorPanel
              error={{
                status: (mutation.error as any)?.response?.status || 0,
                code: (mutation.error as any)?.response?.status?.toString() || 'ERROR',
                message:
                  (mutation.error as any)?.response?.data?.detail ||
                  (mutation.error as any)?.message ||
                  'An error occurred',
                details: (mutation.error as any)?.response?.data,
              }}
              onRetry={handleTest}
            />
          )}

          {/* Results */}
          {result && (
            <div className="space-y-4">
              {/* Predicted Tolerances */}
              <Card>
                <CardHeader>
                  <CardTitle>예측된 공차 (Predicted Tolerances)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-background border rounded">
                      <span className="font-medium">Flatness</span>
                      <Badge>{result.predicted_tolerances?.flatness.toFixed(4)}</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-background border rounded">
                      <span className="font-medium">Cylindricity</span>
                      <Badge>{result.predicted_tolerances?.cylindricity.toFixed(4)}</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-background border rounded">
                      <span className="font-medium">Position</span>
                      <Badge>{result.predicted_tolerances?.position.toFixed(4)}</Badge>
                    </div>
                    {result.predicted_tolerances?.perpendicularity !== undefined && (
                      <div className="flex items-center justify-between p-3 bg-background border rounded">
                        <span className="font-medium">Perpendicularity</span>
                        <Badge>{result.predicted_tolerances.perpendicularity.toFixed(4)}</Badge>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Manufacturability */}
              <Card>
                <CardHeader>
                  <CardTitle>제조 가능성 (Manufacturability)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Score</span>
                      <div className="flex items-center gap-2">
                        <div className="w-32 h-2 bg-accent rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary"
                            style={{ width: `${result.manufacturability?.score * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-semibold">
                          {((result.manufacturability?.score || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Difficulty</span>
                      <Badge variant={getDifficultyColor(result.manufacturability?.difficulty || '')}>
                        {result.manufacturability?.difficulty}
                      </Badge>
                    </div>
                    {result.manufacturability?.recommendations && (
                      <div>
                        <p className="font-medium mb-2">Recommendations</p>
                        <ul className="space-y-1 text-sm text-muted-foreground">
                          {result.manufacturability.recommendations.map((rec, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <span className="text-primary">•</span>
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Assemblability */}
              <Card>
                <CardHeader>
                  <CardTitle>조립 가능성 (Assemblability)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-background border rounded">
                      <span className="font-medium">Score</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 bg-accent rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary"
                            style={{ width: `${result.assemblability?.score * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-semibold">
                          {((result.assemblability?.score || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-background border rounded">
                      <span className="font-medium">Clearance</span>
                      <Badge>{result.assemblability?.clearance.toFixed(4)}</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-background border rounded">
                      <span className="font-medium">Interference Risk</span>
                      <Badge variant={getRiskColor(result.assemblability?.interference_risk || '')}>
                        {result.assemblability?.interference_risk}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Process Parameters */}
              {result.process_parameters && (
                <Card>
                  <CardHeader>
                    <CardTitle>공정 파라미터 (Process Parameters)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 bg-background border rounded">
                        <span className="font-medium">Correlation Length</span>
                        <Badge>{result.process_parameters.correlation_length.toFixed(4)}</Badge>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-background border rounded">
                        <span className="font-medium">Systematic Deviation</span>
                        <Badge>{result.process_parameters.systematic_deviation.toFixed(4)}</Badge>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-background border rounded">
                        <span className="font-medium">Random Deviation Std</span>
                        <Badge>{result.process_parameters.random_deviation_std.toFixed(4)}</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              <JSONViewer data={result} title="Full JSON Response" defaultExpanded={false} />
            </div>
          )}

          {/* Request Inspector */}
          {selectedTrace && <RequestInspector trace={selectedTrace} />}

          {/* Empty State */}
          {!result && !mutation.isError && !mutation.isPending && (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>입력 파라미터를 설정하고 분석을 실행하세요</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
