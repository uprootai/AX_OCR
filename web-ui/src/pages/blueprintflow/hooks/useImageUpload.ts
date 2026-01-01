/**
 * useImageUpload Hook
 * 이미지 업로드 및 샘플 선택 로직
 */

import { useRef, useCallback } from 'react';
import { useWorkflowStore } from '../../../store/workflowStore';

interface UseImageUploadOptions {
  onShowToast?: (message: string, type: 'success' | 'error' | 'warning' | 'info') => void;
}

export function useImageUpload(options: UseImageUploadOptions = {}) {
  const { onShowToast } = options;
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadedImage = useWorkflowStore((state) => state.uploadedImage);
  const uploadedFileName = useWorkflowStore((state) => state.uploadedFileName);
  const setUploadedImage = useWorkflowStore((state) => state.setUploadedImage);

  // Handle file input change event
  const handleImageUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      onShowToast?.('⚠️ 이미지 파일만 업로드 가능합니다', 'warning');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target?.result as string;
      setUploadedImage(base64, file.name);
    };
    reader.readAsDataURL(file);
  }, [setUploadedImage, onShowToast]);

  // Handle file selection (from upload or sample selection)
  const handleFileSelect = useCallback((file: File | null) => {
    if (!file) {
      setUploadedImage(null, null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      return;
    }

    if (!file.type.startsWith('image/')) {
      onShowToast?.('⚠️ 이미지 파일만 업로드 가능합니다', 'warning');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target?.result as string;
      setUploadedImage(base64, file.name);
    };
    reader.readAsDataURL(file);
  }, [setUploadedImage, onShowToast]);

  // Remove uploaded image
  const handleRemoveImage = useCallback(() => {
    setUploadedImage(null, null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [setUploadedImage]);

  // Trigger file input click
  const triggerFileInput = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  // Load sample image
  const loadSampleImage = useCallback(async (samplePath: string) => {
    try {
      const response = await fetch(samplePath);
      const blob = await response.blob();
      const filename = samplePath.split('/').pop() || 'sample.jpg';
      const file = new File([blob], filename, { type: 'image/jpeg' });
      handleFileSelect(file);
    } catch (error) {
      console.error('Failed to load sample image:', error);
      onShowToast?.('✗ 샘플 이미지 로드 실패', 'error');
    }
  }, [handleFileSelect, onShowToast]);

  return {
    fileInputRef,
    uploadedImage,
    uploadedFileName,
    handleImageUpload,
    handleFileSelect,
    handleRemoveImage,
    triggerFileInput,
    loadSampleImage,
  };
}
