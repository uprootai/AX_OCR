"""
Excel Export Executor
P&ID 분석 결과를 Excel 파일로 내보내기
"""
from typing import Dict, Any
from datetime import datetime

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
import httpx


class ExcelExportExecutor(BaseNodeExecutor):
    """Excel Export 실행기 - P&ID 분석 결과 Excel 내보내기"""

    API_BASE_URL = "http://blueprint-ai-bom-backend:5020"

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
                "excel_url": {"type": "string"},
                "filename": {"type": "string"},
                "summary": {"type": "object"},
            },
        }

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Excel 파일 생성

        Inputs:
            - session_data: 분석 세션 데이터
            - image: 원본 이미지 정보

        Parameters:
            - export_type: 내보내기 범위
            - project_name: 프로젝트명
            - drawing_no: 도면 번호
            - include_rejected: 거부된 항목 포함 여부

        Returns:
            - excel_url: Excel 다운로드 URL
            - filename: 생성된 파일명
            - summary: 내보내기 요약
        """
        # 세션 데이터 추출
        session_data = {}
        session_id = ""

        if "session_data" in inputs:
            session_data = inputs.get("session_data", {})
        if "session_id" in inputs:
            session_id = inputs.get("session_id", "")

        # from_ prefix 입력 확인
        for key, value in inputs.items():
            if key.startswith("from_") and isinstance(value, dict):
                if "pid_valves" in value or "pid_equipment" in value:
                    session_data = value
                if "session_id" in value:
                    session_id = value.get("session_id", "")
                for data_key in ["pid_valves", "pid_equipment", "pid_checklist_items", "pid_deviations"]:
                    if data_key in value and data_key not in session_data:
                        session_data[data_key] = value[data_key]

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

        if not session_id:
            if session_data:
                session_id = f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            else:
                return {
                    "excel_url": "",
                    "filename": "",
                    "summary": {
                        "success": False,
                        "error": "세션 데이터가 없습니다."
                    }
                }

        # 데이터 통계
        valves = session_data.get("pid_valves", [])
        equipment = session_data.get("pid_equipment", [])
        checklist = session_data.get("pid_checklist_items", [])
        deviations = session_data.get("pid_deviations", [])

        total_items = len(valves) + len(equipment) + len(checklist) + len(deviations)
        if total_items == 0:
            return {
                "excel_url": "",
                "filename": "",
                "summary": {
                    "success": False,
                    "error": "내보낼 데이터가 없습니다."
                }
            }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.API_BASE_URL}/api/v1/pid-features/{session_id}/export",
                    params={
                        "export_type": export_type,
                        "project_name": project_name,
                        "drawing_no": drawing_no,
                        "include_rejected": str(include_rejected).lower()
                    }
                )

                if response.status_code != 200:
                    return {
                        "excel_url": "",
                        "filename": "",
                        "summary": {
                            "success": False,
                            "error": f"Excel 생성 실패: {response.status_code}"
                        }
                    }

                content_disp = response.headers.get("Content-Disposition", "")
                filename = f"PID_Analysis_{export_type}_{drawing_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                if "filename=" in content_disp:
                    filename = content_disp.split("filename=")[1].strip('"')

                excel_url = f"/api/v1/pid-features/{session_id}/export?export_type={export_type}"

                return {
                    "excel_url": excel_url,
                    "filename": filename,
                    "summary": {
                        "success": True,
                        "export_type": export_type,
                        "sheets": {
                            "valve": len(valves) if export_type in ["valve", "all"] else 0,
                            "equipment": len(equipment) if export_type in ["equipment", "all"] else 0,
                            "checklist": len(checklist) if export_type in ["checklist", "all"] else 0,
                            "deviation": len(deviations) if export_type in ["deviation", "all"] else 0,
                        }
                    }
                }

        except httpx.ConnectError:
            return {
                "excel_url": "",
                "filename": "",
                "summary": {
                    "success": False,
                    "error": "Blueprint AI BOM 백엔드에 연결할 수 없습니다."
                }
            }


# 레지스트리에 등록
ExecutorRegistry.register("excelexport", ExcelExportExecutor)
