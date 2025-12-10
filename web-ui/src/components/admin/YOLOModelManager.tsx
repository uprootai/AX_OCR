/**
 * YOLO Model Manager Component
 *
 * YOLO API의 여러 모델을 관리하는 UI
 * - 모델 목록 조회
 * - 모델 등록/수정/삭제
 * - 모델 파일 업로드
 */
import { useState, useEffect, useCallback } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import {
  RefreshCw,
  Plus,
  Trash2,
  Edit,
  Upload,
  Package,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import axios from 'axios';

interface YOLOModel {
  id: string;
  file: string;
  name: string;
  description: string;
  classes: number;
  best_for?: string;
  file_exists: boolean;
  file_size_mb: number;
  supports_sahi?: boolean;
}

interface ModelsResponse {
  models: YOLOModel[];
  default_model: string;
  total: number;
}

interface YOLOModelManagerProps {
  apiBaseUrl?: string;
}

export function YOLOModelManager({ apiBaseUrl = 'http://localhost:5005' }: YOLOModelManagerProps) {
  const [models, setModels] = useState<YOLOModel[]>([]);
  const [defaultModel, setDefaultModel] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingModel, setEditingModel] = useState<YOLOModel | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  // 모델 목록 가져오기
  const fetchModels = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get<ModelsResponse>(`${apiBaseUrl}/api/v1/models`);
      setModels(response.data.models);
      setDefaultModel(response.data.default_model);
    } catch (err) {
      setError('모델 목록을 가져오는데 실패했습니다.');
      console.error('Failed to fetch models:', err);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  // 모델 삭제
  const handleDelete = async (modelId: string) => {
    if (!confirm(`'${modelId}' 모델을 삭제하시겠습니까?`)) return;

    try {
      await axios.delete(`${apiBaseUrl}/api/v1/models/${modelId}`);
      fetchModels();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      alert(error.response?.data?.detail || '모델 삭제 실패');
    }
  };

  // 모델 업데이트
  const handleUpdate = async (modelId: string, data: Partial<YOLOModel>) => {
    try {
      await axios.post(`${apiBaseUrl}/api/v1/models/${modelId}`, {
        name: data.name,
        description: data.description,
        best_for: data.best_for,
        classes: data.classes,
      });
      setEditingModel(null);
      fetchModels();
    } catch (err) {
      alert('모델 업데이트 실패');
      console.error(err);
    }
  };

  // 파일 업로드
  const handleFileUpload = async (modelId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post(`${apiBaseUrl}/api/v1/models/${modelId}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      fetchModels();
      alert('모델 파일 업로드 완료');
    } catch (err) {
      alert('파일 업로드 실패');
      console.error(err);
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-blue-500" />
          <h3 className="text-lg font-semibold">YOLO 모델 관리</h3>
          <Badge variant="outline">{models.length}개</Badge>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAddForm(true)}
          >
            <Plus className="w-4 h-4 mr-1" />
            모델 추가
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchModels}
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            새로고침
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 mb-4 text-red-600 bg-red-50 dark:bg-red-900/20 rounded-lg">
          {error}
        </div>
      )}

      {/* 모델 목록 */}
      <div className="space-y-4">
        {models.map((model) => (
          <div
            key={model.id}
            className={`p-4 border rounded-lg ${
              model.id === defaultModel
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700'
            }`}
          >
            {editingModel?.id === model.id ? (
              // 편집 모드
              <EditModelForm
                model={editingModel}
                onSave={(data) => handleUpdate(model.id, data)}
                onCancel={() => setEditingModel(null)}
              />
            ) : (
              // 보기 모드
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-sm text-gray-500">{model.id}</span>
                    {model.id === defaultModel && (
                      <Badge variant="default" className="text-xs bg-blue-500 text-white">기본</Badge>
                    )}
                    {model.supports_sahi && (
                      <Badge variant="outline" className="text-xs">SAHI</Badge>
                    )}
                  </div>
                  <h4 className="font-medium">{model.name}</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {model.description}
                  </p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    <span>클래스: {model.classes}개</span>
                    <span>파일: {model.file}</span>
                    <span>{model.file_size_mb}MB</span>
                    {model.file_exists ? (
                      <span className="flex items-center text-green-600">
                        <CheckCircle className="w-3 h-3 mr-1" />
                        파일 존재
                      </span>
                    ) : (
                      <span className="flex items-center text-red-600">
                        <XCircle className="w-3 h-3 mr-1" />
                        파일 없음
                      </span>
                    )}
                  </div>
                  {model.best_for && (
                    <p className="text-xs text-blue-600 mt-1">
                      용도: {model.best_for}
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setEditingModel(model)}
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                  <label className="cursor-pointer inline-flex items-center justify-center h-8 w-8 rounded-md text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-800">
                    <Upload className="w-4 h-4" />
                    <input
                      type="file"
                      accept=".pt"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleFileUpload(model.id, file);
                      }}
                    />
                  </label>
                  {model.id !== defaultModel && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(model.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 모델 추가 폼 */}
      {showAddForm && (
        <AddModelForm
          apiBaseUrl={apiBaseUrl}
          onSuccess={() => {
            setShowAddForm(false);
            fetchModels();
          }}
          onCancel={() => setShowAddForm(false)}
        />
      )}
    </Card>
  );
}

// 모델 편집 폼
function EditModelForm({
  model,
  onSave,
  onCancel,
}: {
  model: YOLOModel;
  onSave: (data: Partial<YOLOModel>) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(model.name);
  const [description, setDescription] = useState(model.description);
  const [bestFor, setBestFor] = useState(model.best_for || '');
  const [classes, setClasses] = useState(model.classes);

  return (
    <div className="space-y-3">
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="모델 이름"
        className="w-full p-2 border rounded"
      />
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="설명"
        className="w-full p-2 border rounded"
        rows={2}
      />
      <input
        type="text"
        value={bestFor}
        onChange={(e) => setBestFor(e.target.value)}
        placeholder="용도 (예: P&ID, 기계도면)"
        className="w-full p-2 border rounded"
      />
      <input
        type="number"
        value={classes}
        onChange={(e) => setClasses(parseInt(e.target.value) || 0)}
        placeholder="클래스 개수"
        className="w-32 p-2 border rounded"
      />
      <div className="flex gap-2">
        <Button size="sm" onClick={() => onSave({ name, description, best_for: bestFor, classes })}>
          저장
        </Button>
        <Button variant="outline" size="sm" onClick={onCancel}>
          취소
        </Button>
      </div>
    </div>
  );
}

// 모델 추가 폼
function AddModelForm({
  apiBaseUrl,
  onSuccess,
  onCancel,
}: {
  apiBaseUrl: string;
  onSuccess: () => void;
  onCancel: () => void;
}) {
  const [modelId, setModelId] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [bestFor, setBestFor] = useState('');
  const [classes, setClasses] = useState(1);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!modelId || !name || !file) {
      alert('모델 ID, 이름, 파일은 필수입니다.');
      return;
    }

    setLoading(true);
    try {
      // 1. 모델 정보 등록
      await axios.post(`${apiBaseUrl}/api/v1/models/${modelId}`, {
        name,
        description,
        best_for: bestFor,
        classes,
        file: `${modelId}.pt`,
      });

      // 2. 파일 업로드
      const formData = new FormData();
      formData.append('file', file);
      await axios.post(`${apiBaseUrl}/api/v1/models/${modelId}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      onSuccess();
    } catch (err) {
      alert('모델 추가 실패');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-4 p-4 border rounded-lg bg-gray-50 dark:bg-gray-800">
      <h4 className="font-medium mb-3">새 모델 추가</h4>
      <div className="space-y-3">
        <input
          type="text"
          value={modelId}
          onChange={(e) => setModelId(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '_'))}
          placeholder="모델 ID (영문, 숫자, _ 만)"
          className="w-full p-2 border rounded"
        />
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="모델 이름"
          className="w-full p-2 border rounded"
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="설명"
          className="w-full p-2 border rounded"
          rows={2}
        />
        <input
          type="text"
          value={bestFor}
          onChange={(e) => setBestFor(e.target.value)}
          placeholder="용도"
          className="w-full p-2 border rounded"
        />
        <input
          type="number"
          value={classes}
          onChange={(e) => setClasses(parseInt(e.target.value) || 1)}
          placeholder="클래스 개수"
          className="w-32 p-2 border rounded"
        />
        <div>
          <label className="block text-sm mb-1">모델 파일 (.pt)</label>
          <input
            type="file"
            accept=".pt"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full p-2 border rounded"
          />
          {file && <span className="text-xs text-gray-500">{file.name} ({(file.size / 1024 / 1024).toFixed(1)}MB)</span>}
        </div>
        <div className="flex gap-2">
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? '추가 중...' : '추가'}
          </Button>
          <Button variant="outline" onClick={onCancel}>
            취소
          </Button>
        </div>
      </div>
    </div>
  );
}

export default YOLOModelManager;
