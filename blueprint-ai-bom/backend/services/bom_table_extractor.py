"""BOM Table Extractor Service

도면 이미지에서 BOM 테이블을 직접 추출하는 서비스
- DocLayout-YOLO: BOM 테이블 영역 검출
- TableStructureRecognizer: 테이블 구조 인식 및 OCR
- 자동 회전 감지 및 보정 (세로 텍스트 처리)

통합 일자: 2026-01-17
회전 보정 추가: 2026-01-17
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class ExtractedBOMItem:
    """추출된 BOM 항목"""
    item_no: Optional[int] = None
    part_name: str = ""
    material: str = ""
    quantity: int = 1
    spec: str = ""
    remark: str = ""
    confidence: float = 0.0
    raw_cells: Dict[str, str] = field(default_factory=dict)


@dataclass
class BOMTableExtractionResult:
    """BOM 테이블 추출 결과"""
    success: bool
    items: List[ExtractedBOMItem] = field(default_factory=list)
    table_type: str = "unknown"  # "title_block", "parts_list", "revision"
    raw_structure: Optional[Dict[str, Any]] = None
    raw_ocr: List[Dict[str, Any]] = field(default_factory=list)
    table_bbox: Optional[Tuple[float, float, float, float]] = None
    processing_time_ms: float = 0.0
    error_message: str = ""


class BOMTableExtractor:
    """도면에서 BOM 테이블 추출"""

    # 컬럼 매핑 패턴 (다양한 표현 지원)
    COLUMN_PATTERNS = {
        "item_no": [r"no\.?", r"item", r"품번", r"번호", r"#"],
        "part_name": [r"part\s*name", r"name", r"description", r"품명", r"부품명", r"명칭"],
        "material": [r"material", r"재질", r"재료", r"mat"],
        "quantity": [r"qty", r"quantity", r"수량", r"q'?ty"],
        "spec": [r"spec", r"specification", r"size", r"규격", r"사이즈", r"치수"],
        "remark": [r"remark", r"remarks", r"note", r"비고", r"notes"],
    }

    def __init__(self):
        self._layout_analyzer = None
        self._table_recognizer = None

    @property
    def layout_analyzer(self):
        """레이아웃 분석기 (지연 로딩)"""
        if self._layout_analyzer is None:
            from services.layout_analyzer import get_layout_analyzer
            self._layout_analyzer = get_layout_analyzer()
        return self._layout_analyzer

    @property
    def table_recognizer(self):
        """테이블 구조 인식기 (지연 로딩)"""
        if self._table_recognizer is None:
            from services.table_structure_recognizer import get_table_structure_recognizer
            self._table_recognizer = get_table_structure_recognizer()
        return self._table_recognizer

    def extract_from_image(
        self,
        image_path: str,
        conf_threshold: float = 0.1,
        table_index: int = 0
    ) -> BOMTableExtractionResult:
        """
        이미지 파일에서 BOM 테이블 추출

        Args:
            image_path: 이미지 파일 경로
            conf_threshold: 테이블 검출 신뢰도 임계값
            table_index: 추출할 테이블 인덱스 (여러 개인 경우)

        Returns:
            BOMTableExtractionResult: 추출 결과
        """
        import time
        start_time = time.time()

        try:
            # 1. 이미지 로드
            image = Image.open(image_path).convert("RGB")

            # 2. 테이블 영역 검출
            if not self.layout_analyzer.is_available:
                return BOMTableExtractionResult(
                    success=False,
                    error_message="DocLayout-YOLO 사용 불가",
                    processing_time_ms=(time.time() - start_time) * 1000
                )

            detections = self.layout_analyzer.detect(image_path, conf_threshold=conf_threshold)
            table_detections = [d for d in detections if d.region_type == "BOM_TABLE"]

            if not table_detections:
                return BOMTableExtractionResult(
                    success=False,
                    error_message="BOM 테이블 영역을 검출하지 못했습니다",
                    processing_time_ms=(time.time() - start_time) * 1000
                )

            if table_index >= len(table_detections):
                return BOMTableExtractionResult(
                    success=False,
                    error_message=f"테이블 인덱스 초과 (검출: {len(table_detections)}개)",
                    processing_time_ms=(time.time() - start_time) * 1000
                )

            # 3. 선택된 테이블 영역 크롭
            table_det = table_detections[table_index]
            table_image = image.crop(table_det.bbox)

            # 4. 테이블 추출
            result = self.extract_from_table_image(table_image)
            result.table_bbox = table_det.bbox
            result.processing_time_ms = (time.time() - start_time) * 1000

            return result

        except Exception as e:
            logger.error(f"[BOMTableExtractor] 추출 실패: {e}")
            return BOMTableExtractionResult(
                success=False,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )

    def extract_from_table_image(
        self,
        table_image: Image.Image,
        upscale_factor: int = 5,
        auto_rotate: bool = True
    ) -> BOMTableExtractionResult:
        """
        테이블 이미지에서 BOM 데이터 추출

        Args:
            table_image: 테이블 영역 이미지
            upscale_factor: OCR 업스케일 배율
            auto_rotate: 자동 회전 감지 및 보정 (기본값: True)

        Returns:
            BOMTableExtractionResult: 추출 결과

        Note:
            자동 회전은 OCR에만 적용됩니다. 테이블 구조 인식은 원본 이미지에서
            수행하고, 회전이 필요한 경우 OCR만 회전된 이미지에서 수행합니다.
            이는 TableTransformer가 회전된 이미지에서 구조를 인식하지 못하는
            문제를 해결합니다.
        """
        import time
        start_time = time.time()

        try:
            if not self.table_recognizer.is_available:
                return BOMTableExtractionResult(
                    success=False,
                    error_message="TableStructureRecognizer 사용 불가",
                    processing_time_ms=(time.time() - start_time) * 1000
                )

            applied_rotation = 0
            ocr_image = table_image  # OCR용 이미지 (회전 가능)

            # 0. 자동 회전 감지 (OCR용)
            if auto_rotate:
                applied_rotation, rotation_results = self.table_recognizer.detect_text_rotation(
                    table_image,
                    angles=[0, 90, 180, 270]
                )
                if applied_rotation != 0:
                    logger.info(f"[BOMTableExtractor] OCR용 이미지 {applied_rotation}° 회전 적용")
                    ocr_image = self.table_recognizer._rotate_image(table_image, applied_rotation)

            # 1. 테이블 구조 인식 (원본 이미지에서 수행)
            structure_result = self.table_recognizer.recognize_structure(table_image)
            structure = structure_result.structure

            # 구조 인식 실패 시 회전된 이미지로 재시도
            if structure.rows == 0 or structure.columns == 0:
                if applied_rotation != 0:
                    logger.info("[BOMTableExtractor] 원본 구조 인식 실패, 회전된 이미지로 재시도")
                    rotated_result = self.table_recognizer.recognize_structure(ocr_image)
                    if rotated_result.structure.rows > 0 and rotated_result.structure.columns > 0:
                        structure = rotated_result.structure
                        # 회전된 이미지가 구조 인식에 성공하면 그 이미지 사용
                        table_image = ocr_image
                        logger.info(f"[BOMTableExtractor] 회전된 이미지에서 구조 인식 성공: {structure.rows}행 x {structure.columns}열")

            if structure.rows == 0 or structure.columns == 0:
                # 구조 인식 실패해도 OCR 결과는 반환
                ocr_results = self.table_recognizer.extract_whole_table_text(
                    ocr_image,
                    upscale_factor=upscale_factor,
                    confidence_threshold=0.3
                )
                return BOMTableExtractionResult(
                    success=False,
                    error_message="테이블 구조를 인식하지 못했습니다 (OCR 결과는 포함됨)",
                    raw_structure={"applied_rotation": applied_rotation},
                    raw_ocr=ocr_results,
                    processing_time_ms=(time.time() - start_time) * 1000
                )

            # 2. 전체 테이블 OCR (회전된 이미지에서 수행 - 더 정확함)
            ocr_results = self.table_recognizer.extract_whole_table_text(
                ocr_image,
                upscale_factor=upscale_factor,
                confidence_threshold=0.3
            )

            # 3. 셀별 OCR (구조 매핑용 - 원본/회전 이미지 사용)
            cell_result = self.table_recognizer.recognize_and_extract(
                table_image,
                upscale_factor=upscale_factor,
                skip_ocr=False
            )
            table_dict = self.table_recognizer.get_table_as_dict(cell_result.structure)

            # 4. 테이블 타입 판별
            table_type = self._detect_table_type(ocr_results, table_dict)

            # 5. BOM 항목 파싱
            items = self._parse_bom_items(table_dict, ocr_results, table_type)

            return BOMTableExtractionResult(
                success=True,
                items=items,
                table_type=table_type,
                raw_structure={
                    "rows": structure.rows,
                    "columns": structure.columns,
                    "data": table_dict.get("data", []),
                    "applied_rotation": applied_rotation
                },
                raw_ocr=ocr_results,
                processing_time_ms=(time.time() - start_time) * 1000
            )

        except Exception as e:
            logger.error(f"[BOMTableExtractor] 테이블 추출 실패: {e}")
            return BOMTableExtractionResult(
                success=False,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )

    def _detect_table_type(
        self,
        ocr_results: List[Dict[str, Any]],
        table_dict: Dict[str, Any]
    ) -> str:
        """테이블 타입 판별"""
        all_text = " ".join([r["text"].lower() for r in ocr_results])

        # Parts List 키워드
        if any(kw in all_text for kw in ["part name", "material", "qty", "quantity", "품명", "수량"]):
            return "parts_list"

        # Title Block 키워드
        if any(kw in all_text for kw in ["dwg", "drawing", "date", "scale", "approved", "도면번호", "승인"]):
            return "title_block"

        # Revision 키워드
        if any(kw in all_text for kw in ["revision", "rev", "change", "개정"]):
            return "revision"

        return "unknown"

    def _parse_bom_items(
        self,
        table_dict: Dict[str, Any],
        ocr_results: List[Dict[str, Any]],
        table_type: str
    ) -> List[ExtractedBOMItem]:
        """테이블 데이터를 BOM 항목으로 파싱"""
        items = []
        data = table_dict.get("data", [])

        if not data or len(data) < 2:
            return items

        # 헤더 행 찾기 (첫 번째 행 가정)
        header_row = data[0]
        column_mapping = self._map_columns(header_row)

        # 데이터 행 파싱
        for row_idx, row in enumerate(data[1:], start=1):
            item = ExtractedBOMItem()
            item.raw_cells = {f"col_{i}": cell for i, cell in enumerate(row)}

            # 컬럼 매핑에 따라 필드 할당
            if "item_no" in column_mapping:
                col = column_mapping["item_no"]
                if col < len(row):
                    try:
                        item.item_no = int(re.sub(r'\D', '', row[col] or "0") or "0")
                    except (ValueError, TypeError):
                        item.item_no = row_idx

            if "part_name" in column_mapping:
                col = column_mapping["part_name"]
                if col < len(row):
                    item.part_name = row[col] or ""

            if "material" in column_mapping:
                col = column_mapping["material"]
                if col < len(row):
                    item.material = row[col] or ""

            if "quantity" in column_mapping:
                col = column_mapping["quantity"]
                if col < len(row):
                    try:
                        item.quantity = int(re.sub(r'\D', '', row[col] or "1") or "1")
                    except (ValueError, TypeError):
                        item.quantity = 1

            if "spec" in column_mapping:
                col = column_mapping["spec"]
                if col < len(row):
                    item.spec = row[col] or ""

            if "remark" in column_mapping:
                col = column_mapping["remark"]
                if col < len(row):
                    item.remark = row[col] or ""

            # 유효한 항목만 추가 (최소한 부품명이 있어야 함)
            if item.part_name or item.item_no:
                items.append(item)

        return items

    def _map_columns(self, header_row: List[str]) -> Dict[str, int]:
        """헤더 행에서 컬럼 인덱스 매핑"""
        mapping = {}

        for col_idx, header in enumerate(header_row):
            if not header:
                continue
            header_lower = header.lower().strip()

            for field_name, patterns in self.COLUMN_PATTERNS.items():
                if field_name in mapping:
                    continue  # 이미 매핑됨

                for pattern in patterns:
                    if re.search(pattern, header_lower, re.IGNORECASE):
                        mapping[field_name] = col_idx
                        break

        return mapping

    def extract_all_tables(
        self,
        image_path: str,
        conf_threshold: float = 0.1
    ) -> List[BOMTableExtractionResult]:
        """
        이미지에서 모든 BOM 테이블 추출

        Args:
            image_path: 이미지 파일 경로
            conf_threshold: 테이블 검출 신뢰도 임계값

        Returns:
            List[BOMTableExtractionResult]: 모든 테이블 추출 결과
        """
        results = []

        try:
            # 테이블 영역 검출
            detections = self.layout_analyzer.detect(image_path, conf_threshold=conf_threshold)
            table_detections = [d for d in detections if d.region_type == "BOM_TABLE"]

            if not table_detections:
                return [BOMTableExtractionResult(
                    success=False,
                    error_message="BOM 테이블 영역을 검출하지 못했습니다"
                )]

            image = Image.open(image_path).convert("RGB")

            for idx, table_det in enumerate(table_detections):
                table_image = image.crop(table_det.bbox)
                result = self.extract_from_table_image(table_image)
                result.table_bbox = table_det.bbox
                results.append(result)

                logger.info(f"[BOMTableExtractor] 테이블 #{idx + 1}: "
                           f"{result.table_type}, {len(result.items)}개 항목")

        except Exception as e:
            logger.error(f"[BOMTableExtractor] 전체 테이블 추출 실패: {e}")
            results.append(BOMTableExtractionResult(
                success=False,
                error_message=str(e)
            ))

        return results

    def to_bom_service_format(
        self,
        extraction_result: BOMTableExtractionResult,
        session_id: str = ""
    ) -> Dict[str, Any]:
        """
        추출 결과를 BOMService 형식으로 변환

        Args:
            extraction_result: BOM 테이블 추출 결과
            session_id: 세션 ID

        Returns:
            Dict: BOMService.generate_bom() 호환 형식
        """
        from datetime import datetime

        items = []
        for idx, item in enumerate(extraction_result.items, start=1):
            items.append({
                "item_no": item.item_no or idx,
                "class_name": item.part_name,
                "model_name": item.spec or "-",
                "quantity": item.quantity,
                "unit_price": 0,  # 추후 가격 DB 매핑
                "total_price": 0,
                "avg_confidence": item.confidence,
                "detection_ids": [],
                "lead_time": "-",
                "supplier": "-",
                "remarks": item.remark or None,
                "dimensions": [item.spec] if item.spec else [],
                "material": item.material,
                "source": "table_extraction",
            })

        total_quantity = sum(item["quantity"] for item in items)

        return {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "items": items,
            "summary": {
                "total_items": len(items),
                "total_quantity": total_quantity,
                "subtotal": 0,
                "vat": 0,
                "total": 0,
            },
            "extraction_source": "table_structure_recognizer",
            "table_type": extraction_result.table_type,
            "raw_structure": extraction_result.raw_structure,
        }


# 싱글톤 인스턴스
_bom_table_extractor: Optional[BOMTableExtractor] = None


def get_bom_table_extractor() -> BOMTableExtractor:
    """BOM 테이블 추출기 인스턴스 반환 (싱글톤)"""
    global _bom_table_extractor
    if _bom_table_extractor is None:
        _bom_table_extractor = BOMTableExtractor()
    return _bom_table_extractor
