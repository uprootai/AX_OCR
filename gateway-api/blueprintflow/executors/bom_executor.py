"""
Blueprint AI BOM Executor
Human-in-the-Loop 기반 BOM 생성 노드 실행기
"""

import logging
import httpx
from typing import Dict, Any, Optional
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
        BOM 생성 실행

        Args:
            inputs: 입력 데이터 (image, detections)
            context: 실행 컨텍스트

        Returns:
            BOM 데이터 또는 검증 UI URL
        """
        try:
            # 파라미터 추출
            skip_verification = self.parameters.get("skip_verification", False)
            confidence = self.parameters.get("confidence", 0.7)
            auto_approve_threshold = self.parameters.get("auto_approve_threshold", 0.95)
            export_format = self.parameters.get("export_format", "excel")

            # 1. 세션 생성 및 이미지 업로드
            # 여러 가능한 이미지 키 지원 (image, visualized_image, segmented_image 등)
            image_data = (
                inputs.get("image") or
                inputs.get("visualized_image") or
                inputs.get("segmented_image") or
                inputs.get("upscaled_image")
            )
            if not image_data:
                available_keys = list(inputs.keys())
                raise ValueError(f"이미지 입력이 필요합니다. 사용 가능한 키: {available_keys}")

            session_id = await self._create_session(image_data)
            logger.info(f"세션 생성됨: {session_id}")

            # 2. 내부 YOLO 검출 실행 (항상 내부 검출 사용 - 더 안정적)
            # 참고: 외부 detections는 현재 지원하지 않음 (bbox 형식 호환성 문제)
            logger.info(f"세션 {session_id}에 대해 내부 YOLO 검출 실행")
            await self._run_detection(session_id, confidence)

            # 3. Human-in-the-Loop 검증 필요 여부 결정
            if not skip_verification:
                # 검증 UI URL 반환
                verification_url = f"{self.FRONTEND_URL}/verification?session={session_id}"
                return {
                    "status": "pending_verification",
                    "session_id": session_id,
                    "verification_url": verification_url,
                    "message": "검증이 필요합니다. UI에서 검출 결과를 확인하세요.",
                    "interactive": True,
                    "ui_action": {
                        "type": "open_url",
                        "url": verification_url,
                        "label": "검증 UI 열기"
                    }
                }

            # 4. 자동 모드: 신뢰도 기반 자동 승인
            await self._auto_approve(session_id, auto_approve_threshold)

            # 5. BOM 생성
            bom_data = await self._generate_bom(session_id)

            # 6. 내보내기 URL 생성
            export_url = f"{self.BASE_URL}/bom/{session_id}/download?format={export_format}"

            return {
                "status": "completed",
                "session_id": session_id,
                "bom_data": bom_data,
                "items": bom_data.get("items", []),
                "summary": bom_data.get("summary", {}),
                "approved_count": bom_data.get("approved_count", 0),
                "export_url": export_url
            }

        except Exception as e:
            logger.error(f"BOM 실행 실패: {e}")
            raise

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        confidence = self.parameters.get("confidence", 0.7)
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            return False, "confidence는 0과 1 사이의 숫자여야 합니다"

        auto_approve_threshold = self.parameters.get("auto_approve_threshold", 0.95)
        if not isinstance(auto_approve_threshold, (int, float)) or not 0 <= auto_approve_threshold <= 1:
            return False, "auto_approve_threshold는 0과 1 사이의 숫자여야 합니다"

        export_format = self.parameters.get("export_format", "excel")
        valid_formats = ["excel", "csv", "json", "pdf"]
        if export_format not in valid_formats:
            return False, f"export_format은 {valid_formats} 중 하나여야 합니다"

        return True, None

    async def _create_session(self, image_data: Any) -> str:
        """세션 생성 및 이미지 업로드"""
        import base64

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
                    file_bytes = base64.b64decode(image_data)
                    # 이미지 포맷 감지 (JPEG: FF D8 FF, PNG: 89 50 4E 47)
                    if file_bytes[:2] == b'\xff\xd8':
                        ext, mime_type = "jpg", "image/jpeg"
                    elif file_bytes[:4] == b'\x89PNG':
                        ext, mime_type = "png", "image/png"
                    else:
                        ext, mime_type = "png", "image/png"  # 기본값

                    files = {"file": (f"image.{ext}", file_bytes, mime_type)}
                    response = await client.post(
                        f"{self.BASE_URL}/sessions/upload",
                        files=files
                    )
                except Exception as e:
                    logger.error(f"Base64 디코딩 실패: {e}")
                    raise ValueError(f"이미지 데이터를 디코딩할 수 없습니다: {e}")
            else:
                # 바이트 데이터인 경우
                files = {"file": ("image.png", image_data, "image/png")}
                response = await client.post(
                    f"{self.BASE_URL}/sessions/upload",
                    files=files
                )

            response.raise_for_status()
            result = response.json()
            return result["session_id"]

    async def _import_detections(self, session_id: str, detections: list):
        """외부 검출 결과 가져오기"""
        async with httpx.AsyncClient(timeout=60) as client:
            for detection in detections:
                await client.post(
                    f"{self.BASE_URL}/detection/{session_id}/manual",
                    json={
                        "class_name": detection.get("class_name", "unknown"),
                        "bbox": detection.get("bbox", {})
                    }
                )

    async def _run_detection(self, session_id: str, confidence: float):
        """검출 실행"""
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.BASE_URL}/detection/{session_id}/detect",
                json={"confidence": confidence}
            )
            response.raise_for_status()

    async def _auto_approve(self, session_id: str, threshold: float):
        """신뢰도 기반 자동 승인"""
        async with httpx.AsyncClient(timeout=60) as client:
            # 검출 결과 조회
            response = await client.get(
                f"{self.BASE_URL}/detection/{session_id}/detections"
            )
            response.raise_for_status()
            data = response.json()

            # 신뢰도가 임계값 이상인 것만 승인
            updates = []
            for detection in data.get("detections", []):
                if detection.get("confidence", 0) >= threshold:
                    updates.append({
                        "detection_id": detection["id"],
                        "status": "approved"
                    })
                else:
                    updates.append({
                        "detection_id": detection["id"],
                        "status": "rejected"
                    })

            if updates:
                await client.put(
                    f"{self.BASE_URL}/detection/{session_id}/verify/bulk",
                    json={"updates": updates}
                )

    async def _generate_bom(self, session_id: str) -> Dict[str, Any]:
        """BOM 생성"""
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.BASE_URL}/bom/{session_id}/generate"
            )
            response.raise_for_status()
            return response.json()


# 실행기 등록
ExecutorRegistry.register("blueprint-ai-bom", BOMExecutor)
