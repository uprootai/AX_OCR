"""Session Schemas"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from .classification import DrawingType  # 도면 타입은 classification.py에서 정의


class SessionStatus(str, Enum):
    """세션 상태"""
    CREATED = "created"
    UPLOADED = "uploaded"
    DETECTING = "detecting"
    DETECTED = "detected"
    VERIFYING = "verifying"
    VERIFIED = "verified"
    GENERATING_BOM = "generating_bom"
    COMPLETED = "completed"
    ERROR = "error"


class SessionCreate(BaseModel):
    """세션 생성 요청"""
    filename: str
    file_path: str
    drawing_type: DrawingType = DrawingType.AUTO  # 빌더에서 설정한 도면 타입


class SessionResponse(BaseModel):
    """세션 응답"""
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    filename: str
    file_path: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    detection_count: int = 0
    verified_count: int = 0
    bom_generated: bool = False
    error_message: Optional[str] = None

    # 이미지 정보
    image_width: Optional[int] = None
    image_height: Optional[int] = None

    # 도면 분류 정보
    drawing_type: DrawingType = DrawingType.AUTO
    drawing_type_source: str = "builder"  # builder, vlm, manual
    drawing_type_confidence: Optional[float] = None  # VLM 분류 시 신뢰도


class SessionDetail(BaseModel):
    """세션 상세 정보"""
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    filename: str
    file_path: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime

    # 도면 분류 정보
    drawing_type: DrawingType = DrawingType.AUTO
    drawing_type_source: str = "builder"  # builder, vlm, manual
    drawing_type_confidence: Optional[float] = None  # VLM 분류 시 신뢰도
    vlm_classification_result: Optional[str] = None  # VLM 분류 결과 (auto인 경우)

    # 검출 정보
    detections: List[Dict[str, Any]] = []
    detection_count: int = 0

    # 검증 정보
    verification_status: Dict[str, str] = {}
    verified_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0

    # BOM 정보
    bom_data: Optional[Dict[str, Any]] = None
    bom_generated: bool = False

    # 이미지 정보
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    image_base64: Optional[str] = None
