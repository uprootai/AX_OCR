"""
Compose Router
레이어 합성 API 엔드포인트
"""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import numpy as np

from services import (
    compose_layers,
    ComposerStyle,
    ComposerResult,
    LayerType,
    generate_svg_overlay,
    render_to_image
)
from services.image_renderer import (
    image_to_base64,
    base64_to_image,
    resize_image,
    add_legend
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["compose"])


# =====================
# Schemas
# =====================

class StyleConfig(BaseModel):
    """스타일 설정"""
    # Symbol
    symbol_color: List[int] = Field(default=[0, 120, 255], description="심볼 색상 (BGR)")
    symbol_thickness: int = Field(default=2, ge=1, le=10)
    symbol_fill_alpha: float = Field(default=0.1, ge=0.0, le=1.0)
    show_symbol_labels: bool = True
    symbol_label_size: float = Field(default=0.5, ge=0.1, le=2.0)

    # Line
    line_thickness: int = Field(default=2, ge=1, le=10)
    show_flow_arrows: bool = False
    arrow_size: int = Field(default=10, ge=5, le=30)

    # Text
    text_color: List[int] = Field(default=[255, 165, 0], description="텍스트 색상 (BGR)")
    text_thickness: int = Field(default=1, ge=1, le=5)
    show_text_values: bool = True

    # Region
    region_fill_alpha: float = Field(default=0.15, ge=0.0, le=1.0)
    region_dash_length: int = Field(default=10, ge=5, le=30)
    show_region_labels: bool = True


class ComposeRequest(BaseModel):
    """합성 요청"""
    image_base64: str = Field(..., description="Base64 인코딩된 원본 이미지")
    layers: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="레이어 데이터 {symbols: [...], lines: [...], texts: [...], regions: [...]}"
    )
    enabled_layers: List[str] = Field(
        default=["symbols", "lines", "texts", "regions"],
        description="활성화할 레이어 목록"
    )
    style: Optional[StyleConfig] = None
    output_format: str = Field(default="png", description="출력 형식 (png, jpg, webp)")
    quality: int = Field(default=95, ge=1, le=100, description="JPEG/WebP 품질")
    include_svg: bool = Field(default=True, description="SVG 오버레이 포함 여부")
    include_legend: bool = Field(default=False, description="범례 포함 여부")
    max_size: Optional[List[int]] = Field(default=None, description="최대 출력 크기 [width, height]")


class ComposeResponse(BaseModel):
    """합성 응답"""
    success: bool
    image_base64: Optional[str] = None
    svg_overlay: Optional[str] = None
    statistics: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class SVGOnlyRequest(BaseModel):
    """SVG만 생성 요청"""
    layers: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="레이어 데이터"
    )
    image_size: List[int] = Field(..., description="이미지 크기 [width, height]")
    enabled_layers: List[str] = Field(
        default=["symbols", "lines", "texts", "regions"]
    )
    style: Optional[StyleConfig] = None


class SVGOnlyResponse(BaseModel):
    """SVG만 생성 응답"""
    success: bool
    svg: str
    statistics: Dict[str, Any] = Field(default_factory=dict)


class LayersOnlyRequest(BaseModel):
    """레이어만 합성 요청 (이미지 없이)"""
    image_size: List[int] = Field(..., description="캔버스 크기 [width, height]")
    background_color: List[int] = Field(default=[255, 255, 255], description="배경색 (BGR)")
    layers: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    enabled_layers: List[str] = Field(default=["symbols", "lines", "texts", "regions"])
    style: Optional[StyleConfig] = None
    output_format: str = Field(default="png")


class InfoResponse(BaseModel):
    """서비스 정보"""
    service: str
    version: str
    supported_layers: List[str]
    supported_formats: List[str]
    default_style: Dict[str, Any]


# =====================
# Helper Functions
# =====================

def style_config_to_composer_style(config: Optional[StyleConfig]) -> ComposerStyle:
    """StyleConfig를 ComposerStyle로 변환"""
    if config is None:
        return ComposerStyle()

    return ComposerStyle(
        symbol_color=tuple(config.symbol_color),
        symbol_thickness=config.symbol_thickness,
        symbol_fill_alpha=config.symbol_fill_alpha,
        show_symbol_labels=config.show_symbol_labels,
        symbol_label_size=config.symbol_label_size,
        line_thickness=config.line_thickness,
        show_flow_arrows=config.show_flow_arrows,
        arrow_size=config.arrow_size,
        text_color=tuple(config.text_color),
        text_thickness=config.text_thickness,
        show_text_values=config.show_text_values,
        region_fill_alpha=config.region_fill_alpha,
        region_dash_length=config.region_dash_length,
        show_region_labels=config.show_region_labels
    )


def parse_enabled_layers(layer_names: List[str]) -> List[LayerType]:
    """문자열 레이어 이름을 LayerType으로 변환"""
    result = []
    for name in layer_names:
        try:
            result.append(LayerType(name.lower()))
        except ValueError:
            logger.warning(f"Unknown layer type: {name}")
    return result


# =====================
# Endpoints
# =====================

@router.get("/info", response_model=InfoResponse)
async def get_info():
    """서비스 정보 조회"""
    default_style = ComposerStyle()
    return InfoResponse(
        service="PID Composer",
        version="1.0.0",
        supported_layers=["symbols", "lines", "texts", "regions"],
        supported_formats=["png", "jpg", "webp"],
        default_style={
            "symbol_color": list(default_style.symbol_color),
            "symbol_thickness": default_style.symbol_thickness,
            "symbol_fill_alpha": default_style.symbol_fill_alpha,
            "show_symbol_labels": default_style.show_symbol_labels,
            "line_thickness": default_style.line_thickness,
            "show_flow_arrows": default_style.show_flow_arrows,
            "text_color": list(default_style.text_color),
            "text_thickness": default_style.text_thickness,
            "region_fill_alpha": default_style.region_fill_alpha,
            "show_region_labels": default_style.show_region_labels
        }
    )


@router.post("/compose", response_model=ComposeResponse)
async def compose_image(request: ComposeRequest):
    """
    이미지에 레이어 합성

    원본 이미지 위에 심볼, 라인, 텍스트, 영역 레이어를 합성합니다.
    """
    try:
        # 이미지 디코딩
        image = base64_to_image(request.image_base64)
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image data")

        # 스타일 변환
        style = style_config_to_composer_style(request.style)
        enabled_layers = parse_enabled_layers(request.enabled_layers)

        # 레이어 합성
        result: ComposerResult = compose_layers(
            image=image,
            layers=request.layers,
            enabled_layers=enabled_layers,
            style=style
        )

        if not result.success:
            return ComposeResponse(
                success=False,
                error=result.error
            )

        result_image = result.image

        # 범례 추가
        if request.include_legend:
            layer_counts = {
                'symbols': len(request.layers.get('symbols', [])),
                'lines': len(request.layers.get('lines', [])),
                'texts': len(request.layers.get('texts', [])),
                'regions': len(request.layers.get('regions', []))
            }
            result_image = add_legend(result_image, layer_counts)

        # 리사이즈
        if request.max_size:
            result_image = resize_image(result_image, max_size=tuple(request.max_size))

        # Base64 인코딩
        image_b64 = image_to_base64(result_image, request.output_format, request.quality)

        # SVG 생성
        svg_overlay = None
        if request.include_svg:
            h, w = image.shape[:2]
            svg_overlay = generate_svg_overlay(
                layers=request.layers,
                image_size=(w, h),
                enabled_layers=enabled_layers,
                style=style
            )

        # 통계
        statistics = result.statistics.copy()
        statistics.update({
            "output_format": request.output_format,
            "enabled_layers": request.enabled_layers,
            "symbols_count": len(request.layers.get('symbols', [])),
            "lines_count": len(request.layers.get('lines', [])),
            "texts_count": len(request.layers.get('texts', [])),
            "regions_count": len(request.layers.get('regions', []))
        })

        return ComposeResponse(
            success=True,
            image_base64=image_b64,
            svg_overlay=svg_overlay,
            statistics=statistics
        )

    except Exception as e:
        logger.error(f"Compose failed: {e}")
        import traceback
        traceback.print_exc()
        return ComposeResponse(
            success=False,
            error=str(e)
        )


@router.post("/compose/svg", response_model=SVGOnlyResponse)
async def compose_svg_only(request: SVGOnlyRequest):
    """
    SVG 오버레이만 생성

    이미지 없이 레이어 데이터로 SVG만 생성합니다.
    프론트엔드에서 원본 이미지 위에 오버레이로 사용합니다.
    """
    try:
        style = style_config_to_composer_style(request.style)
        enabled_layers = parse_enabled_layers(request.enabled_layers)

        svg = generate_svg_overlay(
            layers=request.layers,
            image_size=tuple(request.image_size),
            enabled_layers=enabled_layers,
            style=style
        )

        statistics = {
            "image_size": request.image_size,
            "enabled_layers": request.enabled_layers,
            "symbols_count": len(request.layers.get('symbols', [])),
            "lines_count": len(request.layers.get('lines', [])),
            "texts_count": len(request.layers.get('texts', [])),
            "regions_count": len(request.layers.get('regions', []))
        }

        return SVGOnlyResponse(
            success=True,
            svg=svg,
            statistics=statistics
        )

    except Exception as e:
        logger.error(f"SVG generation failed: {e}")
        return SVGOnlyResponse(
            success=False,
            svg="",
            statistics={"error": str(e)}
        )


@router.post("/compose/layers", response_model=ComposeResponse)
async def compose_layers_only(request: LayersOnlyRequest):
    """
    레이어만 합성 (빈 캔버스)

    원본 이미지 없이 빈 캔버스에 레이어를 그립니다.
    """
    try:
        # 빈 캔버스 생성
        w, h = request.image_size
        canvas = np.full((h, w, 3), request.background_color[::-1], dtype=np.uint8)  # BGR

        style = style_config_to_composer_style(request.style)
        enabled_layers = parse_enabled_layers(request.enabled_layers)

        result: ComposerResult = compose_layers(
            image=canvas,
            layers=request.layers,
            enabled_layers=enabled_layers,
            style=style
        )

        if not result.success:
            return ComposeResponse(
                success=False,
                error=result.error
            )

        image_b64 = image_to_base64(result.image, request.output_format)

        statistics = result.statistics.copy()
        statistics.update({
            "canvas_size": request.image_size,
            "background_color": request.background_color
        })

        return ComposeResponse(
            success=True,
            image_base64=image_b64,
            statistics=statistics
        )

    except Exception as e:
        logger.error(f"Layers-only compose failed: {e}")
        return ComposeResponse(
            success=False,
            error=str(e)
        )


@router.post("/preview")
async def preview_style(
    style: StyleConfig,
    layer_type: str = "symbols"
):
    """
    스타일 미리보기

    작은 샘플 이미지로 스타일을 미리 확인합니다.
    """
    try:
        # 200x200 샘플 캔버스
        canvas = np.full((200, 200, 3), (255, 255, 255), dtype=np.uint8)

        # 샘플 데이터
        sample_layers = {
            "symbols": [{"bbox": {"x": 50, "y": 50, "width": 100, "height": 80}, "class_name": "Valve", "confidence": 0.95}],
            "lines": [{"start_point": [10, 90], "end_point": [190, 90], "line_type": "pipe"}],
            "texts": [{"bbox": [60, 150, 140, 170], "text": "Sample"}],
            "regions": [{"bbox": [20, 20, 180, 180], "region_type": "signal_group"}]
        }

        composer_style = style_config_to_composer_style(style)

        # 선택된 레이어만
        enabled = [LayerType(layer_type)] if layer_type in ["symbols", "lines", "texts", "regions"] else [LayerType.SYMBOLS]

        result = compose_layers(
            image=canvas,
            layers=sample_layers,
            enabled_layers=enabled,
            style=composer_style
        )

        if result.success:
            return {
                "success": True,
                "preview_base64": image_to_base64(result.image, "png")
            }
        else:
            return {"success": False, "error": result.error}

    except Exception as e:
        return {"success": False, "error": str(e)}
