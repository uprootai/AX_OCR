"""
PID Analyzer Executor
P&ID 연결성 분석 및 BOM 추출 API 호출
"""
from typing import Dict, Any, Optional
import logging
import json

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
import httpx


class PidAnalyzerExecutor(BaseNodeExecutor):
    """PID Analyzer 실행기 - 연결성 분석 및 BOM 생성"""

    API_BASE_URL = "http://pid-analyzer-api:5018"

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        P&ID 연결성 분석 실행

        Inputs (이전 노드 출력에서 받음):
            - symbols: YOLO 검출 결과 (detections, model_type=pid_class_aware)
            - lines: Line Detector 결과
            - intersections: Line Detector 교차점 결과
            - image: 원본 이미지 (시각화용, optional)

        Parameters:
            - generate_bom: BOM 생성 여부
            - generate_valve_list: 밸브 시그널 리스트 생성
            - generate_equipment_list: 장비 리스트 생성
            - visualize: 시각화

        Returns:
            - connections: 연결 관계 목록
            - graph: 연결성 그래프
            - bom: 부품 리스트
            - valve_list: 밸브 시그널 리스트
            - equipment_list: 장비 리스트
        """
        # 입력 데이터 추출 (이전 노드 출력에서)
        # 다중 부모 노드인 경우 from_ prefix로 들어옴
        symbols = []
        lines = []
        intersections = []
        texts = []      # OCR 텍스트 (Valve Signal 추출용)
        regions = []    # Line Detector 영역 (Valve Signal 추출용)
        image_base64 = ""

        # 직접 입력 확인 (단일 부모)
        if "detections" in inputs:
            symbols = inputs.get("detections", [])
        if "symbols" in inputs:
            symbols = inputs.get("symbols", [])
        if "lines" in inputs:
            lines = inputs.get("lines", [])
        if "intersections" in inputs:
            intersections = inputs.get("intersections", [])
        if "image" in inputs:
            image_base64 = inputs.get("image", "")
        # OCR 텍스트 입력 (PaddleOCR 등에서)
        if "texts" in inputs:
            texts = inputs.get("texts", [])
        if "text_results" in inputs:
            texts = inputs.get("text_results", [])
        # Line Detector 영역 입력
        if "regions" in inputs:
            regions = inputs.get("regions", [])

        # from_ prefix 입력 확인 (다중 부모 - Merge 패턴)
        for key, value in inputs.items():
            if key.startswith("from_") and isinstance(value, dict):
                # YOLO 출력에서 detections 추출
                if "detections" in value and not symbols:
                    symbols = value.get("detections", [])
                # Line Detector 출력에서 lines 추출
                if "lines" in value and not lines:
                    lines = value.get("lines", [])
                if "intersections" in value and not intersections:
                    intersections = value.get("intersections", [])
                # 이미지 추출 (시각화용)
                if not image_base64:
                    image_base64 = value.get("image") or value.get("visualization") or value.get("visualized_image", "")
                # OCR 텍스트 추출 (PaddleOCR 등에서)
                if not texts:
                    texts = value.get("texts") or value.get("text_results", [])
                # Line Detector 영역 추출
                if not regions:
                    regions = value.get("regions", [])

        # 입력 검증 - 필수 입력이 없으면 친절한 안내 메시지
        has_symbols = bool(symbols) and len(symbols) > 0
        has_lines = bool(lines) and len(lines) > 0

        if not has_symbols and not has_lines:
            # 입력 키 확인 (디버깅용)
            input_keys = list(inputs.keys()) if inputs else []

            raise ValueError(
                "P&ID Analyzer에 필요한 입력이 없습니다.\n\n"
                f"📥 받은 입력 키: {input_keys if input_keys else '(없음)'}\n\n"
                "📋 필요한 입력:\n"
                "  • symbols/detections: YOLO 노드의 검출 결과 (model_type=pid_class_aware)\n"
                "  • lines: Line Detector 노드의 라인 검출 결과\n\n"
                "⚠️ 연결 확인:\n"
                "  1. YOLO → P&ID Analyzer 연결 필요\n"
                "  2. Line Detector → P&ID Analyzer 연결 필요\n"
                "  3. P&ID Analyzer는 두 노드의 출력을 받아야 합니다!\n\n"
                "💡 권장 파이프라인:\n"
                "  Image Input ─┬→ YOLO (P&ID) ─┬→ P&ID Analyzer\n"
                "               └→ Line Detector┘\n\n"
                "📌 Templates에서 'P&ID Analysis Pipeline'을 사용하면 자동 연결됩니다!"
            )

        # 파라미터 추출
        generate_bom = self.parameters.get("generate_bom", True)
        generate_valve_list = self.parameters.get("generate_valve_list", True)
        generate_equipment_list = self.parameters.get("generate_equipment_list", True)
        visualize = self.parameters.get("visualize", True)
        enable_ocr = self.parameters.get("enable_ocr", True)

        # 장비 태그 검출 파라미터 (신규)
        detect_equipment_tags = self.parameters.get("detect_equipment_tags", False)
        equipment_profile = self.parameters.get("equipment_profile", "bwms")
        export_equipment_excel = self.parameters.get("export_equipment_excel", False)

        # JSON Body 구성
        json_body = {
            "symbols": symbols,
            "lines": lines,
            "intersections": intersections,
            "texts": texts,          # OCR 텍스트 (Valve Signal 추출용)
            "regions": regions,      # Line Detector 영역 (BWMS Signal 박스 등)
            "image_base64": image_base64 if visualize else None,
            "generate_bom": generate_bom,
            "generate_valve_list": generate_valve_list,
            "generate_equipment_list": generate_equipment_list,
            "enable_ocr": enable_ocr,
            "visualize": visualize
        }

        # API 호출
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.API_BASE_URL}/api/v1/analyze",
                json=json_body
            )

            if response.status_code != 200:
                raise Exception(f"PID Analyzer API 에러: {response.status_code} - {response.text}")

            # 대용량 JSON 파싱 최적화: orjson 사용 (기본 json보다 5-10배 빠름)
            import orjson
            result = orjson.loads(response.content)

        # 장비 태그 검출 (detect_equipment_tags가 활성화된 경우)
        detected_equipment_tags = []
        equipment_summary = {}
        equipment_excel_url = None

        if detect_equipment_tags and image_base64:
            try:
                detected_equipment_tags, equipment_summary, equipment_excel_url = await self._detect_equipment_tags(
                    image_base64=image_base64,
                    profile_id=equipment_profile,
                    export_excel=export_equipment_excel,
                    context=context
                )
            except Exception as e:
                # 장비 태그 검출 실패는 전체 실패로 처리하지 않음
                self.logger.warning(f"장비 태그 검출 경고: {e}")

        if not result.get("success", False):
            raise Exception(f"PID Analyzer 실패: {result.get('error', 'Unknown error')}")

        data = result.get("data", {})
        visualization = data.get("visualization", "")

        # 원본 이미지 패스스루 (후속 노드에서 필요) - 시각화가 아닌 원본
        original_image = image_base64 if image_base64 else visualization

        output = {
            # 입력 데이터 전달 (다음 노드에서 사용)
            "symbols": symbols,  # YOLO에서 받은 symbols 전달
            "detections": symbols,  # 별칭
            "lines": lines,      # Line Detector에서 받은 lines 전달
            "texts": texts,      # OCR 텍스트 패스스루
            "regions": regions,  # Line Detector 영역 패스스루
            # P&ID Analyzer 결과
            "connections": data.get("connections", []),
            "graph": data.get("graph", {}),
            "bom": data.get("bom", []),
            "valve_list": data.get("valve_list", []),
            "equipment_list": data.get("equipment_list", []),
            "statistics": data.get("statistics", {}),
            "visualized_image": visualization,  # 프론트엔드 호환 필드명
            "image": original_image,  # 원본 이미지 패스스루
            "processing_time": result.get("processing_time", 0),
            # 장비 태그 검출 결과 (신규)
            "detected_equipment_tags": detected_equipment_tags,
            "equipment_tag_summary": equipment_summary,
            "equipment_excel_url": equipment_excel_url,
            "equipment_profile": equipment_profile if detect_equipment_tags else None,
        }

        # drawing_type 패스스루 (BOM 세션 생성에 필요)
        if inputs.get("drawing_type"):
            output["drawing_type"] = inputs["drawing_type"]

        # features 패스스루 (세션 UI 동적 구성에 필요)
        if inputs.get("features"):
            output["features"] = inputs["features"]

        return output

    async def _detect_equipment_tags(
        self,
        image_base64: str,
        profile_id: str,
        export_excel: bool,
        context: Dict[str, Any]
    ) -> tuple[list, dict, Optional[str]]:
        """
        장비 태그 검출 API 호출

        Args:
            image_base64: Base64 인코딩 이미지
            profile_id: 장비 프로파일 (bwms, hvac, process)
            export_excel: Excel 내보내기 여부
            context: 실행 컨텍스트

        Returns:
            (equipment_list, summary, excel_url)
        """
        import base64
        import io

        # Base64 이미지를 바이트로 변환
        if image_base64.startswith("data:"):
            # data:image/png;base64, 프리픽스 제거
            image_base64 = image_base64.split(",", 1)[1]

        image_bytes = base64.b64decode(image_base64)

        # 장비 검출 API 호출
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": ("image.png", io.BytesIO(image_bytes), "image/png")}
            data = {"profile_id": profile_id, "language": "en"}

            response = await client.post(
                f"{self.API_BASE_URL}/api/v1/equipment/detect",
                files=files,
                data=data
            )

            if response.status_code != 200:
                raise Exception(f"장비 검출 API 에러: {response.status_code}")

            import orjson
            result = orjson.loads(response.content)

        if not result.get("success", False):
            raise Exception(f"장비 검출 실패: {result.get('error', 'Unknown')}")

        equipment_data = result.get("data", {})
        equipment_list = equipment_data.get("equipment", [])
        summary = equipment_data.get("summary", {})

        # Excel 내보내기 (옵션)
        excel_url = None
        if export_excel and equipment_list:
            try:
                # Excel 파일 생성 요청
                project_name = context.get("workflow_name", "Unknown Project")
                drawing_no = context.get("node_id", "N/A")

                async with httpx.AsyncClient(timeout=120.0) as excel_client:
                    files = {"file": ("image.png", io.BytesIO(image_bytes), "image/png")}
                    data = {
                        "profile_id": profile_id,
                        "project_name": project_name,
                        "drawing_no": drawing_no,
                        "language": "en"
                    }

                    response = await excel_client.post(
                        f"{self.API_BASE_URL}/api/v1/equipment/export-excel",
                        files=files,
                        data=data
                    )

                    if response.status_code == 200:
                        # Excel 바이너리를 Base64로 변환
                        excel_base64 = base64.b64encode(response.content).decode('utf-8')
                        excel_url = f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{excel_base64}"

            except Exception as e:
                self.logger.warning(f"Excel 생성 경고: {e}")

        return equipment_list, summary, excel_url

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # Boolean 파라미터 검증
        bool_params = [
            "generate_bom", "generate_valve_list", "generate_equipment_list",
            "visualize", "enable_ocr", "detect_equipment_tags", "export_equipment_excel"
        ]
        for param in bool_params:
            if param in self.parameters:
                if not isinstance(self.parameters[param], bool):
                    return False, f"{param}은 boolean 값이어야 합니다"

        # 장비 프로파일 검증
        valid_profiles = ["bwms", "hvac", "process"]
        equipment_profile = self.parameters.get("equipment_profile", "bwms")
        if equipment_profile not in valid_profiles:
            return False, f"equipment_profile은 {valid_profiles} 중 하나여야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "description": "YOLO 검출 결과 (model_type=pid_class_aware)"
                },
                "lines": {
                    "type": "array",
                    "description": "Line Detector 결과"
                },
                "intersections": {
                    "type": "array",
                    "description": "교차점 정보"
                },
                "texts": {
                    "type": "array",
                    "description": "OCR 텍스트 결과 (PaddleOCR 등에서, Valve Signal 추출용)"
                },
                "regions": {
                    "type": "array",
                    "description": "Line Detector 영역 (점선 박스 등, BWMS Signal 영역)"
                },
                "image": {
                    "type": "string",
                    "description": "원본 이미지 (base64, 시각화용)"
                }
            },
            "required": ["symbols", "lines"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                # 패스스루 필드 (다음 노드에서 사용)
                "symbols": {
                    "type": "array",
                    "description": "YOLO 검출 결과 (패스스루)"
                },
                "lines": {
                    "type": "array",
                    "description": "Line Detector 결과 (패스스루)"
                },
                "texts": {
                    "type": "array",
                    "description": "OCR 텍스트 (패스스루)"
                },
                "regions": {
                    "type": "array",
                    "description": "Line Detector 영역 (패스스루)"
                },
                # P&ID Analyzer 결과
                "connections": {
                    "type": "array",
                    "description": "심볼 간 연결 관계"
                },
                "graph": {
                    "type": "object",
                    "description": "연결성 그래프"
                },
                "bom": {
                    "type": "array",
                    "description": "부품 리스트 (BOM)"
                },
                "valve_list": {
                    "type": "array",
                    "description": "밸브 시그널 리스트"
                },
                "equipment_list": {
                    "type": "array",
                    "description": "장비 리스트"
                },
                "detected_equipment_tags": {
                    "type": "array",
                    "description": "산업별 장비 태그 (프로파일 기반 검출)"
                },
                "equipment_tag_summary": {
                    "type": "object",
                    "description": "장비 태그 요약 (타입별 개수 등)"
                },
                "equipment_excel_url": {
                    "type": "string",
                    "description": "장비 목록 Excel 다운로드 URL (Base64)"
                },
                "equipment_profile": {
                    "type": "string",
                    "description": "사용된 장비 프로파일 (bwms, hvac, process)"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("pidanalyzer", PidAnalyzerExecutor)
