import { useState } from 'react';
import { useAPIConfigStore, type APIConfig } from '../../../store/apiConfigStore';
import type { FormData, APIMetadata } from './types';
import { DEFAULT_FORM_DATA } from './types';

const DEFAULT_METADATA: APIMetadata = {
  inputs: [],
  outputs: [],
  parameters: [],
};

export function useAddAPIForm(onClose: () => void) {
  const { addAPI, customAPIs } = useAPIConfigStore();

  const [formData, setFormData] = useState<FormData>(DEFAULT_FORM_DATA);
  const [apiMetadata, setApiMetadata] = useState<APIMetadata>(DEFAULT_METADATA);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [searchUrl, setSearchUrl] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchSuccess, setSearchSuccess] = useState(false);
  const [searchError, setSearchError] = useState('');

  const resetForm = () => {
    setFormData(DEFAULT_FORM_DATA);
    setErrors({});
  };

  /**
   * API 자동 검색 - /api/v1/info 엔드포인트에서 메타데이터 가져오기
   */
  const handleAutoDiscover = async () => {
    if (!searchUrl) {
      setSearchError('URL을 입력해주세요');
      return;
    }

    if (!/^https?:\/\/.+/.test(searchUrl)) {
      setSearchError('올바른 URL 형식이 아닙니다 (http:// 또는 https://로 시작)');
      return;
    }

    setIsSearching(true);
    setSearchError('');
    setSearchSuccess(false);

    try {
      const infoUrl = `${searchUrl}/api/v1/info`;
      const response = await fetch(infoUrl);

      if (!response.ok) {
        throw new Error(`API 정보를 가져올 수 없습니다 (HTTP ${response.status})`);
      }

      const apiInfo = await response.json();

      const urlObj = new URL(searchUrl);
      const port = parseInt(urlObj.port) || (urlObj.protocol === 'https:' ? 443 : 80);

      setFormData({
        id: apiInfo.id || '',
        name: apiInfo.name || '',
        displayName: apiInfo.display_name || apiInfo.displayName || '',
        baseUrl: searchUrl,
        port: port,
        icon: apiInfo.icon || apiInfo.blueprintflow?.icon || '🏷️',
        color: apiInfo.color || apiInfo.blueprintflow?.color || '#a855f7',
        category: apiInfo.category || apiInfo.blueprintflow?.category || 'ocr',
        description: apiInfo.description || '',
        enabled: true,
      });

      setApiMetadata({
        inputs: apiInfo.inputs || [],
        outputs: apiInfo.outputs || [],
        parameters: apiInfo.parameters || [],
        outputMappings: apiInfo.output_mappings || {},
        inputMappings: apiInfo.input_mappings || {},
        endpoint: apiInfo.endpoint || '/api/v1/process',
        method: apiInfo.method || 'POST',
        requiresImage: apiInfo.requires_image ?? true,
      });

      setSearchSuccess(true);
      setSearchError('');
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : 'API 정보를 가져오는데 실패했습니다');
      setSearchSuccess(false);
    } finally {
      setIsSearching(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.id) {
      newErrors.id = 'API ID는 필수입니다';
    } else if (!/^[a-z0-9-]+$/.test(formData.id)) {
      newErrors.id = 'API ID는 영문 소문자, 숫자, 하이픈(-)만 사용 가능합니다';
    } else if (customAPIs.find(api => api.id === formData.id)) {
      newErrors.id = '이미 존재하는 API ID입니다';
    }

    if (!formData.name) {
      newErrors.name = 'API 이름은 필수입니다';
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.name)) {
      newErrors.name = 'API 이름은 영문, 숫자, 언더스코어(_)만 사용 가능합니다';
    }

    if (!formData.displayName) {
      newErrors.displayName = '표시 이름은 필수입니다';
    }

    if (!formData.baseUrl) {
      newErrors.baseUrl = 'Base URL은 필수입니다';
    } else if (!/^https?:\/\/.+/.test(formData.baseUrl)) {
      newErrors.baseUrl = 'URL 형식이 올바르지 않습니다 (http:// 또는 https://로 시작)';
    }

    if (formData.port < 1024 || formData.port > 65535) {
      newErrors.port = '포트는 1024~65535 범위여야 합니다';
    }

    if (!formData.description) {
      newErrors.description = '설명은 필수입니다';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validateForm()) return;

    const newAPI: APIConfig = {
      ...formData,
      inputs: apiMetadata.inputs.length > 0
        ? apiMetadata.inputs.map(i => ({ ...i, description: i.description || '' }))
        : [{ name: 'input', type: 'any', description: '📥 입력 데이터' }],
      outputs: apiMetadata.outputs.length > 0
        ? apiMetadata.outputs.map(o => ({ ...o, description: o.description || '' }))
        : [{ name: 'output', type: 'any', description: '📤 출력 데이터' }],
      parameters: (apiMetadata.parameters || []).map(p => ({
        name: p.name,
        type: (p.type || 'string') as 'string' | 'number' | 'boolean' | 'select',
        default: p.default ?? '',
        description: '',
      })),
      endpoint: apiMetadata.endpoint,
      method: apiMetadata.method,
      requiresImage: apiMetadata.requiresImage,
      outputMappings: apiMetadata.outputMappings,
      inputMappings: apiMetadata.inputMappings,
    };

    addAPI(newAPI);
    resetForm();
    onClose();
  };

  const handleCancel = () => {
    resetForm();
    onClose();
  };

  return {
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
  };
}
