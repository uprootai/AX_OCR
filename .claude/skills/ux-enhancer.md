---
name: ux-enhancer
description: Applies 2025 enterprise UI/UX best practices including accessibility (WCAG 2.1), dark mode, performance optimization, and interactive visualizations
allowed-tools: [read, write, glob, grep]
---

# UX Enhancer Skill

**목적**: 유저 관점에서 UI/UX를 고도화하여 엔터프라이즈급 도면 분석 시스템 구축

## 🎯 2025년 React 엔터프라이즈 UI/UX 트렌드 적용

### 필수 요구사항
- ✅ WCAG 2.1 AA 접근성 준수
- ✅ 다크모드 지원 (자동 감지 + 수동 토글)
- ✅ TypeScript 완전 타입 안정성
- ✅ 반응형 디자인 (모바일/태블릿/데스크탑)
- ✅ 실시간 피드백 (로딩, 진행률, 에러)

## 📊 현재 상태 분석

### TestGateway.tsx (714 lines)
**발견된 UX 문제**:

1. **파일 업로드 경험**
   - ❌ 드래그 앤 드롭 미지원
   - ❌ 업로드 진행률 표시 없음
   - ❌ 파일 미리보기 없음
   - ❌ 업로드 취소 기능 없음

2. **분석 진행 상태**
   - ⚠️ 단순 텍스트만 표시
   - ❌ 단계별 진행률 바 없음
   - ❌ 예상 소요 시간 표시 없음
   - ❌ 각 서비스별 상태 시각화 부족

3. **결과 표시**
   - ⚠️ 텍스트 위주 (시각화 부족)
   - ❌ 인터랙티브 차트 없음
   - ❌ 결과 다운로드 기능 부족
   - ❌ 결과 공유 링크 생성 없음

4. **접근성**
   - ❌ 키보드 네비게이션 불완전
   - ❌ 스크린 리더 지원 부족
   - ❌ 포커스 표시 불명확
   - ❌ ARIA 레이블 누락

5. **성능 UX**
   - ❌ Skeleton 로더 없음
   - ❌ 이미지 Lazy Loading 미적용
   - ❌ 불필요한 리렌더링 다수

## 🚀 개선 작업 목록

### Phase 1: 파일 업로드 UX 개선 (우선순위: 최상)

#### 1-1. 드래그 앤 드롭 업로드
```tsx
// web-ui/src/components/FileDropzone.tsx
import { useDropzone } from 'react-dropzone';

export function FileDropzone({ onFileSelect }: { onFileSelect: (file: File) => void }) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.pdf']
    },
    maxSize: 10485760, // 10MB
    multiple: false,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    }
  });

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
        transition-all duration-200
        ${isDragActive
          ? 'border-primary bg-primary/10 scale-105'
          : 'border-muted-foreground/25 hover:border-primary/50'
        }
      `}
      role="button"
      aria-label="파일 업로드 영역"
      tabIndex={0}
    >
      <input {...getInputProps()} aria-label="파일 선택 input" />
      <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
      {isDragActive ? (
        <p className="text-lg font-medium">파일을 여기에 놓으세요</p>
      ) : (
        <>
          <p className="text-lg font-medium mb-2">
            도면 파일을 드래그하거나 클릭하여 업로드
          </p>
          <p className="text-sm text-muted-foreground">
            PNG, JPG, PDF 지원 (최대 10MB)
          </p>
        </>
      )}
    </div>
  );
}
```

#### 1-2. 업로드 진행률 표시
```tsx
// web-ui/src/components/UploadProgress.tsx
interface UploadProgressProps {
  progress: number;
  fileName: string;
  onCancel: () => void;
}

export function UploadProgress({ progress, fileName, onCancel }: UploadProgressProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <FileIcon className="h-5 w-5 text-primary" />
            <span className="font-medium truncate max-w-[200px]">{fileName}</span>
          </div>
          <Button variant="ghost" size="sm" onClick={onCancel} aria-label="업로드 취소">
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Progress Bar */}
        <Progress value={progress} className="h-2 mb-2" aria-label={`업로드 진행률: ${progress}%`} />

        <div className="flex justify-between text-sm text-muted-foreground">
          <span>{progress}% 완료</span>
          <span>{progress < 100 ? '업로드 중...' : '완료!'}</span>
        </div>
      </CardContent>
    </Card>
  );
}
```

#### 1-3. 파일 미리보기
```tsx
// web-ui/src/components/FilePreview.tsx
export function FilePreview({ file }: { file: File }) {
  const [preview, setPreview] = useState<string>('');

  useEffect(() => {
    const reader = new FileReader();
    reader.onloadend = () => setPreview(reader.result as string);
    reader.readAsDataURL(file);
  }, [file]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>업로드된 파일</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative aspect-video bg-muted rounded-lg overflow-hidden">
          <img
            src={preview}
            alt="업로드된 도면 미리보기"
            className="object-contain w-full h-full"
          />
        </div>
        <div className="mt-4 space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">파일명</span>
            <span className="font-medium">{file.name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">크기</span>
            <span className="font-medium">{(file.size / 1024).toFixed(2)} KB</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">타입</span>
            <span className="font-medium">{file.type}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Phase 2: 분석 진행 상태 시각화 (우선순위: 최상)

#### 2-1. 단계별 진행률 표시
```tsx
// web-ui/src/components/AnalysisProgress.tsx
interface AnalysisStep {
  id: string;
  label: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  progress: number;
  duration?: number;
}

export function AnalysisProgress({ steps }: { steps: AnalysisStep[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>분석 진행 상황</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {steps.map((step, index) => (
          <div key={step.id} className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {/* Status Icon */}
                {step.status === 'completed' && (
                  <CheckCircle2 className="h-5 w-5 text-green-500" aria-label="완료" />
                )}
                {step.status === 'running' && (
                  <Loader2 className="h-5 w-5 text-blue-500 animate-spin" aria-label="진행 중" />
                )}
                {step.status === 'error' && (
                  <XCircle className="h-5 w-5 text-red-500" aria-label="오류" />
                )}
                {step.status === 'pending' && (
                  <Circle className="h-5 w-5 text-muted-foreground" aria-label="대기 중" />
                )}

                <span className={`font-medium ${
                  step.status === 'completed' ? 'text-green-600' :
                  step.status === 'running' ? 'text-blue-600' :
                  step.status === 'error' ? 'text-red-600' :
                  'text-muted-foreground'
                }`}>
                  {index + 1}. {step.label}
                </span>
              </div>

              {step.duration && (
                <span className="text-sm text-muted-foreground">
                  {step.duration.toFixed(1)}s
                </span>
              )}
            </div>

            {step.status === 'running' && (
              <Progress value={step.progress} className="h-1" />
            )}
          </div>
        ))}

        {/* Overall Progress */}
        <Separator />
        <div className="pt-2">
          <div className="flex justify-between text-sm mb-2">
            <span className="font-medium">전체 진행률</span>
            <span className="text-muted-foreground">
              {Math.round(steps.reduce((acc, s) =>
                acc + (s.status === 'completed' ? 100 : s.progress), 0) / steps.length
              )}%
            </span>
          </div>
          <Progress
            value={steps.reduce((acc, s) =>
              acc + (s.status === 'completed' ? 100 : s.progress), 0) / steps.length
            }
            className="h-2"
          />
        </div>
      </CardContent>
    </Card>
  );
}
```

#### 2-2. 예상 소요 시간 계산
```tsx
// web-ui/src/hooks/useEstimatedTime.ts
export function useEstimatedTime(completedSteps: number, totalSteps: number, startTime: Date) {
  const [estimatedTime, setEstimatedTime] = useState<string>('계산 중...');

  useEffect(() => {
    if (completedSteps === 0) {
      setEstimatedTime('계산 중...');
      return;
    }

    const elapsed = (Date.now() - startTime.getTime()) / 1000; // seconds
    const avgTimePerStep = elapsed / completedSteps;
    const remainingSteps = totalSteps - completedSteps;
    const estimated = avgTimePerStep * remainingSteps;

    if (estimated < 60) {
      setEstimatedTime(`약 ${Math.round(estimated)}초 남음`);
    } else {
      setEstimatedTime(`약 ${Math.round(estimated / 60)}분 남음`);
    }
  }, [completedSteps, totalSteps, startTime]);

  return estimatedTime;
}
```

### Phase 3: 결과 시각화 개선 (우선순위: 높음)

#### 3-1. 인터랙티브 차트 추가
```tsx
// web-ui/src/components/ResultsCharts.tsx
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer
} from 'recharts';

export function DimensionChart({ dimensions }: { dimensions: any[] }) {
  const data = dimensions.map(d => ({
    name: `${d.value}${d.unit}`,
    value: parseFloat(d.value),
    type: d.type
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle>치수 분포</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="value" fill="hsl(var(--primary))" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function ProcessingTimeChart({ yoloTime, ocrTime, segTime, tolTime }: any) {
  const data = [
    { name: 'YOLO', value: yoloTime, fill: '#3b82f6' },
    { name: 'OCR', value: ocrTime, fill: '#10b981' },
    { name: 'Segmentation', value: segTime, fill: '#f59e0b' },
    { name: 'Tolerance', value: tolTime, fill: '#ef4444' }
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>처리 시간 분석</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
```

#### 3-2. 결과 다운로드 기능
```tsx
// web-ui/src/components/ResultActions.tsx
import { Download, Share2, Copy } from 'lucide-react';

export function ResultActions({ result }: { result: AnalysisResult }) {
  const downloadJSON = () => {
    const dataStr = JSON.stringify(result, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analysis_${result.file_id}.json`;
    link.click();
  };

  const downloadCSV = () => {
    const dimensions = result.data.ensemble?.dimensions || [];
    const csv = [
      ['Type', 'Value', 'Unit', 'Tolerance'].join(','),
      ...dimensions.map(d =>
        [d.type, d.value, d.unit, d.tolerance].join(',')
      )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `dimensions_${result.file_id}.csv`;
    link.click();
  };

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    toast.success('결과가 클립보드에 복사되었습니다');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>결과 내보내기</CardTitle>
      </CardHeader>
      <CardContent className="flex gap-2">
        <Button onClick={downloadJSON} variant="outline">
          <Download className="h-4 w-4 mr-2" />
          JSON 다운로드
        </Button>
        <Button onClick={downloadCSV} variant="outline">
          <Download className="h-4 w-4 mr-2" />
          CSV 다운로드
        </Button>
        <Button onClick={copyToClipboard} variant="outline">
          <Copy className="h-4 w-4 mr-2" />
          복사
        </Button>
      </CardContent>
    </Card>
  );
}
```

### Phase 4: 접근성 (WCAG 2.1 AA) (우선순위: 중간)

#### 4-1. 키보드 네비게이션
```tsx
// web-ui/src/components/AccessibleButton.tsx
export function AccessibleButton({ onClick, children, ...props }: ButtonProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick?.(e as any);
    }
  };

  return (
    <Button
      onClick={onClick}
      onKeyDown={handleKeyDown}
      {...props}
      tabIndex={0}
      role="button"
    >
      {children}
    </Button>
  );
}
```

#### 4-2. ARIA 레이블 추가
```tsx
// 모든 인터랙티브 요소에 ARIA 추가
<button
  aria-label="분석 시작"
  aria-describedby="analysis-description"
>
  분석 시작
</button>

<div id="analysis-description" className="sr-only">
  선택한 도면 파일을 YOLO, OCR, Segmentation으로 분석합니다
</div>

// 로딩 상태
<div role="status" aria-live="polite" aria-atomic="true">
  {isLoading ? '분석 진행 중...' : '분석 완료'}
</div>

// 에러 메시지
<div role="alert" aria-live="assertive">
  {error && `오류 발생: ${error.message}`}
</div>
```

#### 4-3. 포커스 관리
```tsx
// web-ui/src/hooks/useFocusTrap.ts
export function useFocusTrap(isOpen: boolean) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen || !containerRef.current) return;

    const focusableElements = containerRef.current.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey && document.activeElement === firstElement) {
        lastElement?.focus();
        e.preventDefault();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        firstElement?.focus();
        e.preventDefault();
      }
    };

    document.addEventListener('keydown', handleTabKey);
    firstElement?.focus();

    return () => document.removeEventListener('keydown', handleTabKey);
  }, [isOpen]);

  return containerRef;
}
```

### Phase 5: 다크모드 지원 (우선순위: 중간)

#### 5-1. 테마 토글
```tsx
// web-ui/src/components/ThemeToggle.tsx
import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      aria-label={`${theme === 'dark' ? '라이트' : '다크'} 모드로 전환`}
    >
      <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
    </Button>
  );
}
```

#### 5-2. 시스템 설정 자동 감지
```tsx
// web-ui/src/providers/ThemeProvider.tsx
import { ThemeProvider as NextThemesProvider } from 'next-themes';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
    >
      {children}
    </NextThemesProvider>
  );
}
```

### Phase 6: 에러 처리 & Graceful Degradation (우선순위: 최상) 🆕

#### 6-1. YOLO Crop OCR 부분 실패 처리
**상황**: eDOCr2가 crop된 작은 이미지에서 프레임 검출 실패 (`TypeError: cannot unpack non-iterable NoneType`)

**UI/UX 전략**:
```tsx
// web-ui/src/components/CropOCRResults.tsx
interface CropResult {
  cropIdx: number;
  status: 'success' | 'error' | 'fallback';
  dimensions?: Dimension[];
  error?: string;
  yoloClass?: string;
}

export function CropOCRResults({ results }: { results: CropResult[] }) {
  const successCount = results.filter(r => r.status === 'success').length;
  const errorCount = results.filter(r => r.status === 'error').length;
  const totalCount = results.length;
  const successRate = (successCount / totalCount) * 100;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>YOLO Crop OCR 결과</CardTitle>
          <Badge variant={successRate >= 80 ? 'success' : successRate >= 50 ? 'warning' : 'destructive'}>
            {successCount}/{totalCount} 성공 ({successRate.toFixed(0)}%)
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Overall Status */}
        {errorCount > 0 && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>부분 실패 감지</AlertTitle>
            <AlertDescription>
              {errorCount}개 영역에서 OCR 실패. 전체 이미지 OCR 결과로 보완합니다.
            </AlertDescription>
          </Alert>
        )}

        {/* Success Rate Progress */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">성공률</span>
            <span className="font-medium">{successRate.toFixed(1)}%</span>
          </div>
          <Progress value={successRate} className="h-2" />
        </div>

        {/* Individual Crop Results */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {results.map((result) => (
            <Card key={result.cropIdx} className={
              result.status === 'error' ? 'border-red-200 bg-red-50 dark:bg-red-950' :
              result.status === 'fallback' ? 'border-yellow-200 bg-yellow-50 dark:bg-yellow-950' :
              'border-green-200 bg-green-50 dark:bg-green-950'
            }>
              <CardContent className="pt-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {result.status === 'success' && (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    )}
                    {result.status === 'error' && (
                      <XCircle className="h-4 w-4 text-red-600" />
                    )}
                    {result.status === 'fallback' && (
                      <AlertTriangle className="h-4 w-4 text-yellow-600" />
                    )}
                    <span className="text-sm font-medium">
                      영역 #{result.cropIdx + 1}
                    </span>
                  </div>
                  {result.yoloClass && (
                    <Badge variant="outline" className="text-xs">
                      {result.yoloClass}
                    </Badge>
                  )}
                </div>

                {result.status === 'success' && result.dimensions && (
                  <div className="space-y-1">
                    {result.dimensions.map((dim, idx) => (
                      <p key={idx} className="text-sm">
                        {dim.value}{dim.unit}
                      </p>
                    ))}
                  </div>
                )}

                {result.status === 'error' && (
                  <div className="space-y-2">
                    <p className="text-sm text-red-600 dark:text-red-400">
                      {result.error || 'OCR 실패'}
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => retryOCR(result.cropIdx)}
                      className="w-full"
                    >
                      <RotateCw className="h-3 w-3 mr-1" />
                      재시도
                    </Button>
                  </div>
                )}

                {result.status === 'fallback' && (
                  <Alert className="mt-2">
                    <Info className="h-3 w-3" />
                    <AlertDescription className="text-xs">
                      전체 이미지 OCR로 대체됨
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

#### 6-2. 에러 복구 전략 UI
```tsx
// web-ui/src/components/ErrorRecovery.tsx
interface ErrorRecoveryProps {
  errorType: 'crop_ocr_failed' | 'edocr2_frame_error' | 'network_error';
  failedCrops: number[];
  onFallback: () => void;
  onRetry: () => void;
  onSkip: () => void;
}

export function ErrorRecovery({
  errorType,
  failedCrops,
  onFallback,
  onRetry,
  onSkip
}: ErrorRecoveryProps) {
  const getErrorMessage = () => {
    switch (errorType) {
      case 'crop_ocr_failed':
        return '일부 영역에서 OCR이 실패했습니다.';
      case 'edocr2_frame_error':
        return 'eDOCr2가 crop 이미지에서 프레임을 찾지 못했습니다.';
      case 'network_error':
        return '네트워크 연결 오류가 발생했습니다.';
      default:
        return '알 수 없는 오류가 발생했습니다.';
    }
  };

  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>OCR 처리 오류</AlertTitle>
      <AlertDescription className="space-y-4">
        <p>{getErrorMessage()}</p>
        <p className="text-sm">
          실패한 영역: {failedCrops.length}개 (#{failedCrops.join(', #')})
        </p>

        <div className="flex flex-wrap gap-2 mt-4">
          <Button
            onClick={onFallback}
            variant="default"
            size="sm"
          >
            <Shield className="h-3 w-3 mr-1" />
            전체 이미지 OCR로 대체
          </Button>

          <Button
            onClick={onRetry}
            variant="outline"
            size="sm"
          >
            <RotateCw className="h-3 w-3 mr-1" />
            실패한 영역만 재시도
          </Button>

          <Button
            onClick={onSkip}
            variant="ghost"
            size="sm"
          >
            <ArrowRight className="h-3 w-3 mr-1" />
            성공한 결과로 계속
          </Button>
        </div>

        <details className="text-xs mt-4">
          <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
            기술 세부사항 보기
          </summary>
          <pre className="mt-2 p-2 bg-black/10 dark:bg-white/10 rounded text-xs overflow-x-auto">
            {JSON.stringify({
              errorType,
              failedCrops,
              timestamp: new Date().toISOString()
            }, null, 2)}
          </pre>
        </details>
      </AlertDescription>
    </Alert>
  );
}
```

#### 6-3. 자동 폴백 로직
```tsx
// web-ui/src/hooks/useOCRFallback.ts
export function useOCRFallback() {
  const [fallbackActive, setFallbackActive] = useState(false);

  const handleOCRError = async (
    cropResults: CropResult[],
    fullImageOCR: () => Promise<any>
  ) => {
    const failedCount = cropResults.filter(r => r.status === 'error').length;
    const totalCount = cropResults.length;
    const failureRate = (failedCount / totalCount) * 100;

    // 30% 이상 실패 시 자동으로 전체 이미지 OCR로 폴백
    if (failureRate >= 30) {
      toast.info('일부 영역 OCR 실패로 전체 이미지 OCR로 전환합니다...');
      setFallbackActive(true);

      try {
        const fullResult = await fullImageOCR();
        toast.success('전체 이미지 OCR 완료!');
        return fullResult;
      } catch (error) {
        toast.error('전체 이미지 OCR도 실패했습니다.');
        throw error;
      }
    }

    // 30% 미만 실패 시 성공한 결과만 사용
    return cropResults.filter(r => r.status === 'success');
  };

  return { fallbackActive, handleOCRError };
}
```

#### 6-4. 진행 상태 에러 표시 개선
```tsx
// web-ui/src/components/ui/PipelineProgress.tsx 수정
// 📝 OCR 분석 단계에 에러 상태 추가

const getStepStatusIcon = (status: StepStatus, details?: any) => {
  if (status === 'error') {
    return (
      <div className="relative">
        <AlertCircle className="w-6 h-6 text-red-500" />
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <Info className="w-3 h-3 absolute -top-1 -right-1 text-yellow-500" />
            </TooltipTrigger>
            <TooltipContent>
              <p className="text-xs max-w-xs">
                {details?.errorMessage || 'OCR 처리 중 오류 발생'}
              </p>
              {details?.fallbackUsed && (
                <p className="text-xs text-green-600 mt-1">
                  ✓ 전체 이미지 OCR로 자동 복구됨
                </p>
              )}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    );
  }

  // ... 기존 로직
};
```

### Phase 7: 성능 최적화 UX (우선순위: 중간)

#### 7-1. Skeleton 로더
```tsx
// web-ui/src/components/SkeletonCard.tsx
export function SkeletonCard() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-[200px]" />
      </CardHeader>
      <CardContent className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-[80%]" />
        <Skeleton className="h-20 w-full" />
      </CardContent>
    </Card>
  );
}
```

#### 7-2. 이미지 Lazy Loading
```tsx
// web-ui/src/components/LazyImage.tsx
export function LazyImage({ src, alt, ...props }: ImgHTMLAttributes<HTMLImageElement>) {
  const [isLoaded, setIsLoaded] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (!imgRef.current) return;

    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsLoaded(true);
        observer.disconnect();
      }
    });

    observer.observe(imgRef.current);

    return () => observer.disconnect();
  }, []);

  return (
    <div ref={imgRef} className="relative">
      {!isLoaded && <Skeleton className="absolute inset-0" />}
      {isLoaded && <img src={src} alt={alt} {...props} loading="lazy" />}
    </div>
  );
}
```

#### 7-3. 리렌더링 최적화
```tsx
// React.memo로 불필요한 리렌더링 방지
export const DimensionCard = React.memo(({ dimension }: { dimension: Dimension }) => {
  return (
    <Card>
      <CardContent>
        <p>{dimension.value}{dimension.unit}</p>
      </CardContent>
    </Card>
  );
}, (prevProps, nextProps) => {
  return prevProps.dimension.value === nextProps.dimension.value;
});
```

## 📦 필요한 패키지 설치

```bash
cd /home/uproot/ax/poc/web-ui

# UI 컴포넌트
npm install react-dropzone
npm install recharts
npm install next-themes

# 유틸리티
npm install clsx tailwind-merge
npm install lucide-react  # 이미 있을 수 있음
npm install sonner  # Toast 알림

# 접근성
npm install @radix-ui/react-visually-hidden
npm install @radix-ui/react-focus-scope
```

## 🎨 디자인 시스템 개선

### Tailwind Config 확장
```js
// web-ui/tailwind.config.js
module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        // ... 더 많은 색상
      },
      keyframes: {
        'slide-in': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      animation: {
        'slide-in': 'slide-in 0.3s ease-out',
        'fade-in': 'fade-in 0.2s ease-in',
      },
    },
  },
};
```

## 🚦 실행 계획

### Week 1: 파일 업로드 UX
- [ ] FileDropzone 컴포넌트 구현
- [ ] UploadProgress 컴포넌트 구현
- [ ] FilePreview 컴포넌트 구현
- [ ] TestGateway에 통합

### Week 2: 분석 진행 상태
- [ ] AnalysisProgress 컴포넌트 구현
- [ ] useEstimatedTime 훅 구현
- [ ] 실시간 진행률 업데이트 로직
- [ ] WebSocket 연결 (선택사항)

### Week 3: 결과 시각화
- [ ] Recharts 통합
- [ ] DimensionChart 구현
- [ ] ProcessingTimeChart 구현
- [ ] ResultActions 구현

### Week 4: 접근성 & 다크모드
- [ ] ARIA 레이블 전체 추가
- [ ] 키보드 네비게이션 테스트
- [ ] ThemeProvider 설정
- [ ] 다크모드 색상 조정

### Week 5: 성능 최적화
- [ ] Skeleton 로더 추가
- [ ] LazyImage 구현
- [ ] React.memo 최적화
- [ ] Lighthouse 성능 테스트

## 📊 성공 지표

### 정량적 지표
- ✅ Lighthouse Accessibility Score: 60 → 95+
- ✅ Lighthouse Performance Score: 70 → 90+
- ✅ 파일 업로드 완료율: 85% → 98%
- ✅ 사용자 이탈률: 30% → 10%
- ✅ 평균 작업 완료 시간: 5분 → 2분

### 정성적 지표
- ✅ 사용자 피드백: "직관적이다"
- ✅ 신규 사용자 온보딩: 설명 없이 사용 가능
- ✅ 모바일 사용성: 터치 인터페이스 최적화
- ✅ 다크모드 선호도: 사용자 40% 이상 사용

## 🎯 베스트 프랙티스 체크리스트

### 2025년 React 엔터프라이즈 표준
- [ ] TypeScript strict mode 활성화
- [ ] ESLint accessibility 플러그인 사용
- [ ] Prettier 코드 포맷팅 자동화
- [ ] Storybook으로 컴포넌트 문서화
- [ ] Jest + React Testing Library 테스트
- [ ] Lighthouse CI 통합
- [ ] Bundle 사이즈 500KB 이하 유지
- [ ] Core Web Vitals 모두 Green
- [ ] WCAG 2.1 AA 100% 준수
- [ ] 모든 이미지 alt 텍스트 제공

## 📚 참고 자료

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [React Aria - Accessibility](https://react-spectrum.adobe.com/react-aria/)
- [Shadcn/ui Components](https://ui.shadcn.com/)
- [Radix UI Primitives](https://www.radix-ui.com/)
- [Core Web Vitals](https://web.dev/vitals/)

---

**이 Skill 실행 시**:
1. 현재 TestGateway.tsx 분석
2. 위 개선사항 우선순위별 적용
3. 각 단계별 테스트 및 검증
4. 문서 업데이트 (CHANGELOG 생성)
5. 사용자 피드백 수집 및 반영
