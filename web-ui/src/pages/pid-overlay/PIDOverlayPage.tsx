/**
 * PIDOverlayPage - P&ID 오버레이 테스트 페이지
 *
 * P&ID 도면의 심볼을 검출하여 시각화하는 페이지입니다.
 * Design Checker API의 pipeline/detect 엔드포인트를 사용합니다.
 *
 * Note: 전체 레이어(심볼+라인+텍스트+영역)가 필요한 경우
 * BlueprintFlow를 사용하세요.
 */

import { useState } from 'react';
import { PIDOverlayViewer } from '../../components/pid';
import { Info, Settings } from 'lucide-react';

export function PIDOverlayPage() {
  const [lastResult, setLastResult] = useState<{
    symbols: number;
    lines: number;
    texts: number;
    regions: number;
  } | null>(null);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">P&ID 심볼 검출 뷰어</h1>
        <p className="text-gray-600 dark:text-gray-400">
          P&ID 도면을 업로드하면 YOLO를 통해 심볼을 자동으로 검출하여 시각화합니다.
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
          💡 전체 분석(심볼+라인+텍스트+영역)은 <a href="/blueprintflow" className="text-blue-500 hover:underline">BlueprintFlow</a>를 사용하세요.
        </p>
      </div>

      {/* Info panel */}
      <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800 dark:text-blue-200">
            <p className="font-semibold mb-1">사용 방법</p>
            <ul className="list-disc list-inside space-y-1 text-blue-700 dark:text-blue-300">
              <li>P&ID 도면 이미지를 업로드합니다 (PNG, JPG)</li>
              <li>레이어 토글 버튼으로 표시할 항목을 선택합니다</li>
              <li>심볼, 라인 등에 마우스를 올리면 상세 정보가 표시됩니다</li>
              <li>SVG/이미지 모드를 전환하여 다른 형식으로 볼 수 있습니다</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Main viewer */}
      <PIDOverlayViewer
        apiUrl="http://localhost:5019"
        onOverlayGenerated={(data) => {
          setLastResult({
            symbols: data.statistics.symbols_count,
            lines: data.statistics.lines_count,
            texts: data.statistics.texts_count,
            regions: data.statistics.regions_count,
          });
        }}
      />

      {/* Result summary */}
      {lastResult && (
        <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <Settings className="w-4 h-4" />
            분석 결과 요약
          </h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-3 bg-white dark:bg-gray-700 rounded-lg">
              <div className="text-2xl font-bold text-orange-500">{lastResult.symbols}</div>
              <div className="text-xs text-gray-500">심볼</div>
            </div>
            <div className="text-center p-3 bg-white dark:bg-gray-700 rounded-lg">
              <div className="text-2xl font-bold text-blue-500">{lastResult.lines}</div>
              <div className="text-xs text-gray-500">라인</div>
            </div>
            <div className="text-center p-3 bg-white dark:bg-gray-700 rounded-lg">
              <div className="text-2xl font-bold text-amber-500">{lastResult.texts}</div>
              <div className="text-xs text-gray-500">텍스트</div>
            </div>
            <div className="text-center p-3 bg-white dark:bg-gray-700 rounded-lg">
              <div className="text-2xl font-bold text-cyan-500">{lastResult.regions}</div>
              <div className="text-xs text-gray-500">영역</div>
            </div>
          </div>
        </div>
      )}

      {/* API info */}
      <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <h3 className="text-sm font-semibold mb-2">API 엔드포인트</h3>
        <code className="text-xs bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">
          POST http://localhost:5019/api/v1/pipeline/detect
        </code>
        <div className="mt-3 text-xs text-gray-500">
          <p className="font-semibold">파라미터:</p>
          <ul className="list-disc list-inside mt-1">
            <li><code>model_type</code> - YOLO 모델 타입 (pid_class_aware)</li>
            <li><code>confidence</code> - 검출 신뢰도 임계값</li>
            <li><code>use_sahi</code> - SAHI 슬라이싱 사용</li>
            <li><code>visualize</code> - 시각화 이미지 생성</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default PIDOverlayPage;
