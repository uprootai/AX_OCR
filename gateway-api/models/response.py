"""
Response Models for Gateway API

응답 관련 Pydantic 모델들을 정의합니다.
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any


class HealthResponse(BaseModel):
    """Health check 응답"""
    status: str
    service: str
    version: str
    timestamp: str
    services: Dict[str, str]


class DetectionResult(BaseModel):
    """YOLO 검출 결과"""
    class_id: int = Field(..., description="클래스 ID")
    class_name: str = Field(..., description="클래스 이름")
    confidence: float = Field(..., description="신뢰도 (0-1)")
    bbox: Dict[str, int] = Field(..., description="바운딩 박스 {x, y, width, height}")


class YOLOResults(BaseModel):
    """YOLO 검출 결과"""
    detections: List[DetectionResult] = Field(default=[], description="검출된 객체 목록")
    total_detections: int = Field(0, description="총 검출 개수")
    processing_time: float = Field(0, description="YOLO 처리 시간 (초)")
    model_used: Optional[str] = Field(None, description="사용된 모델")
    visualized_image: Optional[str] = Field(None, description="Base64 인코딩된 시각화 이미지")


class DimensionData(BaseModel):
    """치수 정보"""
    value: Optional[str] = Field(None, description="치수 값")
    unit: Optional[str] = Field(None, description="단위")
    tolerance: Optional[Dict[str, Any]] = Field(None, description="공차 정보")
    bbox: Optional[Dict[str, int]] = Field(None, description="위치")


class OCRResults(BaseModel):
    """OCR 결과"""
    dimensions: List[DimensionData] = Field(default=[], description="추출된 치수")
    gdt_symbols: List[Dict[str, Any]] = Field(default=[], description="GD&T 기호")
    text_blocks: List[Dict[str, Any]] = Field(default=[], description="텍스트 블록")
    tables: List[Any] = Field(default=[], description="테이블 데이터 (nested structure)")
    processing_time: float = Field(0, description="OCR 처리 시간 (초)")
    visualized_image: Optional[str] = Field(None, description="Base64 인코딩된 시각화 이미지")


class ComponentData(BaseModel):
    """세그멘테이션 컴포넌트"""
    component_id: Optional[int] = Field(None, description="컴포넌트 ID")
    id: Optional[int] = Field(None, description="컴포넌트 ID (alternative)")
    class_id: Optional[int] = Field(None, description="클래스 ID")
    classification: Optional[str] = Field(None, description="분류 이름")
    bbox: Dict[str, Any] = Field(default={}, description="바운딩 박스")
    area: Optional[int] = Field(None, description="면적 (픽셀)")
    confidence: Optional[float] = Field(None, description="신뢰도")

    model_config = ConfigDict(extra="allow")  # Allow additional fields from EDGNet


class SegmentationResults(BaseModel):
    """세그멘테이션 결과"""
    components: List[Any] = Field(default=[], description="감지된 컴포넌트")  # Changed to Any for flexibility
    total_components: int = Field(0, description="총 컴포넌트 수")
    processing_time: float = Field(0, description="세그멘테이션 처리 시간 (초)")
    visualized_image: Optional[str] = Field(None, description="Base64 인코딩된 시각화 이미지")

    model_config = ConfigDict(extra="allow")  # Allow additional fields


class ToleranceResult(BaseModel):
    """공차 예측 결과"""
    feasibility_score: Optional[float] = Field(None, description="제조 가능성 점수 (0-1)")
    predicted_tolerance: Optional[float] = Field(None, description="예측된 공차 (mm)")
    material: Optional[str] = Field(None, description="재질")
    manufacturing_process: Optional[str] = Field(None, description="제조 공정")
    processing_time: float = Field(0, description="공차 예측 처리 시간 (초)")

    model_config = ConfigDict(extra="allow")  # Allow additional fields from Skin Model API


class ProcessData(BaseModel):
    """전체 처리 결과 데이터"""
    yolo_results: Optional[YOLOResults] = Field(None, description="YOLO 검출 결과")
    ocr_results: Optional[OCRResults] = Field(None, description="OCR 추출 결과")
    segmentation_results: Optional[SegmentationResults] = Field(None, description="세그멘테이션 결과")
    tolerance_results: Optional[ToleranceResult] = Field(None, description="공차 예측 결과")
    ensemble: Optional[Dict[str, Any]] = Field(None, description="앙상블 병합 결과")
    pipeline_mode: str = Field("hybrid", description="사용된 파이프라인 모드")

    model_config = {
        "json_schema_extra": {
            "example": {
                "yolo_results": {
                    "detections": [
                        {
                            "class_id": 1,
                            "class_name": "linear_dim",
                            "confidence": 0.92,
                            "bbox": {"x": 100, "y": 200, "width": 50, "height": 30}
                        }
                    ],
                    "total_detections": 28,
                    "processing_time": 0.15
                },
                "ocr_results": {
                    "dimensions": [
                        {
                            "value": "50.5",
                            "unit": "mm",
                            "tolerance": {"upper": "+0.1", "lower": "-0.1"}
                        }
                    ],
                    "processing_time": 2.34
                },
                "segmentation_results": {
                    "components": [
                        {
                            "component_id": 1,
                            "class_id": 1,
                            "bbox": {"x": 10, "y": 20, "width": 100, "height": 50},
                            "area": 5000
                        }
                    ],
                    "total_components": 15,
                    "processing_time": 1.23
                },
                "tolerance_results": {
                    "feasibility_score": 0.85,
                    "predicted_tolerance": 0.05,
                    "material": "aluminum",
                    "manufacturing_process": "machining",
                    "processing_time": 0.45
                },
                "pipeline_mode": "hybrid"
            }
        }
    }


class ProcessResponse(BaseModel):
    """전체 파이프라인 처리 응답"""
    status: str = Field(..., description="처리 상태 (success/error)")
    data: ProcessData = Field(..., description="처리 결과 데이터")
    processing_time: float = Field(..., description="총 처리 시간 (초)")
    file_id: str = Field(..., description="파일 식별자")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "data": {
                    "yolo_results": {
                        "total_detections": 28,
                        "processing_time": 0.15
                    },
                    "ocr_results": {
                        "dimensions": [],
                        "processing_time": 2.34
                    },
                    "pipeline_mode": "hybrid"
                },
                "processing_time": 5.67,
                "file_id": "abc123-def456"
            }
        }
    }


class CostBreakdown(BaseModel):
    """비용 세부 내역"""
    material_cost: float = Field(..., description="재료비 (USD)")
    machining_cost: float = Field(..., description="가공비 (USD)")
    tolerance_premium: float = Field(..., description="공차 정밀도 추가 비용 (USD)")
    total_cost: float = Field(..., description="총 비용 (USD)")


class QuoteData(BaseModel):
    """견적서 데이터"""
    quote_number: str = Field(..., description="견적서 번호")
    part_name: Optional[str] = Field(None, description="부품 이름")
    material: Optional[str] = Field(None, description="재질")
    estimated_weight: Optional[float] = Field(None, description="예상 중량 (kg)")
    estimated_machining_time: Optional[float] = Field(None, description="예상 가공 시간 (시간)")
    cost_breakdown: CostBreakdown = Field(..., description="비용 세부 내역")
    dimensions_analyzed: int = Field(0, description="분석된 치수 개수")
    gdt_analyzed: int = Field(0, description="분석된 GD&T 개수")
    confidence_score: float = Field(0, description="견적 신뢰도 (0-1)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "quote_number": "Q2025-001",
                "part_name": "Intermediate Shaft",
                "material": "Steel",
                "estimated_weight": 2.5,
                "estimated_machining_time": 4.5,
                "cost_breakdown": {
                    "material_cost": 12.50,
                    "machining_cost": 225.00,
                    "tolerance_premium": 27.00,
                    "total_cost": 264.50
                },
                "dimensions_analyzed": 15,
                "gdt_analyzed": 5,
                "confidence_score": 0.88
            }
        }
    }


class QuoteResponse(BaseModel):
    """견적서 생성 응답"""
    status: str = Field(..., description="처리 상태 (success/error)")
    data: QuoteData = Field(..., description="견적서 데이터")
    processing_time: float = Field(..., description="처리 시간 (초)")
