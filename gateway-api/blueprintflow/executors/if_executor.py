"""
IF Node Executor
조건부 분기 제어 노드
"""
from typing import Dict, Any, Optional
import operator

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry


class IfExecutor(BaseNodeExecutor):
    """IF 조건 분기 실행기"""

    # 지원되는 연산자
    OPERATORS = {
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        ">=": operator.ge,
        "<": operator.lt,
        "<=": operator.le,
        "in": lambda a, b: a in b,
        "not_in": lambda a, b: a not in b,
        "contains": lambda a, b: b in a,
        "exists": lambda a, b: a is not None,
    }

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        조건 평가 및 분기 결정

        Parameters:
            - condition: 조건 설정
              {
                  "field": "total_detections",  # 평가할 필드
                  "operator": ">",              # 연산자
                  "value": 0                    # 비교 값
              }

        Returns:
            - condition_met: 조건 만족 여부 (True/False)
            - branch: "true" 또는 "false"
            - evaluated_value: 평가된 실제 값
        """
        condition = self.parameters.get("condition")

        if not condition:
            raise ValueError("condition 파라미터가 필요합니다")

        # 조건 파싱
        field = condition.get("field")
        op = condition.get("operator")
        expected_value = condition.get("value")

        if not field or not op:
            raise ValueError("condition에 'field'와 'operator'가 필요합니다")

        # 입력에서 필드 값 추출
        actual_value = self._get_field_value(inputs, field)

        # 연산자 가져오기
        op_func = self.OPERATORS.get(op)
        if not op_func:
            raise ValueError(
                f"지원하지 않는 연산자: {op}. "
                f"지원되는 연산자: {list(self.OPERATORS.keys())}"
            )

        # 조건 평가
        try:
            condition_met = op_func(actual_value, expected_value)
        except Exception as e:
            self.logger.error(f"조건 평가 중 에러: {e}")
            condition_met = False

        branch = "true" if condition_met else "false"

        self.logger.info(
            f"IF 조건 평가: {field} {op} {expected_value} => "
            f"{actual_value} => {condition_met} (branch: {branch})"
        )

        return {
            "condition_met": condition_met,
            "branch": branch,
            "evaluated_value": actual_value,
            "expected_value": expected_value,
            "operator": op,
            "field": field,
        }

    def _get_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """
        중첩된 딕셔너리에서 필드 값 추출
        예: "detections.total_count" => data["detections"]["total_count"]
        """
        keys = field_path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        if "condition" not in self.parameters:
            return False, "condition 파라미터가 필요합니다"

        condition = self.parameters["condition"]

        if not isinstance(condition, dict):
            return False, "condition은 딕셔너리여야 합니다"

        if "field" not in condition:
            return False, "condition에 'field'가 필요합니다"

        if "operator" not in condition:
            return False, "condition에 'operator'가 필요합니다"

        if condition["operator"] not in self.OPERATORS:
            return False, f"지원하지 않는 연산자: {condition['operator']}"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "description": "이전 노드의 출력 데이터"
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "condition_met": {
                    "type": "boolean",
                    "description": "조건 만족 여부"
                },
                "branch": {
                    "type": "string",
                    "enum": ["true", "false"],
                    "description": "분기 방향"
                },
                "evaluated_value": {
                    "description": "평가된 실제 값"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("if", IfExecutor)
