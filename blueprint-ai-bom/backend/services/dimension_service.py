"""치수 OCR 서비스 (eDOCr2 연동)

기존 DetectionService 패턴을 따름:
- httpx를 사용한 외부 API 호출
- 동기 방식 (기존 코드와 일관성 유지)
- 환경변수로 API URL 설정
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

# eDOCr2 API 주소 (Docker 네트워크 내부)
EDOCR2_API_URL = os.getenv("EDOCR2_API_URL", "http://edocr2-v2-api:5002")


class DimensionService:
    """치수 OCR 서비스 (DetectionService 패턴 따름)"""

    MODEL_NAME = "eDOCr2 치수 인식"

    def __init__(self, api_url: str = EDOCR2_API_URL):
        self.api_url = api_url
        logger.info(f"DimensionService 초기화 완료 (edocr2-api: {self.api_url})")

    def extract_dimensions(
        self,
        image_path: str,
        confidence_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        이미지에서 치수 추출 (동기 방식)

        Args:
            image_path: 이미지 파일 경로
            confidence_threshold: 최소 신뢰도

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
        dimensions = []

        logger.debug(f"edocr2-api 호출: image={Path(image_path).name}, conf={confidence_threshold}")

        try:
            with open(image_path, 'rb') as f:
                file_bytes = f.read()

            filename = Path(image_path).name
            content_type = mimetypes.guess_type(filename)[0] or "image/png"

            with httpx.Client(timeout=120.0) as client:
                files = {"file": (filename, file_bytes, content_type)}
                data = {
                    "confidence": confidence_threshold,
                    "mode": "dimension",  # 치수 인식 모드
                }

                response = client.post(
                    f"{self.api_url}/api/v2/ocr",
                    files=files,
                    data=data
                )

            if response.status_code == 200:
                result = response.json()
                # eDOCr2 API v2 응답 구조: {"status": "success", "data": {"dimensions": [...], ...}}
                data = result.get("data", {})
                raw_detections = data.get("dimensions", [])

                logger.info(f"edocr2-api 응답: {len(raw_detections)}개 치수 검출")

                # 응답 파싱
                for idx, det in enumerate(raw_detections):
                    dimension = self._parse_detection(det, idx)
                    if dimension and dimension.confidence >= confidence_threshold:
                        dimensions.append(dimension)
            else:
                logger.error(f"edocr2-api 오류: {response.status_code} - {response.text}")
                raise Exception(f"edocr2-api failed: {response.text}")

        except httpx.ConnectError as e:
            logger.error(f"edocr2-api 연결 실패: {e}")
            raise Exception(f"Cannot connect to edocr2-api at {self.api_url}")
        except Exception as e:
            logger.error(f"치수 추출 오류: {e}")
            raise

        processing_time = (time.time() - start_time) * 1000  # ms

        return {
            "dimensions": [d.model_dump() for d in dimensions],
            "total_count": len(dimensions),
            "model_id": "edocr2",
            "processing_time_ms": processing_time,
            "image_width": image_width,
            "image_height": image_height,
        }

    def _parse_detection(self, det: dict, idx: int) -> Optional[Dimension]:
        """
        eDOCr2 응답을 Dimension 객체로 변환

        eDOCr2 v2 응답 형식:
        {
            "value": "Ø50 H7",
            "unit": "mm",
            "type": "text_dimension",
            "tolerance": null,
            "location": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
        }
        """
        try:
            dim_id = f"dim_{idx:03d}_{uuid.uuid4().hex[:8]}"

            # eDOCr2 v2 형식: value 필드 사용
            raw_text = det.get("value", det.get("text", ""))

            # eDOCr2는 confidence를 반환하지 않으므로 기본값 0.9 사용
            confidence = det.get("confidence", 0.9)

            # location 파싱 (4개의 좌표점 -> bbox로 변환)
            location = det.get("location", [])
            bbox_data = det.get("bbox", None)

            if location and len(location) == 4:
                # 4개의 점에서 min/max로 bbox 추출
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

    def _parse_dimension_text(self, text: str) -> Tuple[DimensionType, str, Optional[str]]:
        """
        치수 텍스트 파싱

        Returns:
            (DimensionType, parsed_value, tolerance)
        """
        text = text.strip()
        tolerance = None
        dim_type = DimensionType.UNKNOWN
        parsed_value = text

        # 직경 패턴: Ø50, ⌀50, φ50
        if re.match(r'^[Ø⌀φ]\s*\d+', text):
            dim_type = DimensionType.DIAMETER

        # 반경 패턴: R50, R 50
        elif re.match(r'^R\s*\d+', text, re.IGNORECASE):
            dim_type = DimensionType.RADIUS

        # 각도 패턴: 45°, 45deg
        elif re.search(r'\d+\s*[°˚]', text) or 'deg' in text.lower():
            dim_type = DimensionType.ANGLE

        # 표면 거칠기: Ra 1.6, Ra1.6
        elif re.match(r'^Ra\s*[\d.]+', text, re.IGNORECASE):
            dim_type = DimensionType.SURFACE_FINISH

        # 일반 길이: 100, 100mm, 50.5
        elif re.match(r'^\d+\.?\d*', text):
            dim_type = DimensionType.LENGTH

        # 공차 추출: H7, h6, ±0.1, +0.05/-0.02
        tolerance_patterns = [
            r'[HhGgFfEeDdCcBbAa]\d+',  # IT 공차
            r'[±]\s*\d+\.?\d*',  # 대칭 공차
            r'[+\-]\d+\.?\d*\s*/\s*[+\-]?\d+\.?\d*',  # 비대칭 공차
        ]
        for pattern in tolerance_patterns:
            match = re.search(pattern, text)
            if match:
                tolerance = match.group()
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
