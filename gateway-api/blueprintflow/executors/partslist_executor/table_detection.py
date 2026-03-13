"""
Parts List 테이블 검출 유틸리티
Table Detector API 호출 및 Parts List 테이블 선별
"""
from typing import Dict, Any, Optional, List
import logging

import httpx

from .constants import TABLE_DETECTOR_URL

logger = logging.getLogger(__name__)

# Parts List 헤더 식별 키워드
PARTS_LIST_KEYWORDS = ["NO", "PART", "NAME", "MAT", "Q'TY", "QTY", "품명", "재질", "수량"]


async def detect_tables(file_bytes: bytes, ocr_engine: str) -> Dict[str, Any]:
    """Table Detector API로 테이블 검출"""
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=30.0)) as client:
        files = {"file": ("partslist.png", file_bytes, "image/png")}
        data = {
            "mode": "analyze",
            "ocr_engine": ocr_engine,
            "borderless": "false",  # Parts List는 보통 테두리 있음
            "confidence_threshold": "0.6",
            "min_confidence": "60",
            "output_format": "json",
        }

        response = await client.post(
            f"{TABLE_DETECTOR_URL}/api/v1/analyze",
            files=files,
            data=data
        )

        if response.status_code != 200:
            return {"success": False, "error": f"Table Detector 오류: {response.status_code}"}

        import orjson
        return orjson.loads(response.content)


def find_parts_list_table(tables: List[Dict]) -> Optional[Dict]:
    """Parts List 테이블 찾기 (헤더 기반)"""
    best_table = None
    best_score = 0

    for table in tables:
        headers = table.get("headers", [])
        if not headers:
            continue

        # 헤더 매칭 점수 계산
        score = 0
        for header in headers:
            header_upper = str(header).upper()
            for keyword in PARTS_LIST_KEYWORDS:
                if keyword in header_upper:
                    score += 1
                    break

        # 최소 2개 이상 매칭되어야 Parts List로 간주
        if score >= 2 and score > best_score:
            best_score = score
            best_table = table

    return best_table
