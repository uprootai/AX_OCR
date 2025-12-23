"""
PID Analyzer Executor
P&ID 연결성 분석 및 BOM 추출 API 호출
"""
from typing import Dict, Any, Optional
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
            - symbols: YOLO-PID 검출 결과 (detections)
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

        # from_ prefix 입력 확인 (다중 부모 - Merge 패턴)
        for key, value in inputs.items():
            if key.startswith("from_") and isinstance(value, dict):
                # YOLO-PID 출력에서 detections 추출
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
                "  • symbols/detections: YOLO-PID 노드의 검출 결과\n"
                "  • lines: Line Detector 노드의 라인 검출 결과\n\n"
                "⚠️ 연결 확인:\n"
                "  1. YOLO-PID → P&ID Analyzer 연결 필요\n"
                "  2. Line Detector → P&ID Analyzer 연결 필요\n"
                "  3. P&ID Analyzer는 두 노드의 출력을 받아야 합니다!\n\n"
                "💡 권장 파이프라인:\n"
                "  Image Input ─┬→ YOLO-PID ────┬→ P&ID Analyzer\n"
                "               └→ Line Detector┘\n\n"
                "📌 Templates에서 'P&ID Analysis Pipeline'을 사용하면 자동 연결됩니다!"
            )

        # 파라미터 추출
        generate_bom = self.parameters.get("generate_bom", True)
        generate_valve_list = self.parameters.get("generate_valve_list", True)
        generate_equipment_list = self.parameters.get("generate_equipment_list", True)
        visualize = self.parameters.get("visualize", True)

        # JSON Body 구성
        json_body = {
            "symbols": symbols,
            "lines": lines,
            "intersections": intersections,
            "image_base64": image_base64 if visualize else None,
            "generate_bom": generate_bom,
            "generate_valve_list": generate_valve_list,
            "generate_equipment_list": generate_equipment_list,
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

        if not result.get("success", False):
            raise Exception(f"PID Analyzer 실패: {result.get('error', 'Unknown error')}")

        data = result.get("data", {})
        visualization = data.get("visualization", "")

        # 원본 이미지 패스스루 (후속 노드에서 필요) - 시각화가 아닌 원본
        original_image = image_base64 if image_base64 else visualization

        output = {
            # 입력 데이터 전달 (다음 노드에서 사용)
            "symbols": symbols,  # YOLO-PID에서 받은 symbols 전달
            "detections": symbols,  # 별칭
            "lines": lines,      # Line Detector에서 받은 lines 전달
            # P&ID Analyzer 결과
            "connections": data.get("connections", []),
            "graph": data.get("graph", {}),
            "bom": data.get("bom", []),
            "valve_list": data.get("valve_list", []),
            "equipment_list": data.get("equipment_list", []),
            "statistics": data.get("statistics", {}),
            "visualized_image": visualization,  # 프론트엔드 호환 필드명
            "image": original_image,  # 원본 이미지 패스스루
            "processing_time": result.get("processing_time", 0)
        }

        # drawing_type 패스스루 (BOM 세션 생성에 필요)
        if inputs.get("drawing_type"):
            output["drawing_type"] = inputs["drawing_type"]

        return output

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # Boolean 파라미터 검증
        bool_params = ["generate_bom", "generate_valve_list", "generate_equipment_list", "visualize"]
        for param in bool_params:
            if param in self.parameters:
                if not isinstance(self.parameters[param], bool):
                    return False, f"{param}은 boolean 값이어야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "description": "YOLO-PID 검출 결과 (detections)"
                },
                "lines": {
                    "type": "array",
                    "description": "Line Detector 결과"
                },
                "intersections": {
                    "type": "array",
                    "description": "교차점 정보"
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
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("pidanalyzer", PidAnalyzerExecutor)
