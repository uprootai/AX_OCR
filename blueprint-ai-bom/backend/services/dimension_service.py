"""치수 OCR 서비스 (PaddleOCR 우선, eDOCr2 fallback)

기존 DetectionService 패턴을 따름:
- httpx를 사용한 외부 API 호출
- 동기 방식 (기존 코드와 일관성 유지)
- 환경변수로 API URL 설정
- PaddleOCR PP-OCRv5를 기본 엔진으로 사용, 실패 시 eDOCr2 fallback
"""
import os
import uuid
import re
import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import httpx
import mimetypes

from schemas.dimension import (
    Dimension,
    DimensionType,
    DimensionResult,
)
from schemas.detection import VerificationStatus, BoundingBox

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

    # 엔진별 기본 가중치 (OCR Ensemble merge_results 패턴)
    _ENGINE_BASE_WEIGHTS: Dict[str, float] = {
        "paddleocr": 0.35, "paddleocr_tiled": 0.35,
        "edocr2": 0.40,   # 도면 특화 → 최고 가중치
        "easyocr": 0.25, "trocr": 0.20, "suryaocr": 0.20, "doctr": 0.25,
    }

    # 엔진별 치수 유형 특화 보너스
    _ENGINE_SPECIALTY_BONUS: Dict[str, Dict[str, float]] = {
        "edocr2": {"diameter": 0.15, "radius": 0.10, "tolerance": 0.15, "thread": 0.10},
        "paddleocr": {"length": 0.10},
        "paddleocr_tiled": {"length": 0.10},
    }

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
        """
        이미지에서 치수 추출 (멀티 OCR 엔진 지원)

        Args:
            image_path: 이미지 파일 경로
            confidence_threshold: 최소 신뢰도
            ocr_engines: 사용할 OCR 엔진 목록 (순서대로 실행, 결과 병합)

        Returns:
            치수 결과 dict (dimensions, total_count, processing_time_ms 등)
        """
        import cv2

        start_time = time.time()

        # 이미지 정보 확인
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

        # 엔진이 2개 이상 성공하면 가중 투표 병합
        if len(used_engines) > 1:
            before_count = len(all_dimensions)
            dimensions = self._merge_multi_engine(all_dimensions)
            logger.info(
                f"멀티 엔진 가중 투표 병합: {before_count}개 → {len(dimensions)}개 "
                f"(엔진: {used_engines})"
            )
        else:
            dimensions = all_dimensions

        model_id = "+".join(used_engines) if used_engines else "none"
        processing_time = (time.time() - start_time) * 1000  # ms

        return {
            "dimensions": [d.model_dump() for d in dimensions],
            "total_count": len(dimensions),
            "model_id": model_id,
            "processing_time_ms": processing_time,
            "image_width": image_width,
            "image_height": image_height,
        }

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

        return self._parse_paddleocr_detections(detections, confidence_threshold)

    def _parse_paddleocr_detections(
        self,
        detections: list,
        confidence_threshold: float,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> List[Dimension]:
        """PaddleOCR 검출 결과 → Dimension 리스트 (패턴 필터 + 텍스트 블록 분해)"""
        dimensions: List[Dimension] = []
        for idx, det in enumerate(detections):
            text = det.get("text", "").strip()
            if not text:
                continue

            text = self._fix_diameter_symbol(text)

            # 오프셋 적용: 타일 좌표 → 전체 이미지 좌표
            if offset_x or offset_y:
                det = self._apply_bbox_offset(det, offset_x, offset_y)

            if self._is_dimension_pattern(text):
                dimension = self._parse_paddle_detection(det, idx, text)
                if dimension and dimension.confidence >= confidence_threshold and self._is_valid_dimension(dimension):
                    dimensions.append(dimension)
                    continue
            # 패턴 불일치 또는 유효성 실패 → 텍스트 블록에서 치수 부분 추출
            sub_dims = self._extract_dims_from_text_block(det, idx, text, confidence_threshold)
            dimensions.extend(sub_dims)

        return dimensions

    @staticmethod
    def _apply_bbox_offset(det: dict, offset_x: float, offset_y: float) -> dict:
        """PaddleOCR detection의 bbox 좌표에 타일 오프셋 적용"""
        det = dict(det)  # shallow copy
        bbox_points = det.get("bbox", det.get("position", []))
        if bbox_points and len(bbox_points) == 4:
            shifted = [[pt[0] + offset_x, pt[1] + offset_y] for pt in bbox_points]
            if "bbox" in det:
                det["bbox"] = shifted
            else:
                det["position"] = shifted
        return det

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
        tile_size, stride = 1024, 819  # overlap 20%

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
                    dims = self._parse_paddleocr_detections(
                        resp.json().get("detections", []), confidence_threshold,
                        offset_x=float(tx), offset_y=float(ty),
                    )
                    tile_dims.extend(dims)
                except Exception as e:
                    logger.warning(f"타일({tx},{ty}) 처리 실패: {e}")

        if not tile_dims:
            return full_dims

        merged = self._merge_dimensions(full_dims + tile_dims)
        logger.info(
            f"paddleocr_tiled 병합: 전체 {len(full_dims)} + "
            f"타일 {len(tile_dims)} → {len(merged)}개"
        )
        return merged

    def _call_edocr2(
        self, image_path: str, confidence_threshold: float
    ) -> List[Dimension]:
        """eDOCr2 API 호출 및 치수 파싱 (기존 로직)"""
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
            dimension = self._parse_detection(det, idx)
            if not dimension:
                continue
            if dimension.confidence < confidence_threshold:
                continue
            if not self._is_valid_dimension(dimension):
                continue
            dimensions.append(dimension)

        return dimensions

    # ==================== 범용 OCR 엔진 호출 (EasyOCR, TrOCR, Surya, DocTR) ====================

    # 엔진별 설정: (url_attr, endpoint, timeout, form_data, response_path)
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
        """범용 OCR API 호출 및 치수 파싱 (EasyOCR, TrOCR, Surya, DocTR 공통)"""
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
        # 응답 경로: data.texts[] (대부분) 또는 texts[] (TrOCR fallback)
        texts = result.get("data", result).get("texts", result.get("texts", []))
        logger.info(f"{engine_id}-api 응답: {len(texts)}개 텍스트 검출")

        return self._parse_generic_texts(texts, engine_id, confidence_threshold)

    def _parse_generic_texts(
        self, texts: list, model_id: str, confidence_threshold: float
    ) -> List[Dimension]:
        """범용 OCR 텍스트 결과를 Dimension 리스트로 변환"""
        dimensions: List[Dimension] = []
        for idx, det in enumerate(texts):
            # 텍스트 추출 (dict 또는 str)
            if isinstance(det, dict):
                text = det.get("text", "").strip()
                confidence = float(det.get("confidence", 0.5))
                bbox_raw = det.get("bbox")
            else:
                text = str(det).strip()
                confidence = 0.5
                bbox_raw = None

            if not text or confidence < confidence_threshold:
                continue
            text = self._fix_diameter_symbol(text)
            bbox = self._parse_bbox_flexible(bbox_raw) if bbox_raw else BoundingBox(x1=0, y1=0, x2=0, y2=0)

            if self._is_dimension_pattern(text):
                dim_type, parsed_value, tolerance = self._parse_dimension_text(text)
                dim = Dimension(
                    id=f"dim_{idx:03d}_{uuid.uuid4().hex[:8]}",
                    bbox=bbox, value=parsed_value, raw_text=text,
                    unit=self._extract_unit(text), tolerance=tolerance,
                    dimension_type=dim_type, confidence=confidence, model_id=model_id,
                    verification_status=VerificationStatus.PENDING,
                    modified_value=None, modified_bbox=None, linked_to=None,
                )
                if self._is_valid_dimension(dim):
                    dimensions.append(dim)
            else:
                # 텍스트 블록에서 치수 부분 추출
                for pat in self._SUB_DIM_PATTERNS:
                    for m in pat.finditer(text):
                        sub = self._fix_diameter_symbol(m.group().strip())
                        if not self._is_dimension_pattern(sub):
                            continue
                        dt, pv, tol = self._parse_dimension_text(sub)
                        sub_dim = Dimension(
                            id=f"dim_{idx:03d}_{uuid.uuid4().hex[:8]}",
                            bbox=bbox, value=pv, raw_text=sub,
                            unit=self._extract_unit(sub), tolerance=tol,
                            dimension_type=dt, confidence=confidence, model_id=model_id,
                            verification_status=VerificationStatus.PENDING,
                            modified_value=None, modified_bbox=None, linked_to=None,
                        )
                        if self._is_valid_dimension(sub_dim):
                            dimensions.append(sub_dim)
        return dimensions

    @staticmethod
    def _parse_bbox_flexible(bbox_data) -> BoundingBox:
        """다양한 bbox 포맷을 BoundingBox로 변환

        지원: [x1,y1,x2,y2] | [[x1,y1],[x2,y2],...] | {x1,y1,x2,y2}
        """
        if isinstance(bbox_data, dict):
            return BoundingBox(
                x1=float(bbox_data.get("x1", 0)), y1=float(bbox_data.get("y1", 0)),
                x2=float(bbox_data.get("x2", 0)), y2=float(bbox_data.get("y2", 0)),
            )
        if isinstance(bbox_data, list) and len(bbox_data) == 4:
            if isinstance(bbox_data[0], (list, tuple)):
                xs = [pt[0] for pt in bbox_data]
                ys = [pt[1] for pt in bbox_data]
                return BoundingBox(
                    x1=float(min(xs)), y1=float(min(ys)),
                    x2=float(max(xs)), y2=float(max(ys)),
                )
            return BoundingBox(
                x1=float(bbox_data[0]), y1=float(bbox_data[1]),
                x2=float(bbox_data[2]), y2=float(bbox_data[3]),
            )
        return BoundingBox(x1=0, y1=0, x2=0, y2=0)

    def _merge_dimensions(
        self, dimensions: List[Dimension], iou_threshold: float = 0.5
    ) -> List[Dimension]:
        """bbox IoU 기반 중복 제거 - confidence 높은 결과 유지"""
        if not dimensions:
            return []

        # confidence 내림차순 정렬
        sorted_dims = sorted(dimensions, key=lambda d: d.confidence, reverse=True)
        kept: List[Dimension] = []

        for dim in sorted_dims:
            is_duplicate = False
            for existing in kept:
                if self._compute_iou(dim.bbox, existing.bbox) > iou_threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                kept.append(dim)

        return kept

    @staticmethod
    def _compute_iou(a: BoundingBox, b: BoundingBox) -> float:
        """두 BoundingBox의 IoU (Intersection over Union) 계산"""
        x1 = max(a.x1, b.x1)
        y1 = max(a.y1, b.y1)
        x2 = min(a.x2, b.x2)
        y2 = min(a.y2, b.y2)

        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        if intersection == 0:
            return 0.0

        area_a = max(0, a.x2 - a.x1) * max(0, a.y2 - a.y1)
        area_b = max(0, b.x2 - b.x1) * max(0, b.y2 - b.y1)
        union = area_a + area_b - intersection

        if union == 0:
            return 0.0

        return intersection / union

    @classmethod
    def _get_engine_weight(cls, model_id: str, dim_type: Optional[str] = None) -> float:
        """엔진 기본 가중치 + 치수 유형 특화 보너스 반환"""
        base = cls._ENGINE_BASE_WEIGHTS.get(model_id, 0.10)
        if dim_type:
            bonus = cls._ENGINE_SPECIALTY_BONUS.get(model_id, {}).get(dim_type, 0.0)
            return base + bonus
        return base

    @staticmethod
    def _normalize_dim_value(text: str) -> str:
        """치수 값 정규화 (비교용): Ø/φ/Φ/⌀ → ø, 공백 제거, 소문자"""
        normalized = text.strip().lower()
        normalized = re.sub(r'[ØφΦ⌀]', 'ø', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'\s+', '', normalized)
        return normalized

    def _merge_multi_engine(
        self, dimensions: List[Dimension], iou_threshold: float = 0.5
    ) -> List[Dimension]:
        """멀티 엔진 가중 투표 병합 (OCR Ensemble merge_results 패턴)

        1. IoU 클러스터링  2. 값별 가중 투표  3. 최고 득점 선택
        4. 합의 보너스 (+0.05/엔진, 최대 +0.15)  5. 대표 Dimension
        """
        if not dimensions:
            return []

        used = set()
        clusters: List[List[Dimension]] = []
        for i, dim in enumerate(dimensions):
            if i in used:
                continue
            cluster = [dim]
            used.add(i)
            for j in range(i + 1, len(dimensions)):
                if j in used:
                    continue
                if self._compute_iou(dim.bbox, dimensions[j].bbox) > iou_threshold:
                    cluster.append(dimensions[j])
                    used.add(j)
            clusters.append(cluster)

        merged: List[Dimension] = []
        for cluster in clusters:
            if len(cluster) == 1:
                merged.append(cluster[0])
                continue

            value_votes: Dict[str, float] = {}
            value_engines: Dict[str, List[str]] = {}
            value_original: Dict[str, str] = {}
            value_dims: Dict[str, List[Dimension]] = {}

            for dim in cluster:
                norm = self._normalize_dim_value(dim.raw_text)
                dt = dim.dimension_type
                dim_type_str = dt.value if hasattr(dt, 'value') else (dt if isinstance(dt, str) else None)
                weight = self._get_engine_weight(dim.model_id, dim_type_str)
                value_votes[norm] = value_votes.get(norm, 0.0) + weight * dim.confidence
                value_engines.setdefault(norm, []).append(dim.model_id)
                if norm not in value_original:
                    value_original[norm] = dim.raw_text
                elif re.search(r'[ØφΦ⌀]', dim.raw_text) and not re.search(r'[ØφΦ⌀]', value_original[norm]):
                    value_original[norm] = dim.raw_text
                value_dims.setdefault(norm, []).append(dim)

            best_norm = max(value_votes, key=lambda k: value_votes[k])
            unique_engines = set(value_engines[best_norm])
            agreement_bonus = min(len(unique_engines) * 0.05, 0.15)

            representative = max(value_dims[best_norm], key=lambda d: d.confidence)
            original_text = value_original[best_norm]
            boosted_conf = min(representative.confidence + agreement_bonus, 1.0)

            dim_type, parsed_value, tolerance = self._parse_dimension_text(original_text)
            result_dim = Dimension(
                id=representative.id,
                bbox=representative.bbox,
                value=parsed_value,
                raw_text=original_text,
                unit=representative.unit or self._extract_unit(original_text),
                tolerance=tolerance,
                dimension_type=dim_type if dim_type != DimensionType.UNKNOWN else representative.dimension_type,
                confidence=boosted_conf,
                model_id="+".join(sorted(unique_engines)),
                verification_status=representative.verification_status,
                modified_value=representative.modified_value,
                modified_bbox=representative.modified_bbox,
                linked_to=representative.linked_to,
            )
            merged.append(result_dim)

            if len(unique_engines) > 1:
                logger.debug(
                    f"가중 투표: '{original_text}' 채택 "
                    f"(vote={value_votes[best_norm]:.3f}, engines={list(unique_engines)})"
                )

        logger.info(f"가중 투표 병합 완료: {len(dimensions)}개 → {len(merged)}개")
        return merged

    def _parse_paddle_detection(
        self, det: dict, idx: int, text: str
    ) -> Optional[Dimension]:
        """PaddleOCR 응답을 Dimension 객체로 변환"""
        try:
            dim_id = f"dim_{idx:03d}_{uuid.uuid4().hex[:8]}"
            confidence = float(det.get("confidence", 0.5))

            # bbox 파싱: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] 또는 position
            bbox_points = det.get("bbox", det.get("position", []))
            if bbox_points and len(bbox_points) == 4:
                xs = [pt[0] for pt in bbox_points]
                ys = [pt[1] for pt in bbox_points]
                bbox = BoundingBox(
                    x1=float(min(xs)),
                    y1=float(min(ys)),
                    x2=float(max(xs)),
                    y2=float(max(ys)),
                )
            else:
                bbox = BoundingBox(x1=0, y1=0, x2=0, y2=0)

            dim_type, parsed_value, tolerance = self._parse_dimension_text(text)
            unit = self._extract_unit(text)

            return Dimension(
                id=dim_id,
                bbox=bbox,
                value=parsed_value,
                raw_text=text,
                unit=unit,
                tolerance=tolerance,
                dimension_type=dim_type,
                confidence=confidence,
                model_id="paddleocr",
                verification_status=VerificationStatus.PENDING,
                modified_value=None,
                modified_bbox=None,
                linked_to=None,
            )
        except Exception as e:
            logger.error(f"PaddleOCR 치수 파싱 실패: {e}")
            return None

    def _fix_diameter_symbol(self, text: str) -> str:
        """PaddleOCR이 Ø를 0으로 읽는 문제 보정

        - "0392" → "Ø392" (독립 텍스트에서 0+3자리이상 숫자)
        - "PCD0430" → "PCDØ430"
        - "(2x0361)" → "(2xØ361)"
        - 단, "0.5" 같은 소수는 변환하지 않음
        """
        return re.sub(r'(?<![.\d])0(\d{2,})', r'Ø\1', text)

    def _is_dimension_pattern(self, text: str) -> bool:
        """PaddleOCR 텍스트가 치수 패턴인지 확인"""
        exclude_patterns = [
            r'Rev\.', r'\d{4}[.\-/]\d{2}[.\-/]\d{2}', r'^[A-Z]\d+-\d+',
            r'^[A-Z]{2}\d{5,}', r'(?i)Dwg|DATE|SCALE|PART|MATERIAL|FINISH|WEIGHT',
        ]
        for pat in exclude_patterns:
            if re.search(pat, text):
                return False

        dimension_patterns = [
            r'^\d+\.?\d*$', r'^[ØφΦ⌀]\s*\d+', r'^R\s*\d+', r'^M\s*\d+',
            r'^PCD[Ø]?\d+', r'^\d+\.?\d*\s*[±]', r'^\d+\.?\d*\s*[+\-]\s*\d',
            r'^\d+\.?\d*\s*[°˚]', r'^\(\d+[x×]', r'^\(\d+\.?\d*\)$',
            r'^\d+\.?\d*\s*\(\*?\)', r'^\d+\.?\d*\s*mm', r'^\d+\.?\d*\s*[A-Z]\d+$',
            r'^\(\d+\)\s*[ØφΦ⌀]\s*\d+', r'^\(\d+\)\s*\d+\.?\d*[°˚]',
            r'^\(\d+\)\s*\d+\.?\d*$', r'^[±]\s*\d+',
            r'^\(\d+\)\s*M\s*\d+', r'^\(\d+\)\s*R\s*\d+',
        ]
        for pat in dimension_patterns:
            if re.search(pat, text):
                return True

        return False

    _SUB_DIM_PATTERNS = [
        re.compile(r'\(\d+\)\s*[ØφΦ⌀]\s*\d+\.?\d*'),
        re.compile(r'\(\d+\)\s*M\d+\.?\d*'),
        re.compile(r'\(\d+\)\s*\d+\.?\d*[°˚]'),
        re.compile(r'[ØφΦ⌀]\s*\d+\.?\d*'),
        re.compile(r'M\d+\.?\d*(?:\s*[x×]\s*\d+)?'),
        re.compile(r'R\s*\d+\.?\d*'),
        re.compile(r'PCD\s*[ØφΦ⌀]?\s*\d+\.?\d*'),
        re.compile(r'[±]\s*\d+\.?\d*'),
        re.compile(r'\b\d+\.?\d*\s*(?=Drill|drill|Tap|tap|thru|Hole|hole)'),
    ]

    def _extract_dims_from_text_block(
        self, det: dict, base_idx: int, text: str, confidence_threshold: float
    ) -> List[Dimension]:
        """긴 텍스트 블록에서 치수 패턴을 추출하여 개별 Dimension으로 변환

        예: "(4)M20 Tap, & Ø17.5 Drill, thru." → [M20, Ø17.5]
        """
        if len(text) < 5:
            return []

        found: List[Dimension] = []
        seen_spans = set()

        for pat in self._SUB_DIM_PATTERNS:
            for m in pat.finditer(text):
                span = (m.start(), m.end())
                # 이미 더 넓은 매치에 포함된 부분은 건너뜀
                if any(s <= span[0] and span[1] <= e for s, e in seen_spans):
                    continue
                seen_spans.add(span)

                sub_text = m.group().strip()
                sub_text = self._fix_diameter_symbol(sub_text)
                if not self._is_dimension_pattern(sub_text):
                    continue

                # 원본 bbox를 공유 (텍스트 블록 전체의 bbox)
                dim = self._parse_paddle_detection(det, base_idx + len(found), sub_text)
                if dim and dim.confidence >= confidence_threshold and self._is_valid_dimension(dim):
                    found.append(dim)

        return found

    def _parse_detection(self, det: dict, idx: int) -> Optional[Dimension]:
        """eDOCr2 응답을 Dimension 객체로 변환"""
        try:
            dim_id = f"dim_{idx:03d}_{uuid.uuid4().hex[:8]}"
            raw_text = det.get("value", det.get("text", ""))
            confidence = det.get("confidence", 0.9)
            location = det.get("location", [])
            bbox_data = det.get("bbox", None)

            if location and len(location) == 4:
                xs = [pt[0] for pt in location]
                ys = [pt[1] for pt in location]
                bbox = BoundingBox(
                    x1=float(min(xs)),
                    y1=float(min(ys)),
                    x2=float(max(xs)),
                    y2=float(max(ys))
                )
            elif isinstance(bbox_data, dict):
                bbox = BoundingBox(
                    x1=float(bbox_data.get("x1", 0)),
                    y1=float(bbox_data.get("y1", 0)),
                    x2=float(bbox_data.get("x2", 0)),
                    y2=float(bbox_data.get("y2", 0))
                )
            elif isinstance(bbox_data, list) and len(bbox_data) >= 4:
                bbox = BoundingBox(
                    x1=float(bbox_data[0]),
                    y1=float(bbox_data[1]),
                    x2=float(bbox_data[2]),
                    y2=float(bbox_data[3])
                )
            else:
                bbox = BoundingBox(x1=0, y1=0, x2=0, y2=0)

            # 치수 유형 및 값 파싱
            dim_type, parsed_value, tolerance = self._parse_dimension_text(raw_text)

            # eDOCr2 type 필드 활용
            edocr2_type = det.get("type", "")
            if edocr2_type and dim_type == DimensionType.UNKNOWN:
                type_mapping = {
                    "dimension": DimensionType.LENGTH,
                    "diameter": DimensionType.DIAMETER,
                    "radius": DimensionType.RADIUS,
                    "angle": DimensionType.ANGLE,
                    "tolerance": DimensionType.TOLERANCE,
                    "text_dimension": DimensionType.UNKNOWN,  # 텍스트로 표시된 치수
                }
                dim_type = type_mapping.get(edocr2_type, DimensionType.UNKNOWN)

            # 단위는 eDOCr2가 제공하거나 텍스트에서 추출
            unit = det.get("unit") or self._extract_unit(raw_text)

            return Dimension(
                id=dim_id,
                bbox=bbox,
                value=parsed_value,
                raw_text=raw_text,
                unit=unit,
                tolerance=tolerance,
                dimension_type=dim_type,
                confidence=confidence,
                model_id="edocr2",
                verification_status=VerificationStatus.PENDING,
                modified_value=None,
                modified_bbox=None,
                linked_to=None
            )

        except Exception as e:
            logger.error(f"치수 파싱 실패: {e}")
            return None

    def _is_valid_dimension(self, dim: Dimension) -> bool:
        """OCR 결과 품질 필터 - 깨진 텍스트, 오탐 제거"""
        text = dim.raw_text.strip()
        if len(text) <= 1:
            return False
        if not re.search(r'\d', text):
            return False
        garbage_ratio = sum(1 for c in text if c in ':;|{}[]\\') / max(len(text), 1)
        if garbage_ratio > 0.3:
            return False
        if '\n' in text or len(text) > 30:
            return False
        if sum(1 for c in text if c.isdigit()) / max(len(text), 1) < 0.3:
            return False
        if (dim.bbox.x2 - dim.bbox.x1) > 500:
            return False
        numeric_match = re.match(r'^[ØφΦ⌀]?\s*(\d+\.?\d*)', text)
        if numeric_match and float(numeric_match.group(1)) >= 5000:
            return False
        return True

    def _parse_dimension_text(self, text: str) -> Tuple[DimensionType, str, Optional[str]]:
        """치수 텍스트 파싱 → (DimensionType, parsed_value, tolerance)"""
        text = text.strip()
        tolerance = None
        dim_type = DimensionType.UNKNOWN
        parsed_value = text

        # 복합 패턴 (구체적인 패턴 먼저)
        match = re.match(r'^[ØφΦ⌀]\s*(\d+\.?\d*)\s*[±]\s*(\d+\.?\d*)', text)  # Φ50±0.05
        if match:
            return DimensionType.DIAMETER, parsed_value, f"±{match.group(2)}"
        match = re.match(r'^[ØφΦ⌀]\s*(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)\s*/\s*-\s*(\d+\.?\d*)', text)
        if match:
            return DimensionType.DIAMETER, parsed_value, f"+{match.group(2)}/-{match.group(3)}"
        match = re.match(r'^[ØφΦ⌀]\s*(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)', text)
        if match:
            return DimensionType.DIAMETER, parsed_value, f"+{match.group(3)}/-{match.group(2)}"
        match = re.match(r'^[ØφΦ⌀]\s*(\d+\.?\d*)\s*([A-Za-z]\d+)', text)  # Ø50H7
        if match:
            return DimensionType.DIAMETER, parsed_value, match.group(2)
        match = re.match(r'^M\s*(\d+\.?\d*)(?:\s*[×xX]\s*(\d+\.?\d*))?', text)
        if match:
            return DimensionType.THREAD, parsed_value, tolerance
        match = re.match(r'^C\s*(\d+\.?\d*)(?:\s*[×xX]\s*(\d+\.?\d*)\s*°)?', text, re.IGNORECASE)
        if match:
            return DimensionType.CHAMFER, parsed_value, tolerance

        # 단일 패턴
        if re.match(r'^[ØφΦ⌀]\s*\d+', text):
            dim_type = DimensionType.DIAMETER
        elif re.match(r'^R\s*\d+', text, re.IGNORECASE):
            dim_type = DimensionType.RADIUS
        elif re.search(r'\d+\s*[°˚]', text) or 'deg' in text.lower():
            dim_type = DimensionType.ANGLE
        elif re.match(r'^Ra\s*[\d.]+', text, re.IGNORECASE):
            dim_type = DimensionType.SURFACE_FINISH
        elif re.match(r'^\d+\.?\d*', text):
            dim_type = DimensionType.LENGTH

        # 공차 추출 (특수 치수 타입은 IT 공차 제외)
        skip_it_tolerance = dim_type in (
            DimensionType.RADIUS,
            DimensionType.CHAMFER,
            DimensionType.THREAD,
            DimensionType.ANGLE,
            DimensionType.SURFACE_FINISH,
        )

        tolerance_patterns = [
            (r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)',  # 50-0.02+0.05
             lambda m: f"+{m.group(3)}/-{m.group(2)}", False),
            (r'(\d+\.?\d*)\s*\+\s*(\d+\.?\d*)\s*/\s*0(?!\d)',      # 50 +0.05/0
             lambda m: f"+{m.group(2)}/0", False),
            (r'(\d+\.?\d*)\s*0\s*/\s*-\s*(\d+\.?\d*)',             # 50 0/-0.05
             lambda m: f"0/-{m.group(2)}", False),
            (r'\+\s*(\d+\.?\d*)\s*/\s*-\s*(\d+\.?\d*)',            # +0.05/-0.02
             lambda m: f"+{m.group(1)}/-{m.group(2)}", False),
            (r'[±]\s*(\d+\.?\d*)', lambda m: f"±{m.group(1)}", False),  # ±0.1
            (r'(?<![RrCcMm])([HhGgFfEeDdBbAaJjKkNnPpSsTtUuVvXxYyZz])(\d+)',  # IT: H7
             lambda m: f"{m.group(1)}{m.group(2)}", True),
        ]

        if tolerance is None:
            for pattern, formatter, is_it_tolerance in tolerance_patterns:
                if is_it_tolerance and skip_it_tolerance:
                    continue
                match = re.search(pattern, text)
                if match:
                    tolerance = formatter(match)
                    break

        return dim_type, parsed_value, tolerance

    def _extract_unit(self, text: str) -> Optional[str]:
        """단위 추출"""
        text_lower = text.lower()
        if 'mm' in text_lower:
            return 'mm'
        elif 'cm' in text_lower:
            return 'cm'
        elif 'in' in text_lower or '"' in text:
            return 'inch'
        elif '°' in text or 'deg' in text_lower:
            return 'degree'
        elif 'm' in text_lower and 'mm' not in text_lower:
            return 'm'
        return None

    def add_manual_dimension(
        self,
        value: str,
        bbox: Dict[str, float],
        confidence: float = 1.0,
        dimension_type: DimensionType = DimensionType.UNKNOWN
    ) -> Dict[str, Any]:
        """수동 치수 추가"""
        dim_id = f"dim_manual_{uuid.uuid4().hex[:8]}"

        dim_type, parsed_value, tolerance = self._parse_dimension_text(value)
        if dimension_type != DimensionType.UNKNOWN:
            dim_type = dimension_type

        unit = self._extract_unit(value)

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
