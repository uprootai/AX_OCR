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
    imgsz: int = 640,
    visualize: bool = True,
    model_type: str = "engineering",
    task: str = "detect",
    use_sahi: bool = False,
    slice_height: int = 512,
    slice_width: int = 512,
    overlap_ratio: float = 0.25
) -> Dict[str, Any]:
    """
    YOLO API 호출

    Args:
        file_bytes: 이미지 파일 바이트
        filename: 파일 이름
        conf_threshold: 신뢰도 임계값 (기본 0.25)
        iou_threshold: IoU 임계값 (기본 0.7)
        imgsz: 이미지 크기 (기본 640)
        visualize: 시각화 생성 여부 (기본 True)
        model_type: 모델 타입 (engineering, pid_symbol, pid_class_agnostic, pid_class_aware)
        task: 작업 종류 (detect/segment, 기본 detect)
        use_sahi: SAHI 슬라이싱 사용 여부 (pid_* 모델은 자동 활성화)
        slice_height: SAHI 슬라이스 높이 (기본 512)
        slice_width: SAHI 슬라이스 너비 (기본 512)
        overlap_ratio: SAHI 오버랩 비율 (기본 0.25)

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
