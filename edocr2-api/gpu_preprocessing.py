#!/usr/bin/env python3
"""
eDOCr2 GPU 전처리 모듈

GPU 가속 이미지 전처리:
- CLAHE (대비 향상)
- Gaussian 노이즈 제거
- Adaptive Thresholding (이진화)
- GPU 메모리 효율적 관리

VRAM 예상 사용량: ~3.5 GB (4K 이미지 기준)
"""

import numpy as np
import cv2
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# GPU 사용 가능 여부 확인
GPU_AVAILABLE = False
try:
    import cupy as cp
    import cupyx.scipy.ndimage as cupy_ndimage
    GPU_AVAILABLE = True
    logger.info("✅ GPU preprocessing enabled (cuPy)")
except ImportError:
    logger.warning("⚠️  cuPy not available, falling back to CPU preprocessing")
    cp = None


class GPUImagePreprocessor:
    """GPU 가속 이미지 전처리기"""

    def __init__(self, use_gpu: bool = True):
        """
        Args:
            use_gpu: GPU 사용 여부 (기본값: True)
        """
        self.use_gpu = use_gpu and GPU_AVAILABLE

        if self.use_gpu:
            logger.info("🚀 GPU 전처리 모드 활성화")
            # GPU 메모리 풀 초기화
            self.mempool = cp.get_default_memory_pool()
            self.pinned_mempool = cp.get_default_pinned_memory_pool()
        else:
            logger.info("💻 CPU 전처리 모드")

    def get_gpu_memory_usage(self) -> dict:
        """GPU 메모리 사용량 반환"""
        if not self.use_gpu:
            return {"used_bytes": 0, "total_bytes": 0}

        return {
            "used_bytes": self.mempool.used_bytes(),
            "total_bytes": self.mempool.total_bytes()
        }

    def clear_gpu_memory(self):
        """GPU 메모리 풀 정리"""
        if self.use_gpu:
            self.mempool.free_all_blocks()
            self.pinned_mempool.free_all_blocks()
            logger.debug("🧹 GPU 메모리 정리 완료")

    def apply_clahe_gpu(self, image: np.ndarray, clip_limit: float = 2.0,
                        tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
        """
        GPU 가속 CLAHE (대비 향상)

        Args:
            image: 입력 이미지 (grayscale)
            clip_limit: 대비 제한 값 (기본값: 2.0)
            tile_grid_size: 타일 크기 (기본값: 8x8)

        Returns:
            대비가 향상된 이미지
        """
        if not self.use_gpu:
            # CPU fallback
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            return clahe.apply(image)

        # GPU CLAHE
        # cuPy에는 CLAHE가 없으므로 OpenCV로 처리
        # (CLAHE는 복잡한 히스토그램 연산이 필요하여 GPU 이점이 적음)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        return clahe.apply(image)

    def apply_gaussian_blur_gpu(self, image: np.ndarray,
                                kernel_size: int = 5,
                                sigma: float = 1.0) -> np.ndarray:
        """
        GPU 가속 Gaussian Blur (노이즈 제거)

        Args:
            image: 입력 이미지
            kernel_size: 커널 크기 (기본값: 5)
            sigma: Gaussian sigma 값 (기본값: 1.0)

        Returns:
            블러 처리된 이미지
        """
        if not self.use_gpu:
            # CPU fallback
            return cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)

        # GPU Gaussian Blur
        img_gpu = cp.asarray(image)
        blurred_gpu = cupy_ndimage.gaussian_filter(img_gpu, sigma=sigma)
        result = cp.asnumpy(blurred_gpu)

        # 메모리 정리
        del img_gpu, blurred_gpu

        return result

    def apply_adaptive_threshold_gpu(self, image: np.ndarray,
                                     block_size: int = 11,
                                     C: float = 2.0) -> np.ndarray:
        """
        GPU 가속 Adaptive Thresholding (이진화)

        Args:
            image: 입력 이미지 (grayscale)
            block_size: 블록 크기 (기본값: 11, 홀수여야 함)
            C: 상수 (기본값: 2.0)

        Returns:
            이진화된 이미지
        """
        if not self.use_gpu:
            # CPU fallback
            return cv2.adaptiveThreshold(
                image, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                block_size, C
            )

        # GPU Adaptive Threshold (cuPy 구현)
        img_gpu = cp.asarray(image, dtype=cp.float32)

        # Gaussian 평균 계산
        mean_gpu = cupy_ndimage.uniform_filter(img_gpu, size=block_size)

        # Threshold 적용
        threshold_gpu = mean_gpu - C
        binary_gpu = cp.where(img_gpu > threshold_gpu, 255, 0).astype(cp.uint8)

        result = cp.asnumpy(binary_gpu)

        # 메모리 정리
        del img_gpu, mean_gpu, threshold_gpu, binary_gpu

        return result

    def preprocess_pipeline(self, image: np.ndarray,
                           apply_clahe: bool = True,
                           apply_blur: bool = True,
                           apply_threshold: bool = True,
                           clahe_params: Optional[dict] = None,
                           blur_params: Optional[dict] = None,
                           threshold_params: Optional[dict] = None) -> np.ndarray:
        """
        전체 전처리 파이프라인

        Args:
            image: 입력 이미지 (grayscale or BGR)
            apply_clahe: CLAHE 적용 여부
            apply_blur: Gaussian Blur 적용 여부
            apply_threshold: Adaptive Threshold 적용 여부
            clahe_params: CLAHE 파라미터
            blur_params: Blur 파라미터
            threshold_params: Threshold 파라미터

        Returns:
            전처리된 이미지
        """
        # 기본 파라미터
        clahe_params = clahe_params or {}
        blur_params = blur_params or {}
        threshold_params = threshold_params or {}

        # Grayscale 변환
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        processed = gray

        # 1. CLAHE (대비 향상)
        if apply_clahe:
            processed = self.apply_clahe_gpu(processed, **clahe_params)
            logger.debug("✓ CLAHE 적용")

        # 2. Gaussian Blur (노이즈 제거)
        if apply_blur:
            processed = self.apply_gaussian_blur_gpu(processed, **blur_params)
            logger.debug("✓ Gaussian Blur 적용")

        # 3. Adaptive Threshold (이진화)
        if apply_threshold:
            processed = self.apply_adaptive_threshold_gpu(processed, **threshold_params)
            logger.debug("✓ Adaptive Threshold 적용")

        return processed

    def preprocess_for_ocr(self, image: np.ndarray,
                          target_dpi: int = 300) -> np.ndarray:
        """
        OCR에 최적화된 전처리

        Args:
            image: 입력 이미지
            target_dpi: 목표 DPI (기본값: 300)

        Returns:
            OCR 최적화된 이미지
        """
        # Grayscale 변환
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # 크기 조정 (DPI 기반)
        height, width = gray.shape
        scale_factor = target_dpi / 150.0  # 기본 150 DPI 가정

        if scale_factor != 1.0:
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            logger.debug(f"✓ 크기 조정: {width}x{height} → {new_width}x{new_height}")

        # 전처리 파이프라인
        processed = self.preprocess_pipeline(
            gray,
            apply_clahe=True,
            apply_blur=True,
            apply_threshold=False,  # OCR은 보통 grayscale로 처리
            clahe_params={"clip_limit": 3.0, "tile_grid_size": (8, 8)},
            blur_params={"kernel_size": 3, "sigma": 0.8}
        )

        return processed

    def __del__(self):
        """소멸자: GPU 메모리 정리"""
        if self.use_gpu:
            self.clear_gpu_memory()


# 전역 프리프로세서 인스턴스
_preprocessor = None


def get_preprocessor(use_gpu: bool = True) -> GPUImagePreprocessor:
    """
    전역 프리프로세서 인스턴스 반환 (싱글톤 패턴)

    Args:
        use_gpu: GPU 사용 여부

    Returns:
        GPUImagePreprocessor 인스턴스
    """
    global _preprocessor

    if _preprocessor is None:
        _preprocessor = GPUImagePreprocessor(use_gpu=use_gpu)

    return _preprocessor


# 편의 함수
def preprocess_for_ocr(image: np.ndarray, use_gpu: bool = True) -> np.ndarray:
    """
    OCR용 이미지 전처리 (간편 함수)

    Args:
        image: 입력 이미지
        use_gpu: GPU 사용 여부

    Returns:
        전처리된 이미지
    """
    preprocessor = get_preprocessor(use_gpu=use_gpu)
    return preprocessor.preprocess_for_ocr(image)


if __name__ == "__main__":
    # 테스트 코드
    import time

    logging.basicConfig(level=logging.INFO)

    # 테스트 이미지 생성 (4K)
    test_image = np.random.randint(0, 256, (2160, 3840), dtype=np.uint8)

    # GPU 전처리
    if GPU_AVAILABLE:
        print("\n" + "="*60)
        print("🚀 GPU 전처리 테스트")
        print("="*60)

        preprocessor = GPUImagePreprocessor(use_gpu=True)

        start = time.time()
        result = preprocessor.preprocess_for_ocr(test_image)
        gpu_time = time.time() - start

        mem_usage = preprocessor.get_gpu_memory_usage()
        print(f"처리 시간: {gpu_time:.3f}초")
        print(f"GPU 메모리: {mem_usage['used_bytes'] / 1024**2:.1f} MB")
        print(f"결과 크기: {result.shape}")

    # CPU 전처리 (비교)
    print("\n" + "="*60)
    print("💻 CPU 전처리 테스트")
    print("="*60)

    preprocessor_cpu = GPUImagePreprocessor(use_gpu=False)

    start = time.time()
    result_cpu = preprocessor_cpu.preprocess_for_ocr(test_image)
    cpu_time = time.time() - start

    print(f"처리 시간: {cpu_time:.3f}초")
    print(f"결과 크기: {result_cpu.shape}")

    if GPU_AVAILABLE:
        print("\n" + "="*60)
        print(f"⚡ 성능 향상: {cpu_time / gpu_time:.1f}배")
        print("="*60)
