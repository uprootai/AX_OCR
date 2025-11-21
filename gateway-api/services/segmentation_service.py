"""
Segmentation Service

EDGNet API 호출 및 세그멘테이션 처리
"""
import os
import logging
import mimetypes
from typing import Dict, Any
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Configuration
EDGNET_URL = os.getenv("EDGNET_URL", "http://edgnet-api:5002")


async def call_edgnet_segment(
    file_bytes: bytes,
    filename: str,
    visualize: bool = True,
    num_classes: int = 3,
    save_graph: bool = False,
    model: str = "unet"
) -> Dict[str, Any]:
    """
    EDGNet API 호출

    Args:
        file_bytes: 이미지 파일 바이트
        filename: 파일 이름
        visualize: 시각화 생성 여부 (기본 True)
        num_classes: 클래스 수 (기본 3)
        save_graph: 그래프 저장 여부 (기본 False)
        model: 모델 선택 (기본 "unet") - graphsage 또는 unet

    Returns:
        EDGNet 세그멘테이션 결과 dict
    """
    try:
        # 파일 확장자에서 content-type 결정
        content_type = mimetypes.guess_type(filename)[0] or "image/png"
        logger.info(
            f"Calling EDGNet API for {filename} "
            f"(content-type: {content_type}, model={model}, num_classes={num_classes}, "
            f"visualize={visualize}, save_graph={save_graph})"
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": (filename, file_bytes, content_type)}
            data = {
                "model": model,
                "visualize": visualize,
                "num_classes": num_classes,
                "save_graph": save_graph
            }

            response = await client.post(
                f"{EDGNET_URL}/api/v1/segment",
                files=files,
                data=data
            )

            logger.info(f"EDGNet API status: {response.status_code}")
            if response.status_code == 200:
                edgnet_response = response.json()
                logger.info(f"EDGNet response keys: {edgnet_response.keys()}")
                logger.info(f"EDGNet components count: {len(edgnet_response.get('components', []))}")
                logger.info(f"EDGNet nodes count: {edgnet_response.get('graph', {}).get('node_count', 0)}")
                return edgnet_response
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"EDGNet failed: {response.text}"
                )

    except Exception as e:
        logger.error(f"EDGNet API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"EDGNet error: {str(e)}")
