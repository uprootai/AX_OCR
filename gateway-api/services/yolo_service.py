"""
YOLO Detection Service

YOLO API 호출 및 검출 결과 처리
"""
import os
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
    conf_threshold: float = 0.25,
    iou_threshold: float = 0.7,
    imgsz: int = 1280,
    visualize: bool = True,
    model_type: str = "symbol-detector-v1",
    task: str = "detect"
) -> Dict[str, Any]:
    """
    YOLO API 호출

    Args:
        file_bytes: 이미지 파일 바이트
        filename: 파일 이름
        conf_threshold: 신뢰도 임계값 (기본 0.25)
        iou_threshold: IoU 임계값 (기본 0.7)
        imgsz: 이미지 크기 (기본 1280)
        visualize: 시각화 생성 여부 (기본 True)
        model_type: 모델 타입 (기본 symbol-detector-v1)
        task: 작업 종류 (detect/segment, 기본 detect)

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
            f"model_type={model_type}, task={task})"
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": (filename, file_bytes, content_type)}
            data = {
                "conf_threshold": conf_threshold,
                "iou_threshold": iou_threshold,
                "imgsz": imgsz,
                "visualize": visualize,
                "model_type": model_type,
                "task": task
            }

            response = await client.post(
                f"{YOLO_API_URL}/api/v1/detect",
                files=files,
                data=data
            )

            logger.info(f"YOLO API status: {response.status_code}")
            if response.status_code == 200:
                yolo_response = response.json()
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
