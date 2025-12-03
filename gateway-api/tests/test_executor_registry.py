"""
Executor Registry 테스트
"""
import pytest
from blueprintflow.executors.executor_registry import ExecutorRegistry


class TestExecutorRegistry:
    """ExecutorRegistry 테스트"""

    def test_registry_has_core_executors(self):
        """핵심 실행기가 등록되어 있어야 함"""
        core_executors = [
            'imageinput',
            'textinput',
            'yolo',
            'edocr2',
            'edgnet',
            'skinmodel',
            'paddleocr',
            'vl',
            'if',
            'loop',
            'merge',
        ]
        
        for executor_type in core_executors:
            assert ExecutorRegistry.get(executor_type) is not None, \
                f"Executor '{executor_type}' should be registered"

    def test_registry_returns_none_for_unknown(self):
        """등록되지 않은 실행기는 None 반환"""
        result = ExecutorRegistry.get('unknown_executor_type')
        assert result is None

    def test_get_all_types_returns_list(self):
        """get_all_types()는 리스트를 반환해야 함"""
        all_types = ExecutorRegistry.get_all_types()
        assert isinstance(all_types, list)
        assert len(all_types) > 0

    def test_core_types_in_registry(self):
        """핵심 타입이 등록되어 있어야 함"""
        all_types = ExecutorRegistry.get_all_types()

        # 핵심 타입 확인
        expected_types = ['imageinput', 'yolo', 'edocr2', 'edgnet', 'skinmodel']
        for expected in expected_types:
            assert expected in all_types, f"Type '{expected}' should be registered"
