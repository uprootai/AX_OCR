"""
Line Detector Executor
P&ID 라인(배관/신호선) 검출 API 호출
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api
import httpx


class LineDetectorExecutor(BaseNodeExecutor):
    """Line Detector 실행기 - P&ID 라인 검출"""

    API_BASE_URL = "http://line-detector-api:5016"
    PROFILE_OPTIONS = {"pid", "simple", "region_focus", "connectivity"}

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Line Detector 실행

        Parameters:
            - image: base64 인코딩된 이미지 또는 PIL Image
            - method: 검출 방식 (lsd, hough, combined)
            - merge_lines: 공선 라인 병합
            - classify_types: 라인 유형 분류
            - find_intersections: 교차점 검출
            - visualize: 시각화

        Returns:
            - lines: 검출된 라인 목록
            - intersections: 교차점 목록
            - statistics: 통계
            - visualization: 시각화 이미지 (base64)
            - detections: 이전 노드(YOLO)에서 전달받은 심볼 검출 결과 (패스스루)
        """
        # 이전 노드에서 전달받은 detections 보존 (YOLO → Line Detector → PID Analyzer 순차 파이프라인 지원)
        passthrough_detections = inputs.get("detections", [])
        passthrough_symbols = inputs.get("symbols", [])

        # 이미지 준비
        file_bytes = prepare_image_for_api(inputs, context)

        # 파라미터 추출
        profile = self.parameters.get("profile")
        method = self.parameters.get("method")
        merge_lines = self.parameters.get("merge_lines")
        classify_types = self.parameters.get("classify_types")
        classify_colors = self.parameters.get("classify_colors")
        classify_styles = self.parameters.get("classify_styles")
        find_intersections = self.parameters.get("find_intersections")
        detect_regions = self.parameters.get("detect_regions")
        region_line_styles = self.parameters.get("region_line_styles")
        min_region_area = self.parameters.get("min_region_area")
        visualize = self.parameters.get("visualize")
        visualize_regions = self.parameters.get("visualize_regions")
        include_svg = self.parameters.get("include_svg")
        min_length = self.parameters.get("min_length")
        max_lines = self.parameters.get("max_lines")
        filename = self.parameters.get("filename", "pid_image.jpg")

        # API 호출
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=30.0)) as client:
            files = {"file": (filename, file_bytes, "image/jpeg")}
            data: Dict[str, str] = {}
            string_params = {
                "profile": profile,
                "method": method,
                "region_line_styles": region_line_styles,
            }
            boolean_params = {
                "merge_lines": merge_lines,
                "classify_types": classify_types,
                "classify_colors": classify_colors,
                "classify_styles": classify_styles,
                "find_intersections": find_intersections,
                "detect_regions": detect_regions,
                "visualize": visualize,
                "visualize_regions": visualize_regions,
                "include_svg": include_svg,
            }
            numeric_params = {
                "min_region_area": min_region_area,
                "min_length": min_length,
                "max_lines": max_lines,
            }
            for key, value in string_params.items():
                if value is not None:
                    data[key] = str(value)
            for key, value in boolean_params.items():
                if value is not None:
                    data[key] = str(value).lower()
            for key, value in numeric_params.items():
                if value is not None:
                    data[key] = str(value)

            response = await client.post(
                f"{self.API_BASE_URL}/api/v1/process",
                files=files,
                data=data
            )

            if response.status_code != 200:
                raise Exception(f"Line Detector API 에러: {response.status_code} - {response.text}")

            # 대용량 JSON 파싱 최적화: orjson 사용 (기본 json보다 5-10배 빠름)
            import orjson
            result = orjson.loads(response.content)

        if not result.get("success", False):
            raise Exception(f"Line Detector 실패: {result.get('error', 'Unknown error')}")

        data = result.get("data", {})

        # 원본 이미지 패스스루 (후속 노드에서 필요)
        import base64
        original_image = inputs.get("image", "")
        if not original_image and file_bytes:
            original_image = base64.b64encode(file_bytes).decode("utf-8")

        output = {
            # Line Detector 결과
            "lines": data.get("lines", []),
            "intersections": data.get("intersections", []),
            "statistics": data.get("statistics", {}),
            "regions": data.get("regions", []),
            "visualized_image": data.get("visualization", ""),  # 프론트엔드 호환 필드명
            "visualization": data.get("visualization", ""),
            "svg_overlay": data.get("svg_overlay", {}),
            "image": original_image,  # 원본 이미지 패스스루
            "method": data.get("method", method),
            "image_size": data.get("image_size", {}),
            "options_used": data.get("options_used", {}),
            "processing_time": result.get("processing_time", 0),
            # 패스스루: 이전 노드(YOLO)의 결과를 다음 노드(PID Analyzer)로 전달
            "detections": passthrough_detections,
            "symbols": passthrough_symbols,
        }

        # drawing_type 패스스루 (BOM 세션 생성에 필요)
        if inputs.get("drawing_type"):
            output["drawing_type"] = inputs["drawing_type"]

        # features 패스스루 (세션 UI 동적 구성에 필요)
        if inputs.get("features"):
            output["features"] = inputs["features"]

        return output

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # method 검증
        if "method" in self.parameters:
            method = self.parameters["method"]
            if method not in ["lsd", "hough", "combined"]:
                return False, "method는 'lsd', 'hough', 'combined' 중 하나여야 합니다"
        if "profile" in self.parameters:
            profile = self.parameters["profile"]
            if profile not in self.PROFILE_OPTIONS:
                return False, "profile은 'pid', 'simple', 'region_focus', 'connectivity' 중 하나여야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "Base64 인코딩된 P&ID 이미지"
                }
            },
            "required": ["image"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "lines": {
                    "type": "array",
                    "description": "검출된 라인 목록"
                },
                "intersections": {
                    "type": "array",
                    "description": "교차점 목록"
                },
                "statistics": {
                    "type": "object",
                    "description": "라인 통계"
                },
                "regions": {
                    "type": "array",
                    "description": "검출된 점선 박스 영역 목록"
                },
                "visualization": {
                    "type": "string",
                    "description": "시각화 이미지 (base64)"
                },
                "visualized_image": {
                    "type": "string",
                    "description": "프론트엔드 호환 시각화 이미지 (base64)"
                },
                "svg_overlay": {
                    "type": "object",
                    "description": "선/영역 SVG 오버레이"
                },
                "image_size": {
                    "type": "object",
                    "description": "원본 이미지 크기"
                },
                "options_used": {
                    "type": "object",
                    "description": "실제로 적용된 API 옵션"
                },
                "method": {
                    "type": "string",
                    "description": "실제 사용된 검출 방식"
                },
                "processing_time": {
                    "type": "number",
                    "description": "API 처리 시간"
                },
                "detections": {
                    "type": "array",
                    "description": "패스스루: 이전 노드(YOLO)의 심볼 검출 결과"
                },
                "symbols": {
                    "type": "array",
                    "description": "패스스루: 이전 노드의 심볼 결과"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("linedetector", LineDetectorExecutor)
