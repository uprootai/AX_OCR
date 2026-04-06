"""분석 옵션 스키마

도면 분석 시 어떤 기능을 활성화할지 설정.
프리셋을 통해 도면 유형별 최적 설정 제공.
"""
from app_config import DEFAULT_CONFIDENCE_THRESHOLD
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AnalysisOptions(BaseModel):
    """분석 옵션 설정"""
    # 분석 기능 활성화
    enable_symbol_detection: bool = Field(
        default=True,
        description="심볼 검출 활성화 (YOLO)"
    )
    enable_dimension_ocr: bool = Field(
        default=True,
        description="치수 OCR 활성화 (PaddleOCR 우선, eDOCr2 fallback)"
    )
    enable_line_detection: bool = Field(
        default=False,
        description="선 검출 활성화"
    )
    enable_text_extraction: bool = Field(
        default=False,
        description="텍스트 블록 추출 활성화"
    )
    enable_relation_extraction: bool = Field(
        default=True,
        description="치수-객체 관계 추출 활성화 (Phase 2)"
    )

    # OCR 엔진 선택
    ocr_engine: str = Field(
        default="edocr2",
        description="(deprecated) 단일 OCR 엔진 - ocr_engines 사용 권장"
    )
    ocr_engines: List[str] = Field(
        default=["paddleocr_tiled", "edocr2"],
        description="사용할 OCR 엔진 목록 (순서대로 실행, 가중 투표 병합). "
                    "가동 중: paddleocr, paddleocr_tiled, edocr2, easyocr. "
                    "미가동: trocr, suryaocr, doctr"
    )

    # 검출 설정
    confidence_threshold: float = Field(
        default=DEFAULT_CONFIDENCE_THRESHOLD,  # @AX:WARN - default is 0.4
        ge=0.0,
        le=1.0,
        description="신뢰도 임계값"
    )

    # 심볼 검출 설정
    symbol_model_type: str = Field(
        default="panasia",
        description="심볼 검출 모델 타입 (panasia: classExamples 매칭, bom_detector: 일반 전력설비)"
    )

    # 프리셋 (선택 시 자동 설정)
    preset: Optional[str] = Field(
        None,
        description="프리셋 (mechanical_part, pid, assembly, electrical)"
    )


class AnalysisOptionsUpdate(BaseModel):
    """분석 옵션 업데이트"""
    enable_symbol_detection: Optional[bool] = None
    enable_dimension_ocr: Optional[bool] = None
    enable_line_detection: Optional[bool] = None
    enable_text_extraction: Optional[bool] = None
    enable_relation_extraction: Optional[bool] = None
    ocr_engine: Optional[str] = None
    ocr_engines: Optional[List[str]] = None
    confidence_threshold: Optional[float] = None
    symbol_model_type: Optional[str] = None
    preset: Optional[str] = None


class AnalysisResult(BaseModel):
    """분석 결과 통합"""
    session_id: str
    options: AnalysisOptions

    # 각 분석 결과
    detections: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="심볼 검출 결과"
    )
    dimensions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="치수 OCR 결과"
    )
    lines: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="선 검출 결과"
    )
    texts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="텍스트 블록 결과"
    )
    relations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="치수-객체 관계 (Phase 2)"
    )

    # 처리 정보
    processing_time_ms: float = 0.0
    errors: List[str] = Field(default_factory=list)


# 프리셋 정의
PRESETS: Dict[str, Dict[str, Any]] = {
    "mechanical_part": {
        "name": "기계 부품도",
        "description": "치수, 공차 중심 분석 (심볼 검출 비활성화)",
        "icon": "⚙️",
        "enable_symbol_detection": False,
        "enable_dimension_ocr": True,
        "enable_line_detection": True,  # 치수선 기반 관계 추출에 필요
        "enable_text_extraction": True,
        "enable_relation_extraction": True,
        "ocr_engine": "edocr2",
        "ocr_engines": ["paddleocr_tiled", "edocr2"],
        "confidence_threshold": DEFAULT_CONFIDENCE_THRESHOLD
    },
    "electrical": {
        "name": "전력 설비 단선도",
        "description": "전기 심볼 검출 (파나시아 MCP Panel)",
        "icon": "⚡",
        "enable_symbol_detection": True,
        "enable_dimension_ocr": False,
        "enable_line_detection": False,
        "enable_text_extraction": False,
        "enable_relation_extraction": False,  # 치수 없음
        "ocr_engine": "edocr2",
        "ocr_engines": ["edocr2"],
        "confidence_threshold": DEFAULT_CONFIDENCE_THRESHOLD,
        "symbol_model_type": "panasia"  # classExamples 참조 이미지와 매칭
    },
    "pid": {
        "name": "P&ID 배관도",
        "description": "심볼 + 연결선 + 태그 분석",
        "icon": "🔧",
        "enable_symbol_detection": True,
        "enable_dimension_ocr": False,
        "enable_line_detection": True,
        "enable_text_extraction": True,
        "enable_relation_extraction": False,  # 치수 없음
        "ocr_engine": "paddleocr",
        "ocr_engines": ["paddleocr"],
        "confidence_threshold": DEFAULT_CONFIDENCE_THRESHOLD,
        "symbol_model_type": "pid"
    },
    "assembly": {
        "name": "조립도",
        "description": "부품 심볼 + 치수 복합 분석",
        "icon": "🔩",
        "enable_symbol_detection": True,
        "enable_dimension_ocr": True,
        "enable_line_detection": True,  # 치수선 기반 관계 추출에 필요
        "enable_text_extraction": True,
        "enable_relation_extraction": True,
        "ocr_engine": "paddleocr",
        "ocr_engines": ["paddleocr_tiled", "edocr2"],
        "confidence_threshold": DEFAULT_CONFIDENCE_THRESHOLD
    }
}


def get_preset(preset_name: str) -> Optional[Dict[str, Any]]:
    """프리셋 조회"""
    return PRESETS.get(preset_name)


def apply_preset_to_options(options: AnalysisOptions, preset_name: str) -> AnalysisOptions:
    """프리셋을 옵션에 적용"""
    preset = PRESETS.get(preset_name)
    if not preset:
        return options

    # 프리셋 값 적용
    data = options.model_dump()
    for key, value in preset.items():
        if key in data and key not in ['name', 'description', 'icon']:
            data[key] = value
    data['preset'] = preset_name

    return AnalysisOptions(**data)
