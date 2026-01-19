"""Detection Schemas"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    """검증 상태"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    MANUAL = "manual"


class DetectionBackend(str, Enum):
    """검출 백엔드"""
    YOLO = "yolo"
    DETECTRON2 = "detectron2"


class DetectionConfig(BaseModel):
    """검출 설정 - 모델별 최적화 값"""
    confidence: float = Field(default=0.40, ge=0.05, le=1.0, description="신뢰도 임계값")
    iou_threshold: float = Field(default=0.50, ge=0.1, le=0.95, description="NMS IOU 임계값")
    imgsz: int = Field(default=1024, ge=320, le=4096, description="입력 이미지 크기")
    model_type: str = Field(
        default="bom_detector",
        description="YOLO 모델 타입 (bom_detector, pid_symbol, pid_class_aware, pid_class_agnostic, engineering)"
    )
    use_sahi: bool = Field(default=False, description="P&ID용 SAHI 슬라이싱 활성화")
    device: Optional[str] = Field(default=None, description="디바이스 (cuda/cpu)")

    # Detectron2 통합 옵션
    backend: DetectionBackend = Field(
        default=DetectionBackend.YOLO,
        description="검출 백엔드 (yolo: 빠른 검출, detectron2: 마스킹 포함)"
    )
    return_masks: bool = Field(
        default=False,
        description="마스크 반환 여부 (detectron2 전용, RLE 인코딩)"
    )
    return_polygons: bool = Field(
        default=True,
        description="폴리곤 반환 여부 (detectron2 전용, SVG/Canvas용 윤곽선)"
    )


class BoundingBox(BaseModel):
    """바운딩 박스"""
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center(self) -> tuple:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)


class MaskRLE(BaseModel):
    """RLE 인코딩된 마스크"""
    size: List[int] = Field(description="마스크 크기 [height, width]")
    counts: List[int] = Field(description="RLE 카운트")


class Detection(BaseModel):
    """단일 검출 결과"""
    id: str = Field(description="검출 ID")
    class_id: int = Field(description="클래스 ID")
    class_name: str = Field(description="클래스 이름")
    confidence: float = Field(ge=0.0, le=1.0, description="신뢰도")
    bbox: BoundingBox = Field(description="바운딩 박스")
    model_id: str = Field(description="검출 모델 ID")

    # 검증 관련
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        description="검증 상태"
    )
    modified_class_name: Optional[str] = Field(
        default=None,
        description="수정된 클래스 이름"
    )
    modified_bbox: Optional[BoundingBox] = Field(
        default=None,
        description="수정된 바운딩 박스"
    )

    # Detectron2 마스킹 결과 (선택적)
    mask: Optional[MaskRLE] = Field(
        default=None,
        description="RLE 인코딩된 인스턴스 마스크 (detectron2)"
    )
    polygons: Optional[List[List[List[float]]]] = Field(
        default=None,
        description="윤곽선 폴리곤 좌표 (detectron2, SVG/Canvas용)"
    )


class DetectionResult(BaseModel):
    """검출 결과"""
    session_id: str
    detections: List[Detection]
    total_count: int
    model_id: str
    processing_time_ms: float
    image_width: int
    image_height: int


class VerificationUpdate(BaseModel):
    """검증 업데이트 요청"""
    detection_id: str
    status: VerificationStatus
    modified_class_name: Optional[str] = None
    modified_bbox: Optional[BoundingBox] = None


class BulkVerificationUpdate(BaseModel):
    """일괄 검증 업데이트 요청"""
    updates: List[VerificationUpdate]


class ManualDetection(BaseModel):
    """수동 검출 추가 (YOLO 노드에서 가져온 검출도 이 스키마 사용)"""
    class_name: str
    bbox: BoundingBox
    confidence: float = 1.0  # YOLO에서 가져올 때 실제 신뢰도 전달, 수동 추가 시 1.0
    label: Optional[str] = None  # BWMS 장비 라벨 (ECU-1, FMU-1 등)


class BulkImportRequest(BaseModel):
    """일괄 검출 가져오기 요청 (YOLO 노드에서 대량 검출 결과 가져올 때 사용)"""
    detections: List[ManualDetection]
    initial_status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        description="가져온 검출의 초기 상태 (YOLO: pending, 수작업: manual)"
    )
