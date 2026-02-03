"""
PID Features Executor
TECHCROSS 통합 워크플로우 - Valve/Equipment/Checklist 한 번에 검출
"""
from typing import Dict, Any, List
from datetime import datetime
import uuid
import base64

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
import httpx


class PIDFeaturesExecutor(BaseNodeExecutor):
    """PID Features 실행기 - TECHCROSS 통합 분석"""

    API_BASE_URL = "http://blueprint-ai-bom-backend:5020"

    # ========================================
    # API 호출 헬퍼 메서드
    # ========================================

    async def _post_api(
        self,
        endpoint: str,
        json_data: dict = None,
        files: dict = None,
        params: dict = None,
        timeout: int = 120
    ) -> tuple[bool, dict | None, str | None]:
        """POST API 호출 헬퍼 메서드"""
        url = f"{self.API_BASE_URL}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=float(timeout)) as client:
                response = await client.post(url, json=json_data, files=files, params=params)
                if response.status_code >= 400:
                    return False, None, f"{response.status_code} - {response.text}"
                try:
                    return True, response.json(), None
                except Exception:
                    return True, {"status_code": response.status_code}, None
        except httpx.ConnectError as e:
            return False, None, f"연결 실패: {e}"
        except Exception as e:
            return False, None, f"오류: {e}"

    def validate_parameters(self) -> tuple[bool, str | None]:
        """파라미터 유효성 검사"""
        confidence_threshold = self.parameters.get("confidence_threshold", 0.7)
        if not 0 <= confidence_threshold <= 1:
            return False, "confidence_threshold는 0과 1 사이여야 합니다."
        product_type = self.parameters.get("product_type", "ALL")
        valid_types = ["ALL", "ECS", "HYCHLOR"]
        if product_type not in valid_types:
            return False, f"product_type은 {valid_types} 중 하나여야 합니다."
        return True, None

    def get_input_schema(self) -> dict:
        """입력 스키마 정의"""
        return {
            "type": "object",
            "properties": {
                "image": {"type": "object", "description": "P&ID 이미지"},
                "detections": {"type": "array", "description": "YOLO 검출 결과"},
                "ocr_results": {"type": "array", "description": "OCR 결과"},
            },
        }

    def get_output_schema(self) -> dict:
        """출력 스키마 정의"""
        return {
            "type": "object",
            "properties": {
                "valves": {"type": "array"},
                "equipment": {"type": "array"},
                "checklist": {"type": "array"},
                "verification_queue": {"type": "array"},
                "session_id": {"type": "string"},
            },
        }

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        P&ID 통합 분석 실행

        Inputs:
            - image: P&ID 도면 이미지
            - detections: YOLO 검출 결과
            - ocr_results: OCR 결과
            - lines: 라인 검출 결과

        Parameters:
            - features: 분석할 기능 목록
            - product_type: BWMS 제품 타입
            - confidence_threshold: 자동 검증 임계값
            - auto_verify_high_confidence: 높은 신뢰도 자동 검증

        Returns:
            - valves: 밸브 목록
            - equipment: 장비 목록
            - checklist: 체크리스트 결과
            - verification_queue: 검증 대기 큐
            - session_id: 세션 ID
        """
        # 이미지 추출
        image_data = None
        filename = ""

        if "image" in inputs:
            image_info = inputs.get("image", {})
            if isinstance(image_info, dict):
                image_data = image_info.get("data")
                filename = image_info.get("filename", "")
            elif isinstance(image_info, str):
                filename = image_info

        # 검출 결과 추출
        detections = inputs.get("detections", [])
        ocr_results = inputs.get("ocr_results", [])
        lines = inputs.get("lines", [])

        # from_ prefix 입력 확인
        for key, value in inputs.items():
            if key.startswith("from_") and isinstance(value, dict):
                if "detections" in value and not detections:
                    detections = value.get("detections", [])
                if "ocr_results" in value and not ocr_results:
                    ocr_results = value.get("ocr_results", [])
                if "lines" in value and not lines:
                    lines = value.get("lines", [])
                if "image" in value and not image_data:
                    img = value.get("image", {})
                    if isinstance(img, dict):
                        image_data = img.get("data")
                        filename = img.get("filename", filename)

        # 파라미터 추출
        features = self.parameters.get("features", ["valve_signal", "equipment", "checklist"])
        product_type = self.parameters.get("product_type", "ALL")
        confidence_threshold = float(self.parameters.get("confidence_threshold", 0.7))
        auto_verify = self.parameters.get("auto_verify_high_confidence", True)

        # 세션 생성
        session_id = f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # 결과 초기화
        valves: List[Dict] = []
        equipment: List[Dict] = []
        checklist: List[Dict] = []
        verification_queue: List[Dict] = []

        # 1. 세션 생성 및 이미지 업로드
        if image_data:
            file_data = base64.b64decode(image_data) if isinstance(image_data, str) else image_data
            await self._post_api(
                f"/api/v1/session/{session_id}/upload",
                files={"file": (filename, file_data)}
            )

        # 2. 검출 결과 저장
        if detections:
            await self._post_api(
                f"/api/v1/session/{session_id}/detections",
                json_data={"detections": detections}
            )

        # 3. 밸브 검출
        if "valve_signal" in features:
            success, data, error = await self._post_api(
                f"/api/v1/pid-features/{session_id}/valve-signal/detect"
            )
            if success and data:
                valves = data.get("valves", [])
                # 검증 큐에 추가
                for v in valves:
                    if v.get("confidence", 1.0) < confidence_threshold:
                        verification_queue.append({
                            "item_id": v.get("valve_id", ""),
                            "item_type": "valve",
                            "confidence": v.get("confidence", 0),
                            "data": v
                        })
                    elif auto_verify:
                        v["verification_status"] = "auto_verified"
            elif error and "연결 실패" in error:
                return {
                    "valves": [],
                    "equipment": [],
                    "checklist": [],
                    "verification_queue": [],
                    "session_id": session_id,
                    "error": "Blueprint AI BOM 백엔드에 연결할 수 없습니다."
                }

        # 4. 장비 검출
        if "equipment" in features:
            success, data, error = await self._post_api(
                f"/api/v1/pid-features/{session_id}/equipment/detect"
            )
            if success and data:
                equipment = data.get("equipment", [])
                # 검증 큐에 추가
                for e in equipment:
                    if e.get("confidence", 1.0) < confidence_threshold:
                        verification_queue.append({
                            "item_id": e.get("tag", ""),
                            "item_type": "equipment",
                            "confidence": e.get("confidence", 0),
                            "data": e
                        })
                    elif auto_verify:
                        e["verification_status"] = "auto_verified"

        # 5. 체크리스트 검증
        if "checklist" in features:
            success, data, _ = await self._post_api(
                f"/api/v1/pid-features/{session_id}/checklist/check",
                params={"product_type": product_type}
            )
            if success and data:
                checklist = data.get("checklist_items", [])
                # Fail 항목은 검증 큐에 추가
                for c in checklist:
                    if c.get("auto_status") == "fail":
                        verification_queue.append({
                            "item_id": c.get("item_no", ""),
                            "item_type": "checklist",
                            "confidence": 0.5,  # Fail은 검토 필요
                            "data": c
                        })

        return {
            "valves": valves,
            "equipment": equipment,
            "checklist": checklist,
            "verification_queue": verification_queue,
            "session_id": session_id,
            "summary": {
                "valve_count": len(valves),
                "equipment_count": len(equipment),
                "checklist_count": len(checklist),
                "pending_verification": len(verification_queue),
                "product_type": product_type
            }
        }


# 레지스트리에 등록
ExecutorRegistry.register("pidfeatures", PIDFeaturesExecutor)
