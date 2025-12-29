"""
Line Detector Process Router
/api/v1/process 엔드포인트
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from collections import Counter

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel
import cv2
import numpy as np

from services import (
    # Constants
    LINE_STYLE_TYPES,
    LINE_PURPOSE_TYPES,
    REGION_TYPES,
    # Detection
    detect_lines_lsd,
    detect_lines_hough,
    merge_collinear_lines,
    find_intersections,
    # Classification
    classify_line_type,
    classify_all_lines_by_color,
    classify_all_lines_by_style,
    classify_line_purpose,
    # Region
    find_dashed_regions,
    # Visualization
    visualize_lines,
    visualize_regions,
    numpy_to_base64,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Process"])

# Configuration
API_PORT = int(os.getenv("LINE_DETECTOR_PORT", "5016"))


class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None


@router.get("/info")
async def get_info():
    """API 정보 (BlueprintFlow 메타데이터)"""
    return {
        "id": "line-detector",
        "name": "Line Detector",
        "display_name": "P&ID Line Detector",
        "version": "1.1.0",
        "description": "P&ID 라인(배관/신호선) 검출, 스타일 분류, 영역 검출 API",
        "base_url": f"http://localhost:{API_PORT}",
        "endpoint": "/api/v1/process",
        "method": "POST",
        "requires_image": True,
        "blueprintflow": {
            "category": "segmentation",
            "color": "#8b5cf6",
            "icon": "GitCommitHorizontal"
        },
        "inputs": [
            {"name": "image", "type": "Image", "required": True, "description": "P&ID 도면 이미지"}
        ],
        "outputs": [
            {"name": "lines", "type": "LineSegment[]", "description": "검출된 라인 목록"},
            {"name": "intersections", "type": "Intersection[]", "description": "교차점 목록"},
            {"name": "regions", "type": "Region[]", "description": "점선 박스 영역 목록"},
            {"name": "visualization", "type": "Image", "description": "시각화 이미지"}
        ],
        "parameters": [
            {"name": "method", "type": "select", "options": ["lsd", "hough", "combined"], "default": "lsd"},
            {"name": "merge_lines", "type": "boolean", "default": True},
            {"name": "classify_types", "type": "boolean", "default": True},
            {"name": "classify_colors", "type": "boolean", "default": True, "description": "색상 기반 라인 분류"},
            {"name": "classify_styles", "type": "boolean", "default": True, "description": "스타일 분류 (실선/점선)"},
            {"name": "find_intersections", "type": "boolean", "default": True},
            {"name": "detect_regions", "type": "boolean", "default": False, "description": "점선 박스 영역 검출"},
            {"name": "region_line_styles", "type": "multiselect", "options": ["dashed", "dash_dot", "dotted"], "default": ["dashed", "dash_dot"], "description": "영역 검출에 사용할 라인 스타일"},
            {"name": "min_region_area", "type": "number", "default": 5000, "description": "최소 영역 크기 (픽셀²)"},
            {"name": "visualize", "type": "boolean", "default": True},
            {"name": "visualize_regions", "type": "boolean", "default": True, "description": "영역 시각화 포함"},
            {"name": "min_length", "type": "number", "default": 0, "description": "최소 라인 길이 (픽셀). 0=필터링 안함"},
            {"name": "max_lines", "type": "number", "default": 0, "description": "최대 라인 수 제한. 0=제한 없음"}
        ],
        "line_style_types": LINE_STYLE_TYPES,
        "line_purpose_types": LINE_PURPOSE_TYPES,
        "region_types": REGION_TYPES
    }


@router.post("/process", response_model=ProcessResponse)
async def process(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    method: str = Form(default="lsd", description="검출 방식 (lsd, hough, combined)"),
    merge_lines: bool = Form(default=True, description="공선 라인 병합"),
    classify_types: bool = Form(default=True, description="라인 유형 분류 (배관/신호선)"),
    classify_colors: bool = Form(default=True, description="색상 기반 라인 분류"),
    classify_styles: bool = Form(default=True, description="스타일 분류 (실선/점선)"),
    find_intersections_flag: bool = Form(default=True, alias="find_intersections", description="교차점 검출"),
    detect_regions: bool = Form(default=False, description="점선 박스 영역 검출"),
    region_line_styles: str = Form(default="dashed,dash_dot", description="영역 검출에 사용할 라인 스타일"),
    min_region_area: int = Form(default=5000, description="최소 영역 크기 (픽셀²)"),
    visualize: bool = Form(default=True, description="결과 시각화"),
    visualize_regions_flag: bool = Form(default=True, alias="visualize_regions", description="영역 시각화 포함"),
    min_length: float = Form(default=0, description="최소 라인 길이 (픽셀)"),
    max_lines: int = Form(default=0, description="최대 라인 수 제한")
):
    """
    P&ID 라인 검출 메인 엔드포인트
    """
    start_time = time.time()

    try:
        # 이미지 로드
        image_bytes = await file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        logger.info(f"Processing image: {file.filename}, size: {image.shape}")

        # 라인 검출
        if method == "lsd":
            lines = detect_lines_lsd(image)
        elif method == "hough":
            lines = detect_lines_hough(image)
        else:
            lsd_lines = detect_lines_lsd(image)
            hough_lines = detect_lines_hough(image)
            lines = lsd_lines + hough_lines

        logger.info(f"Detected {len(lines)} lines using {method}")

        # 공선 라인 병합
        if merge_lines:
            original_count = len(lines)
            lines = merge_collinear_lines(lines)
            logger.info(f"Merged lines: {original_count} -> {len(lines)}")

        # 최소 길이 필터링
        if min_length > 0:
            original_count = len(lines)
            lines = [l for l in lines if l.get('length', 0) >= min_length]
            logger.info(f"Length filter (>= {min_length}px): {original_count} -> {len(lines)}")

        # 최대 라인 수 제한
        if max_lines > 0 and len(lines) > max_lines:
            original_count = len(lines)
            lines = sorted(lines, key=lambda l: l.get('length', 0), reverse=True)[:max_lines]
            for i, line in enumerate(lines):
                line['id'] = i
            logger.info(f"Max lines limit ({max_lines}): {original_count} -> {len(lines)}")

        # 라인 유형 분류
        if classify_types:
            for line in lines:
                line['line_type'] = classify_line_type(line, lines)
                line['confidence'] = 0.85

        # 색상 기반 라인 분류
        if classify_colors:
            lines = classify_all_lines_by_color(image, lines)
            logger.info(f"Color classification applied to {len(lines)} lines")

        # 스타일 분류
        if classify_styles:
            lines = classify_all_lines_by_style(image, lines)
            logger.info(f"Style classification applied to {len(lines)} lines")

        # 교차점 검출
        intersections = []
        if find_intersections_flag:
            intersections = find_intersections(lines)
            logger.info(f"Found {len(intersections)} intersections")

        # 점선 박스 영역 검출
        regions = []
        if detect_regions and classify_styles:
            styles_list = [s.strip() for s in region_line_styles.split(",") if s.strip()]
            if not styles_list:
                styles_list = ['dashed', 'dash_dot']

            regions = find_dashed_regions(
                image, lines,
                min_area=min_region_area,
                line_styles=styles_list
            )
            logger.info(f"Found {len(regions)} closed regions with styles {styles_list}")

            # 각 영역 내 라인 용도 분류
            for region in regions:
                x1, y1, x2, y2 = region['bbox']
                lines_in_region = []
                for line in lines:
                    mid_x = (line['start_point'][0] + line['end_point'][0]) / 2
                    mid_y = (line['start_point'][1] + line['end_point'][1]) / 2
                    if x1 <= mid_x <= x2 and y1 <= mid_y <= y2:
                        purpose_info = classify_line_purpose(line)
                        line['purpose'] = purpose_info['purpose']
                        line['purpose_korean'] = purpose_info['purpose_korean']
                        lines_in_region.append(line)

                region['lines_inside'] = lines_in_region

        # 시각화
        visualization_base64 = None
        if visualize:
            vis_image = visualize_lines(image, lines, intersections)

            if detect_regions and visualize_regions_flag and regions:
                vis_image = visualize_regions(vis_image, regions, draw_labels=True)
                logger.info(f"Visualized {len(regions)} regions")

            visualization_base64 = numpy_to_base64(vis_image)

        # 통계 계산
        pipe_count = sum(1 for l in lines if l.get('line_type') == 'pipe')
        signal_count = sum(1 for l in lines if l.get('line_type') == 'signal')
        unknown_count = sum(1 for l in lines if l.get('line_type') == 'unknown')

        color_stats = {}
        if classify_colors:
            color_counts = Counter(l.get('color_type', 'unknown') for l in lines)
            color_stats = {
                "by_color_type": dict(color_counts),
                "process_lines": color_counts.get('process', 0),
                "water_lines": color_counts.get('water', 0),
                "steam_lines": color_counts.get('steam', 0),
                "signal_lines_color": color_counts.get('signal', 0),
                "electrical_lines": color_counts.get('electrical', 0),
                "air_lines": color_counts.get('air', 0),
            }

        style_stats = {}
        if classify_styles:
            style_counts = Counter(l.get('line_style', 'unknown') for l in lines)
            style_stats = {
                "by_line_style": dict(style_counts),
                "solid_lines": style_counts.get('solid', 0),
                "dashed_lines": style_counts.get('dashed', 0),
                "dotted_lines": style_counts.get('dotted', 0),
                "dash_dot_lines": style_counts.get('dash_dot', 0),
                "double_lines": style_counts.get('double', 0),
                "wavy_lines": style_counts.get('wavy', 0),
                "unknown_style_lines": style_counts.get('unknown', 0),
            }

        region_stats = {}
        if detect_regions:
            region_type_counts = Counter(r.get('region_type', 'unknown') for r in regions)
            total_region_area = sum(r.get('area', 0) for r in regions)
            avg_region_area = total_region_area / len(regions) if regions else 0

            region_stats = {
                "total_regions": len(regions),
                "by_region_type": dict(region_type_counts),
                "total_region_area": total_region_area,
                "avg_region_area": round(avg_region_area, 1),
                "rectangular_regions": sum(1 for r in regions if r.get('is_rectangular', False)),
                "region_detection_styles": region_line_styles.split(","),
            }

        processing_time = time.time() - start_time

        result = {
            "lines": lines,
            "intersections": intersections,
            "regions": regions,
            "statistics": {
                "total_lines": len(lines),
                "pipe_lines": pipe_count,
                "signal_lines": signal_count,
                "unknown_lines": unknown_count,
                "intersection_count": len(intersections),
                **color_stats,
                **style_stats,
                **region_stats
            },
            "visualization": visualization_base64,
            "method": method,
            "image_size": {"width": image.shape[1], "height": image.shape[0]},
            "options_used": {
                "classify_types": classify_types,
                "classify_colors": classify_colors,
                "classify_styles": classify_styles,
                "detect_regions": detect_regions,
                "region_line_styles": region_line_styles if detect_regions else None,
                "min_region_area": min_region_area if detect_regions else None
            }
        }

        return ProcessResponse(
            success=True,
            data=result,
            processing_time=round(processing_time, 3)
        )

    except Exception as e:
        logger.error(f"Processing error: {e}")
        import traceback
        traceback.print_exc()
        return ProcessResponse(
            success=False,
            data={},
            processing_time=time.time() - start_time,
            error=str(e)
        )
