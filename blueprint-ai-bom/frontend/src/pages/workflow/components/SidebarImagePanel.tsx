/**
 * Sidebar Image Panel - 세션 이미지 목록, 다중 선택, 페이지네이션, GT 업로드
 */

import React, { useRef, useState, useCallback, useEffect } from 'react';
import {
  Loader2,
  ChevronRight,
  ChevronDown,
  Upload,
  ImagePlus,
  Images,
  FileArchive,
  CheckCircle,
  CheckSquare,
  Square,
  ChevronsLeft,
  ChevronsRight,
  ChevronLeft,
  RefreshCw,
  Link2,
} from 'lucide-react';
import { sessionApi, testImagesApi } from '../../../lib/api';
import type { TestImage } from '../../../lib/api';
import { API_BASE_URL } from '../../../lib/constants';
import type { SessionImage } from '../../../types';

// 샘플 이미지 카테고리 분류
const categorizeSample = (filename: string): string => {
  const l = filename.toLowerCase();
  if (/pid|mcp|panel|bwms/.test(l)) return 'P&ID';
  if (/bom|bearing|dse|table|shaft|interm/.test(l)) return 'BOM/기계';
  return '일반';
};

// 파일명 → 읽기 쉬운 레이블
const SAMPLE_LABELS: Record<string, string> = {
  'sample7_mcp_panel_body.jpg': 'MCP Panel Body',
  'bwms_pid_sample.png': 'BWMS P&ID',
  'sample6_pid_diagram.png': 'P&ID Diagram',
  '-MCP_1_PANEL BODY_1-page-001.jpg': 'MCP Panel Body (GT)',
  'dse_bearing_assy_t1.png': 'DSE 베어링 조립도',
  'dse_thrust_bearing_assy.png': 'DSE 스러스트 베어링',
  'sample2_interm_shaft.jpg': '중간축 도면',
  'sample3_s60me_shaft.jpg': 'S60ME 축 도면',
  'sample8_blueprint_31.jpg': 'Blueprint #31',
  'img_00031.jpg': 'Blueprint #31 (alt)',
  'img_00035.jpg': 'Blueprint #35 (alt)',
};

// 페이지네이션 상수
const IMAGES_PER_PAGE = 20;

// 이미지 + GT 상태
export interface ImageWithGT extends SessionImage {
  has_gt?: boolean;
  gt_filename?: string;
}

interface SidebarImagePanelProps {
  currentSession: {
    session_id: string;
    filename: string;
  } | null;
  effectiveDrawingType?: string;
  onImageSelect?: (imageId: string, image: SessionImage) => void;
  onImagesSelect?: (imageIds: string[], images: SessionImage[]) => void;
  onImagesAdded?: () => void;
  onUploadGT?: (imageId: string, file: File) => Promise<void>;
  onLoadSession: (sessionId: string) => void;
}

export function SidebarImagePanel({
  currentSession,
  onImageSelect,
  onImagesSelect,
  onImagesAdded,
  onUploadGT,
  onLoadSession,
}: SidebarImagePanelProps) {
  const imageUploadRef = useRef<HTMLInputElement>(null);
  const gtUploadRef = useRef<HTMLInputElement>(null);

  const [images, setImages] = useState<ImageWithGT[]>([]);
  const [selectedImageId, setSelectedImageId] = useState<string | null>(null);
  const [selectedImageIds, setSelectedImageIds] = useState<Set<string>>(new Set());
  const [isMultiSelectMode, setIsMultiSelectMode] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [isLoadingImages, setIsLoadingImages] = useState(false);
  const [imageError, setImageError] = useState<string | null>(null);
  const [showImageReview, setShowImageReview] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploadingImages, setIsUploadingImages] = useState(false);
  const [isLoadingTestImage, setIsLoadingTestImage] = useState(false);
  const [sampleImages, setSampleImages] = useState<TestImage[]>([]);
  const [uploadingGTFor, setUploadingGTFor] = useState<string | null>(null);

  // 이미지 목록 로드 (메인 이미지 포함)
  const loadImageData = useCallback(async () => {
    if (!currentSession) return;
    setIsLoadingImages(true);
    setImageError(null);
    try {
      const imageList = await sessionApi.listImages(currentSession.session_id);

      const mainImage: ImageWithGT = {
        image_id: 'main',
        filename: currentSession.filename,
        file_path: '',
        review_status: 'processed',
        detections: [],
        detection_count: 0,
        verified_count: 0,
        approved_count: 0,
        rejected_count: 0,
        order_index: 0,
        has_gt: false,
      };

      const imagesWithGT: ImageWithGT[] = imageList.map(img => ({
        ...img,
        has_gt: (img as ImageWithGT).has_gt || false,
        gt_filename: (img as ImageWithGT).gt_filename,
      }));

      setImages([mainImage, ...imagesWithGT]);
    } catch (err) {
      console.error('Failed to load images:', err);
      setImageError('이미지 목록 로드 실패');
    } finally {
      setIsLoadingImages(false);
    }
  }, [currentSession]);

  // GT 파일 업로드 핸들러
  const handleGTUpload = useCallback(async (imageId: string, file: File) => {
    if (!onUploadGT) return;
    setUploadingGTFor(imageId);
    try {
      await onUploadGT(imageId, file);
      setImages(prev => prev.map(img =>
        img.image_id === imageId
          ? { ...img, has_gt: true, gt_filename: file.name }
          : img
      ));
    } catch (err) {
      console.error('GT upload failed:', err);
      alert('GT 파일 업로드에 실패했습니다.');
    } finally {
      setUploadingGTFor(null);
      if (gtUploadRef.current) {
        gtUploadRef.current.value = '';
      }
    }
  }, [onUploadGT]);

  const handleGTFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>, imageId: string) => {
    const file = e.target.files?.[0];
    if (file) {
      handleGTUpload(imageId, file);
    }
  }, [handleGTUpload]);

  // 이미지 업로드 핸들러 (일반 이미지 + ZIP 지원)
  const handleImageUpload = useCallback(async (files: FileList | File[]) => {
    if (!currentSession || files.length === 0) return;

    setIsUploadingImages(true);
    try {
      const formData = new FormData();
      Array.from(files).forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch(
        `${API_BASE_URL}/sessions/${currentSession.session_id}/images/bulk-upload`,
        { method: 'POST', body: formData }
      );

      if (!response.ok) throw new Error('Upload failed');

      const result = await response.json();
      console.log('Images uploaded:', result);
      onImagesAdded?.();
      await loadImageData();
    } catch (error) {
      console.error('Image upload failed:', error);
      alert('이미지 업로드에 실패했습니다.');
    } finally {
      setIsUploadingImages(false);
      if (imageUploadRef.current) {
        imageUploadRef.current.value = '';
      }
    }
  }, [currentSession, onImagesAdded, loadImageData]);

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) handleImageUpload(files);
  }, [handleImageUpload]);

  // 드래그 앤 드롭
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation(); setIsDragging(true);
  }, []);
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation(); setIsDragging(false);
  }, []);
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation(); setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) handleImageUpload(files);
  }, [handleImageUpload]);

  // 세션 변경 시 이미지 로드
  useEffect(() => {
    if (currentSession) {
      loadImageData();
    } else {
      setImages([]); setSelectedImageId(null);
    }
  }, [currentSession?.session_id, loadImageData]);

  // 페이지네이션 계산
  const totalPages = Math.ceil(images.length / IMAGES_PER_PAGE);
  const paginatedImages = images.slice(
    (currentPage - 1) * IMAGES_PER_PAGE,
    currentPage * IMAGES_PER_PAGE
  );

  useEffect(() => {
    if (currentPage > totalPages && totalPages > 0) setCurrentPage(totalPages);
  }, [totalPages, currentPage]);

  // 이미지 선택 핸들러
  const handleSelectImage = (imageId: string) => {
    if (isMultiSelectMode) {
      setSelectedImageIds(prev => {
        const newSet = new Set(prev);
        if (newSet.has(imageId)) { newSet.delete(imageId); } else { newSet.add(imageId); }
        const selectedImages = images.filter(img => newSet.has(img.image_id));
        onImagesSelect?.(Array.from(newSet), selectedImages);
        return newSet;
      });
    } else {
      setSelectedImageId(imageId);
      const image = images.find((img) => img.image_id === imageId);
      if (image) onImageSelect?.(imageId, image);
    }
  };

  const handleSelectAll = () => {
    const allIds = new Set(images.map(img => img.image_id));
    setSelectedImageIds(allIds);
    onImagesSelect?.(Array.from(allIds), images);
  };

  const handleDeselectAll = () => {
    setSelectedImageIds(new Set());
    onImagesSelect?.([], []);
  };

  const handleSelectCurrentPage = () => {
    setSelectedImageIds(prev => {
      const newSet = new Set(prev);
      paginatedImages.forEach(img => newSet.add(img.image_id));
      const selectedImages = images.filter(img => newSet.has(img.image_id));
      onImagesSelect?.(Array.from(newSet), selectedImages);
      return newSet;
    });
  };

  const toggleMultiSelectMode = () => {
    setIsMultiSelectMode(prev => !prev);
    if (isMultiSelectMode) {
      setSelectedImageIds(new Set());
      onImagesSelect?.([], []);
    }
  };

  // 샘플 이미지 목록 로드 (마운트 시 1회)
  useEffect(() => {
    testImagesApi.list()
      .then(res => setSampleImages(res.images))
      .catch(err => console.error('Failed to load sample list:', err));
  }, []);

  // 샘플 이미지 선택 핸들러
  const handleSampleSelect = useCallback(async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const filename = e.target.value;
    if (!filename) return;
    setIsLoadingTestImage(true);
    try {
      const result = await testImagesApi.load(filename, currentSession?.session_id);
      onLoadSession(result.session_id);
    } catch (error) {
      console.error('Failed to load sample image:', error);
      alert('샘플 이미지 로드에 실패했습니다.');
    } finally {
      setIsLoadingTestImage(false);
      e.target.value = '';
    }
  }, [currentSession?.session_id, onLoadSession]);

  if (!currentSession) return null;

  return (
    <div className="mt-3 border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden">
      {/* GT 파일 업로드용 hidden input */}
      <input
        ref={gtUploadRef}
        type="file"
        accept=".txt,.json,.xml"
        onChange={(e) => uploadingGTFor && handleGTFileSelect(e, uploadingGTFor)}
        className="hidden"
      />

      {/* 헤더 */}
      <div
        className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
        onClick={() => setShowImageReview(!showImageReview)}
        title="클릭하여 이미지 목록 펼치기/접기"
      >
        <span className="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300">
          <Images className="w-4 h-4" />
          <span>세션 이미지</span>
          <span className="text-xs px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded-full">
            {images.length}
          </span>
        </span>
        <div className="flex items-center space-x-1">
          <button
            onClick={(e) => { e.stopPropagation(); loadImageData(); }}
            disabled={isLoadingImages}
            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-500 rounded"
            title="이미지 목록 새로고침"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-gray-500 ${isLoadingImages ? 'animate-spin' : ''}`} />
          </button>
          {showImageReview ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </div>
      </div>

      {showImageReview && (
        <div className="p-2 space-y-2">
          {imageError && (
            <p className="text-xs text-red-500 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded">{imageError}</p>
          )}

          {/* 다중 선택 컨트롤 */}
          {images.length > 1 && (
            <div className="flex items-center justify-between gap-1 pb-1 border-b border-gray-100 dark:border-gray-700">
              <button
                onClick={toggleMultiSelectMode}
                className={`flex items-center space-x-1 px-2 py-1 rounded text-[10px] transition-colors ${
                  isMultiSelectMode
                    ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                title="다중 선택 모드 토글"
              >
                {isMultiSelectMode ? <CheckSquare className="w-3 h-3" /> : <Square className="w-3 h-3" />}
                <span>다중 선택</span>
              </button>

              {isMultiSelectMode && (
                <div className="flex items-center gap-1">
                  <button onClick={handleSelectAll} className="px-1.5 py-0.5 text-[9px] bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 rounded hover:bg-green-200 dark:hover:bg-green-900" title="전체 선택">전체</button>
                  <button onClick={handleSelectCurrentPage} className="px-1.5 py-0.5 text-[9px] bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-900" title="현재 페이지 선택">페이지</button>
                  <button onClick={handleDeselectAll} className="px-1.5 py-0.5 text-[9px] bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded hover:bg-gray-200 dark:hover:bg-gray-600" title="선택 해제">해제</button>
                </div>
              )}

              {isMultiSelectMode && selectedImageIds.size > 0 && (
                <span className="text-[9px] text-blue-600 dark:text-blue-400 font-medium">
                  {selectedImageIds.size}개
                </span>
              )}
            </div>
          )}

          {/* 이미지 목록 */}
          {isLoadingImages && images.length === 0 ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
            </div>
          ) : images.length === 0 ? (
            <div className="text-center py-3 text-gray-400">
              <Images className="w-6 h-6 mx-auto mb-1 opacity-50" />
              <p className="text-xs">이미지가 없습니다</p>
              <p className="text-[10px] mt-0.5">아래에서 이미지/ZIP을 추가하세요</p>
            </div>
          ) : (
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {paginatedImages.map((image, index) => {
                const globalIndex = (currentPage - 1) * IMAGES_PER_PAGE + index;
                const isMainImage = image.image_id === 'main';
                const isSelected = isMultiSelectMode
                  ? selectedImageIds.has(image.image_id)
                  : selectedImageId === image.image_id || (selectedImageId === null && isMainImage);
                return (
                  <div
                    key={image.image_id}
                    className={`flex items-center space-x-2 p-2 rounded-lg cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-blue-100 dark:bg-blue-900/40 border-2 border-blue-400 shadow-sm'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700 border-2 border-transparent'
                    }`}
                    onClick={() => handleSelectImage(image.image_id)}
                    title={isMainImage
                      ? '세션 생성 시 업로드된 원본 이미지입니다'
                      : `클릭하여 "${image.filename}" 이미지를 ${isMultiSelectMode ? '선택/해제' : '메인 화면에서 검토'}합니다`}
                  >
                    {/* 체크박스 / 인덱스 */}
                    {isMultiSelectMode ? (
                      <div className={`w-5 h-5 flex items-center justify-center rounded border-2 transition-colors ${
                        isSelected
                          ? 'bg-blue-500 border-blue-500 text-white'
                          : 'border-gray-300 dark:border-gray-500 bg-white dark:bg-gray-700'
                      }`}>
                        {isSelected && <CheckCircle className="w-3.5 h-3.5" />}
                      </div>
                    ) : isMainImage ? (
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                        isSelected ? 'bg-green-500 text-white' : 'bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300'
                      }`}>원본</span>
                    ) : (
                      <span className={`w-5 h-5 flex items-center justify-center rounded-full text-[10px] font-bold ${
                        isSelected ? 'bg-blue-500 text-white' : 'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300'
                      }`}>{globalIndex}</span>
                    )}
                    {/* 썸네일 */}
                    <div className="w-8 h-8 rounded bg-gray-200 dark:bg-gray-600 overflow-hidden flex-shrink-0">
                      {image.thumbnail_base64 ? (
                        <img src={`data:image/jpeg;base64,${image.thumbnail_base64}`} alt={image.filename} className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Images className="w-3 h-3 text-gray-400" />
                        </div>
                      )}
                    </div>
                    {/* 파일명 */}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">{image.filename}</p>
                      <div className="flex items-center gap-1 text-[10px]">
                        {image.detection_count > 0 && (
                          <span className="text-gray-400">{image.detection_count}개</span>
                        )}
                        {(image as ImageWithGT).has_gt ? (
                          <span className="flex items-center gap-0.5 px-1.5 py-0.5 bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400 rounded" title={`GT: ${(image as ImageWithGT).gt_filename}`}>
                            <Link2 className="w-3 h-3" />GT
                          </span>
                        ) : (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setUploadingGTFor(image.image_id);
                              gtUploadRef.current?.click();
                            }}
                            disabled={uploadingGTFor === image.image_id}
                            className="flex items-center gap-0.5 px-1.5 py-0.5 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 hover:bg-orange-200 dark:hover:bg-orange-900/50 rounded transition-colors"
                            title="GT 라벨 업로드 (.txt, .json, .xml)"
                          >
                            {uploadingGTFor === image.image_id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Upload className="w-3 h-3" />}GT
                          </button>
                        )}
                      </div>
                    </div>
                    {!isMultiSelectMode && isSelected && (
                      <CheckCircle className="w-4 h-4 text-blue-500 flex-shrink-0" />
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* 페이지네이션 */}
          {images.length > IMAGES_PER_PAGE && (
            <div className="flex items-center justify-between pt-2 border-t border-gray-100 dark:border-gray-700">
              <button onClick={() => setCurrentPage(1)} disabled={currentPage === 1} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed" title="첫 페이지">
                <ChevronsLeft className="w-3.5 h-3.5 text-gray-500" />
              </button>
              <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed" title="이전 페이지">
                <ChevronLeft className="w-3.5 h-3.5 text-gray-500" />
              </button>
              <div className="flex items-center space-x-1">
                <input type="number" min={1} max={totalPages} value={currentPage}
                  onChange={(e) => { setCurrentPage(Math.max(1, Math.min(totalPages, parseInt(e.target.value) || 1))); }}
                  className="w-8 h-5 text-center text-[10px] border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                />
                <span className="text-[10px] text-gray-500">/ {totalPages}</span>
              </div>
              <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed" title="다음 페이지">
                <ChevronRight className="w-3.5 h-3.5 text-gray-500" />
              </button>
              <button onClick={() => setCurrentPage(totalPages)} disabled={currentPage === totalPages} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed" title="마지막 페이지">
                <ChevronsRight className="w-3.5 h-3.5 text-gray-500" />
              </button>
            </div>
          )}

          {/* 이미지 추가 영역 */}
          <div
            className={`p-2 rounded border-2 border-dashed transition-colors ${
              isDragging
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-300 dark:border-gray-600 hover:border-blue-400'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <button
              onClick={() => imageUploadRef.current?.click()}
              disabled={isUploadingImages}
              className="w-full flex items-center justify-center space-x-2 px-2 py-1.5 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded text-xs disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="이미지 또는 ZIP 파일을 업로드하여 세션에 추가합니다"
            >
              {isUploadingImages ? (
                <><Loader2 className="w-3.5 h-3.5 animate-spin" /><span>업로드 중...</span></>
              ) : (
                <><ImagePlus className="w-3.5 h-3.5" /><span>이미지 추가</span></>
              )}
            </button>
            <p className="mt-1 text-[9px] text-center text-gray-400">
              <FileArchive className="w-2.5 h-2.5 inline mr-0.5" />
              드래그 앤 드롭 (이미지/ZIP)
            </p>
            {/* 샘플 이미지 선택 */}
            {sampleImages.length > 0 && (
              <div className="relative mt-2">
                {isLoadingTestImage && (
                  <div className="absolute inset-0 flex items-center justify-center bg-white/60 dark:bg-gray-800/60 rounded z-10">
                    <Loader2 className="w-4 h-4 text-orange-500 animate-spin" />
                  </div>
                )}
                <select
                  onChange={handleSampleSelect}
                  disabled={isLoadingTestImage}
                  className="w-full px-2 py-1 text-[10px] bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-300 border border-orange-200 dark:border-orange-800 rounded cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-colors hover:bg-orange-100 dark:hover:bg-orange-900/40"
                  title="테스트용 샘플 이미지를 선택하여 새 세션을 생성합니다"
                  defaultValue=""
                >
                  <option value="">샘플 이미지 선택...</option>
                  {(['P&ID', 'BOM/기계', '일반'] as const).map(category => {
                    const items = sampleImages.filter(img => categorizeSample(img.filename) === category);
                    if (items.length === 0) return null;
                    return (
                      <optgroup key={category} label={category === 'P&ID' ? '\uD83D\uDD27 P&ID' : category === 'BOM/기계' ? '\uD83D\uDCCA BOM/기계' : '\uD83D\uDCD0 일반'}>
                        {items.map(img => (
                          <option key={img.filename} value={img.filename}>
                            {SAMPLE_LABELS[img.filename] || img.filename}
                          </option>
                        ))}
                      </optgroup>
                    );
                  })}
                </select>
              </div>
            )}
            <input ref={imageUploadRef} type="file" accept="image/*,.zip" multiple onChange={handleFileSelect} className="hidden" />
          </div>
        </div>
      )}
    </div>
  );
}
