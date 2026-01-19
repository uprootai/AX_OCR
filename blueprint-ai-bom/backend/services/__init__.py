"""Blueprint AI BOM - Services

서비스 레이어: 비즈니스 로직 담당
- SessionService: 세션 생성, 조회, 업데이트, 삭제
- DetectionService: YOLO/Detectron2 기반 객체 검출
- Detectron2Service: Mask R-CNN 인스턴스 세그멘테이션 (2026-01-17 추가)
- BOMService: BOM 생성 및 내보내기 (Excel, CSV, JSON, PDF)
- LayoutAnalyzer: DocLayout-YOLO 기반 레이아웃 분석 (2025-12-31 추가)
- PDFReportService: P&ID 분석 결과 PDF 리포트 생성 (2025-12-31 추가)
- TableStructureRecognizer: TableTransformer+EasyOCR 기반 테이블 구조 인식 (2026-01-17 추가)
"""

from .session_service import SessionService
from .detection_service import DetectionService
from .detectron2_service import Detectron2Service, get_detectron2_service
from .bom_service import BOMService
from .layout_analyzer import LayoutAnalyzer, get_layout_analyzer
from .pdf_report_service import PDFReportService, get_pdf_report_service
from .table_structure_recognizer import (
    TableStructureRecognizer,
    get_table_structure_recognizer,
    TableStructure,
    TableCell,
    TableRecognitionResult,
)
from .bom_table_extractor import (
    BOMTableExtractor,
    get_bom_table_extractor,
    ExtractedBOMItem,
    BOMTableExtractionResult,
)

__all__ = [
    "SessionService",
    "DetectionService",
    "Detectron2Service",
    "get_detectron2_service",
    "BOMService",
    "LayoutAnalyzer",
    "get_layout_analyzer",
    "PDFReportService",
    "get_pdf_report_service",
    "TableStructureRecognizer",
    "get_table_structure_recognizer",
    "TableStructure",
    "TableCell",
    "TableRecognitionResult",
    "BOMTableExtractor",
    "get_bom_table_extractor",
    "ExtractedBOMItem",
    "BOMTableExtractionResult",
]
