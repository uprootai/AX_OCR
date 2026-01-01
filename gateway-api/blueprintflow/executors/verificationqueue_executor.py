"""
Verification Queue Executor
Human-in-the-Loop 검증 큐 관리
"""
from typing import Dict, Any, List

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
import httpx


class VerificationQueueExecutor(BaseNodeExecutor):
    """Verification Queue 실행기 - Human-in-the-Loop 검증 큐 관리"""

    API_BASE_URL = "http://blueprint-ai-bom-backend:5020"

    def validate_parameters(self) -> tuple[bool, str | None]:
        """파라미터 유효성 검사"""
        auto_approve_threshold = self.parameters.get("auto_approve_threshold", 0.95)
        if not 0 <= auto_approve_threshold <= 1:
            return False, "auto_approve_threshold는 0과 1 사이여야 합니다."
        batch_size = self.parameters.get("batch_size", 20)
        if batch_size < 1:
            return False, "batch_size는 1 이상이어야 합니다."
        return True, None

    def get_input_schema(self) -> dict:
        """입력 스키마 정의"""
        return {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "세션 ID"},
                "verification_queue": {"type": "array", "description": "검증 대기 항목"},
            },
        }

    def get_output_schema(self) -> dict:
        """출력 스키마 정의"""
        return {
            "type": "object",
            "properties": {
                "verified_items": {"type": "array"},
                "rejected_items": {"type": "array"},
                "pending_items": {"type": "array"},
                "summary": {"type": "object"},
            },
        }

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        검증 큐 조회 및 관리

        Inputs:
            - session_id: 세션 ID
            - verification_queue: 검증 대기 항목 목록 (선택)

        Parameters:
            - queue_filter: 큐 필터 (all, valve, equipment, checklist)
            - sort_by: 정렬 기준
            - batch_size: 배치 크기
            - auto_approve_threshold: 자동 승인 임계값

        Returns:
            - verified_items: 검증 완료 항목
            - rejected_items: 거부된 항목
            - pending_items: 대기 중 항목
            - summary: 검증 현황 요약
        """
        # 세션 ID 추출
        session_id = inputs.get("session_id", "")
        verification_queue = inputs.get("verification_queue", [])

        # from_ prefix 입력 확인
        for key, value in inputs.items():
            if key.startswith("from_") and isinstance(value, dict):
                if "session_id" in value and not session_id:
                    session_id = value.get("session_id", "")
                if "verification_queue" in value and not verification_queue:
                    verification_queue = value.get("verification_queue", [])

        if not session_id:
            session_id = context.get("session_id", "")

        # 파라미터 추출
        queue_filter = self.parameters.get("queue_filter", "all")
        sort_by = self.parameters.get("sort_by", "confidence_asc")
        batch_size = int(self.parameters.get("batch_size", 20))
        auto_approve_threshold = float(self.parameters.get("auto_approve_threshold", 0.95))

        # 결과 초기화
        verified_items: List[Dict] = []
        rejected_items: List[Dict] = []
        pending_items: List[Dict] = []

        # 세션 ID가 없으면 입력 큐에서 처리
        if not session_id and verification_queue:
            # 로컬 처리
            for item in verification_queue:
                confidence = item.get("confidence", 0)
                item_type = item.get("item_type", "")

                # 필터 적용
                if queue_filter != "all" and item_type != queue_filter:
                    continue

                # 자동 승인 처리
                if confidence >= auto_approve_threshold:
                    item["verification_status"] = "auto_verified"
                    verified_items.append(item)
                else:
                    pending_items.append(item)

            # 정렬
            if sort_by == "confidence_asc":
                pending_items.sort(key=lambda x: x.get("confidence", 0))
            elif sort_by == "confidence_desc":
                pending_items.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            elif sort_by == "type":
                pending_items.sort(key=lambda x: x.get("item_type", ""))

            # 배치 크기 적용
            pending_items = pending_items[:batch_size]

            return {
                "verified_items": verified_items,
                "rejected_items": rejected_items,
                "pending_items": pending_items,
                "summary": {
                    "total": len(verification_queue),
                    "verified": len(verified_items),
                    "rejected": len(rejected_items),
                    "pending": len(pending_items),
                    "auto_approved": len([v for v in verified_items if v.get("verification_status") == "auto_verified"]),
                    "progress_rate": len(verified_items) / max(len(verification_queue), 1) * 100
                }
            }

        # API 호출
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 검증 큐 조회
                resp = await client.get(
                    f"{self.API_BASE_URL}/api/v1/pid-features/{session_id}/verify/queue",
                    params={"item_type": queue_filter}
                )

                if resp.status_code == 200:
                    data = resp.json()
                    all_items = data.get("items", [])

                    # 상태별 분류
                    for item in all_items:
                        status = item.get("verification_status", "pending")
                        confidence = item.get("confidence", 0)

                        if status == "verified" or status == "auto_verified":
                            verified_items.append(item)
                        elif status == "rejected":
                            rejected_items.append(item)
                        else:
                            # 자동 승인 처리
                            if confidence >= auto_approve_threshold:
                                item["verification_status"] = "auto_verified"
                                verified_items.append(item)
                            else:
                                pending_items.append(item)

                    # 정렬
                    if sort_by == "confidence_asc":
                        pending_items.sort(key=lambda x: x.get("confidence", 0))
                    elif sort_by == "confidence_desc":
                        pending_items.sort(key=lambda x: x.get("confidence", 0), reverse=True)

                    # 배치 크기 적용
                    pending_items = pending_items[:batch_size]

                # 요약 조회
                summary_resp = await client.get(
                    f"{self.API_BASE_URL}/api/v1/pid-features/{session_id}/summary"
                )
                summary = {}
                if summary_resp.status_code == 200:
                    summary = summary_resp.json()

                return {
                    "verified_items": verified_items,
                    "rejected_items": rejected_items,
                    "pending_items": pending_items,
                    "summary": {
                        "total": len(verified_items) + len(rejected_items) + len(pending_items),
                        "verified": len(verified_items),
                        "rejected": len(rejected_items),
                        "pending": len(pending_items),
                        "auto_approved": len([v for v in verified_items if v.get("verification_status") == "auto_verified"]),
                        "progress_rate": summary.get("verification_progress", 0),
                        "valve_count": summary.get("valve_count", 0),
                        "equipment_count": summary.get("equipment_count", 0),
                        "checklist_count": summary.get("checklist_count", 0)
                    }
                }

        except httpx.ConnectError:
            return {
                "verified_items": [],
                "rejected_items": [],
                "pending_items": verification_queue[:batch_size] if verification_queue else [],
                "summary": {
                    "error": "Blueprint AI BOM 백엔드에 연결할 수 없습니다."
                }
            }

        except Exception as e:
            return {
                "verified_items": [],
                "rejected_items": [],
                "pending_items": [],
                "summary": {
                    "error": f"검증 큐 조회 오류: {str(e)}"
                }
            }


# 레지스트리에 등록
ExecutorRegistry.register("verificationqueue", VerificationQueueExecutor)
