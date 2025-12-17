"""
Blueprint AI BOM Executor
Human-in-the-Loop 기반 BOM 생성 노드 실행기
"""

import logging
import httpx
from io import BytesIO
from typing import Dict, Any, Optional, Tuple
from PIL import Image
from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry

logger = logging.getLogger(__name__)


class BOMExecutor(BaseNodeExecutor):
    """
    Blueprint AI BOM 실행기

    Human-in-the-Loop 검증이 필요한 경우 UI URL을 반환하고,
    자동 모드에서는 직접 BOM을 생성합니다.
    """

    # Blueprint AI BOM 백엔드 URL
    BASE_URL = "http://blueprint-ai-bom-backend:5020"
    FRONTEND_URL = "http://localhost:3000"

    async def execute(self, inputs: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
        """
        BOM 세션 생성 및 검증 UI 열기

        이 노드는 자체적으로 검출을 수행하지 않습니다.
        반드시 YOLO 노드에서 detections를 받아야 합니다.
        세션 생성 후 검증 UI URL을 반환합니다.

        Args:
            inputs: 입력 데이터 (image, detections - 둘 다 필수)
            context: 실행 컨텍스트

        Returns:
            검증 UI URL
        """
        try:

            # 1. 이미지 확인 (필수)
            image_data = (
                inputs.get("image") or
                inputs.get("visualized_image") or
                inputs.get("segmented_image") or
                inputs.get("upscaled_image")
            )
            if not image_data:
                available_keys = list(inputs.keys())
                raise ValueError(f"이미지 입력이 필요합니다. 사용 가능한 키: {available_keys}")

            # 2. detections 확인 (필수 - YOLO 노드에서 받아야 함)
            external_detections = inputs.get("detections")
            if not external_detections or len(external_detections) == 0:
                raise ValueError(
                    "detections 입력이 필요합니다. YOLO 노드를 연결하세요. "
                    "Blueprint AI BOM 노드는 자체 검출을 수행하지 않습니다."
                )

            # 3. 세션 생성 (이미지 크기 자동 추출 및 업데이트)
            session_id, image_width, image_height = await self._create_session(image_data)
            logger.info(f"세션 생성됨: {session_id} (이미지 크기: {image_width}x{image_height})")

            # 4. YOLO 노드의 검출 결과 가져오기
            logger.info(f"YOLO detections 가져오기: {len(external_detections)}개")
            await self._import_detections_v2(session_id, external_detections)

            # 5. 검증 UI URL 반환 (항상 Human-in-the-Loop)
            # WorkflowPage 사용 - GT 비교, Precision, Recall, F1 Score 표시
            verification_url = f"{self.FRONTEND_URL}/workflow?session={session_id}"
            return {
                "status": "pending_verification",
                "session_id": session_id,
                "verification_url": verification_url,
                "detection_count": len(external_detections),
                "image_width": image_width,
                "image_height": image_height,
                "message": "검증 UI에서 검출 결과를 확인하고 BOM을 생성하세요.",
                "interactive": True,
                "ui_action": {
                    "type": "open_url",
                    "url": verification_url,
                    "label": "검증 UI 열기"
                }
            }

        except Exception as e:
            logger.error(f"BOM 실행 실패: {e}")
            raise

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사 - 파라미터 없음"""
        return True, None

    async def _create_session(self, image_data: Any) -> Tuple[str, int, int]:
        """세션 생성 및 이미지 업로드

        Returns:
            Tuple[str, int, int]: (session_id, image_width, image_height)
        """
        import base64

        file_bytes = None

        async with httpx.AsyncClient(timeout=60) as client:
            # Data URL 형식 (data:image/png;base64,...)
            if isinstance(image_data, str) and image_data.startswith("data:"):
                # data:image/png;base64,... 형식 파싱
                header, data = image_data.split(",", 1)
                mime_type = header.split(";")[0].split(":")[1]
                ext = mime_type.split("/")[1]
                file_bytes = base64.b64decode(data)

                files = {"file": (f"image.{ext}", file_bytes, mime_type)}
                response = await client.post(
                    f"{self.BASE_URL}/sessions/upload",
                    files=files
                )
            elif isinstance(image_data, str):
                # Plain base64 string (without data: prefix)
                try:
                    # URL인 경우 (http:// 또는 https://로 시작, 단 /9j/는 JPEG base64이므로 제외)
                    if image_data.startswith(("http://", "https://")):
                        logger.info(f"URL 형식 이미지 감지: {image_data[:100]}...")
                        # URL에서 이미지 다운로드
                        img_response = await client.get(image_data)
                        img_response.raise_for_status()
                        file_bytes = img_response.content
                    else:
                        # Base64 디코딩 (/9j/는 JPEG, iVBOR은 PNG)
                        logger.info(f"Base64 이미지 디코딩 시도 (길이: {len(image_data)}, prefix: {image_data[:10]})")
                        file_bytes = base64.b64decode(image_data)

                    # 이미지 포맷 감지 (JPEG: FF D8 FF, PNG: 89 50 4E 47)
                    if file_bytes[:2] == b'\xff\xd8':
                        ext, mime_type = "jpg", "image/jpeg"
                    elif file_bytes[:4] == b'\x89PNG':
                        ext, mime_type = "png", "image/png"
                    else:
                        ext, mime_type = "png", "image/png"  # 기본값

                    logger.info(f"이미지 포맷: {mime_type}, 크기: {len(file_bytes)} bytes")

                    files = {"file": (f"image.{ext}", file_bytes, mime_type)}
                    response = await client.post(
                        f"{self.BASE_URL}/sessions/upload",
                        files=files
                    )
                except Exception as e:
                    logger.error(f"이미지 처리 실패: {type(e).__name__}: {e}")
                    logger.error(f"image_data 타입: {type(image_data)}, 길이: {len(image_data) if isinstance(image_data, str) else 'N/A'}")
                    logger.error(f"image_data 샘플: {image_data[:200] if isinstance(image_data, str) else str(image_data)[:200]}...")
                    raise ValueError(f"이미지 데이터를 디코딩할 수 없습니다: {type(e).__name__}: {e}")
            else:
                # 바이트 데이터인 경우
                file_bytes = image_data
                files = {"file": ("image.png", image_data, "image/png")}
                response = await client.post(
                    f"{self.BASE_URL}/sessions/upload",
                    files=files
                )

            response.raise_for_status()
            result = response.json()
            session_id = result["session_id"]

            # 이미지 크기 추출 (PIL 사용)
            image_width, image_height = 0, 0
            if file_bytes:
                try:
                    img = Image.open(BytesIO(file_bytes))
                    image_width, image_height = img.size
                    logger.info(f"이미지 크기 추출: {image_width}x{image_height}")

                    # 세션에 이미지 크기 업데이트
                    patch_response = await client.patch(
                        f"{self.BASE_URL}/sessions/{session_id}",
                        json={"image_width": image_width, "image_height": image_height}
                    )
                    if patch_response.status_code == 200:
                        logger.info(f"세션 이미지 크기 업데이트 완료: {session_id}")
                    else:
                        logger.warning(f"세션 이미지 크기 업데이트 실패: {patch_response.status_code}")
                except Exception as e:
                    logger.warning(f"이미지 크기 추출 실패: {e}")

            return session_id, image_width, image_height

    async def _import_detections(self, session_id: str, detections: list):
        """외부 검출 결과 가져오기 (레거시)"""
        async with httpx.AsyncClient(timeout=60) as client:
            for detection in detections:
                await client.post(
                    f"{self.BASE_URL}/detection/{session_id}/manual",
                    json={
                        "class_name": detection.get("class_name", "unknown"),
                        "bbox": detection.get("bbox", {})
                    }
                )

    async def _import_detections_v2(self, session_id: str, detections: list):
        """YOLO 노드의 검출 결과를 Blueprint AI BOM 세션에 가져오기 (Bulk API 사용)

        YOLO 노드의 출력 형식 (두 가지 가능):
        1. {x1, y1, x2, y2} - 코너 좌표
        2. {x, y, width, height} - 중심점/크기 또는 좌상단/크기

        기존 방식: 50개 검출 → 50번 HTTP 요청 (~150ms)
        Bulk 방식: 50개 검출 → 1번 HTTP 요청 (~3ms)
        """
        # 1. 모든 검출 결과를 먼저 변환
        bulk_detections = []

        for det in detections:
            try:
                class_name = det.get("class_name", "unknown")
                confidence = det.get("confidence", 1.0)
                bbox = det.get("bbox", {})

                # bbox 형식 정규화
                if isinstance(bbox, dict):
                    if "width" in bbox and "height" in bbox:
                        x = bbox.get("x", 0)
                        y = bbox.get("y", 0)
                        w = bbox.get("width", 0)
                        h = bbox.get("height", 0)
                        bbox_data = {
                            "x1": int(x),
                            "y1": int(y),
                            "x2": int(x + w),
                            "y2": int(y + h)
                        }
                    else:
                        bbox_data = {
                            "x1": int(bbox.get("x1", 0)),
                            "y1": int(bbox.get("y1", 0)),
                            "x2": int(bbox.get("x2", 0)),
                            "y2": int(bbox.get("y2", 0))
                        }
                elif isinstance(bbox, list) and len(bbox) == 4:
                    bbox_data = {
                        "x1": int(bbox[0]),
                        "y1": int(bbox[1]),
                        "x2": int(bbox[2]),
                        "y2": int(bbox[3])
                    }
                else:
                    logger.warning(f"알 수 없는 bbox 형식: {bbox}")
                    continue

                # bbox 유효성 검사
                if bbox_data["x2"] <= bbox_data["x1"] or bbox_data["y2"] <= bbox_data["y1"]:
                    logger.warning(f"유효하지 않은 bbox (크기 0 이하): {bbox_data}")
                    continue

                bulk_detections.append({
                    "class_name": class_name,
                    "bbox": bbox_data,
                    "confidence": confidence
                })

            except Exception as e:
                logger.warning(f"검출 변환 중 오류: {e}")
                continue

        # 2. Bulk API로 한 번에 전송
        if bulk_detections:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.BASE_URL}/detection/{session_id}/import-bulk",
                    json={"detections": bulk_detections}
                )

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Bulk import 완료: {result.get('imported_count', 0)}/{len(bulk_detections)}개")
                else:
                    logger.error(f"Bulk import 실패: {response.status_code} - {response.text}")
        else:
            logger.warning("가져올 검출 결과가 없습니다")


# 실행기 등록
ExecutorRegistry.register("blueprint-ai-bom", BOMExecutor)
