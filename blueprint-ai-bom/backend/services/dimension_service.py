"""치수 OCR 서비스 (PaddleOCR 우선, eDOCr2 fallback)

기존 DetectionService 패턴을 따름:
- httpx를 사용한 외부 API 호출
- 동기 방식 (기존 코드와 일관성 유지)
- 환경변수로 API URL 설정
- PaddleOCR PP-OCRv5를 기본 엔진으로 사용, 실패 시 eDOCr2 fallback

파싱/검증: dimension_parser.py, 병합: dimension_merger.py
"""
import os
import uuid
import time
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import httpx
import mimetypes

from schemas.dimension import Dimension, DimensionType, DimensionResult
from schemas.detection import VerificationStatus, BoundingBox

# 배럴 re-export (기존 내부 참조 유지)
from .dimension_parser import (  # noqa: F401
    RA_STANDARD_VALUES,
    fix_diameter_symbol,
    is_dimension_pattern,
    is_valid_dimension,
    parse_dimension_text,
    extract_unit,
    parse_bbox_flexible,
    apply_bbox_offset,
    parse_paddle_detection,
    parse_edocr2_detection,
    parse_paddleocr_detections,
    parse_generic_texts,
    extract_dims_from_text_block,
    SUB_DIM_PATTERNS,
)
from .dimension_merger import (  # noqa: F401
    ENGINE_BASE_WEIGHTS,
    ENGINE_SPECIALTY_BONUS,
    compute_iou,
    get_engine_weight,
    normalize_dim_value,
    merge_dimensions,
    merge_multi_engine,
)

logger = logging.getLogger(__name__)

# API 주소 (Docker 네트워크 내부)
EDOCR2_API_URL = os.getenv("EDOCR2_API_URL", "http://edocr2-v2-api:5002")
PADDLEOCR_API_URL = os.getenv("PADDLEOCR_API_URL", "http://paddleocr-api:5006")
EASYOCR_API_URL = os.getenv("EASYOCR_API_URL", "http://easyocr-api:5015")
TROCR_API_URL = os.getenv("TROCR_API_URL", "http://trocr-api:5009")
SURYAOCR_API_URL = os.getenv("SURYAOCR_API_URL", "http://surya-ocr-api:5013")
DOCTR_API_URL = os.getenv("DOCTR_API_URL", "http://doctr-api:5014")


class DimensionService:
    """치수 OCR 서비스 (PaddleOCR 우선, eDOCr2 fallback)"""

    MODEL_NAME = "치수 인식 (PaddleOCR + eDOCr2)"

    def __init__(
        self,
        api_url: str = EDOCR2_API_URL,
        paddleocr_url: str = PADDLEOCR_API_URL,
        easyocr_url: str = EASYOCR_API_URL,
        trocr_url: str = TROCR_API_URL,
        suryaocr_url: str = SURYAOCR_API_URL,
        doctr_url: str = DOCTR_API_URL,
    ):
        self.api_url = api_url
        self.paddleocr_url = paddleocr_url
        self.easyocr_url = easyocr_url
        self.trocr_url = trocr_url
        self.suryaocr_url = suryaocr_url
        self.doctr_url = doctr_url
        logger.info(
            f"DimensionService 초기화 완료 (6 engines: "
            f"paddleocr, edocr2, easyocr, trocr, suryaocr, doctr)"
        )

    def extract_dimensions(
        self,
        image_path: str,
        confidence_threshold: float = 0.5,
        ocr_engines: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """이미지에서 치수 추출 (멀티 OCR 엔진 지원)"""
        import cv2

        start_time = time.time()

        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")

        image_height, image_width = image.shape[:2]

        engines = ocr_engines or ["paddleocr"]
        engine_dispatch = {
            "paddleocr": self._call_paddleocr,
            "paddleocr_tiled": self._call_paddleocr_tiled,
            "edocr2": self._call_edocr2,
            "easyocr": self._call_easyocr,
            "trocr": self._call_trocr,
            "suryaocr": self._call_suryaocr,
            "doctr": self._call_doctr,
        }

        all_dimensions: List[Dimension] = []
        used_engines: List[str] = []

        for engine in engines:
            call_fn = engine_dispatch.get(engine)
            if not call_fn:
                logger.warning(f"알 수 없는 OCR 엔진: {engine}, 건너뜀")
                continue
            try:
                dims = call_fn(image_path, confidence_threshold)
                all_dimensions.extend(dims)
                used_engines.append(engine)
                logger.info(f"{engine}: {len(dims)}개 치수 검출")
            except Exception as e:
                logger.warning(f"{engine} 실패: {e}")

        if len(used_engines) > 1:
            before_count = len(all_dimensions)
            dimensions = merge_multi_engine(all_dimensions)
            logger.info(
                f"멀티 엔진 가중 투표 병합: {before_count}개 → {len(dimensions)}개 "
                f"(엔진: {used_engines})"
            )
        else:
            dimensions = all_dimensions

        # 도면 마진/제목란/리비전 영역 confidence 페널티
        for d in dimensions:
            cx, cy = (d.bbox.x1 + d.bbox.x2) / 2, (d.bbox.y1 + d.bbox.y2) / 2
            xr = cx / image_width if image_width else 0
            yr = cy / image_height if image_height else 0
            in_margin = (
                xr > 0.65 and yr > 0.85
                or xr > 0.75 and yr < 0.15
                or yr < 0.03 or yr > 0.97
                or xr < 0.03 or xr > 0.97
            )
            if in_margin:
                d.confidence *= 0.5

        model_id = "+".join(used_engines) if used_engines else "none"
        processing_time = (time.time() - start_time) * 1000

        return {
            "dimensions": [d.model_dump() for d in dimensions],
            "total_count": len(dimensions),
            "model_id": model_id,
            "processing_time_ms": processing_time,
            "image_width": image_width,
            "image_height": image_height,
        }

    # ==================== OCR 엔진 호출 ====================

    def _call_paddleocr(
        self, image_path: str, confidence_threshold: float
    ) -> List[Dimension]:
        """PaddleOCR API 호출 및 치수 파싱"""
        logger.debug(f"paddleocr-api 호출: image={Path(image_path).name}, conf={confidence_threshold}")

        with open(image_path, 'rb') as f:
            file_bytes = f.read()

        filename = Path(image_path).name
        content_type = mimetypes.guess_type(filename)[0] or "image/png"

        with httpx.Client(timeout=60.0) as client:
            files = {"file": (filename, file_bytes, content_type)}
            data = {
                "lang": "en",
                "ocr_version": "PP-OCRv5",
                "min_confidence": str(confidence_threshold),
            }
            response = client.post(
                f"{self.paddleocr_url}/api/v1/ocr",
                files=files,
                data=data,
            )

        if response.status_code != 200:
            raise Exception(f"paddleocr-api failed: {response.status_code} - {response.text}")

        result = response.json()
        detections = result.get("detections", [])
        logger.info(f"paddleocr-api 응답: {len(detections)}개 텍스트 검출")

        return parse_paddleocr_detections(detections, confidence_threshold)

    def _call_paddleocr_tiled(
        self, image_path: str, confidence_threshold: float
    ) -> List[Dimension]:
        """타일링 PaddleOCR: 전체 + 1024×1024 타일 OCR로 소형 텍스트 복원"""
        import cv2

        full_dims = self._call_paddleocr(image_path, confidence_threshold)

        image = cv2.imread(image_path)
        if image is None:
            return full_dims
        img_h, img_w = image.shape[:2]
        tile_size, stride = 1024, 819

        if img_w <= tile_size and img_h <= tile_size:
            return full_dims

        tile_coords = []
        for y in range(0, img_h, stride):
            for x in range(0, img_w, stride):
                x_end, y_end = min(x + tile_size, img_w), min(y + tile_size, img_h)
                if (x_end - x) >= 256 and (y_end - y) >= 256:
                    tile_coords.append((x, y, x_end, y_end))

        logger.info(f"paddleocr_tiled: {img_w}×{img_h} → {len(tile_coords)}개 타일")

        tile_dims: List[Dimension] = []
        with httpx.Client(timeout=30.0) as client:
            for tx, ty, tx_end, ty_end in tile_coords:
                try:
                    _, buf = cv2.imencode('.png', image[ty:ty_end, tx:tx_end])
                    resp = client.post(
                        f"{self.paddleocr_url}/api/v1/ocr",
                        files={"file": ("tile.png", buf.tobytes(), "image/png")},
                        data={
                            "lang": "en", "ocr_version": "PP-OCRv5",
                            "min_confidence": str(confidence_threshold),
                            "det_db_thresh": "0.2", "det_db_box_thresh": "0.4",
                        },
                    )
                    if resp.status_code != 200:
                        logger.warning(f"타일({tx},{ty}) OCR 실패: {resp.status_code}")
                        continue
                    dims = parse_paddleocr_detections(
                        resp.json().get("detections", []), confidence_threshold,
                        offset_x=float(tx), offset_y=float(ty),
                    )
                    tile_dims.extend(dims)
                except Exception as e:
                    logger.warning(f"타일({tx},{ty}) 처리 실패: {e}")

        if not tile_dims:
            return full_dims

        merged = merge_dimensions(full_dims + tile_dims)
        logger.info(
            f"paddleocr_tiled 병합: 전체 {len(full_dims)} + "
            f"타일 {len(tile_dims)} → {len(merged)}개"
        )
        return merged

    def _call_edocr2(
        self, image_path: str, confidence_threshold: float
    ) -> List[Dimension]:
        """eDOCr2 API 호출 및 치수 파싱"""
        logger.debug(f"edocr2-api 호출: image={Path(image_path).name}, conf={confidence_threshold}")

        with open(image_path, 'rb') as f:
            file_bytes = f.read()

        filename = Path(image_path).name
        content_type = mimetypes.guess_type(filename)[0] or "image/png"

        with httpx.Client(timeout=600.0) as client:
            files = {"file": (filename, file_bytes, content_type)}
            data = {
                "extract_dimensions": "true",
                "extract_gdt": "true",
                "extract_text": "false",
                "use_gpu_preprocessing": "true",
                "visualize": "false",
            }
            response = client.post(
                f"{self.api_url}/api/v2/ocr",
                files=files,
                data=data,
            )

        if response.status_code != 200:
            raise Exception(f"edocr2-api failed: {response.status_code} - {response.text}")

        result = response.json()
        api_data = result.get("data", {})
        raw_detections = api_data.get("dimensions", [])
        logger.info(f"edocr2-api 응답: {len(raw_detections)}개 치수 검출")

        dimensions: List[Dimension] = []
        for idx, det in enumerate(raw_detections):
            dimension = parse_edocr2_detection(det, idx)
            if not dimension:
                continue
            if dimension.confidence < confidence_threshold:
                continue
            if not is_valid_dimension(dimension):
                continue
            dimensions.append(dimension)

        return dimensions

    # ==================== 범용 OCR 엔진 (EasyOCR, TrOCR, Surya, DocTR) ====================

    _GENERIC_ENGINE_CONFIGS = {
        "easyocr": {
            "url_attr": "easyocr_url", "endpoint": "/api/v1/ocr", "timeout": 120.0,
            "form_data": {"languages": "en", "detail": "true"},
        },
        "trocr": {
            "url_attr": "trocr_url", "endpoint": "/api/v1/ocr", "timeout": 120.0,
            "form_data": {"model_type": "printed", "max_length": "64", "num_beams": "4"},
        },
        "suryaocr": {
            "url_attr": "suryaocr_url", "endpoint": "/api/v1/ocr", "timeout": 120.0,
            "form_data": {"languages": "en", "detect_layout": "false"},
        },
        "doctr": {
            "url_attr": "doctr_url", "endpoint": "/api/v1/ocr", "timeout": 60.0,
            "form_data": {"det_arch": "db_resnet50", "reco_arch": "crnn_vgg16_bn", "straighten_pages": "false"},
        },
    }

    def _call_easyocr(self, image_path: str, confidence_threshold: float) -> List[Dimension]:
        return self._call_generic_ocr("easyocr", image_path, confidence_threshold)

    def _call_trocr(self, image_path: str, confidence_threshold: float) -> List[Dimension]:
        return self._call_generic_ocr("trocr", image_path, confidence_threshold)

    def _call_suryaocr(self, image_path: str, confidence_threshold: float) -> List[Dimension]:
        return self._call_generic_ocr("suryaocr", image_path, confidence_threshold)

    def _call_doctr(self, image_path: str, confidence_threshold: float) -> List[Dimension]:
        return self._call_generic_ocr("doctr", image_path, confidence_threshold)

    def _call_generic_ocr(
        self, engine_id: str, image_path: str, confidence_threshold: float
    ) -> List[Dimension]:
        """범용 OCR API 호출 및 치수 파싱"""
        config = self._GENERIC_ENGINE_CONFIGS[engine_id]
        base_url = getattr(self, config["url_attr"])
        endpoint = config["endpoint"]
        timeout = config["timeout"]

        logger.debug(f"{engine_id}-api 호출: image={Path(image_path).name}")

        with open(image_path, 'rb') as f:
            file_bytes = f.read()

        filename = Path(image_path).name
        content_type = mimetypes.guess_type(filename)[0] or "image/png"

        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{base_url}{endpoint}",
                files={"file": (filename, file_bytes, content_type)},
                data=config["form_data"],
            )

        if response.status_code != 200:
            raise Exception(f"{engine_id}-api failed: {response.status_code} - {response.text}")

        result = response.json()
        texts = result.get("data", result).get("texts", result.get("texts", []))
        logger.info(f"{engine_id}-api 응답: {len(texts)}개 텍스트 검출")

        return parse_generic_texts(texts, engine_id, confidence_threshold)

    # ==================== 수동 치수 추가 / 헬스체크 ====================

    def add_manual_dimension(
        self,
        value: str,
        bbox: Dict[str, float],
        confidence: float = 1.0,
        dimension_type: DimensionType = DimensionType.UNKNOWN
    ) -> Dict[str, Any]:
        """수동 치수 추가"""
        dim_id = f"dim_manual_{uuid.uuid4().hex[:8]}"

        dim_type, parsed_value, tolerance = parse_dimension_text(value)
        if dimension_type != DimensionType.UNKNOWN:
            dim_type = dimension_type

        unit = extract_unit(value)

        dimension = Dimension(
            id=dim_id,
            bbox=BoundingBox(**bbox),
            value=parsed_value,
            raw_text=value,
            unit=unit,
            tolerance=tolerance,
            dimension_type=dim_type,
            confidence=confidence,
            model_id="manual",
            verification_status=VerificationStatus.MANUAL,
            modified_value=None,
            modified_bbox=None,
            linked_to=None
        )

        return dimension.model_dump()

    def health_check(self) -> bool:
        """헬스체크"""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.api_url}/api/v1/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"eDOCr2 health check failed: {e}")
            return False
