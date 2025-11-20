"""
Merge Node Executor
병렬 실행된 노드들의 출력을 합병
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry


class MergeExecutor(BaseNodeExecutor):
    """Merge 병렬 합병 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        병렬 노드 출력 합병

        Parameters:
            - merge_strategy: 합병 전략
              - "concat_arrays": 배열을 연결
              - "merge_dicts": 딕셔너리를 병합
              - "keep_all": 모든 입력을 그대로 유지 (default)

        Returns:
            - merged_data: 합병된 데이터
            - source_count: 입력 소스 개수
        """
        merge_strategy = self.parameters.get("merge_strategy", "keep_all")

        # 입력 데이터 분석
        sources = {}
        for key, value in inputs.items():
            if key.startswith("from_"):
                source_name = key.replace("from_", "")
                sources[source_name] = value

        self.logger.info(f"Merge: {len(sources)}개 소스로부터 데이터 합병")

        # 합병 전략에 따라 처리
        if merge_strategy == "concat_arrays":
            merged_data = self._concat_arrays(sources)
        elif merge_strategy == "merge_dicts":
            merged_data = self._merge_dicts(sources)
        else:  # keep_all
            merged_data = sources

        return {
            "merged_data": merged_data,
            "source_count": len(sources),
            "sources": list(sources.keys()),
            "merge_strategy": merge_strategy,
        }

    def _concat_arrays(self, sources: Dict[str, Any]) -> Dict[str, list]:
        """
        배열 필드를 연결
        예: detections 배열을 모두 합침
        """
        result = {}

        for source_name, source_data in sources.items():
            if isinstance(source_data, dict):
                for key, value in source_data.items():
                    if isinstance(value, list):
                        if key not in result:
                            result[key] = []
                        result[key].extend(value)
                    else:
                        # 배열이 아닌 필드는 마지막 값 사용
                        result[key] = value

        return result

    def _merge_dicts(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """
        딕셔너리를 병합 (키 충돌 시 마지막 값 사용)
        """
        result = {}

        for source_name, source_data in sources.items():
            if isinstance(source_data, dict):
                result.update(source_data)
            else:
                result[source_name] = source_data

        return result

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        if "merge_strategy" in self.parameters:
            valid_strategies = ["concat_arrays", "merge_dicts", "keep_all"]
            if self.parameters["merge_strategy"] not in valid_strategies:
                return False, f"merge_strategy는 {valid_strategies} 중 하나여야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        return {
            "type": "object",
            "description": "여러 부모 노드의 출력"
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        return {
            "type": "object",
            "properties": {
                "merged_data": {
                    "type": "object",
                    "description": "합병된 데이터"
                },
                "source_count": {
                    "type": "integer",
                    "description": "입력 소스 개수"
                },
                "sources": {
                    "type": "array",
                    "description": "소스 노드 이름 목록"
                }
            }
        }


# 실행기 등록
ExecutorRegistry.register("merge", MergeExecutor)
