"""
Dimension Updater Executor
기존 BOM 세션에 eDOCr2 치수를 비동기 추가하는 경량 노드
"""
import logging
import httpx
from typing import Dict, Any, Optional

from .base_executor import BaseNodeExecutor
from .executor_registry import ExecutorRegistry

logger = logging.getLogger(__name__)


class DimensionUpdaterExecutor(BaseNodeExecutor):
    """
    BOM 세션에 치수 데이터를 비동기 import

    입력:
      - session_id: aibom 노드에서 생성된 세션 ID
      - dimensions: edocr2 노드에서 추출된 치수 리스트
    """
    BASE_URL = "http://blueprint-ai-bom-backend:5020"

    async def execute(self, inputs: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 다중 부모 입력 병합 (from_aibom_1, from_edocr2_1 등)
        if any(k.startswith("from_") for k in inputs):
            merged: Dict[str, Any] = {}
            for k, v in inputs.items():
                if k.startswith("from_") and isinstance(v, dict):
                    merged.update(v)
                elif not k.startswith("from_"):
                    merged[k] = v
            inputs = merged

        session_id = inputs.get("session_id")
        dimensions = inputs.get("dimensions", [])

        if not session_id:
            raise ValueError("session_id 필요 (aibom 노드 연결 필요)")

        if not dimensions:
            return {
                "session_id": session_id,
                "imported_count": 0,
                "dimensions": [],
                "message": "치수 데이터 없음 (edocr2 연결 확인)",
            }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.BASE_URL}/analysis/dimensions/{session_id}/import-bulk",
                json={
                    "dimensions": dimensions,
                    "source": "edocr2",
                    "auto_approve_threshold": None,
                },
            )
            resp.raise_for_status()
            result = resp.json()

        count = result.get("imported_count", 0)
        logger.info(f"세션 {session_id}에 치수 {count}개 비동기 import 완료")

        return {
            "session_id": session_id,
            "imported_count": count,
            "dimensions": dimensions,
            "message": f"치수 {count}개가 BOM 세션에 추가됨",
        }

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        return True, None


ExecutorRegistry.register("dimension_updater", DimensionUpdaterExecutor)
