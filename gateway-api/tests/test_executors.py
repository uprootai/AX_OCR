"""
Executor Unit Tests
개별 실행기의 파라미터 검증, 스키마, 기본 동작 테스트
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

from blueprintflow.executors.executor_registry import ExecutorRegistry
from blueprintflow.executors.base_executor import BaseNodeExecutor
from blueprintflow.executors.yolo_executor import YoloExecutor
from blueprintflow.executors.edocr2_executor import Edocr2Executor
from blueprintflow.executors.paddleocr_executor import PaddleocrExecutor
from blueprintflow.executors.edgnet_executor import EdgnetExecutor
from blueprintflow.executors.skinmodel_executor import SkinmodelExecutor
from blueprintflow.executors.imageinput_executor import ImageInputExecutor
from blueprintflow.executors.textinput_executor import TextInputExecutor
from blueprintflow.executors.if_executor import IfExecutor
from blueprintflow.executors.loop_executor import LoopExecutor
from blueprintflow.executors.merge_executor import MergeExecutor


class TestExecutorRegistry:
    """ExecutorRegistry 테스트"""

    def test_registry_has_all_core_executors(self):
        """모든 핵심 실행기가 등록되어 있어야 함"""
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
            'knowledge',
            'tesseract',
            'trocr',
            'esrgan',
            'ocr_ensemble',
        ]

        for executor_type in core_executors:
            executor_class = ExecutorRegistry.get(executor_type)
            assert executor_class is not None, \
                f"Executor '{executor_type}' should be registered"
            assert issubclass(executor_class, BaseNodeExecutor), \
                f"Executor '{executor_type}' should be a subclass of BaseNodeExecutor"

    def test_registry_has_pid_executors(self):
        """P&ID 분석 실행기가 등록되어 있어야 함"""
        pid_executors = [
            'linedetector',
            'yolopid',
            'pidanalyzer',
            'designchecker',
        ]

        for executor_type in pid_executors:
            executor_class = ExecutorRegistry.get(executor_type)
            assert executor_class is not None, \
                f"P&ID Executor '{executor_type}' should be registered"

    def test_registry_returns_none_for_unknown(self):
        """등록되지 않은 실행기는 None 반환"""
        result = ExecutorRegistry.get('unknown_executor_type')
        assert result is None

    def test_registry_returns_none_for_empty_string(self):
        """빈 문자열에 대해 None 반환"""
        result = ExecutorRegistry.get('')
        assert result is None

    def test_get_all_types_returns_complete_list(self):
        """get_all_types()는 모든 등록된 타입을 반환해야 함"""
        all_types = ExecutorRegistry.get_all_types()
        assert isinstance(all_types, list)
        assert len(all_types) >= 16  # At least core + pid executors


class TestYoloExecutor:
    """YOLO Executor 테스트"""

    def test_default_parameters(self):
        """기본 파라미터로 초기화"""
        executor = YoloExecutor('node-1', 'yolo', {})
        assert executor.node_id == 'node-1'
        assert executor.node_type == 'yolo'
        assert executor.parameters == {}

    def test_validate_valid_confidence(self):
        """유효한 confidence 값 검증"""
        executor = YoloExecutor('node-1', 'yolo', {'confidence': 0.5})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True
        assert error is None

    def test_validate_invalid_confidence_range(self):
        """범위 밖의 confidence 값 검증 실패"""
        executor = YoloExecutor('node-1', 'yolo', {'confidence': 1.5})
        is_valid, error = executor.validate_parameters()
        assert is_valid is False
        assert '0~1' in error

    def test_validate_invalid_confidence_negative(self):
        """음수 confidence 값 검증 실패"""
        executor = YoloExecutor('node-1', 'yolo', {'confidence': -0.1})
        is_valid, error = executor.validate_parameters()
        assert is_valid is False

    def test_validate_invalid_confidence_type(self):
        """잘못된 타입의 confidence 값 검증 실패"""
        executor = YoloExecutor('node-1', 'yolo', {'confidence': 'high'})
        is_valid, error = executor.validate_parameters()
        assert is_valid is False

    def test_validate_valid_iou(self):
        """유효한 iou 값 검증"""
        executor = YoloExecutor('node-1', 'yolo', {'iou': 0.45})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_validate_invalid_iou(self):
        """범위 밖의 iou 값 검증 실패"""
        executor = YoloExecutor('node-1', 'yolo', {'iou': 2.0})
        is_valid, error = executor.validate_parameters()
        assert is_valid is False
        assert '0~1' in error

    def test_validate_visualize_bool(self):
        """visualize는 boolean이어야 함"""
        executor = YoloExecutor('node-1', 'yolo', {'visualize': True})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_validate_visualize_invalid(self):
        """visualize에 잘못된 타입 전달 시 실패"""
        executor = YoloExecutor('node-1', 'yolo', {'visualize': 'yes'})
        is_valid, error = executor.validate_parameters()
        assert is_valid is False

    def test_input_schema(self):
        """입력 스키마 확인"""
        executor = YoloExecutor('node-1', 'yolo', {})
        schema = executor.get_input_schema()
        assert 'properties' in schema
        assert 'image' in schema['properties']
        assert 'required' in schema

    def test_output_schema(self):
        """출력 스키마 확인"""
        executor = YoloExecutor('node-1', 'yolo', {})
        schema = executor.get_output_schema()
        assert 'properties' in schema
        assert 'detections' in schema['properties']
        assert 'total_detections' in schema['properties']


class TestEdocr2Executor:
    """eDOCr2 Executor 테스트"""

    def test_initialization(self):
        """초기화 테스트"""
        executor = Edocr2Executor('node-1', 'edocr2', {})
        assert executor.node_id == 'node-1'
        assert executor.node_type == 'edocr2'

    def test_validate_empty_parameters(self):
        """빈 파라미터 검증"""
        executor = Edocr2Executor('node-1', 'edocr2', {})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True


class TestPaddleocrExecutor:
    """PaddleOCR Executor 테스트"""

    def test_initialization(self):
        """초기화 테스트"""
        executor = PaddleocrExecutor('node-1', 'paddleocr', {})
        assert executor.node_id == 'node-1'
        assert executor.node_type == 'paddleocr'

    def test_validate_parameters(self):
        """파라미터 검증"""
        executor = PaddleocrExecutor('node-1', 'paddleocr', {'lang': 'en'})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True


class TestEdgnetExecutor:
    """EDGNet Executor 테스트"""

    def test_initialization(self):
        """초기화 테스트"""
        executor = EdgnetExecutor('node-1', 'edgnet', {})
        assert executor.node_id == 'node-1'
        assert executor.node_type == 'edgnet'

    def test_validate_parameters(self):
        """파라미터 검증"""
        executor = EdgnetExecutor('node-1', 'edgnet', {})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True


class TestSkinmodelExecutor:
    """SkinModel Executor 테스트"""

    def test_initialization(self):
        """초기화 테스트"""
        executor = SkinmodelExecutor('node-1', 'skinmodel', {})
        assert executor.node_id == 'node-1'
        assert executor.node_type == 'skinmodel'

    def test_validate_parameters(self):
        """파라미터 검증"""
        executor = SkinmodelExecutor('node-1', 'skinmodel', {})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True


class TestImageInputExecutor:
    """ImageInput Executor 테스트"""

    def test_initialization(self):
        """초기화 테스트"""
        executor = ImageInputExecutor('node-1', 'imageinput', {})
        assert executor.node_id == 'node-1'
        assert executor.node_type == 'imageinput'

    def test_validate_parameters(self):
        """파라미터 검증"""
        executor = ImageInputExecutor('node-1', 'imageinput', {})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True


class TestTextInputExecutor:
    """TextInput Executor 테스트"""

    def test_initialization(self):
        """초기화 테스트"""
        executor = TextInputExecutor('node-1', 'textinput', {'text': 'hello'})
        assert executor.node_id == 'node-1'
        assert executor.node_type == 'textinput'

    def test_validate_parameters_with_text(self):
        """텍스트 파라미터 검증"""
        executor = TextInputExecutor('node-1', 'textinput', {'text': 'hello world'})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_validate_parameters_empty_text_fails(self):
        """빈 텍스트 파라미터 검증 실패"""
        executor = TextInputExecutor('node-1', 'textinput', {})
        is_valid, error = executor.validate_parameters()
        assert is_valid is False
        assert '텍스트' in error


class TestIfExecutor:
    """IF Executor 테스트"""

    def test_initialization(self):
        """초기화 테스트"""
        condition = {'field': 'count', 'operator': '>', 'value': 0}
        executor = IfExecutor('node-1', 'if', {'condition': condition})
        assert executor.node_id == 'node-1'
        assert executor.node_type == 'if'

    def test_validate_parameters_with_valid_condition(self):
        """유효한 조건 파라미터 검증"""
        condition = {'field': 'count', 'operator': '>', 'value': 0}
        executor = IfExecutor('node-1', 'if', {'condition': condition})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True

    def test_validate_parameters_missing_condition_fails(self):
        """조건 파라미터 누락 시 실패"""
        executor = IfExecutor('node-1', 'if', {})
        is_valid, error = executor.validate_parameters()
        assert is_valid is False
        assert 'condition' in error

    def test_validate_parameters_string_condition_fails(self):
        """문자열 조건은 실패해야 함 (dict 필요)"""
        executor = IfExecutor('node-1', 'if', {'condition': 'data.count > 0'})
        is_valid, error = executor.validate_parameters()
        assert is_valid is False
        assert '딕셔너리' in error


class TestLoopExecutor:
    """Loop Executor 테스트"""

    def test_initialization(self):
        """초기화 테스트"""
        executor = LoopExecutor('node-1', 'loop', {'max_iterations': 10})
        assert executor.node_id == 'node-1'
        assert executor.node_type == 'loop'

    def test_validate_parameters(self):
        """파라미터 검증"""
        executor = LoopExecutor('node-1', 'loop', {})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True


class TestMergeExecutor:
    """Merge Executor 테스트"""

    def test_initialization(self):
        """초기화 테스트"""
        executor = MergeExecutor('node-1', 'merge', {'mode': 'combine'})
        assert executor.node_id == 'node-1'
        assert executor.node_type == 'merge'

    def test_validate_parameters(self):
        """파라미터 검증"""
        executor = MergeExecutor('node-1', 'merge', {})
        is_valid, error = executor.validate_parameters()
        assert is_valid is True


class TestBaseExecutorRun:
    """BaseNodeExecutor.run() 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_run_success_returns_metadata(self):
        """성공 시 메타데이터 반환"""
        executor = YoloExecutor('node-1', 'yolo', {})

        # Mock the execute method
        mock_result = {
            'detections': [{'class': 'valve', 'confidence': 0.9}],
            'total_detections': 1,
            'visualized_image': ''
        }
        executor.execute = AsyncMock(return_value=mock_result)

        result = await executor.run({'image': 'test_image'}, {})

        assert result['success'] is True
        assert result['node_id'] == 'node-1'
        assert result['node_type'] == 'yolo'
        assert 'data' in result
        assert 'execution_time_ms' in result
        assert 'timestamp' in result

    @pytest.mark.asyncio
    async def test_run_failure_returns_error(self):
        """실패 시 에러 반환"""
        executor = YoloExecutor('node-1', 'yolo', {})

        # Mock the execute method to raise an exception
        executor.execute = AsyncMock(side_effect=Exception('API connection failed'))

        result = await executor.run({'image': 'test_image'}, {})

        assert result['success'] is False
        assert result['node_id'] == 'node-1'
        assert 'error' in result
        assert 'API connection failed' in result['error']

    @pytest.mark.asyncio
    async def test_run_validation_failure(self):
        """파라미터 검증 실패 시 에러 반환"""
        executor = YoloExecutor('node-1', 'yolo', {'confidence': 2.0})  # Invalid

        result = await executor.run({'image': 'test_image'}, {})

        assert result['success'] is False
        assert '파라미터 검증 실패' in result['error']


class TestExecutorSchemas:
    """모든 실행기의 스키마 테스트"""

    def test_all_executors_have_input_schema(self):
        """모든 실행기가 입력 스키마를 반환"""
        all_types = ExecutorRegistry.get_all_types()

        for executor_type in all_types:
            executor_class = ExecutorRegistry.get(executor_type)
            if executor_class:
                executor = executor_class('test', executor_type, {})
                schema = executor.get_input_schema()
                assert isinstance(schema, dict), \
                    f"Executor '{executor_type}' should return dict for input schema"
                assert 'type' in schema or 'properties' in schema, \
                    f"Executor '{executor_type}' should have valid input schema"

    def test_all_executors_have_output_schema(self):
        """모든 실행기가 출력 스키마를 반환"""
        all_types = ExecutorRegistry.get_all_types()

        for executor_type in all_types:
            executor_class = ExecutorRegistry.get(executor_type)
            if executor_class:
                executor = executor_class('test', executor_type, {})
                schema = executor.get_output_schema()
                assert isinstance(schema, dict), \
                    f"Executor '{executor_type}' should return dict for output schema"


class TestExecutorValidation:
    """모든 실행기의 파라미터 검증 테스트"""

    def test_all_executors_validate_empty_params(self):
        """모든 실행기가 빈 파라미터로 검증 가능"""
        all_types = ExecutorRegistry.get_all_types()

        for executor_type in all_types:
            executor_class = ExecutorRegistry.get(executor_type)
            if executor_class:
                executor = executor_class('test', executor_type, {})
                is_valid, error = executor.validate_parameters()
                # Most executors should accept empty parameters
                # (they have defaults)
                assert isinstance(is_valid, bool), \
                    f"Executor '{executor_type}' validate_parameters should return bool"
