"""테이블 추출 서비스 (Table Detector API 호출) + 일반 텍스트 OCR

도면 내 부품표(Parts List), 타이틀 블록, NOTES 등을 추출.
- 도면 영역별 크롭 후 Table Detector API (5022) 호출
- img2table extract 모드 사용 (TATR은 도면에 비효과적)
- PaddleOCR/EasyOCR로 비테이블 텍스트 영역 추출
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
PADDLEOCR_API_URL = os.getenv(
    "PADDLEOCR_API_URL", "http://paddleocr-api:5006"
)
EASYOCR_API_URL = os.getenv(
    "EASYOCR_API_URL", "http://easyocr-api:5015"
)
ESRGAN_API_URL = os.getenv(
    "ESRGAN_API_URL", "http://esrgan-api:5010"
)

# 도면 영역별 크롭 비율 (x_start%, y_start%, x_end%, y_end%)
_CROP_REGIONS = {
    "title_block": (0.55, 0.65, 1.0, 1.0),       # 우하단 타이틀 블록
    "revision_table": (0.55, 0.0, 1.0, 0.20),     # 우상단 리비전 테이블
    "parts_list_right": (0.60, 0.20, 1.0, 0.65),  # 우측 부품표
}

# 비테이블 텍스트 영역 (PaddleOCR/EasyOCR로 추출)
_TEXT_REGIONS = {
    "title_block": (0.55, 0.65, 1.0, 1.0),        # 타이틀 블록 텍스트
    "notes_area": (0.0, 0.65, 0.55, 1.0),          # 좌하단 NOTES 영역
}

# E1-B-3: OCR 오류 수정 사전 (부품명/도면 용어)
# 키: 오류 패턴 (대문자), 값: 올바른 텍스트
_OCR_CORRECTIONS = {
    # 문자 혼동 (A↔R, 3↔R, 0↔O, 1↔I/L, 5↔S, 8↔B)
    "BEAAING": "BEARING",
    "BEAFING": "BEARING",
    "BEAR1NG": "BEARING",
    "3ING": "RING",
    "R1NG": "RING",
    "ASSY": "ASSY",
    "ASSV": "ASSY",
    "A55Y": "ASSY",
    "CASING": "CASING",
    "CAS1NG": "CASING",
    "THRUST": "THRUST",
    "THRUS7": "THRUST",
    "SHAFT": "SHAFT",
    "SHAF7": "SHAFT",
    "5HAFT": "SHAFT",
    "SLEEVE": "SLEEVE",
    "5LEEVE": "SLEEVE",
    "SEAL": "SEAL",
    "5EAL": "SEAL",
    "GASKET": "GASKET",
    "GA5KET": "GASKET",
    "FLANGE": "FLANGE",
    "F1ANGE": "FLANGE",
    "HOUSING": "HOUSING",
    "HOUS1NG": "HOUSING",
    "COVER": "COVER",
    "C0VER": "COVER",
    "PLATE": "PLATE",
    "P1ATE": "PLATE",
    "BOLT": "BOLT",
    "B0LT": "BOLT",
    "SCREW": "SCREW",
    "5CREW": "SCREW",
    "WASHER": "WASHER",
    "WA5HER": "WASHER",
    "SPACER": "SPACER",
    "5PACER": "SPACER",
    "SPRING": "SPRING",
    "5PRING": "SPRING",
    "RETAINER": "RETAINER",
    "RETA1NER": "RETAINER",
    "COLLAR": "COLLAR",
    "C0LLAR": "COLLAR",
    "BUSHING": "BUSHING",
    "BUSH1NG": "BUSHING",
    "IMPELLER": "IMPELLER",
    "1MPELLER": "IMPELLER",
    "DIFFUSER": "DIFFUSER",
    "D1FFUSER": "DIFFUSER",
    "VOLUTE": "VOLUTE",
    "V0LUTE": "VOLUTE",
    # 테이블 헤더 용어
    "ESRIPTION": "DESCRIPTION",
    "ESRIPTIO": "DESCRIPTION",
    "ESORIPTION": "DESCRIPTION",
    "ESORIPTIO": "DESCRIPTION",
    "ESORIPTOIN": "DESCRIPTION",
    "ESORIPTON": "DESCRIPTION",
    "DESCR1PT10N": "DESCRIPTION",
    "0ESCRIPTION": "DESCRIPTION",
    "DESCR IPT ION": "DESCRIPTION",
    "DESCRPTION": "DESCRIPTION",
    "MATERIA1": "MATERIAL",
    "MATER1AL": "MATERIAL",
    "MATERIA!": "MATERIAL",
    "MATERIÅL": "MATERIAL",
    "MATERAL": "MATERIAL",
    "QUANT1TY": "QUANTITY",
    "QUANTITV": "QUANTITY",
    "QTY": "QTY",
    "Q7Y": "QTY",
    "PART NO": "PART NO",
    "PART N0": "PART NO",
    "1TEM": "ITEM",
    "ITEM": "ITEM",
    "REMARK5": "REMARKS",
    "REMARK": "REMARK",
    # 추가 헤더/필드명
    "SIZE MFG NO": "SIZE MFG NO",
    "S1ZE": "SIZE",
    "5IZE": "SIZE",
    "MFG NO": "MFG NO",
    "MFG N0": "MFG NO",
    "MFG ND": "MFG NO",
    "MFGNO": "MFG NO",
    "MFG.NO": "MFG NO",
    "UNIT": "UNIT",
    "UN1T": "UNIT",
    "WEIGHT": "WEIGHT",
    "WE1GHT": "WEIGHT",
    "REV": "REV",
    "REVISION": "REVISION",
    "REV1S1ON": "REVISION",
}

# 추가 패턴 규칙 (정규식 기반 교정)
_OCR_PATTERN_RULES = [
    # 숫자/문자 혼동 패턴
    (r"([A-Z])1([A-Z])", r"\1I\2"),      # A1B → AIB
    (r"([A-Z])0([A-Z])", r"\1O\2"),      # A0B → AOB
    (r"^1([A-Z])", r"I\1"),              # 1TEM → ITEM
    (r"([A-Z])1$", r"\1I"),              # BEAR1 → BEARI
    (r"^0([A-Z])", r"O\1"),              # 0RING → ORING
    (r"5([A-Z]{2,})", r"S\1"),           # 5HAFT → SHAFT
    (r"([A-Z]{2,})5$", r"\1S"),          # REMARK5 → REMARKS
    # 특수 문자 혼동
    (r"!", r"L"),                        # MATERIA! → MATERIAL
    (r"\|", r"I"),                       # P|ATE → PIATE
    # 한글 OCR 오류 (영문 도면에서 발생)
    (r"매G", r"MFG"),                    # 매G NO → MFG NO
    (r"면거침", r""),                    # 잘못된 한글 제거
    (r"방경년", r""),                    # 잘못된 한글 제거
    (r"세도", r""),                      # 잘못된 한글 제거
    # 공백 처리
    (r"DESCR\s*IPT\s*ION", r"DESCRIPTION"),  # DESCR IPT ION → DESCRIPTION
    (r"ESORIPT\s*ION", r"DESCRIPTION"),      # ESORIPT ION → DESCRIPTION
    (r"MATERIA\s*L", r"MATERIAL"),           # MATERIA L → MATERIAL
    # 필드명 오류
    (r"MFG\s*ND", r"MFG NO"),                # MFG ND → MFG NO
    (r"SIZE\s+MFG\s*N[DO0]", r"SIZE MFG NO"), # SIZE MFG ND/NO/N0 → SIZE MFG NO
]


class TableService:
    """테이블 검출/추출 서비스 + 일반 텍스트 OCR"""

    def __init__(
        self,
        api_url: str = TABLE_DETECTOR_API_URL,
        paddleocr_url: str = PADDLEOCR_API_URL,
        easyocr_url: str = EASYOCR_API_URL,
        esrgan_url: str = ESRGAN_API_URL,
    ):
        self.api_url = api_url
        self.paddleocr_url = paddleocr_url
        self.easyocr_url = easyocr_url
        self.esrgan_url = esrgan_url

    def extract_tables(
        self,
        image_path: str,
        mode: str = "extract",
        ocr_engine: str = "paddle",
        borderless: bool = False,
        confidence_threshold: float = 0.7,
        min_confidence: int = 50,
        enable_cell_reocr: bool = False,
        enable_crop_upscale: bool = False,
        upscale_scale: int = 2,
    ) -> Dict[str, Any]:
        """이미지에서 테이블 추출 (영역별 크롭 + 품질 필터링)

        Args:
            enable_cell_reocr: EasyOCR로 셀 텍스트 재인식하여 품질 개선
            enable_crop_upscale: 크롭 이미지를 ESRGAN으로 업스케일 후 OCR
            upscale_scale: 업스케일 배율 (2 또는 4)
        """
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
        reocr_stats = {"corrected": 0, "total": 0}
        upscale_stats = {"upscaled": 0, "failed": 0}

        # 1단계: 영역별 크롭 → 각각 extract
        for region_name, (x1r, y1r, x2r, y2r) in _CROP_REGIONS.items():
            crop_box = (int(w * x1r), int(h * y1r), int(w * x2r), int(h * y2r))
            cropped = img.crop(crop_box)

            if cropped.size[0] < 100 or cropped.size[1] < 50:
                continue

            buf = io.BytesIO()
            cropped.save(buf, format="JPEG", quality=95)
            crop_bytes = buf.getvalue()

            # E1-B-2: 크롭 이미지 업스케일 (OCR 전)
            if enable_crop_upscale:
                upscaled_bytes = self._upscale_crop(crop_bytes, scale=upscale_scale)
                if upscaled_bytes:
                    crop_bytes = upscaled_bytes
                    upscale_stats["upscaled"] += 1
                    logger.info(f"크롭 업스케일 완료: {region_name} ({upscale_scale}x)")
                else:
                    upscale_stats["failed"] += 1
                    logger.warning(f"크롭 업스케일 실패: {region_name}")

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
                    # E1-B: 셀 재OCR
                    if enable_cell_reocr:
                        table, stats = self._reocr_table_cells(table, crop_bytes)
                        reocr_stats["corrected"] += stats["corrected"]
                        reocr_stats["total"] += stats["total"]
                    # E1-B-3: 사전 기반 교정 (항상 적용)
                    table, dict_corrections = self._apply_table_dictionary_correction(table)
                    reocr_stats["corrected"] += dict_corrections
                    all_tables.append(table)

            for region in result.get("regions", []):
                if region.get("label") != "table_fallback":
                    region["source_region"] = region_name
                    all_regions.append(region)

        elapsed = (time.time() - start) * 1000

        log_msg = (
            f"테이블 추출 완료: {len(all_regions)}개 영역, "
            f"{len(all_tables)}개 테이블 ({len(_CROP_REGIONS)}개 영역 검색), "
            f"{elapsed:.0f}ms"
        )
        if enable_crop_upscale and upscale_stats["upscaled"] > 0:
            log_msg += f" [업스케일: {upscale_stats['upscaled']}개 영역]"
        if enable_cell_reocr and reocr_stats["total"] > 0:
            log_msg += f" [재OCR: {reocr_stats['corrected']}/{reocr_stats['total']} 셀 수정]"
        logger.info(log_msg)

        return {
            "tables": all_tables,
            "regions": all_regions,
            "tables_count": len(all_tables),
            "regions_count": len(all_regions),
            "image_size": {"width": w, "height": h},
            "processing_time_ms": elapsed,
            "reocr_stats": reocr_stats if enable_cell_reocr else None,
            "upscale_stats": upscale_stats if enable_crop_upscale else None,
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

    def _upscale_crop(
        self, crop_bytes: bytes, scale: int = 2, denoise: float = 0.5
    ) -> bytes | None:
        """ESRGAN으로 크롭 이미지 업스케일

        Args:
            crop_bytes: 크롭된 이미지 바이트
            scale: 업스케일 배율 (2 또는 4)
            denoise: 노이즈 제거 강도 (0-1)

        Returns:
            업스케일된 이미지 바이트, 실패 시 None
        """
        try:
            with httpx.Client(timeout=90.0) as client:
                files = {"file": ("crop.jpg", crop_bytes, "image/jpeg")}
                data = {
                    "scale": str(scale),
                    "denoise_strength": str(denoise),
                }
                resp = client.post(
                    f"{self.esrgan_url}/api/v1/upscale",
                    files=files,
                    data=data,
                )

            if resp.status_code != 200:
                logger.warning(f"ESRGAN API 실패: {resp.status_code}")
                return None

            # ESRGAN API는 항상 바이너리 PNG 이미지를 반환
            raw_content = resp.read()
            if len(raw_content) > 0:
                return raw_content
            else:
                logger.warning("ESRGAN 응답이 비어있음")
                return None

        except httpx.ConnectError:
            logger.warning(f"ESRGAN API 연결 실패 ({self.esrgan_url})")
            return None
        except Exception as e:
            logger.warning(f"ESRGAN 업스케일 오류: {e}")
            return None

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

    # ==================== E1-B: 셀 재OCR ====================

    def _reocr_table_cells(
        self, table: Dict[str, Any], crop_bytes: bytes
    ) -> Tuple[Dict[str, Any], Dict[str, int]]:
        """EasyOCR로 테이블 셀 텍스트 재인식

        Table Detector가 추출한 테이블의 셀 텍스트를 EasyOCR로 다시 인식하여
        "BEAAING" → "BEARING", "3ING" → "RING" 같은 오류를 수정합니다.

        Args:
            table: Table Detector extract 결과 테이블
            crop_bytes: 테이블 영역 크롭 이미지 바이트

        Returns:
            (수정된 테이블, {"corrected": int, "total": int})
        """
        from difflib import SequenceMatcher

        data = table.get("data", [])
        stats = {"corrected": 0, "total": 0}

        if not data:
            return table, stats

        # EasyOCR로 영역 전체 OCR
        easyocr_results = self._call_ocr_on_region(
            crop_bytes, "cell_reocr.jpg", engine="easyocr", lang="en"
        )

        if not easyocr_results:
            logger.debug("셀 재OCR: EasyOCR 결과 없음")
            return table, stats

        # EasyOCR 결과를 단어 단위로 분리하여 lookup 생성
        ocr_words: Dict[str, Tuple[str, float]] = {}
        for det in easyocr_results:
            text = det.get("text", "").strip()
            conf = det.get("confidence", 0.0)
            if not text or conf < 0.5:
                continue
            # 전체 텍스트 추가
            key = text.upper().replace(" ", "").replace("-", "")
            if key and key not in ocr_words:
                ocr_words[key] = (text, conf)
            # 공백으로 분리된 단어도 추가
            for word in text.split():
                word_key = word.upper().replace("-", "")
                if len(word_key) >= 2 and word_key not in ocr_words:
                    ocr_words[word_key] = (word, conf)

        if not ocr_words:
            return table, stats

        # 각 셀 텍스트 수정
        new_data = []
        for row in data:
            new_row = []
            for cell_text in row:
                stats["total"] += 1
                if cell_text and isinstance(cell_text, str) and len(cell_text) >= 2:
                    corrected, was_corrected = self._find_better_match(
                        cell_text, ocr_words
                    )
                    if was_corrected:
                        stats["corrected"] += 1
                        logger.debug(f"셀 재OCR: '{cell_text}' → '{corrected}'")
                    new_row.append(corrected)
                else:
                    new_row.append(cell_text)
            new_data.append(new_row)

        table["data"] = new_data
        if stats["corrected"] > 0:
            table["reocr_applied"] = True
            table["reocr_corrections"] = stats["corrected"]

        return table, stats

    def _find_better_match(
        self, original: str, ocr_words: Dict[str, Tuple[str, float]]
    ) -> Tuple[str, bool]:
        """EasyOCR 결과에서 더 나은 매칭 찾기

        Args:
            original: Table Detector가 인식한 원본 텍스트
            ocr_words: {normalized_key: (text, confidence)} EasyOCR 결과

        Returns:
            (수정된 텍스트, 수정 여부)
        """
        from difflib import SequenceMatcher

        original_norm = original.upper().replace(" ", "").replace("-", "")

        # 1. 정확히 일치하면 원본 유지
        if original_norm in ocr_words:
            return original, False

        # 2. 유사도 기반 매칭 (최소 70% 이상)
        best_match = original
        best_ratio = 0.7
        was_corrected = False

        for key, (text, conf) in ocr_words.items():
            # 길이가 너무 다르면 스킵
            if abs(len(key) - len(original_norm)) > 2:
                continue

            ratio = SequenceMatcher(None, original_norm, key).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = text
                was_corrected = True

        return best_match, was_corrected

    # ==================== E1-B-3: 사전 기반 교정 ====================

    @staticmethod
    def _apply_dictionary_correction(text: str) -> Tuple[str, bool]:
        """OCR 오류 사전을 사용하여 텍스트 교정

        Args:
            text: 원본 텍스트

        Returns:
            (교정된 텍스트, 교정 여부)
        """
        import re

        if not text or len(text) < 2:
            return text, False

        original = text
        corrected = text

        # 1. 단어 단위로 사전 매칭
        words = corrected.split()
        new_words = []
        any_corrected = False

        for word in words:
            word_upper = word.upper()
            if word_upper in _OCR_CORRECTIONS:
                # 사전에서 교정값 찾음
                replacement = _OCR_CORRECTIONS[word_upper]
                # 원본 대소문자 패턴 유지 시도
                if word.isupper():
                    new_words.append(replacement.upper())
                elif word.islower():
                    new_words.append(replacement.lower())
                elif word.istitle():
                    new_words.append(replacement.title())
                else:
                    new_words.append(replacement)
                any_corrected = True
            else:
                new_words.append(word)

        corrected = " ".join(new_words)

        # 2. 패턴 규칙 적용 (단어 단위 교정 후)
        for pattern, replacement in _OCR_PATTERN_RULES:
            new_corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
            if new_corrected != corrected:
                corrected = new_corrected
                any_corrected = True

        # 3. 전체 텍스트 사전 매칭 (공백 제거 후)
        text_no_space = corrected.upper().replace(" ", "").replace("-", "")
        if text_no_space in _OCR_CORRECTIONS:
            corrected = _OCR_CORRECTIONS[text_no_space]
            any_corrected = True

        return corrected, any_corrected and (corrected != original)

    def _apply_table_dictionary_correction(
        self, table: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        """테이블 전체에 사전 기반 교정 적용

        Args:
            table: 테이블 데이터

        Returns:
            (교정된 테이블, 교정 수)
        """
        data = table.get("data", [])
        if not data:
            return table, 0

        corrections = 0
        new_data = []

        for row in data:
            new_row = []
            for cell_text in row:
                if cell_text and isinstance(cell_text, str):
                    corrected, was_corrected = self._apply_dictionary_correction(cell_text)
                    if was_corrected:
                        corrections += 1
                        logger.info(f"사전 교정: '{cell_text}' → '{corrected}'")
                    new_row.append(corrected)
                else:
                    new_row.append(cell_text)
            new_data.append(new_row)

        table["data"] = new_data
        if corrections > 0:
            table["dictionary_corrections"] = corrections

        return table, corrections

    # ==================== 일반 텍스트 OCR ====================

    def extract_text_regions(
        self,
        image_path: str,
        ocr_engine: str = "paddleocr",
        lang: str = "en",
    ) -> Dict[str, Any]:
        """표제란/NOTES 등 비테이블 텍스트 영역 OCR

        Table Detector와 별개로, PaddleOCR/EasyOCR을 직접 호출하여
        비테이블 영역의 일반 텍스트(한글/영어)를 추출합니다.

        Returns:
            {"text_regions": [...], "processing_time_ms": float}
        """
        start = time.time()

        try:
            from PIL import Image
        except ImportError:
            logger.warning("PIL 없음 — 텍스트 영역 추출 불가")
            return {"text_regions": [], "processing_time_ms": 0}

        img = Image.open(image_path)
        w, h = img.size

        text_regions = []

        for region_name, (x1r, y1r, x2r, y2r) in _TEXT_REGIONS.items():
            crop_box = (int(w * x1r), int(h * y1r), int(w * x2r), int(h * y2r))
            cropped = img.crop(crop_box)

            if cropped.size[0] < 50 or cropped.size[1] < 50:
                continue

            buf = io.BytesIO()
            cropped.save(buf, format="JPEG", quality=95)
            crop_bytes = buf.getvalue()

            detections = self._call_ocr_on_region(
                crop_bytes, f"{region_name}.jpg", ocr_engine, lang
            )

            if not detections:
                continue

            # 크롭 좌표 → 원본 이미지 좌표로 변환
            adjusted = []
            for det in detections:
                text = det.get("text", "").strip()
                if not text or len(text) < 2:
                    continue
                conf = det.get("confidence", 0.0)
                if conf < 0.3:
                    continue

                bbox = det.get("bbox", det.get("position", []))
                if bbox and len(bbox) == 4:
                    # 4점 bbox → offset 적용
                    abs_bbox = [
                        [pt[0] + crop_box[0], pt[1] + crop_box[1]]
                        for pt in bbox
                    ]
                else:
                    abs_bbox = []

                adjusted.append({
                    "text": text,
                    "confidence": conf,
                    "bbox": abs_bbox,
                })

            if adjusted:
                text_regions.append({
                    "region": region_name,
                    "crop_box": list(crop_box),
                    "detections": adjusted,
                    "text_count": len(adjusted),
                    "full_text": " ".join(d["text"] for d in adjusted),
                })

        elapsed = (time.time() - start) * 1000
        logger.info(
            f"텍스트 영역 OCR 완료: {len(text_regions)}개 영역, "
            f"총 {sum(r['text_count'] for r in text_regions)}개 텍스트, "
            f"{elapsed:.0f}ms"
        )

        return {
            "text_regions": text_regions,
            "processing_time_ms": elapsed,
        }

    def _call_ocr_on_region(
        self, file_bytes: bytes, filename: str,
        engine: str = "paddleocr", lang: str = "en",
    ) -> list:
        """PaddleOCR 또는 EasyOCR로 이미지 영역 OCR"""
        try:
            with httpx.Client(timeout=60.0) as client:
                files = {"file": (filename, file_bytes, "image/jpeg")}

                if engine == "easyocr":
                    data = {"languages": lang, "detail": "true"}
                    url = f"{self.easyocr_url}/api/v1/ocr"
                else:
                    data = {
                        "lang": lang,
                        "ocr_version": "PP-OCRv5",
                        "min_confidence": "0.3",
                    }
                    url = f"{self.paddleocr_url}/api/v1/ocr"

                resp = client.post(url, files=files, data=data)

            if resp.status_code != 200:
                logger.warning(f"OCR API {engine} 실패: {resp.status_code}")
                return []

            result = resp.json()

            # EasyOCR: {"data": {"texts": [...]}}
            # PaddleOCR: {"detections": [...]} or {"results": [...]}
            if engine == "easyocr":
                data_obj = result.get("data", {})
                if isinstance(data_obj, dict):
                    return data_obj.get("texts", [])
            return result.get("detections", result.get("results", []))

        except httpx.ConnectError:
            logger.warning(f"OCR API {engine} 연결 실패")
            return []
        except Exception as e:
            logger.warning(f"OCR API {engine} 호출 실패: {e}")
            return []

    # ==================== 헬스체크 ====================

    def health_check(self) -> bool:
        """Table Detector 서비스 상태 확인"""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self.api_url}/health")
                return resp.status_code == 200
        except Exception:
            return False
