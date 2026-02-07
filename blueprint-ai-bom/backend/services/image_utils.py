"""이미지 유틸리티 - 리사이즈, 최적화

업로드된 도면 이미지를 ML 모델에 최적화된 크기로 조정.
"""
import logging
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

# PIL 대용량 이미지 제한 해제 (읽기용)
Image.MAX_IMAGE_PIXELS = None

# 최적 크기 설정 (eDOCr2, YOLO 등 ML 모델 기준)
MAX_DIMENSION = 8000  # 가장 긴 변의 최대 픽셀
MAX_PIXELS = 64_000_000  # 최대 총 픽셀 수 (64MP)
WARN_PIXELS = 50_000_000  # 경고 임계값 (50MP)


def resize_image_if_needed(
    image_path: str | Path,
    max_dimension: int = MAX_DIMENSION,
    max_pixels: int = MAX_PIXELS,
    backup_suffix: str = "_original_huge",
) -> dict:
    """필요 시 이미지 리사이즈

    Args:
        image_path: 이미지 파일 경로
        max_dimension: 가장 긴 변의 최대 픽셀 (기본 8000)
        max_pixels: 최대 총 픽셀 수 (기본 64MP)
        backup_suffix: 원본 백업 파일 접미사

    Returns:
        dict: {
            "resized": bool,  # 리사이즈 여부
            "original_size": (w, h),
            "new_size": (w, h),
            "original_pixels": int,
            "new_pixels": int,
            "backup_path": str | None,
        }
    """
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"이미지 파일 없음: {image_path}")

    # 이미지 로드
    img = Image.open(image_path)
    original_size = img.size
    original_pixels = original_size[0] * original_size[1]

    result = {
        "resized": False,
        "original_size": original_size,
        "new_size": original_size,
        "original_pixels": original_pixels,
        "new_pixels": original_pixels,
        "backup_path": None,
    }

    # 리사이즈 필요 여부 확인
    w, h = original_size
    needs_resize = False

    if max(w, h) > max_dimension:
        needs_resize = True
        logger.info(f"[ImageUtils] 리사이즈 필요: 최대 변 {max(w, h)}px > {max_dimension}px")
    elif original_pixels > max_pixels:
        needs_resize = True
        logger.info(f"[ImageUtils] 리사이즈 필요: {original_pixels:,}px > {max_pixels:,}px")
    elif original_pixels > WARN_PIXELS:
        logger.warning(f"[ImageUtils] 대용량 이미지 경고: {original_pixels:,}px")

    if not needs_resize:
        img.close()
        return result

    # 새 크기 계산 (비율 유지)
    ratio = min(
        max_dimension / max(w, h),
        (max_pixels / original_pixels) ** 0.5  # 픽셀 수 기준
    )
    new_w = int(w * ratio)
    new_h = int(h * ratio)

    logger.info(f"[ImageUtils] 리사이즈: {w}x{h} → {new_w}x{new_h}")

    # 원본 백업
    backup_path = image_path.parent / f"{image_path.stem}{backup_suffix}{image_path.suffix}"
    if not backup_path.exists():
        import shutil
        shutil.copy(image_path, backup_path)
        result["backup_path"] = str(backup_path)
        logger.info(f"[ImageUtils] 원본 백업: {backup_path}")

    # 리사이즈 및 저장
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)
    img.close()

    # PNG 저장 (품질 유지)
    img_resized.save(image_path, format="PNG", optimize=True)
    img_resized.close()

    result["resized"] = True
    result["new_size"] = (new_w, new_h)
    result["new_pixels"] = new_w * new_h

    logger.info(
        f"[ImageUtils] 리사이즈 완료: "
        f"{original_pixels:,}px → {result['new_pixels']:,}px "
        f"({result['new_pixels']/original_pixels*100:.1f}%)"
    )

    return result


def get_optimal_size(width: int, height: int) -> tuple[int, int]:
    """ML 모델에 최적화된 크기 계산 (리사이즈 없이 계산만)

    Returns:
        (new_width, new_height)
    """
    pixels = width * height

    if max(width, height) <= MAX_DIMENSION and pixels <= MAX_PIXELS:
        return (width, height)

    ratio = min(
        MAX_DIMENSION / max(width, height),
        (MAX_PIXELS / pixels) ** 0.5
    )

    return (int(width * ratio), int(height * ratio))
