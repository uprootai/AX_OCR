"""
OCR Service - PaddleOCR API 호출 서비스
P&ID 도면 이미지에서 텍스트 추출
"""
import os
import logging
import base64
from typing import Optional
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

# Configuration
PADDLEOCR_URL = os.getenv("PADDLEOCR_URL", "http://paddleocr-api:5006")
PADDLEOCR_TIMEOUT = int(os.getenv("PADDLEOCR_TIMEOUT", "120"))


@dataclass
class OCRResult:
    """OCR 결과 데이터 클래스"""
    text: str
    confidence: float
    bbox: list  # [x1, y1, x2, y2, x3, y3, x4, y4]
    x: float
    y: float
    width: float
    height: float


class OCRService:
    """PaddleOCR API 호출 서비스"""

    def __init__(self, base_url: str = PADDLEOCR_URL):
        self.base_url = base_url.rstrip("/")
        self.timeout = PADDLEOCR_TIMEOUT

    async def extract_text_from_image(
        self,
        image_data: bytes,
        lang: str = "en"
    ) -> list[OCRResult]:
        """
        이미지에서 텍스트 추출

        Args:
            image_data: 이미지 바이너리 데이터
            lang: 언어 설정 (en, korean, ch)

        Returns:
            OCRResult 리스트
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Multipart form data로 전송
                files = {"file": ("image.png", image_data, "image/png")}
                data = {"lang": lang}

                response = await client.post(
                    f"{self.base_url}/api/v1/ocr",
                    files=files,
                    data=data
                )

                if response.status_code != 200:
                    logger.error(f"OCR API error: {response.status_code} - {response.text}")
                    return []

                result = response.json()
                detections = result.get("detections", [])

                ocr_results = []
                for det in detections:
                    position = det.get("position", {})
                    ocr_results.append(OCRResult(
                        text=det.get("text", ""),
                        confidence=det.get("confidence", 0.0),
                        bbox=det.get("bbox", []),
                        x=position.get("x", 0),
                        y=position.get("y", 0),
                        width=position.get("width", 0),
                        height=position.get("height", 0)
                    ))

                logger.info(f"OCR extracted {len(ocr_results)} texts")
                return ocr_results

        except httpx.TimeoutException:
            logger.error(f"OCR API timeout after {self.timeout}s")
            return []
        except Exception as e:
            logger.error(f"OCR API error: {e}")
            return []

    async def extract_text_from_base64(
        self,
        image_base64: str,
        lang: str = "en"
    ) -> list[OCRResult]:
        """
        Base64 인코딩된 이미지에서 텍스트 추출

        Args:
            image_base64: Base64 인코딩된 이미지
            lang: 언어 설정

        Returns:
            OCRResult 리스트
        """
        try:
            image_data = base64.b64decode(image_base64)
            return await self.extract_text_from_image(image_data, lang)
        except Exception as e:
            logger.error(f"Base64 decode error: {e}")
            return []

    def check_health(self) -> bool:
        """OCR API 상태 확인"""
        try:
            import httpx
            with httpx.Client(timeout=5) as client:
                response = client.get(f"{self.base_url}/api/v1/health")
                return response.status_code == 200
        except Exception:
            return False


# 싱글톤 인스턴스
ocr_service = OCRService()
