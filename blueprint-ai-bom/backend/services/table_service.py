"""테이블 추출 서비스 (Table Detector API 호출)

도면 내 부품표(Parts List), 타이틀 블록 등을 추출.
- 도면 영역별 크롭 후 Table Detector API (5022) 호출
- img2table extract 모드 사용 (TATR은 도면에 비효과적)
- 품질 필터링: 빈 셀 비율, 이미지 커버리지 기반
"""
import os
import io
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import httpx
import mimetypes

logger = logging.getLogger(__name__)

TABLE_DETECTOR_API_URL = os.getenv(
    "TABLE_DETECTOR_API_URL", "http://table-detector-api:5022"
)

# 도면 영역별 크롭 비율 (x_start%, y_start%, x_end%, y_end%)
_CROP_REGIONS = {
    "title_block": (0.55, 0.65, 1.0, 1.0),       # 우하단 타이틀 블록
    "revision_table": (0.55, 0.0, 1.0, 0.20),     # 우상단 리비전 테이블
    "parts_list_right": (0.60, 0.20, 1.0, 0.65),  # 우측 부품표
}


class TableService:
    """테이블 검출/추출 서비스"""

    def __init__(self, api_url: str = TABLE_DETECTOR_API_URL):
        self.api_url = api_url

    def extract_tables(
        self,
        image_path: str,
        mode: str = "extract",
        ocr_engine: str = "paddle",
        borderless: bool = False,
        confidence_threshold: float = 0.7,
        min_confidence: int = 50,
    ) -> Dict[str, Any]:
        """이미지에서 테이블 추출 (영역별 크롭 + 품질 필터링)"""
        start = time.time()

        try:
            from PIL import Image
        except ImportError:
            return self._call_api_simple(image_path, mode, ocr_engine,
                                         borderless, min_confidence)

        img = Image.open(image_path)
        w, h = img.size

        all_tables = []
        all_regions = []

        # 1단계: 영역별 크롭 → 각각 extract
        for region_name, (x1r, y1r, x2r, y2r) in _CROP_REGIONS.items():
            crop_box = (int(w * x1r), int(h * y1r), int(w * x2r), int(h * y2r))
            cropped = img.crop(crop_box)

            if cropped.size[0] < 100 or cropped.size[1] < 50:
                continue

            buf = io.BytesIO()
            cropped.save(buf, format="JPEG", quality=95)
            crop_bytes = buf.getvalue()

            result = self._call_api(
                crop_bytes, f"{region_name}.jpg", ocr_engine,
                borderless, min_confidence,
            )
            if not result:
                continue

            for table in result.get("tables", []):
                table["source_region"] = region_name
                table["crop_box"] = list(crop_box)
                # 품질 필터
                if self._is_quality_table(table):
                    all_tables.append(table)

            for region in result.get("regions", []):
                if region.get("label") != "table_fallback":
                    region["source_region"] = region_name
                    all_regions.append(region)

        elapsed = (time.time() - start) * 1000

        logger.info(
            f"테이블 추출 완료: {len(all_regions)}개 영역, "
            f"{len(all_tables)}개 테이블 ({len(_CROP_REGIONS)}개 영역 검색), "
            f"{elapsed:.0f}ms"
        )

        return {
            "tables": all_tables,
            "regions": all_regions,
            "tables_count": len(all_tables),
            "regions_count": len(all_regions),
            "image_size": {"width": w, "height": h},
            "processing_time_ms": elapsed,
        }

    def _call_api(
        self, file_bytes: bytes, filename: str,
        ocr_engine: str, borderless: bool, min_confidence: int,
    ) -> Dict[str, Any] | None:
        """Table Detector API extract 엔드포인트 호출"""
        try:
            with httpx.Client(timeout=60.0) as client:
                files = {"file": (filename, file_bytes, "image/jpeg")}
                data = {
                    "ocr_engine": ocr_engine,
                    "borderless": str(borderless).lower(),
                    "min_confidence": str(min_confidence),
                }
                resp = client.post(
                    f"{self.api_url}/api/v1/extract", files=files, data=data
                )
            if resp.status_code != 200:
                logger.warning(f"Table API {resp.status_code}: {resp.text[:200]}")
                return None
            return resp.json()
        except httpx.ConnectError:
            logger.warning(f"Table Detector 연결 실패 ({self.api_url})")
            return None
        except Exception as e:
            logger.warning(f"Table API 호출 실패: {e}")
            return None

    def _call_api_simple(
        self, image_path: str, mode: str, ocr_engine: str,
        borderless: bool, min_confidence: int,
    ) -> Dict[str, Any]:
        """PIL 없이 단순 API 호출 (fallback)"""
        start = time.time()
        with open(image_path, "rb") as f:
            file_bytes = f.read()
        filename = Path(image_path).name
        content_type = mimetypes.guess_type(filename)[0] or "image/png"
        try:
            with httpx.Client(timeout=120.0) as client:
                files = {"file": (filename, file_bytes, content_type)}
                data = {
                    "ocr_engine": ocr_engine,
                    "borderless": str(borderless).lower(),
                    "min_confidence": str(min_confidence),
                }
                resp = client.post(
                    f"{self.api_url}/api/v1/{mode}", files=files, data=data
                )
            if resp.status_code != 200:
                raise Exception(f"table-detector-api: {resp.status_code}")
            result = resp.json()
            elapsed = (time.time() - start) * 1000
            return {
                "tables": result.get("tables", []),
                "regions": result.get("regions", []),
                "tables_count": len(result.get("tables", [])),
                "regions_count": len(result.get("regions", [])),
                "processing_time_ms": elapsed,
            }
        except httpx.ConnectError:
            return {"tables": [], "regions": [], "tables_count": 0,
                    "regions_count": 0, "processing_time_ms": 0,
                    "error": "Table Detector 서비스 연결 실패"}

    @staticmethod
    def _is_quality_table(table: Dict[str, Any]) -> bool:
        """테이블 품질 검증 — 빈 셀이 너무 많으면 제외"""
        data = table.get("data", [])
        if not data:
            return False
        rows = table.get("rows", len(data))
        cols = table.get("cols", len(data[0]) if data else 0)
        if rows < 2 or cols < 2:
            return False
        # 빈 셀 비율 계산
        total_cells = 0
        empty_cells = 0
        for row in data:
            for cell in row:
                total_cells += 1
                if not cell or (isinstance(cell, str) and not cell.strip()):
                    empty_cells += 1
        if total_cells == 0:
            return False
        empty_ratio = empty_cells / total_cells
        if empty_ratio > 0.7:
            logger.debug(f"테이블 제외: 빈 셀 {empty_ratio:.0%}")
            return False
        return True

    def health_check(self) -> bool:
        """Table Detector 서비스 상태 확인"""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.api_url}/health")
                return resp.status_code == 200
        except Exception:
            return False
