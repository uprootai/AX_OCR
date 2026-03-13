import { X, Plus, AlertCircle, Search, CheckCircle, Loader2 } from 'lucide-react';
import { Button } from '../../ui/Button';
import { Card } from '../../ui/Card';
import { useAddAPIForm } from './useAddAPIForm';
import type { AddAPIDialogProps, APICategory } from './types';
import { ICON_OPTIONS, COLOR_OPTIONS } from './types';

export function AddAPIDialogView({ isOpen, onClose }: AddAPIDialogProps) {
  const {
    formData,
    setFormData,
    errors,
    searchUrl,
    setSearchUrl,
    isSearching,
    searchSuccess,
    searchError,
    setSearchError,
    setSearchSuccess,
    handleAutoDiscover,
    handleSubmit,
    handleCancel,
  } = useAddAPIForm(onClose);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Plus className="w-6 h-6 text-primary" />
              <h2 className="text-2xl font-bold">새 API 추가</h2>
            </div>
            <button onClick={handleCancel} className="text-muted-foreground hover:text-foreground">
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Warning */}
          <div className="mb-6 p-4 bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-yellow-800 dark:text-yellow-200">
                <p className="font-semibold mb-1">주의사항</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>API 백엔드 서버가 실행 중이어야 합니다</li>
                  <li>Health check 엔드포인트 (/api/v1/health)가 필요합니다</li>
                  <li>추가 후 자동으로 Dashboard, Settings, BlueprintFlow에 반영됩니다</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Auto Discover Section */}
          <div className="mb-6 p-4 bg-primary/5 border-2 border-primary/20 rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <Search className="w-5 h-5 text-primary" />
              <h3 className="font-semibold text-primary">🚀 API 자동 검색</h3>
            </div>
            <p className="text-sm text-muted-foreground mb-3">
              API URL을 입력하면 자동으로 정보를 가져옵니다 (예: http://localhost:5005)
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                value={searchUrl}
                onChange={(e) => {
                  setSearchUrl(e.target.value);
                  setSearchError('');
                  setSearchSuccess(false);
                }}
                placeholder="http://localhost:5009"
                className="flex-1 px-3 py-2 border rounded-lg bg-background"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleAutoDiscover();
                  }
                }}
              />
              <Button
                onClick={handleAutoDiscover}
                disabled={isSearching || !searchUrl}
                className="px-4"
              >
                {isSearching ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    검색 중...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2" />
                    검색
                  </>
                )}
              </Button>
            </div>
            {searchError && (
              <div className="mt-2 p-2 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded text-sm text-red-600 dark:text-red-400 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>{searchError}</span>
              </div>
            )}
            {searchSuccess && (
              <div className="mt-2 p-2 bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded text-sm text-green-600 dark:text-green-400 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                <span>✅ API 정보를 성공적으로 가져왔습니다! 아래 내용을 확인하고 저장하세요.</span>
              </div>
            )}
          </div>

          {/* Manual Form */}
          <div className="space-y-4">
            {/* API ID */}
            <div>
              <label className="block text-sm font-medium mb-1">
                API ID <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.id}
                onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                placeholder="예: text-classifier"
                className="w-full px-3 py-2 border rounded-lg bg-background"
              />
              {errors.id && <p className="text-sm text-red-500 mt-1">{errors.id}</p>}
              <p className="text-xs text-muted-foreground mt-1">
                영문 소문자, 숫자, 하이픈(-) 사용 가능 (예: text-classifier, ocr-v3)
              </p>
            </div>

            {/* API Name */}
            <div>
              <label className="block text-sm font-medium mb-1">
                API 이름 (코드용) <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="예: textclassifier"
                className="w-full px-3 py-2 border rounded-lg bg-background"
              />
              {errors.name && <p className="text-sm text-red-500 mt-1">{errors.name}</p>}
              <p className="text-xs text-muted-foreground mt-1">
                변수명으로 사용됩니다. 영문, 숫자, 언더스코어(_) 사용 가능
              </p>
            </div>

            {/* Display Name */}
            <div>
              <label className="block text-sm font-medium mb-1">
                표시 이름 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.displayName}
                onChange={(e) => setFormData({ ...formData, displayName: e.target.value })}
                placeholder="예: Text Classifier"
                className="w-full px-3 py-2 border rounded-lg bg-background"
              />
              {errors.displayName && <p className="text-sm text-red-500 mt-1">{errors.displayName}</p>}
              <p className="text-xs text-muted-foreground mt-1">
                UI에 표시될 이름입니다
              </p>
            </div>

            {/* Base URL */}
            <div>
              <label className="block text-sm font-medium mb-1">
                Base URL <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.baseUrl}
                onChange={(e) => setFormData({ ...formData, baseUrl: e.target.value })}
                placeholder="예: http://localhost:5007"
                className="w-full px-3 py-2 border rounded-lg bg-background"
              />
              {errors.baseUrl && <p className="text-sm text-red-500 mt-1">{errors.baseUrl}</p>}
            </div>

            {/* Port */}
            <div>
              <label className="block text-sm font-medium mb-1">
                포트 <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                value={formData.port}
                onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) })}
                min="1024"
                max="65535"
                className="w-full px-3 py-2 border rounded-lg bg-background"
              />
              {errors.port && <p className="text-sm text-red-500 mt-1">{errors.port}</p>}
            </div>

            {/* Icon */}
            <div>
              <label className="block text-sm font-medium mb-2">아이콘</label>
              <div className="grid grid-cols-6 gap-2">
                {ICON_OPTIONS.map(icon => (
                  <button
                    key={icon}
                    onClick={() => setFormData({ ...formData, icon })}
                    className={`p-3 text-2xl border-2 rounded-lg transition-all ${
                      formData.icon === icon
                        ? 'border-primary bg-primary/10'
                        : 'border-border hover:border-primary/50'
                    }`}
                  >
                    {icon}
                  </button>
                ))}
              </div>
            </div>

            {/* Color */}
            <div>
              <label className="block text-sm font-medium mb-2">노드 색상</label>
              <div className="grid grid-cols-5 gap-2">
                {COLOR_OPTIONS.map(color => (
                  <button
                    key={color}
                    onClick={() => setFormData({ ...formData, color })}
                    className={`h-10 rounded-lg border-2 transition-all ${
                      formData.color === color
                        ? 'border-foreground scale-110'
                        : 'border-border hover:scale-105'
                    }`}
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-medium mb-1">카테고리</label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value as APICategory })}
                className="w-full px-3 py-2 border rounded-lg bg-background"
              >
                <option value="detection">🎯 Detection (객체 검출)</option>
                <option value="ocr">📝 OCR (텍스트 인식)</option>
                <option value="segmentation">🎨 Segmentation (영역 분할)</option>
                <option value="preprocessing">🔧 Preprocessing (전처리)</option>
                <option value="analysis">📊 Analysis (분석)</option>
                <option value="ai">🤖 AI (인공지능)</option>
                <option value="knowledge">🧠 Knowledge (지식 엔진)</option>
                <option value="control">⚙️ Control (제어 플로우)</option>
              </select>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium mb-1">
                설명 <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="이 API의 기능을 설명해주세요"
                rows={3}
                className="w-full px-3 py-2 border rounded-lg bg-background"
              />
              {errors.description && <p className="text-sm text-red-500 mt-1">{errors.description}</p>}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 mt-6 pt-6 border-t">
            <Button variant="outline" onClick={handleCancel}>
              취소
            </Button>
            <Button onClick={handleSubmit}>
              <Plus className="w-4 h-4 mr-2" />
              API 추가
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
