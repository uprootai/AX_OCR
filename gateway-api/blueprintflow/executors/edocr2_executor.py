"""
eDOCr2 Node Executor
차원 OCR API 호출 (크롭 업스케일 지원)
"""
import asyncio
import logging
import os
import re
from typing import Dict, Any, Optional, List

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import (
    prepare_image_for_api,
    crop_image_region,
    upscale_via_esrgan,
)
from services import call_edocr2_ocr

logger = logging.getLogger(__name__)

# 도면 영역 4분할 (타이틀블록/부품표 제외, 15-20% 오버랩)
DIMENSION_CROP_PRESETS = {
    "drawing_q1": (0.0, 0.0, 0.55, 0.50),     # 좌상단
    "drawing_q2": (0.35, 0.0, 0.85, 0.50),     # 우상단 (20% 오버랩)
    "drawing_q3": (0.0, 0.35, 0.55, 0.85),     # 좌하단 (15% 오버랩)
    "drawing_q4": (0.35, 0.35, 0.85, 0.85),    # 우하단 (15% 오버랩)
}

CROP_GROUPS = {
    "quadrants": ["drawing_q1", "drawing_q2", "drawing_q3", "drawing_q4"],
}

ESRGAN_URL = os.getenv("ESRGAN_URL", "http://esrgan-api:5010")


class Edocr2Executor(BaseNodeExecutor):
    """eDOCr2 차원 OCR 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        eDOCr2 차원 OCR 실행

        Parameters:
            - image: base64 인코딩된 이미지 또는 PIL Image
            - crop_regions: YOLO 검출 영역 (선택사항)

        Returns:
            - dimensions: 추출된 차원 정보 리스트
            - total_dimensions: 총 차원 개수
            - text: 추출된 텍스트 정보
        """
        file_bytes = prepare_image_for_api(inputs, context)
        enable_crop_upscale = self.parameters.get("enable_crop_upscale", False)

        filename = self.parameters.get("filename", "workflow_image.jpg")
        language = self.parameters.get("language", "eng")
        cluster_threshold = self.parameters.get("cluster_threshold", 20)
        extract_dimensions = self.parameters.get("extract_dimensions", True)
        extract_gdt = self.parameters.get("extract_gdt", True)
        extract_text = self.parameters.get("extract_text", True)
        extract_tables = self.parameters.get("extract_tables", True)
        visualize = self.parameters.get("visualize", True)

        if enable_crop_upscale:
            logger.info("eDOCr2 크롭 업스케일 모드 활성화")
            # 치수만 크롭 업스케일로 추출
            dimensions = await self._execute_crop_upscale(file_bytes, filename, language, cluster_threshold)

            # 텍스트/GDT는 전체 이미지에서 추출 (치수 제외)
            full_result = await call_edocr2_ocr(
                file_bytes=file_bytes,
                filename=filename,
                extract_dimensions=False,
                extract_gdt=extract_gdt,
                extract_text=extract_text,
                extract_tables=extract_tables,
                visualize=visualize,
                language=language,
                cluster_threshold=cluster_threshold,
            )

            output = {
                "dimensions": dimensions,
                "total_dimensions": len(dimensions),
                "text": full_result.get("text", {}),
                "model_used": "eDOCr2-v2 (crop-upscale)",
                "processing_time": full_result.get("processing_time", 0),
                "crop_upscale_info": {
                    "crop_preset": self.parameters.get("crop_preset", "quadrants"),
                    "upscale_scale": int(self.parameters.get("upscale_scale", 2)),
                    "regions_processed": len(
                        CROP_GROUPS.get(self.parameters.get("crop_preset", "quadrants"), [])
                    ),
                },
            }

            if full_result.get("visualized_image"):
                output["visualized_image"] = full_result["visualized_image"]
        else:
            # 기존 동작 (변경 없음)
            result = await call_edocr2_ocr(
                file_bytes=file_bytes,
                filename=filename,
                extract_dimensions=extract_dimensions,
                extract_gdt=extract_gdt,
                extract_text=extract_text,
                extract_tables=extract_tables,
                visualize=visualize,
                language=language,
                cluster_threshold=cluster_threshold,
            )

            output = {
                "dimensions": result.get("dimensions", []),
                "total_dimensions": len(result.get("dimensions", [])),
                "text": result.get("text", {}),
                "model_used": result.get("model", "eDOCr2-v2"),
                "processing_time": result.get("processing_time", 0),
            }

            if result.get("visualized_image"):
                output["visualized_image"] = result["visualized_image"]

        # 원본 이미지 패스스루 (BOM 등 후속 노드에서 사용)
        if inputs.get("image"):
            output["image"] = inputs["image"]

        # drawing_type 패스스루 (BOM 세션 생성에 필요)
        if inputs.get("drawing_type"):
            output["drawing_type"] = inputs["drawing_type"]

        # features 패스스루 (세션 UI 동적 구성에 필요)
        if inputs.get("features"):
            output["features"] = inputs["features"]

        return output

    async def _execute_crop_upscale(
        self,
        file_bytes: bytes,
        filename: str,
        language: str,
        cluster_threshold: int,
    ) -> List[Dict[str, Any]]:
        """4분할 크롭 + ESRGAN 업스케일 + eDOCr2 OCR → 좌표 변환 + 중복 제거"""
        crop_group = self.parameters.get("crop_preset", "quadrants")
        scale = int(self.parameters.get("upscale_scale", 2))
        denoise = float(self.parameters.get("upscale_denoise", 0.3))
        region_names = CROP_GROUPS.get(crop_group, CROP_GROUPS["quadrants"])

        # 모든 크롭을 동시 처리
        tasks = []
        for name in region_names:
            crop_ratio = DIMENSION_CROP_PRESETS[name]
            crop_bytes, ox, oy, cw, ch = crop_image_region(file_bytes, crop_ratio)
            logger.info(f"  크롭 {name}: offset=({ox},{oy}), size=({cw}x{ch})")
            tasks.append(
                self._process_single_crop(crop_bytes, ox, oy, scale, denoise, filename, language, cluster_threshold)
            )

        crop_results = await asyncio.gather(*tasks)

        # 결과 병합 + 중복 제거
        all_dims: List[Dict[str, Any]] = []
        for dims in crop_results:
            all_dims.extend(dims)

        unique = self._deduplicate_dimensions(all_dims)
        filtered = self._filter_false_positives(unique)
        logger.info(
            f"크롭 업스케일 결과: 전체 {len(all_dims)}개 → 중복제거 {len(unique)}개 → 필터링 후 {len(filtered)}개"
        )
        return filtered

    async def _process_single_crop(
        self,
        crop_bytes: bytes,
        offset_x: int,
        offset_y: int,
        scale: int,
        denoise: float,
        filename: str,
        language: str,
        cluster_threshold: int,
    ) -> List[Dict[str, Any]]:
        """단일 크롭 영역: 업스케일 → OCR → 좌표 변환"""
        # 1. ESRGAN 업스케일 (실패 시 원본 사용)
        upscaled = await upscale_via_esrgan(
            crop_bytes, esrgan_url=ESRGAN_URL, scale=scale, denoise_strength=denoise
        )
        ocr_input = upscaled if upscaled else crop_bytes
        actual_scale = scale if upscaled else 1

        # 2. eDOCr2 OCR (치수만 추출)
        result = await call_edocr2_ocr(
            file_bytes=ocr_input,
            filename=filename,
            extract_dimensions=True,
            extract_gdt=False,
            extract_text=False,
            extract_tables=False,
            visualize=False,
            language=language,
            cluster_threshold=cluster_threshold,
        )

        # 3. 좌표 변환 (크롭+업스케일 공간 → 원본 이미지 공간)
        dimensions = result.get("dimensions", [])
        for dim in dimensions:
            if "location" in dim:
                dim["location"] = self._translate_location(dim["location"], offset_x, offset_y, actual_scale)
            if "bbox" in dim:
                dim["bbox"] = self._translate_bbox(dim["bbox"], offset_x, offset_y, actual_scale)
        return dimensions

    @staticmethod
    def _translate_location(
        location: Any, offset_x: int, offset_y: int, scale: int
    ) -> Any:
        """업스케일 좌표를 원본 이미지 좌표로 변환"""
        if isinstance(location, (list, tuple)) and len(location) >= 2:
            # 중첩 리스트: [[x1,y1], [x2,y2], ...] (폴리곤)
            if isinstance(location[0], (list, tuple)):
                return [
                    [offset_x + int(pt[0] / scale), offset_y + int(pt[1] / scale)]
                    for pt in location
                ]
            # 플랫 리스트: [x, y] 또는 [x1, y1, x2, y2]
            translated = list(location)
            translated[0] = offset_x + int(translated[0] / scale)
            translated[1] = offset_y + int(translated[1] / scale)
            if len(translated) >= 4:
                translated[2] = offset_x + int(translated[2] / scale)
                translated[3] = offset_y + int(translated[3] / scale)
            return translated
        if isinstance(location, dict):
            result = dict(location)
            if "x" in result:
                result["x"] = offset_x + int(result["x"] / scale)
            if "y" in result:
                result["y"] = offset_y + int(result["y"] / scale)
            if "width" in result:
                result["width"] = int(result["width"] / scale)
            if "height" in result:
                result["height"] = int(result["height"] / scale)
            return result
        return location

    @staticmethod
    def _translate_bbox(
        bbox: Any, offset_x: int, offset_y: int, scale: int
    ) -> Any:
        """bbox [x1, y1, x2, y2] 또는 [[x1,y1],[x2,y2],...] 를 원본 이미지 좌표로 변환"""
        if isinstance(bbox, (list, tuple)) and len(bbox) >= 2:
            # 중첩 리스트: [[x1,y1], [x2,y2], ...]
            if isinstance(bbox[0], (list, tuple)):
                return [
                    [offset_x + int(pt[0] / scale), offset_y + int(pt[1] / scale)]
                    for pt in bbox
                ]
            # 플랫 리스트: [x1, y1, x2, y2]
            if len(bbox) == 4 and all(isinstance(v, (int, float)) for v in bbox):
                return [
                    offset_x + int(bbox[0] / scale),
                    offset_y + int(bbox[1] / scale),
                    offset_x + int(bbox[2] / scale),
                    offset_y + int(bbox[3] / scale),
                ]
        return bbox

    @staticmethod
    def _deduplicate_dimensions(dimensions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """오버랩 영역에서 동일 치수 중복 제거 (텍스트 일치 + bbox IoU 또는 중심점 거리)"""
        unique: List[Dict[str, Any]] = []
        for dim in dimensions:
            is_dup = False
            dim_value = str(dim.get("value", "")).strip()
            dim_bbox = dim.get("bbox") or dim.get("location")
            for existing in unique:
                existing_value = str(existing.get("value", "")).strip()
                existing_bbox = existing.get("bbox") or existing.get("location")
                if dim_value and dim_value == existing_value:
                    # IoU 기반 또는 중심점 거리 기반 중복 판단
                    if (
                        Edocr2Executor._bbox_iou(dim_bbox, existing_bbox) > 0.3
                        or Edocr2Executor._center_distance(dim_bbox, existing_bbox) < 100
                    ):
                        is_dup = True
                        break
            if not is_dup:
                unique.append(dim)
        return unique

    @staticmethod
    def _center_distance(bbox1: Any, bbox2: Any) -> float:
        """두 bbox의 중심점 간 유클리드 거리"""
        c1 = Edocr2Executor._bbox_center(bbox1)
        c2 = Edocr2Executor._bbox_center(bbox2)
        if c1 is None or c2 is None:
            return float('inf')
        return ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) ** 0.5

    @staticmethod
    def _bbox_center(bbox: Any) -> Optional[tuple]:
        """bbox의 중심점 좌표 반환"""
        if not bbox:
            return None
        if isinstance(bbox, (list, tuple)):
            if len(bbox) >= 4 and isinstance(bbox[0], (int, float)):
                return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
            if isinstance(bbox[0], (list, tuple)):
                xs = [pt[0] for pt in bbox]
                ys = [pt[1] for pt in bbox]
                return (sum(xs) / len(xs), sum(ys) / len(ys))
        return None

    @staticmethod
    def _filter_false_positives(dimensions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """단일 숫자, 쓰레기 패턴 등 false positive 필터링"""
        # 유효한 치수 패턴: 숫자, ⌀, M, R, ±, +, -, ., 괄호
        valid_dim_pattern = re.compile(r'[0-9]')
        # 특수문자 비율 임계값 (숫자+알파벳 외 문자가 60% 이상이면 쓰레기)
        filtered = []
        for dim in dimensions:
            value = str(dim.get("value", "")).strip()
            if not value:
                continue
            # 1) 너무 짧은 값 (1자리 순수 숫자/문자) — M6, R3, ⌀5 등은 유지
            if len(value) <= 2 and not any(c in value for c in "⌀ΦφMRCØ±"):
                logger.debug(f"  필터링 (너무 짧음): {value}")
                continue
            # 2) 숫자가 하나도 없는 값
            if not valid_dim_pattern.search(value):
                logger.debug(f"  필터링 (숫자 없음): {value}")
                continue
            # 3) 특수문자 비율 과다 (숫자+알파벳+공백+()⌀±.+- 외 문자 비율)
            clean_chars = re.findall(r'[0-9a-zA-Z\s()⌀ΦφØ±+\-./°]', value)
            if len(value) > 3 and len(clean_chars) / len(value) < 0.5:
                logger.debug(f"  필터링 (특수문자 과다): {value}")
                continue
            # 4) 숫자 비율 너무 낮음 (비공백 문자 중 숫자 20% 미만 → 쓰레기)
            non_space = re.sub(r'\s', '', value)
            digit_count = sum(1 for c in non_space if c.isdigit())
            if len(non_space) > 3 and digit_count / len(non_space) < 0.2:
                logger.debug(f"  필터링 (숫자 비율 부족): {value}")
                continue
            filtered.append(dim)
        return filtered

    @staticmethod
    def _bbox_iou(bbox1: Any, bbox2: Any) -> float:
        """두 bbox의 IoU(Intersection over Union) 계산"""
        if not bbox1 or not bbox2:
            return 0.0
        # 리스트/튜플 [x1, y1, x2, y2] 형태 기대
        try:
            if isinstance(bbox1, (list, tuple)) and len(bbox1) >= 4:
                x1_1, y1_1, x2_1, y2_1 = bbox1[0], bbox1[1], bbox1[2], bbox1[3]
            else:
                return 0.0
            if isinstance(bbox2, (list, tuple)) and len(bbox2) >= 4:
                x1_2, y1_2, x2_2, y2_2 = bbox2[0], bbox2[1], bbox2[2], bbox2[3]
            else:
                return 0.0

            inter_x1 = max(x1_1, x1_2)
            inter_y1 = max(y1_1, y1_2)
            inter_x2 = min(x2_1, x2_2)
            inter_y2 = min(y2_1, y2_2)

            if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
                return 0.0

            inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
            area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
            area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
            union_area = area1 + area2 - inter_area

            if union_area <= 0:
                return 0.0
            return inter_area / union_area
        except (TypeError, ValueError, IndexError):
            return 0.0

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        crop_preset = self.parameters.get("crop_preset", "quadrants")
        if crop_preset not in CROP_GROUPS:
            return False, f"유효하지 않은 crop_preset: {crop_preset}"

        upscale_scale = self.parameters.get("upscale_scale", 2)
        if int(upscale_scale) not in (2, 4):
            return False, f"upscale_scale은 2 또는 4만 지원: {upscale_scale}"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "Base64 인코딩된 이미지"
                },
                "crop_regions": {
                    "type": "array",
                    "description": "YOLO 검출 영역 (선택사항)",
                    "items": {"type": "object"}
                }
            },
            "required": ["image"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "dimensions": {
                    "type": "array",
                    "description": "추출된 차원 정보"
                },
                "total_dimensions": {
                    "type": "integer",
                    "description": "총 차원 개수"
                },
                "text": {
                    "type": "object",
                    "description": "추출된 텍스트 정보"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("edocr2", Edocr2Executor)
