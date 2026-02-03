"""
PDF Export Executor
P&ID 분석 결과를 PDF 리포트로 내보내기
"""
from typing import Dict, Any
from datetime import datetime

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
import httpx


class PDFExportExecutor(BaseNodeExecutor):
    """PDF Export 실행기 - P&ID 분석 결과 PDF 리포트 생성"""

    API_BASE_URL = "http://blueprint-ai-bom-backend:5020"

    # ========================================
    # API 호출 헬퍼 메서드
    # ========================================

    async def _post_api(
        self,
        endpoint: str,
        json_data: dict = None,
        params: dict = None,
        timeout: int = 60
    ) -> tuple[bool, httpx.Response | None, str | None]:
        """POST API 호출 헬퍼 메서드"""
        url = f"{self.API_BASE_URL}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=float(timeout)) as client:
                response = await client.post(url, json=json_data, params=params)
                if response.status_code >= 400:
                    return False, response, f"{response.status_code} - {response.text}"
                return True, response, None
        except httpx.ConnectError as e:
            return False, None, f"연결 실패: {e}"
        except Exception as e:
            return False, None, f"오류: {e}"

    def validate_parameters(self) -> tuple[bool, str | None]:
        """파라미터 유효성 검사"""
        export_type = self.parameters.get("export_type", "all")
        valid_types = ["all", "valve", "equipment", "checklist", "deviation"]
        if export_type not in valid_types:
            return False, f"export_type은 {valid_types} 중 하나여야 합니다."
        return True, None

    def get_input_schema(self) -> dict:
        """입력 스키마 정의"""
        return {
            "type": "object",
            "properties": {
                "session_data": {"type": "object", "description": "분석 세션 데이터"},
                "session_id": {"type": "string", "description": "세션 ID"},
            },
        }

    def get_output_schema(self) -> dict:
        """출력 스키마 정의"""
        return {
            "type": "object",
            "properties": {
                "pdf_url": {"type": "string"},
                "filename": {"type": "string"},
                "summary": {"type": "object"},
            },
        }

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        PDF 리포트 생성

        Inputs (이전 노드 출력에서 받음):
            - session_data: 분석 세션 데이터 (pid_valves, pid_equipment 등)
            - image: 원본 이미지 정보 (파일명 참조용)

        Parameters:
            - export_type: 내보내기 범위 (all, valve, equipment, checklist, deviation)
            - project_name: 프로젝트명
            - drawing_no: 도면 번호
            - include_rejected: 거부된 항목 포함 여부

        Returns:
            - pdf_url: PDF 다운로드 URL
            - filename: 생성된 파일명
            - summary: 내보내기 요약 (포함 항목 수 등)
        """
        # 세션 데이터 추출
        session_data = {}
        session_id = ""

        # 직접 입력 확인
        if "session_data" in inputs:
            session_data = inputs.get("session_data", {})
        if "session_id" in inputs:
            session_id = inputs.get("session_id", "")

        # from_ prefix 입력 확인 (다중 부모 - Merge 패턴)
        for key, value in inputs.items():
            if key.startswith("from_") and isinstance(value, dict):
                # PID Analyzer 출력
                if "pid_valves" in value or "pid_equipment" in value:
                    session_data = value
                # Blueprint AI BOM 세션
                if "session_id" in value:
                    session_id = value.get("session_id", "")
                # 세션 데이터 병합
                for data_key in ["pid_valves", "pid_equipment", "pid_checklist_items", "pid_deviations"]:
                    if data_key in value and data_key not in session_data:
                        session_data[data_key] = value[data_key]

        # context에서 session_id 확인
        if not session_id:
            session_id = context.get("session_id", "")

        # 이미지에서 도면 번호 추출
        drawing_no = self.parameters.get("drawing_no", "")
        if not drawing_no and "image" in inputs:
            image_info = inputs.get("image", {})
            if isinstance(image_info, dict):
                drawing_no = image_info.get("filename", "")
            elif isinstance(image_info, str):
                drawing_no = image_info

        # 파라미터 추출
        export_type = self.parameters.get("export_type", "all")
        project_name = self.parameters.get("project_name", "Unknown Project")
        include_rejected = self.parameters.get("include_rejected", False)

        # 세션 ID가 없으면 새 세션 생성 또는 에러
        if not session_id:
            # 로컬에서 세션 생성 시도
            if session_data:
                session_id = f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            else:
                return {
                    "pdf_url": "",
                    "filename": "",
                    "summary": {
                        "success": False,
                        "error": "세션 데이터가 없습니다. PID Analyzer 또는 Blueprint AI BOM 노드를 먼저 연결하세요."
                    }
                }

        # 세션 데이터 통계 계산
        valves = session_data.get("pid_valves", [])
        equipment = session_data.get("pid_equipment", [])
        checklist = session_data.get("pid_checklist_items", [])
        deviations = session_data.get("pid_deviations", [])

        # 데이터가 없는 경우
        total_items = len(valves) + len(equipment) + len(checklist) + len(deviations)
        if total_items == 0:
            return {
                "pdf_url": "",
                "filename": "",
                "summary": {
                    "success": False,
                    "valve_count": 0,
                    "equipment_count": 0,
                    "checklist_count": 0,
                    "deviation_count": 0,
                    "error": "내보낼 데이터가 없습니다. 분석 노드를 먼저 실행하세요."
                }
            }

        # API 호출하여 PDF 생성
        # 세션에 데이터 저장 (필요한 경우)
        if session_data:
            await self._post_api(
                f"/api/v1/session/{session_id}/update",
                json_data=session_data
            )

        # PDF 생성 요청
        success, response, error = await self._post_api(
            f"/api/v1/pid-features/{session_id}/export/pdf",
            params={
                "export_type": export_type,
                "project_name": project_name,
                "drawing_no": drawing_no,
                "include_rejected": str(include_rejected).lower()
            }
        )

        if not success:
            # 연결 실패인 경우
            if "연결 실패" in (error or ""):
                return {
                    "pdf_url": "",
                    "filename": "",
                    "summary": {
                        "success": False,
                        "error": "Blueprint AI BOM 백엔드에 연결할 수 없습니다. 컨테이너가 실행 중인지 확인하세요.",
                        "valve_count": len(valves),
                        "equipment_count": len(equipment),
                        "checklist_count": len(checklist),
                        "deviation_count": len(deviations)
                    }
                }
            return {
                "pdf_url": "",
                "filename": "",
                "summary": {
                    "success": False,
                    "error": f"PDF 생성 실패: {error}"
                }
            }

        # Content-Disposition에서 파일명 추출
        content_disp = response.headers.get("Content-Disposition", "") if response else ""
        filename = f"PID_Report_{export_type}_{drawing_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        if "filename=" in content_disp:
            filename = content_disp.split("filename=")[1].strip('"')

        # PDF URL 생성 (실제로는 임시 파일로 저장하거나 base64 반환)
        pdf_url = f"/api/v1/pid-features/{session_id}/export/pdf?export_type={export_type}"

        return {
            "pdf_url": pdf_url,
            "filename": filename,
            "summary": {
                "success": True,
                "export_type": export_type,
                "project_name": project_name,
                "drawing_no": drawing_no,
                "valve_count": len(valves) if export_type in ["valve", "all"] else 0,
                "equipment_count": len(equipment) if export_type in ["equipment", "all"] else 0,
                "checklist_count": len(checklist) if export_type in ["checklist", "all"] else 0,
                "deviation_count": len(deviations) if export_type in ["deviation", "all"] else 0,
                "include_rejected": include_rejected
            }
        }


# 레지스트리에 등록
ExecutorRegistry.register("pdfexport", PDFExportExecutor)
