"""
OCR Service

eDOCr2 및 PaddleOCR API 호출
"""
import os
import logging
import mimetypes
import asyncio
from typing import Dict, Any
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Configuration
EDOCR_V1_URL = os.getenv("EDOCR_V1_URL", "http://edocr2-api:5001")
EDOCR_V2_URL = os.getenv("EDOCR_V2_URL", "http://edocr2-v2-api:5002")
EDOCR2_URL = os.getenv("EDOCR2_URL", EDOCR_V2_URL)
PADDLEOCR_API_URL = os.getenv("PADDLEOCR_API_URL", "http://paddleocr-api:5006")


async def call_edocr2_ocr(
    file_bytes: bytes,
    filename: str,
    version: str = "v2",
    extract_dimensions: bool = True,
    extract_gdt: bool = True,
    extract_text: bool = True,
    extract_tables: bool = True,
    visualize: bool = False,
    language: str = 'eng',
    cluster_threshold: int = 20
) -> Dict[str, Any]:
    """
    eDOCr2 API 호출

    Args:
        file_bytes: 파일 바이트
        filename: 파일 이름
        version: eDOCr 버전 (v1, v2, ensemble)
        extract_dimensions: 치수 추출 여부
        extract_gdt: GD&T 추출 여부
        extract_text: 텍스트 추출 여부
        extract_tables: 테이블 추출 여부
        visualize: 시각화 생성 여부
        language: OCR 언어 (기본 'eng')
        cluster_threshold: 클러스터링 임계값

    Returns:
        eDOCr2 결과 dict (data 필드 직접 반환)
    """
    try:
        # 파일 확장자에서 content-type 결정 (PDF 또는 이미지)
        content_type = mimetypes.guess_type(filename)[0]
        if content_type is None:
            # 파일 확장자로 추측
            if filename.lower().endswith('.pdf'):
                content_type = "application/pdf"
            else:
                content_type = "image/png"

        logger.info(f"Calling eDOCr2 API for {filename} (version={version}, content-type: {content_type})")
        logger.info(
            f"  extract: dim={extract_dimensions}, gdt={extract_gdt}, "
            f"text={extract_text}, tables={extract_tables}"
        )
        logger.info(f"  visualize={visualize}, language={language}, cluster_threshold={cluster_threshold}")

        # Route based on version
        if version == "ensemble":
            # Call both v1 and v2, then merge with weighted average
            logger.info("Using ensemble mode: calling both v1 and v2")

            async with httpx.AsyncClient(timeout=60.0) as client:
                files = {"file": (filename, file_bytes, content_type)}
                data = {
                    "extract_dimensions": extract_dimensions,
                    "extract_gdt": extract_gdt,
                    "extract_text": extract_text,
                    "visualize": visualize
                }

                # Call v1 and v2 in parallel
                v1_task = client.post(f"{EDOCR_V1_URL}/api/v1/ocr", files=files, data=data)
                v2_task = client.post(f"{EDOCR_V2_URL}/api/v2/ocr", files=files, data=data)

                v1_response, v2_response = await asyncio.gather(v1_task, v2_task, return_exceptions=True)

                # Merge results with weighted average (v1: 0.4, v2: 0.6)
                v1_data = v1_response.json().get('data', {}) if hasattr(v1_response, 'json') else {}
                v2_data = v2_response.json().get('data', {}) if hasattr(v2_response, 'json') else {}

                # Simple merge: prefer v2, but include v1 results
                merged_data = {
                    "dimensions": v2_data.get('dimensions', []) + v1_data.get('dimensions', []),
                    "gdt": v2_data.get('gdt', []) + v1_data.get('gdt', []),
                    "possible_text": v2_data.get('possible_text', []) + v1_data.get('possible_text', []),
                    "text": {**v1_data.get('text', {}), **v2_data.get('text', {})}
                }

                logger.info(f"Ensemble results: {len(merged_data['dimensions'])} dims, {len(merged_data['gdt'])} gdts")
                return merged_data

        else:
            # Single version (v1 or v2)
            if version == "v1":
                url = f"{EDOCR_V1_URL}/api/v1/ocr"
            elif version == "v2":
                url = f"{EDOCR_V2_URL}/api/v2/ocr"
            else:
                raise HTTPException(status_code=400, detail=f"Invalid version: {version}. Use v1, v2, or ensemble")

            async with httpx.AsyncClient(timeout=60.0) as client:
                files = {"file": (filename, file_bytes, content_type)}
                data = {
                    "extract_dimensions": extract_dimensions,
                    "extract_gdt": extract_gdt,
                    "extract_text": extract_text,
                    "visualize": visualize
                }

                response = await client.post(url, files=files, data=data)

                logger.info(f"eDOCr2 {version} API status: {response.status_code}")
                if response.status_code == 200:
                    edocr_response = response.json()
                    edocr_data = edocr_response.get('data', {})
                    dimensions_count = len(edocr_data.get('dimensions', []))
                    gdt_count = len(edocr_data.get('gdt', []))
                    possible_text_count = len(edocr_data.get('possible_text', []))
                    logger.info(
                        f"eDOCr2 {version} results: {dimensions_count} dims, "
                        f"{gdt_count} gdts, {possible_text_count} possible_text"
                    )

                    return edocr_data
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"eDOCr2 {version} failed: {response.text}"
                    )

    except Exception as e:
        logger.error(f"eDOCr2 API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"eDOCr2 error: {str(e)}")


async def call_paddleocr(
    file_bytes: bytes,
    filename: str,
    min_confidence: float = 0.3,
    det_db_thresh: float = 0.3,
    det_db_box_thresh: float = 0.5,
    use_angle_cls: bool = True,
    visualize: bool = False
) -> Dict[str, Any]:
    """
    PaddleOCR API 호출

    Args:
        file_bytes: 파일 바이트
        filename: 파일 이름
        min_confidence: 최소 신뢰도 (기본 0.3)
        det_db_thresh: DB 검출 임계값 (기본 0.3)
        det_db_box_thresh: DB 박스 임계값 (기본 0.5)
        use_angle_cls: 각도 분류 사용 여부 (기본 True)
        visualize: 시각화 이미지 생성 여부 (기본 False)

    Returns:
        PaddleOCR 결과 dict
    """
    try:
        content_type = mimetypes.guess_type(filename)[0] or "image/png"
        logger.info(f"Calling PaddleOCR API for {filename} (min_conf={min_confidence}, visualize={visualize})")

        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": (filename, file_bytes, content_type)}
            data = {
                "min_confidence": str(min_confidence),
                "det_db_thresh": str(det_db_thresh),
                "det_db_box_thresh": str(det_db_box_thresh),
                "use_angle_cls": str(use_angle_cls).lower(),
                "visualize": str(visualize).lower()
            }

            response = await client.post(
                f"{PADDLEOCR_API_URL}/api/v1/ocr",
                files=files,
                data=data
            )

            if response.status_code == 200:
                ocr_response = response.json()
                logger.info(f"PaddleOCR detected {ocr_response.get('total_texts', 0)} texts")
                return ocr_response
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"PaddleOCR failed: {response.text}"
                )

    except Exception as e:
        logger.error(f"PaddleOCR API call failed: {e}")
        raise HTTPException(status_code=500, detail=f"PaddleOCR error: {str(e)}")
