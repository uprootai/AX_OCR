"""
BOMExecutor 세션 관련 작업
세션 생성, detection/dimension import 메서드
"""

import logging
from io import BytesIO
from typing import Any, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


class BOMSessionOpsMixin:
    """BOM 세션 생성 및 데이터 import 믹스인"""

    async def _create_session(
        self, image_data: Any, drawing_type: str = "auto", features: list = None,
        project_id: str = None, metadata: dict = None
    ) -> Tuple[str, int, int]:
        """세션 생성 및 이미지 업로드

        Args:
            image_data: 이미지 데이터 (base64, URL, 바이트 등)
            drawing_type: 빌더에서 설정한 도면 타입
            features: 활성화된 기능 목록 (2025-12-24)
            project_id: 프로젝트 ID (BOM 계층 워크플로우)
            metadata: BOM 메타데이터 (drawing_number, material 등)

        Returns:
            Tuple[str, int, int]: (session_id, image_width, image_height)
        """
        import base64
        import httpx
        import json as _json

        file_bytes = None
        # features를 쉼표 구분 문자열로 변환
        features_param = ",".join(features) if features else ""
        upload_url = f"{self.BASE_URL}/sessions/upload?drawing_type={drawing_type}&features={features_param}"

        # project_id, metadata를 쿼리 파라미터로 추가
        if project_id:
            upload_url += f"&project_id={project_id}"
        if metadata:
            metadata_json = _json.dumps(metadata, ensure_ascii=False)
            from urllib.parse import quote
            upload_url += f"&metadata_json={quote(metadata_json)}"

        async with httpx.AsyncClient(timeout=60) as client:
            # Data URL 형식 (data:image/png;base64,...)
            if isinstance(image_data, str) and image_data.startswith("data:"):
                # data:image/png;base64,... 형식 파싱
                header, data = image_data.split(",", 1)
                mime_type = header.split(";")[0].split(":")[1]
                ext = mime_type.split("/")[1]
                file_bytes = base64.b64decode(data)

                files = {"file": (f"image.{ext}", file_bytes, mime_type)}
                response = await client.post(upload_url, files=files)

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
                    response = await client.post(upload_url, files=files)

                except Exception as e:
                    logger.error(f"이미지 처리 실패: {type(e).__name__}: {e}")
                    logger.error(f"image_data 타입: {type(image_data)}, 길이: {len(image_data) if isinstance(image_data, str) else 'N/A'}")
                    logger.error(f"image_data 샘플: {image_data[:200] if isinstance(image_data, str) else str(image_data)[:200]}...")
                    raise ValueError(f"이미지 데이터를 디코딩할 수 없습니다: {type(e).__name__}: {e}")

            else:
                # 바이트 데이터인 경우
                file_bytes = image_data
                files = {"file": ("image.png", image_data, "image/png")}
                response = await client.post(upload_url, files=files)

            response.raise_for_status()
            result = response.json()
            session_id = result["session_id"]

        # 이미지 크기 추출 (PIL 사용) - httpx 컨텍스트 매니저 밖에서 처리
        image_width, image_height = 0, 0
        if file_bytes:
            try:
                img = Image.open(BytesIO(file_bytes))
                image_width, image_height = img.size
                logger.info(f"이미지 크기 추출: {image_width}x{image_height}")

                # 세션에 이미지 크기 업데이트 (헬퍼 메서드 사용)
                success, _, error = await self._patch_api(
                    f"/sessions/{session_id}",
                    json_data={"image_width": image_width, "image_height": image_height}
                )
                if success:
                    logger.info(f"세션 이미지 크기 업데이트 완료: {session_id}")
                else:
                    logger.warning(f"세션 이미지 크기 업데이트 실패: {error}")
            except Exception as e:
                logger.warning(f"이미지 크기 추출 실패: {e}")

        return session_id, image_width, image_height

    async def _import_detections(self, session_id: str, detections: list):
        """외부 검출 결과 가져오기 (레거시 - _import_detections_v2 권장)"""
        for detection in detections:
            await self._post_api(
                f"/detection/{session_id}/manual",
                json_data={
                    "class_name": detection.get("class_name", "unknown"),
                    "bbox": detection.get("bbox", {})
                },
                timeout=60
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
            success, result, error = await self._post_api(
                f"/detection/{session_id}/import-bulk",
                json_data={"detections": bulk_detections},
                timeout=120
            )
            if success and result:
                logger.info(f"Bulk import 완료: {result.get('imported_count', 0)}/{len(bulk_detections)}개")
            else:
                logger.error(f"Bulk import 실패: {error}")
        else:
            logger.warning("가져올 검출 결과가 없습니다")

    async def _import_dimensions(self, session_id: str, dimensions: list):
        """eDOCr2 치수 결과를 Blueprint AI BOM 세션에 가져오기

        eDOCr2 노드의 출력 형식:
        {
            "text": "100mm",
            "bbox": {"x1": 100, "y1": 200, "x2": 300, "y2": 250},
            "confidence": 0.95,
            "type": "length",
            ...
        }
        """
        if not dimensions:
            logger.warning("가져올 치수 결과가 없습니다")
            return

        success, result, error = await self._post_api(
            f"/analysis/dimensions/{session_id}/import-bulk",
            json_data={
                "dimensions": dimensions,
                "source": "edocr2",
                "auto_approve_threshold": None  # 자동 승인 비활성화 - 검증 UI에서 확인
            },
            timeout=120
        )
        if success and result:
            logger.info(f"치수 import 완료: {result.get('imported_count', 0)}개")
        else:
            logger.error(f"치수 import 실패: {error}")
