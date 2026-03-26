"""
BMT Tag Filter Executor
OCR 결과에서 TAG 패턴(V01, PT07 등)을 필터링하고 fuzzy 교정 수행

입력: OCR 결과 (texts 리스트) 또는 크롭별 이미지
출력: 유효 TAG 리스트
"""
import re
import os
import logging
from typing import Dict, Any, Optional, List, Set

from .base_executor import BaseNodeExecutor, APICallerMixin
from .executor_registry import ExecutorRegistry
from .image_utils import decode_base64_image

logger = logging.getLogger(__name__)

# PaddleOCR / Tesseract API URLs
PADDLEOCR_API_URL = os.getenv("PADDLEOCR_API_URL", "http://paddleocr-api:5006")
TESSERACT_API_URL = os.getenv("TESSERACT_API_URL", "http://tesseract-api:5008")

# TAG 인식 패턴
TAG_PATTERNS = [
    re.compile(r"^V\d+(-\d+)?$"),
    re.compile(r"^PT\d+$"),
    re.compile(r"^TT\d+$"),
    re.compile(r"^FT\d+$"),
    re.compile(r"^PI\d+$"),
    re.compile(r"^B\d+$"),
]

# 노이즈 패턴 (TAG가 아닌 텍스트)
NOISE_PATTERNS = [
    re.compile(r"^\d"),
    re.compile(r"GVU"),
    re.compile(r"WORKSPACE"),
    re.compile(r"ENCLOSURE"),
    re.compile(r"MED1A"),
    re.compile(r"DN\d"),
    re.compile(r"^[A-Z]\d$"),
    re.compile(r"SPEC"),
    re.compile(r"PRESSURE"),
    re.compile(r","),
    re.compile(r"FUEL"),
    re.compile(r"NATURAL"),
    re.compile(r"NITROGEN"),
    re.compile(r"STPG"),
    re.compile(r"SUS"),
    re.compile(r"^R\d"),
]

# Fuzzy 교정 맵 (숫자 부분의 잘못된 문자 교정)
CORRECTIONS = {"Z": "7", "O": "0", "I": "1", "S": "5"}


def correct_tag(tag: str) -> str:
    """TAG 숫자 부분의 잘못 인식된 문자 교정"""
    m = re.match(r"^([A-Z]+)(.*)", tag)
    if not m:
        return tag
    prefix = m.group(1)
    suffix = "".join(CORRECTIONS.get(c, c) for c in m.group(2))
    return prefix + suffix


def is_valid_tag(text: str) -> bool:
    """TAG 패턴 유효성 검사"""
    t = text.strip().upper()
    for p in NOISE_PATTERNS:
        if p.search(t):
            return False
    for p in TAG_PATTERNS:
        if p.match(t):
            return True
    return False


class TagFilterExecutor(BaseNodeExecutor, APICallerMixin):
    """BMT TAG 필터링 실행기"""

    DEFAULT_TIMEOUT = 60

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        OCR 결과 또는 크롭 이미지에서 TAG 추출

        입력 모드 1: 이전 노드가 OCR 텍스트를 제공 (texts 리스트)
        입력 모드 2: view_splitter 크롭 이미지로부터 직접 OCR 수행 (crops 리스트)

        Returns:
            - tags: 유효한 TAG 리스트 (정렬)
            - per_crop: 크롭별 TAG 딕셔너리
            - total_tags: TAG 개수
        """
        all_tags: Set[str] = set()
        per_crop: Dict[str, List[str]] = {}

        # 모드 1: OCR 텍스트가 이미 있는 경우
        texts_input = inputs.get("texts", [])
        if texts_input and isinstance(texts_input, list):
            for item in texts_input:
                text = item.get("text", "") if isinstance(item, dict) else str(item)
                self._process_text(text, all_tags)
            per_crop["direct"] = sorted(all_tags)

        # 모드 2: 크롭 이미지로부터 OCR 수행
        crops = inputs.get("crops", [])
        if crops and isinstance(crops, list):
            use_tesseract = self.parameters.get("use_tesseract", True)
            for crop in crops:
                crop_name = crop.get("name", "unknown")
                crop_image_b64 = crop.get("image", "")
                if not crop_image_b64:
                    continue

                crop_tags = set()
                crop_bytes = decode_base64_image(crop_image_b64)

                # PaddleOCR
                paddle_texts = await self._ocr_paddle(crop_bytes)
                for t in paddle_texts:
                    self._process_text(t, crop_tags)

                # Tesseract (옵션)
                if use_tesseract:
                    tess_texts = await self._ocr_tesseract(crop_bytes)
                    for t in tess_texts:
                        self._process_text(t, crop_tags)

                per_crop[crop_name] = sorted(crop_tags)
                all_tags |= crop_tags

        tags_sorted = sorted(all_tags)
        logger.info(f"TAG 추출 완료: {len(tags_sorted)}개 — {tags_sorted}")

        return {
            "tags": tags_sorted,
            "per_crop": per_crop,
            "total_tags": len(tags_sorted),
        }

    def _process_text(self, text: str, tag_set: Set[str]):
        """텍스트를 정규화, 교정, 필터링하여 tag_set에 추가"""
        tw = text.strip().upper().replace(" ", "")
        tw = re.sub(r"[|=(){}\[\]]", "", tw)
        corrected = correct_tag(tw)
        if is_valid_tag(corrected):
            tag_set.add(corrected)
        if is_valid_tag(tw):
            tag_set.add(tw)

    async def _ocr_paddle(self, file_bytes: bytes) -> List[str]:
        """PaddleOCR API 호출"""
        success, result, error = await self._api_call_with_retry(
            "POST",
            "/api/v1/ocr",
            files={"file": ("crop.png", file_bytes, "image/png")},
            timeout=60,
            base_url=PADDLEOCR_API_URL,
        )
        if not success or not result:
            return []
        return [d.get("text", "") for d in result.get("detections", [])]

    async def _ocr_tesseract(self, file_bytes: bytes) -> List[str]:
        """Tesseract API 호출"""
        success, result, error = await self._api_call_with_retry(
            "POST",
            "/api/v1/ocr",
            files={"file": ("crop.png", file_bytes, "image/png")},
            timeout=60,
            base_url=TESSERACT_API_URL,
        )
        if not success or not result:
            return []
        texts = [d.get("text", "") for d in result.get("texts", [])]
        full_text = result.get("full_text", "")
        if full_text:
            texts.append(full_text)
        return texts

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "crops": {
                    "type": "array",
                    "description": "view_splitter 크롭 리스트 (각각 name, bbox, image 포함)",
                },
                "texts": {
                    "type": "array",
                    "description": "이미 추출된 OCR 텍스트 리스트 (대안 입력)",
                },
            },
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "유효한 TAG 리스트",
                },
                "per_crop": {
                    "type": "object",
                    "description": "크롭별 TAG 딕셔너리",
                },
                "total_tags": {"type": "integer", "description": "TAG 개수"},
            },
        }


# 실행기 등록
ExecutorRegistry.register("tag_filter", TagFilterExecutor)
