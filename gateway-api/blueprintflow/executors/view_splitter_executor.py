"""
BMT View Splitter Executor
GAR 배치도 이미지에서 VIEW 라벨을 검출하고 Min-Content 경계로 크롭 생성

입력: base64 이미지
출력: 크롭 정보 리스트 + 각 크롭의 base64 이미지
"""
import re
import logging
import tempfile
import os
from io import BytesIO
from typing import Dict, Any, Optional, List

import numpy as np
from PIL import Image

from .base_executor import BaseNodeExecutor, APICallerMixin
from .executor_registry import ExecutorRegistry
from .image_utils import extract_image_input, decode_base64_image, decode_to_pil_image

logger = logging.getLogger(__name__)

# PaddleOCR API URL (Docker 서비스 이름)
PADDLEOCR_API_URL = os.getenv("PADDLEOCR_API_URL", "http://paddleocr-api:5006")


class ViewSplitterExecutor(BaseNodeExecutor, APICallerMixin):
    """BMT GAR 배치도 VIEW 분할 실행기"""

    API_BASE_URL = PADDLEOCR_API_URL
    DEFAULT_TIMEOUT = 120

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        GAR 배치도 이미지에서 VIEW 라벨 검출 후 Min-Content 크롭 수행

        Parameters:
            - image: base64 인코딩된 GAR 배치도 이미지

        Returns:
            - crops: 크롭 정보 리스트 [{name, bbox, image}]
            - total_crops: 크롭 개수
            - image: 원본 이미지 패스스루
        """
        # 이미지 준비
        image_input = extract_image_input(inputs, context)
        file_bytes = decode_base64_image(image_input)
        pil_image = decode_to_pil_image(image_input)

        # Step 1: PaddleOCR로 VIEW 라벨 검출
        view_labels = await self._detect_view_labels(file_bytes)
        logger.info(f"VIEW 라벨 검출: {len(view_labels)}개")

        # Step 2: Min-Content 크롭 계산
        crops_info = self._min_content_split(pil_image, view_labels)
        logger.info(f"크롭 생성: {len(crops_info)}개")

        # Step 3: 각 크롭 이미지를 base64로 인코딩
        import base64
        crops_output = []
        for crop in crops_info:
            x1, y1, x2, y2 = crop["bbox"]
            roi = pil_image.crop((
                max(0, x1), max(0, y1),
                min(pil_image.width, x2), min(pil_image.height, y2)
            ))
            buf = BytesIO()
            roi.save(buf, format="PNG")
            crop_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            crops_output.append({
                "name": crop["name"],
                "bbox": list(crop["bbox"]),
                "image": crop_b64,
            })

        # 원본 이미지 패스스루
        original_image = inputs.get("image", "")
        if not original_image and file_bytes:
            original_image = base64.b64encode(file_bytes).decode("utf-8")

        return {
            "crops": crops_output,
            "total_crops": len(crops_output),
            "image": original_image,
        }

    async def _detect_view_labels(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """PaddleOCR로 VIEW 라벨 검출"""
        success, result, error = await self._api_call_with_retry(
            "POST",
            "/api/v1/ocr",
            files={"file": ("gar.png", file_bytes, "image/png")},
            timeout=120,
        )
        if not success or not result:
            logger.warning(f"PaddleOCR 호출 실패: {error}")
            return []

        labels = []
        for det in result.get("detections", []):
            if re.search(r"VIEW", det.get("text", ""), re.IGNORECASE):
                bbox = det.get("bbox", [])
                if len(bbox) >= 3:
                    labels.append({
                        "text": det["text"].strip(),
                        "cx": (bbox[0][0] + bbox[2][0]) / 2,
                        "cy": (bbox[0][1] + bbox[2][1]) / 2,
                    })
        return labels

    def _min_content_split(
        self, pil_image: Image.Image, labels: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Min-Content 경계 기반 크롭 계산"""
        try:
            import cv2
        except ImportError:
            cv2 = None

        w, h = pil_image.size
        gray = np.array(pil_image.convert("L"))

        if cv2 is not None:
            _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        else:
            # cv2 없는 경우 numpy로 대체
            binary = np.where(gray <= 240, 255, 0).astype(np.uint8)

        if not labels:
            return [{"name": "FULL", "bbox": (0, 0, w, h)}]

        labels.sort(key=lambda v: v["cy"])

        # 행 클러스터링
        rows: List[List[Dict]] = []
        cur = [labels[0]]
        for v in labels[1:]:
            if v["cy"] - cur[-1]["cy"] < 100:
                cur.append(v)
            else:
                rows.append(cur)
                cur = [v]
        rows.append(cur)
        for row in rows:
            row.sort(key=lambda v: v["cx"])

        def find_min_col(y1, y2, xl, xr, win=20):
            band = binary[y1:y2, xl:xr]
            cs = np.sum(band > 0, axis=0)
            if len(cs) < win:
                return (xl + xr) // 2
            s = np.convolve(cs, np.ones(win) / win, mode="valid")
            return xl + int(np.argmin(s)) + win // 2

        def find_min_row(x1, x2, yt, yb, win=20):
            band = binary[yt:yb, x1:x2]
            rs = np.sum(band > 0, axis=1)
            if len(rs) < win:
                return (yt + yb) // 2
            s = np.convolve(rs, np.ones(win) / win, mode="valid")
            return yt + int(np.argmin(s)) + win // 2

        # 행 간 경계 계산
        row_bounds = [
            find_min_row(
                0, w,
                int(np.mean([v["cy"] for v in rows[i]])),
                int(np.mean([v["cy"] for v in rows[i + 1]])),
            )
            for i in range(len(rows) - 1)
        ]

        # 하단 경계 탐지
        last_ly = max(v["cy"] for v in rows[-1])
        rm = np.mean(gray, axis=1)
        row_bottom = h
        cnt = 0
        for y in range(int(last_ly + 150), h):
            if y >= len(rm):
                break
            if rm[y] > 248:
                cnt += 1
            else:
                cnt = 0
            if cnt >= 20:
                row_bottom = y - 20
                break

        # 크롭 생성
        crops = []
        for ri, row in enumerate(rows):
            yt = row_bounds[ri - 1] if ri > 0 else 0
            yb = row_bounds[ri] if ri < len(row_bounds) else row_bottom
            cb = [
                find_min_col(yt, yb, int(row[vi]["cx"]), int(row[vi + 1]["cx"]))
                for vi in range(len(row) - 1)
            ]
            xe = [0] + cb + [w]
            for vi, v in enumerate(row):
                crops.append({"name": v["text"], "bbox": (xe[vi], yt, xe[vi + 1], yb)})

        # 3D 하단 영역
        if row_bottom < h - 100:
            ly = row_bottom - 30
            crops.append({"name": "3D+LOWER", "bbox": (0, ly, w, h)})
            mid = w // 2
            crops.append({"name": "3D LEFT", "bbox": (0, ly, mid, h)})
            crops.append({"name": "3D RIGHT", "bbox": (mid - 100, ly, w, h)})

        return crops

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image": {"type": "string", "description": "Base64 인코딩된 GAR 배치도 이미지"}
            },
            "required": ["image"],
        }

    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "crops": {
                    "type": "array",
                    "description": "크롭 정보 리스트",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "bbox": {"type": "array", "items": {"type": "integer"}},
                            "image": {"type": "string"},
                        },
                    },
                },
                "total_crops": {"type": "integer", "description": "크롭 개수"},
                "image": {"type": "string", "description": "원본 이미지 패스스루"},
            },
        }


# 실행기 등록
ExecutorRegistry.register("view_splitter", ViewSplitterExecutor)
