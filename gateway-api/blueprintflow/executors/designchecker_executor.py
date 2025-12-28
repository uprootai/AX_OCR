"""
Design Checker Executor
P&ID 도면 설계 오류 검출 및 규정 검증 API 호출
"""
from typing import Dict, Any, Optional
import json

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
import httpx


class DesignCheckerExecutor(BaseNodeExecutor):
    """Design Checker 실행기 - 설계 검증"""

    API_BASE_URL = "http://design-checker-api:5019"

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        설계 검증 실행

        Inputs (이전 노드 출력에서 받음):
            - symbols: YOLO 검출 결과 (model_type=pid_class_aware)
            - connections: PID Analyzer 연결 분석 결과
            - lines: Line Detector 결과 (optional)

        Parameters:
            - categories: 검사할 규칙 카테고리 (쉼표 구분)
            - severity_threshold: 보고할 최소 심각도 (error, warning, info)

        Returns:
            - violations: 위반 사항 목록
            - summary: 검사 요약
            - compliance_score: 규정 준수율 (0-100%)
        """
        # 입력 데이터 추출 (이전 노드 출력에서)
        # 다중 부모 노드인 경우 from_ prefix로 들어옴
        symbols = []
        connections = []
        lines = []

        # 직접 입력 확인 (단일 부모)
        if "detections" in inputs:
            symbols = inputs.get("detections", [])
        if "symbols" in inputs:
            symbols = inputs.get("symbols", [])
        if "connections" in inputs:
            connections = inputs.get("connections", [])
        if "lines" in inputs:
            lines = inputs.get("lines", [])

        # from_ prefix 입력 확인 (다중 부모 - Merge 패턴)
        for key, value in inputs.items():
            if key.startswith("from_") and isinstance(value, dict):
                if "detections" in value and not symbols:
                    symbols = value.get("detections", [])
                if "connections" in value and not connections:
                    connections = value.get("connections", [])
                if "lines" in value and not lines:
                    lines = value.get("lines", [])

        # 입력 검증
        has_symbols = bool(symbols) and len(symbols) > 0
        has_connections = bool(connections) and len(connections) > 0

        # 입력 키 목록 (디버깅용)
        input_keys = list(inputs.keys()) if inputs else []

        # symbols나 connections 키가 전혀 없는 경우 (파이프라인 연결 오류)
        has_symbols_key = "symbols" in inputs or "detections" in inputs or any(
            "symbols" in str(v) or "detections" in str(v) for k, v in inputs.items() if k.startswith("from_")
        )
        has_connections_key = "connections" in inputs

        if not has_symbols_key and not has_connections_key:
            raise ValueError(
                f"Design Checker에 필요한 입력이 없습니다.\n\n"
                f"📥 받은 입력 키: {input_keys}\n"
                f"📊 symbols 개수: {len(symbols)}\n"
                f"📊 connections 개수: {len(connections)}\n\n"
                "📋 필요한 입력:\n"
                "  • symbols: YOLO 노드의 검출 결과 (model_type=pid_class_aware)\n"
                "  • connections: P&ID Analyzer의 연결 분석 결과\n\n"
                "⚠️ 파이프라인 연결을 확인하세요:\n"
                "   1. YOLO 또는 PID Analyzer가 Design Checker에 연결되어야 합니다.\n"
                "   2. 순차 파이프라인에서는 Line Detector가 detections를 전달해야 합니다."
            )

        # symbols/connections 키는 있지만 비어있는 경우 (검출 결과 없음 - 정상적인 상황)
        if not has_symbols and not has_connections:
            # P&ID 심볼이 검출되지 않은 경우 - 검사할 내용이 없으므로 성공 반환
            return {
                "violations": [],
                "summary": {
                    "total": 0,
                    "errors": 0,
                    "warnings": 0,
                    "info": 0,
                    "compliance_score": 100.0,
                    "message": "검출된 심볼이 없어 검사할 항목이 없습니다. P&ID 도면 이미지를 사용해주세요."
                },
                "compliance_score": 100.0,
                "errors": 0,
                "warnings": 0,
                "info_count": 0,
                "rules_checked": 0,
                "checked_at": "",
                "filters_applied": {},
                "processing_time": 0,
                "note": "YOLO가 P&ID 심볼을 검출하지 못했습니다. 입력 이미지가 P&ID 도면인지 확인하세요."
            }

        # 파라미터 추출
        categories = self.parameters.get("categories", "")
        severity_threshold = self.parameters.get("severity_threshold", "info")

        # Form data로 JSON 문자열 전송
        form_data = {
            "symbols": json.dumps(symbols),
            "connections": json.dumps(connections),
            "lines": json.dumps(lines),
            "categories": categories,
            "severity_threshold": severity_threshold
        }

        # API 호출
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.API_BASE_URL}/api/v1/check",
                data=form_data
            )

            if response.status_code != 200:
                raise Exception(f"Design Checker API 에러: {response.status_code} - {response.text}")

            result = response.json()

        if not result.get("success", False):
            raise Exception(f"Design Checker 실패: {result.get('error', 'Unknown error')}")

        data = result.get("data", {})
        summary = data.get("summary", {})

        output = {
            "violations": data.get("violations", []),
            "summary": summary,
            "compliance_score": summary.get("compliance_score", 0),
            "errors": summary.get("errors", 0),
            "warnings": summary.get("warnings", 0),
            "info_count": summary.get("info", 0),
            "rules_checked": data.get("rules_checked", 0),
            "checked_at": data.get("checked_at", ""),
            "filters_applied": data.get("filters_applied", {}),
            "processing_time": result.get("processing_time", 0)
        }

        # 이미지 패스스루 (후속 노드에서 필요)
        if inputs.get("image"):
            output["image"] = inputs["image"]

        # drawing_type 패스스루 (BOM 세션 생성에 필요)
        if inputs.get("drawing_type"):
            output["drawing_type"] = inputs["drawing_type"]

        # features 패스스루 (세션 UI 동적 구성에 필요)
        if inputs.get("features"):
            output["features"] = inputs["features"]

        return output

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # severity_threshold 검증
        if "severity_threshold" in self.parameters:
            threshold = self.parameters["severity_threshold"]
            if threshold not in ["error", "warning", "info"]:
                return False, "severity_threshold는 'error', 'warning', 'info' 중 하나여야 합니다"

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
                "connections": {
                    "type": "array",
                    "description": "PID Analyzer 연결 분석 결과"
                },
                "lines": {
                    "type": "array",
                    "description": "Line Detector 결과"
                }
            },
            "required": ["symbols", "connections"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "violations": {
                    "type": "array",
                    "description": "위반 사항 목록"
                },
                "summary": {
                    "type": "object",
                    "description": "검사 요약"
                },
                "compliance_score": {
                    "type": "number",
                    "description": "규정 준수율 (0-100%)"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("designchecker", DesignCheckerExecutor)
