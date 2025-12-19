"""
YOLO Detection Service

YOLO API 호출 및 검출 결과 처리
"""
import os
import json
import asyncio
import logging
import mimetypes
from typing import Dict, Any
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Configuration
YOLO_API_URL = os.getenv("YOLO_API_URL", "http://yolo-api:5005")


async def call_yolo_detect(
    file_bytes: bytes,
    filename: str,
    conf_threshold: float,
    iou_threshold: float,
    imgsz: int,
    visualize: bool,
    model_type: str,
    task: str,
    use_sahi: bool,
    slice_height: int,
    slice_width: int,
    overlap_ratio: float
) -> Dict[str, Any]:
    """
    YOLO API 호출

    NOTE: 기본값은 nodeDefinitions.ts (또는 api_specs/yolo.yaml)에서만 정의.
    이 함수는 전달받은 값을 그대로 사용.

    Args:
        file_bytes: 이미지 파일 바이트
        filename: 파일 이름
        conf_threshold: 신뢰도 임계값
        iou_threshold: IoU 임계값
        imgsz: 이미지 크기
        visualize: 시각화 생성 여부
        model_type: 모델 타입 (bom_detector, engineering, pid_symbol 등)
        task: 작업 종류 (detect/segment)
        use_sahi: SAHI 슬라이싱 사용 여부
        slice_height: SAHI 슬라이스 높이
        slice_width: SAHI 슬라이스 너비
        overlap_ratio: SAHI 오버랩 비율

    Returns:
        YOLO 검출 결과 dict
    """
    try:
        # 파일 확장자에서 content-type 결정
        content_type = mimetypes.guess_type(filename)[0] or "image/png"
        logger.info(
            f"Calling YOLO API for {filename} "
            f"(content-type: {content_type}, conf={conf_threshold}, "
            f"iou={iou_threshold}, imgsz={imgsz}, visualize={visualize}, "
            f"model_type={model_type}, task={task}, use_sahi={use_sahi})"
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (filename, file_bytes, content_type)}
            data = {
                "conf_threshold": conf_threshold,
                "iou_threshold": iou_threshold,
                "imgsz": imgsz,
                "visualize": visualize,
                "model_type": model_type,
                "task": task,
                "use_sahi": use_sahi,
                "slice_height": slice_height,
                "slice_width": slice_width,
                "overlap_ratio": overlap_ratio
            }

            response = await client.post(
                f"{YOLO_API_URL}/api/v1/detect",
                files=files,
                data=data
            )

            logger.info(f"YOLO API status: {response.status_code}")
            if response.status_code == 200:
                # 비동기 JSON 파싱 (큰 응답에서 이벤트 루프 블로킹 방지)
                # response.content는 이미 읽어온 bytes이므로 블로킹 없음
                response_bytes = response.content
                yolo_response = await asyncio.to_thread(
                    lambda: json.loads(response_bytes.decode('utf-8'))
                )
                logger.info(f"YOLO API response keys: {yolo_response.keys()}")
                logger.info(f"YOLO total_detections: {yolo_response.get('total_detections', 'NOT FOUND')}")
                logger.info(f"YOLO detections count: {len(yolo_response.get('detections', []))}")
                return yolo_response
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"YOLO failed: {response.text}"
                )

    except Exception as e:
        logger.error(f"YOLO API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"YOLO error: {str(e)}")
