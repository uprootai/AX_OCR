"""
Vision Language Service

VL API 호출 및 멀티모달 분석 결과 처리
"""
import os
import logging
import mimetypes
from typing import Dict, Any, Optional
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Configuration
VL_API_URL = os.getenv("VL_API_URL", "http://vl-api:5004")


async def call_vl_api(
    file_bytes: bytes,
    filename: str,
    prompt: str,
    model: str = "claude",
    temperature: float = 0.0,
    task: str = "extract_info"
) -> Dict[str, Any]:
    """
    VL API 호출

    Args:
        file_bytes: 이미지 파일 바이트
        filename: 파일 이름
        prompt: 분석 프롬프트
        model: 사용할 모델 (claude, gpt4-vision 등)
        temperature: 생성 온도 (0.0 ~ 1.0)
        task: 작업 유형 (extract_info, extract_dimensions, infer_manufacturing, generate_qc)

    Returns:
        VL 분석 결과 dict
    """
    try:
        # 파일 확장자에서 content-type 결정
        content_type = mimetypes.guess_type(filename)[0] or "image/png"
        logger.info(
            f"Calling VL API for {filename} "
            f"(model={model}, task={task}, temperature={temperature})"
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (filename, file_bytes, content_type)}
            data = {
                "prompt": prompt,
                "model": model,
                "temperature": temperature,
                "task": task
            }

            response = await client.post(
                f"{VL_API_URL}/api/v1/analyze",
                files=files,
                data=data
            )

            logger.info(f"VL API status: {response.status_code}")
            if response.status_code == 200:
                vl_response = response.json()
                logger.info(f"VL API response keys: {vl_response.keys()}")
                return vl_response
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"VL API failed: {response.text}"
                )

    except httpx.TimeoutException:
        logger.error("VL API call timed out")
        raise HTTPException(status_code=504, detail="VL API timeout")
    except Exception as e:
        logger.error(f"VL API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"VL API error: {str(e)}")
