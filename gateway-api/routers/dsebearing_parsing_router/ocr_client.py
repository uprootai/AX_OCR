"""
DSE Bearing Parsing — eDOCr2 OCR client
"""

import logging
from typing import Dict, Any, List

import httpx

logger = logging.getLogger(__name__)

EDOCR2_URL = "http://edocr2-v2-api:5002"


async def call_edocr2_ocr(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
    """eDOCr2 API 호출하여 OCR 수행"""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (filename, file_content, "image/png")}
            response = await client.post(
                f"{EDOCR2_URL}/api/v2/ocr",
                files=files,
                data={"profile": "bearing", "output_format": "json"}
            )

            if response.status_code == 200:
                result = response.json()
                texts = []
                if result.get("status") == "success" and "data" in result:
                    data = result["data"]

                    # 1. dimensions에서 값 추출
                    if "dimensions" in data:
                        for dim in data["dimensions"]:
                            if isinstance(dim, dict) and "value" in dim:
                                texts.append(dim["value"])

                    # 2. possible_text에서 텍스트 추출
                    if "possible_text" in data:
                        for item in data["possible_text"]:
                            if isinstance(item, dict) and "text" in item:
                                texts.append(item["text"])

                    # 3. text 섹션에서 추출
                    if "text" in data and isinstance(data["text"], dict):
                        for key, value in data["text"].items():
                            if isinstance(value, str):
                                texts.append(value)
                            elif isinstance(value, list):
                                texts.extend([str(v) for v in value])

                    # 4. gdt 섹션에서 추출
                    if "gdt" in data:
                        for gdt in data["gdt"]:
                            if isinstance(gdt, dict) and "value" in gdt:
                                texts.append(gdt["value"])

                elif "texts" in result:
                    texts = result["texts"]
                elif "results" in result:
                    texts = result["results"]

                logger.info(f"eDOCr2 응답: {len(texts)} 텍스트 추출됨")
                return texts
            else:
                logger.warning(f"eDOCr2 API 실패: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"eDOCr2 호출 오류: {e}")
        return []
