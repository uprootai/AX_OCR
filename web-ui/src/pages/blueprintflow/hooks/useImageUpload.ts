/**
 * useImageUpload Hook
 * 이미지 업로드 및 샘플 선택 로직
 */

import { useRef, useCallback } from 'react';
import { useWorkflowStore } from '../../../store/workflowStore';

export function useImageUpload() {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadedImage = useWorkflowStore((state) => state.uploadedImage);
  const uploadedFileName = useWorkflowStore((state) => state.uploadedFileName);
  const setUploadedImage = useWorkflowStore((state) => state.setUploadedImage);

  // Handle file input change event
  const handleImageUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target?.result as string;
      setUploadedImage(base64, file.name);
    };
    reader.readAsDataURL(file);
  }, [setUploadedImage]);

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
      alert('Please upload an image file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target?.result as string;
      setUploadedImage(base64, file.name);
    };
    reader.readAsDataURL(file);
  }, [setUploadedImage]);

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
      alert('Failed to load sample image');
    }
  }, [handleFileSelect]);

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
