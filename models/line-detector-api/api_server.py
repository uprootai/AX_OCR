"""
Line Detector API Server
P&ID 라인(배관/신호선) 검출 및 연결성 분석 API

기술:
- OpenCV Line Segment Detector (LSD)
- Hough Line Transform
- Line Thinning (Zhang-Suen Algorithm)
- Line Type Classification

포트: 5016
"""
import os
import io
import time
import logging
import base64
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import cv2
import numpy as np
from PIL import Image

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_PORT = int(os.getenv("LINE_DETECTOR_PORT", "5016"))


# =====================
# Schemas
# =====================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str


class LineSegment(BaseModel):
    id: int
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    length: float
    angle: float
    line_type: str  # 'pipe', 'signal', 'unknown'
    confidence: float


class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None


# =====================
# Core Functions
# =====================

def thin_image(binary_img: np.ndarray) -> np.ndarray:
    """
    Zhang-Suen Thinning Algorithm
    이미지를 1픽셀 두께로 세선화
    """
    skeleton = cv2.ximgproc.thinning(binary_img, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
    return skeleton


def detect_lines_lsd(image: np.ndarray) -> List[Dict]:
    """
    Line Segment Detector (LSD) 사용
    더 정확한 라인 검출
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # LSD 생성
    lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD)
    lines, widths, precs, nfas = lsd.detect(gray)

    results = []
    if lines is not None:
        for i, line in enumerate(lines):
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))

            results.append({
                'id': i,
                'start_point': (float(x1), float(y1)),
                'end_point': (float(x2), float(y2)),
                'length': float(length),
                'angle': float(angle),
                'width': float(widths[i][0]) if widths is not None else 1.0,
                'precision': float(precs[i][0]) if precs is not None else 0.0,
                'nfa': float(nfas[i][0]) if nfas is not None else 0.0
            })

    return results


def detect_lines_hough(image: np.ndarray, threshold: int = 50) -> List[Dict]:
    """
    Probabilistic Hough Line Transform
    빠른 라인 검출
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # 에지 검출
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # 확률적 Hough 변환
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold, minLineLength=30, maxLineGap=10)

    results = []
    if lines is not None:
        for i, line in enumerate(lines):
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))

            results.append({
                'id': i,
                'start_point': (float(x1), float(y1)),
                'end_point': (float(x2), float(y2)),
                'length': float(length),
                'angle': float(angle)
            })

    return results


def classify_line_type(line: Dict, all_lines: List[Dict]) -> str:
    """
    라인 유형 분류 (배관 vs 신호선)

    규칙 기반 분류:
    - 굵은 실선 → 배관 (pipe)
    - 가는 점선/파선 → 신호선 (signal)
    - 불확실 → unknown
    """
    width = line.get('width', 1.0)

    # 간단한 규칙 기반 분류
    # 실제로는 더 정교한 분류기 필요
    if width > 2.0:
        return 'pipe'
    elif width < 1.5:
        return 'signal'
    else:
        return 'unknown'


def merge_collinear_lines(lines: List[Dict], angle_threshold: float = 5.0,
                          distance_threshold: float = 20.0) -> List[Dict]:
    """
    공선(collinear) 라인 병합
    여러 조각으로 분리된 라인을 하나로 합침
    """
    if not lines:
        return lines

    merged = []
    used = set()

    for i, line1 in enumerate(lines):
        if i in used:
            continue

        current_group = [line1]
        used.add(i)

        for j, line2 in enumerate(lines):
            if j in used:
                continue

            # 각도 차이 확인
            angle_diff = abs(line1['angle'] - line2['angle'])
            if angle_diff > 90:
                angle_diff = 180 - angle_diff

            if angle_diff < angle_threshold:
                # 거리 확인 (끝점 간)
                min_dist = min(
                    np.sqrt((line1['end_point'][0] - line2['start_point'][0])**2 +
                           (line1['end_point'][1] - line2['start_point'][1])**2),
                    np.sqrt((line1['start_point'][0] - line2['end_point'][0])**2 +
                           (line1['start_point'][1] - line2['end_point'][1])**2)
                )

                if min_dist < distance_threshold:
                    current_group.append(line2)
                    used.add(j)

        # 그룹 병합
        if len(current_group) == 1:
            merged.append(current_group[0])
        else:
            # 모든 점 수집
            all_points = []
            for l in current_group:
                all_points.extend([l['start_point'], l['end_point']])

            # 최소/최대 점 찾기
            all_points = np.array(all_points)

            # PCA로 주축 방향 찾기
            mean = np.mean(all_points, axis=0)
            centered = all_points - mean
            cov = np.cov(centered.T)
            eigenvalues, eigenvectors = np.linalg.eig(cov)
            main_axis = eigenvectors[:, np.argmax(eigenvalues)]

            # 주축 방향으로 프로젝션
            projections = np.dot(centered, main_axis)
            min_idx = np.argmin(projections)
            max_idx = np.argmax(projections)

            merged_line = {
                'id': len(merged),
                'start_point': tuple(all_points[min_idx]),
                'end_point': tuple(all_points[max_idx]),
                'length': float(np.linalg.norm(all_points[max_idx] - all_points[min_idx])),
                'angle': float(np.degrees(np.arctan2(main_axis[1], main_axis[0]))),
                'merged_count': len(current_group)
            }
            merged.append(merged_line)

    return merged


def find_intersections(lines: List[Dict]) -> List[Dict]:
    """
    라인 교차점 찾기
    """
    intersections = []

    for i, line1 in enumerate(lines):
        for j, line2 in enumerate(lines):
            if i >= j:
                continue

            # 두 라인의 교차점 계산
            x1, y1 = line1['start_point']
            x2, y2 = line1['end_point']
            x3, y3 = line2['start_point']
            x4, y4 = line2['end_point']

            denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(denom) < 1e-10:
                continue  # 평행

            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
            u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

            if 0 <= t <= 1 and 0 <= u <= 1:
                px = x1 + t * (x2 - x1)
                py = y1 + t * (y2 - y1)

                intersections.append({
                    'point': (float(px), float(py)),
                    'line1_id': line1['id'],
                    'line2_id': line2['id']
                })

    return intersections


def visualize_lines(image: np.ndarray, lines: List[Dict],
                    intersections: List[Dict] = None) -> np.ndarray:
    """
    라인 검출 결과 시각화
    """
    vis = image.copy()

    # 라인 색상 (유형별)
    colors = {
        'pipe': (0, 0, 255),      # Red
        'signal': (255, 0, 0),    # Blue
        'unknown': (0, 255, 0)    # Green
    }

    for line in lines:
        line_type = line.get('line_type', 'unknown')
        color = colors.get(line_type, (0, 255, 0))

        pt1 = (int(line['start_point'][0]), int(line['start_point'][1]))
        pt2 = (int(line['end_point'][0]), int(line['end_point'][1]))

        cv2.line(vis, pt1, pt2, color, 2)

    # 교차점 표시
    if intersections:
        for inter in intersections:
            pt = (int(inter['point'][0]), int(inter['point'][1]))
            cv2.circle(vis, pt, 5, (255, 255, 0), -1)  # Yellow

    return vis


def numpy_to_base64(image: np.ndarray) -> str:
    """NumPy 이미지를 Base64로 변환"""
    _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer).decode('utf-8')


# =====================
# FastAPI App
# =====================

app = FastAPI(
    title="Line Detector API",
    description="P&ID 라인(배관/신호선) 검출 및 연결성 분석 API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# API Endpoints
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크"""
    return HealthResponse(
        status="healthy",
        service="line-detector-api",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """헬스체크 (v1 경로)"""
    return await health_check()


@app.get("/api/v1/info")
async def get_info():
    """API 정보 (BlueprintFlow 메타데이터)"""
    return {
        "id": "line-detector",
        "name": "Line Detector",
        "display_name": "P&ID Line Detector",
        "version": "1.0.0",
        "description": "P&ID 라인(배관/신호선) 검출 및 연결성 분석 API",
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
            {"name": "visualization", "type": "Image", "description": "시각화 이미지"}
        ],
        "parameters": [
            {"name": "method", "type": "select", "options": ["lsd", "hough", "combined"], "default": "lsd"},
            {"name": "merge_lines", "type": "boolean", "default": True},
            {"name": "classify_types", "type": "boolean", "default": True},
            {"name": "find_intersections", "type": "boolean", "default": True},
            {"name": "visualize", "type": "boolean", "default": True}
        ]
    }


@app.post("/api/v1/process", response_model=ProcessResponse)
async def process(
    file: UploadFile = File(..., description="P&ID 도면 이미지"),
    method: str = Form(default="lsd", description="검출 방식 (lsd, hough, combined)"),
    merge_lines: bool = Form(default=True, description="공선 라인 병합"),
    classify_types: bool = Form(default=True, description="라인 유형 분류 (배관/신호선)"),
    find_intersections_flag: bool = Form(default=True, alias="find_intersections", description="교차점 검출"),
    visualize: bool = Form(default=True, description="결과 시각화")
):
    """
    P&ID 라인 검출 메인 엔드포인트

    기능:
    - LSD/Hough 기반 라인 검출
    - 라인 유형 분류 (배관 vs 신호선)
    - 공선 라인 병합
    - 교차점 검출
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
        else:  # combined
            lsd_lines = detect_lines_lsd(image)
            hough_lines = detect_lines_hough(image)
            lines = lsd_lines + hough_lines

        logger.info(f"Detected {len(lines)} lines using {method}")

        # 공선 라인 병합
        if merge_lines:
            original_count = len(lines)
            lines = merge_collinear_lines(lines)
            logger.info(f"Merged lines: {original_count} -> {len(lines)}")

        # 라인 유형 분류
        if classify_types:
            for line in lines:
                line['line_type'] = classify_line_type(line, lines)
                line['confidence'] = 0.85  # 기본 신뢰도

        # 교차점 검출
        intersections = []
        if find_intersections_flag:
            intersections = find_intersections(lines)
            logger.info(f"Found {len(intersections)} intersections")

        # 시각화
        visualization_base64 = None
        if visualize:
            vis_image = visualize_lines(image, lines, intersections)
            visualization_base64 = numpy_to_base64(vis_image)

        # 통계 계산
        pipe_count = sum(1 for l in lines if l.get('line_type') == 'pipe')
        signal_count = sum(1 for l in lines if l.get('line_type') == 'signal')
        unknown_count = sum(1 for l in lines if l.get('line_type') == 'unknown')

        processing_time = time.time() - start_time

        result = {
            "lines": lines,
            "intersections": intersections,
            "statistics": {
                "total_lines": len(lines),
                "pipe_lines": pipe_count,
                "signal_lines": signal_count,
                "unknown_lines": unknown_count,
                "intersection_count": len(intersections)
            },
            "visualization": visualization_base64,
            "method": method,
            "image_size": {"width": image.shape[1], "height": image.shape[0]}
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


# =====================
# Main
# =====================

if __name__ == "__main__":
    logger.info(f"Starting Line Detector API on port {API_PORT}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=API_PORT,
        log_level="info"
    )
