# Executor 개발 가이드

> BlueprintFlow 노드 실행기 개발을 위한 완전한 가이드

## 개요

Executor는 BlueprintFlow에서 각 노드의 실제 로직을 담당하는 Python 클래스입니다.

```
사용자 워크플로우 → 노드 정의(Frontend) → Executor(Backend) → API 호출/로직 실행
```

## 아키텍처

### 파일 구조

```
gateway-api/
├── blueprintflow/
│   └── executors/
│       ├── base_executor.py         # 기본 추상 클래스
│       ├── executor_registry.py     # 레지스트리 (팩토리)
│       ├── generic_api_executor.py  # YAML 스펙 기반 범용 Executor
│       ├── image_utils.py           # 이미지 처리 유틸리티
│       ├── yolo_executor.py         # YOLO 전용 Executor
│       ├── edocr2_executor.py       # eDOCr2 전용 Executor
│       └── ...
├── api_specs/
│   ├── yolo.yaml                    # YOLO API 스펙
│   └── ...
└── services/
    ├── yolo_service.py              # YOLO API 호출 서비스
    └── ...
```

### Executor 생성 우선순위

`ExecutorRegistry.create()`는 다음 순서로 Executor를 생성합니다:

1. **등록된 전용 Executor** (Python 클래스)
2. **YAML 스펙 기반 GenericAPIExecutor**
3. **Custom API Config 기반 GenericAPIExecutor**

## Executor 개발 방법

### 방법 1: 전용 Executor (복잡한 로직)

복잡한 비즈니스 로직이 필요한 경우 전용 Executor 클래스를 구현합니다.

#### 1단계: Executor 클래스 생성

```python
# gateway-api/blueprintflow/executors/mynode_executor.py

"""
MyNode Executor
나의 커스텀 노드 실행기
"""
from typing import Dict, Any, Optional

from ..executors.base_executor import BaseNodeExecutor
from ..executors.executor_registry import ExecutorRegistry
from ..executors.image_utils import prepare_image_for_api


class MyNodeExecutor(BaseNodeExecutor):
    """내 노드 실행기"""

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        노드 실행 로직

        Args:
            inputs: 입력 데이터 (이전 노드의 출력)
            context: 전역 컨텍스트 (워크플로우 변수 등)

        Returns:
            출력 데이터 (다음 노드로 전달)
        """
        # 1. 이미지 준비 (이미지 처리 노드인 경우)
        file_bytes = prepare_image_for_api(inputs, context)

        # 2. 파라미터 추출
        param1 = self.parameters.get("param1", "default")
        param2 = self.parameters["param2"]  # 필수 파라미터

        # 3. API 호출 또는 로직 실행
        result = await self._call_my_api(file_bytes, param1, param2)

        # 4. 결과 반환
        return {
            "output_field": result.get("data"),
            "processing_time": result.get("time", 0),
            # 원본 이미지 패스스루 (후속 노드에서 필요한 경우)
            "image": inputs.get("image", ""),
        }

    async def _call_my_api(self, file_bytes: bytes, param1: str, param2: Any) -> Dict:
        """API 호출 헬퍼 메서드"""
        from services.my_service import call_my_api
        return await call_my_api(file_bytes, param1, param2)

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """
        파라미터 유효성 검사

        Returns:
            (is_valid: bool, error_message: Optional[str])
        """
        # 필수 파라미터 검증
        if "param2" not in self.parameters:
            return False, "param2는 필수입니다"

        # 범위 검증 예시
        if "threshold" in self.parameters:
            threshold = self.parameters["threshold"]
            if not (0 <= threshold <= 1):
                return False, "threshold는 0~1 사이여야 합니다"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마 (JSON Schema)"""
        return {
            "type": "object",
            "properties": {
                "image": {
                    "type": "string",
                    "description": "Base64 인코딩된 이미지"
                }
            },
            "required": ["image"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마 (JSON Schema)"""
        return {
            "type": "object",
            "properties": {
                "output_field": {
                    "type": "object",
                    "description": "처리 결과"
                },
                "processing_time": {
                    "type": "number",
                    "description": "처리 시간 (초)"
                }
            }
        }


# 레지스트리에 등록 (필수!)
ExecutorRegistry.register("mynode", MyNodeExecutor)
```

#### 2단계: __init__.py에 import 추가

```python
# gateway-api/blueprintflow/executors/__init__.py

# 기존 imports...
from .mynode_executor import MyNodeExecutor  # 추가
```

#### 3단계: 단위 테스트 작성

```python
# gateway-api/tests/test_mynode_executor.py

import pytest
from blueprintflow.executors.executor_registry import ExecutorRegistry


def create_executor(executor_type: str, parameters: dict):
    executor_class = ExecutorRegistry.get(executor_type)
    if executor_class is None:
        return None
    return executor_class(node_id="test", node_type=executor_type, parameters=parameters)


class TestMyNodeExecutor:
    def test_validate_valid_params(self):
        """유효한 파라미터 검증"""
        executor = create_executor("mynode", {
            "param1": "value",
            "param2": 123,
            "threshold": 0.5
        })
        is_valid, error = executor.validate_parameters()
        assert is_valid is True
        assert error is None

    def test_validate_missing_required(self):
        """필수 파라미터 누락"""
        executor = create_executor("mynode", {"param1": "value"})
        is_valid, error = executor.validate_parameters()
        assert is_valid is False
        assert "param2" in error

    def test_validate_invalid_threshold(self):
        """잘못된 threshold 값"""
        executor = create_executor("mynode", {
            "param2": 123,
            "threshold": 1.5  # > 1
        })
        is_valid, error = executor.validate_parameters()
        assert is_valid is False
        assert "threshold" in error
```

### 방법 2: YAML 스펙 기반 (간단한 API 래퍼)

단순히 외부 API를 호출하는 경우 YAML 스펙만 정의하면 됩니다.

```yaml
# gateway-api/api_specs/mynode.yaml

kind: APISpec
version: "1.0"

metadata:
  id: mynode
  name: My Node
  version: "1.0.0"
  description: 나의 커스텀 노드
  category: analysis
  port: 5099
  host: mynode-api  # Docker 서비스 이름

server:
  endpoint: /api/v1/process
  method: POST
  contentType: multipart/form-data
  timeout: 60

blueprintflow:
  category: analysis
  icon: custom
  requiresImage: true
  features:
    - my_feature
  inputs:
    - name: image
      type: image
  outputs:
    - name: result
      type: object

parameters:
  - name: param1
    type: string
    default: "default"
    required: false
    description: 파라미터 1
  - name: param2
    type: number
    default: 0.5
    required: true
    description: 파라미터 2

mappings:
  input:
    image: file
    param1: param_1
  output:
    result: data

i18n:
  ko:
    label: 내 노드
    description: 나의 커스텀 분석 노드
  en:
    label: My Node
    description: My custom analysis node
```

GenericAPIExecutor가 자동으로 이 스펙을 기반으로 API 호출을 처리합니다.

## BaseNodeExecutor API

### 생성자

```python
def __init__(self, node_id: str, node_type: str, parameters: Dict[str, Any]):
    """
    Args:
        node_id: 워크플로우 내 노드 고유 ID
        node_type: 노드 타입 이름 (레지스트리 키)
        parameters: Frontend에서 전달된 파라미터
    """
```

### 필수 메서드

| 메서드 | 설명 | 반환 타입 |
|--------|------|----------|
| `execute()` | 노드 실행 로직 | `Dict[str, Any]` |
| `validate_parameters()` | 파라미터 유효성 검사 | `tuple[bool, Optional[str]]` |

### 선택적 메서드

| 메서드 | 설명 | 기본 반환 |
|--------|------|----------|
| `get_input_schema()` | 입력 JSON Schema | `{"type": "object"}` |
| `get_output_schema()` | 출력 JSON Schema | `{"type": "object"}` |

### 제공되는 속성

| 속성 | 타입 | 설명 |
|------|------|------|
| `self.node_id` | `str` | 노드 고유 ID |
| `self.node_type` | `str` | 노드 타입 |
| `self.parameters` | `Dict` | 노드 파라미터 |
| `self.logger` | `Logger` | 로거 인스턴스 |

## 유틸리티

### image_utils.py

```python
from ..executors.image_utils import prepare_image_for_api

# inputs에서 이미지 추출하여 bytes로 변환
file_bytes = prepare_image_for_api(inputs, context)
```

### 지원하는 이미지 소스

1. `inputs["image"]` - Base64 인코딩된 문자열
2. `inputs["image"]` - PIL Image 객체
3. `context["image_bytes"]` - 이미 바이트로 변환된 이미지
4. `context["file_path"]` - 파일 경로

## 테스트

### 테스트 실행

```bash
# 특정 executor 테스트
pytest tests/test_mynode_executor.py -v

# 모든 executor 테스트
pytest tests/test_executors_unit.py -v

# 전체 테스트
pytest tests/ -v --tb=short
```

### 테스트 패턴

```python
# 테스트 헬퍼
def create_executor(executor_type: str, parameters: dict):
    executor_class = ExecutorRegistry.get(executor_type)
    if executor_class is None:
        return None
    return executor_class(node_id="test", node_type=executor_type, parameters=parameters)

# 유효한 파라미터 테스트
def test_valid_params():
    executor = create_executor("mynode", valid_params)
    is_valid, error = executor.validate_parameters()
    assert is_valid is True

# 잘못된 파라미터 테스트
def test_invalid_params():
    executor = create_executor("mynode", invalid_params)
    is_valid, error = executor.validate_parameters()
    assert is_valid is False

# 스키마 테스트
def test_has_input_schema():
    executor = create_executor("mynode", {})
    schema = executor.get_input_schema()
    assert isinstance(schema, dict)
    assert "type" in schema or "properties" in schema
```

## 체크리스트

새 Executor 개발 시:

- [ ] `BaseNodeExecutor` 상속
- [ ] `execute()` 구현
- [ ] `validate_parameters()` 구현
- [ ] `get_input_schema()` 구현 (선택)
- [ ] `get_output_schema()` 구현 (선택)
- [ ] `ExecutorRegistry.register()` 호출
- [ ] `__init__.py`에 import 추가
- [ ] 단위 테스트 작성
- [ ] API 스펙 YAML 작성 (해당 시)
- [ ] Frontend `nodeDefinitions.ts`에 노드 정의 추가

## 예제 코드

### 간단한 Executor

```python
class SimpleExecutor(BaseNodeExecutor):
    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": "Hello, World!"}

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        return True, None

ExecutorRegistry.register("simple", SimpleExecutor)
```

### API 호출 Executor

```python
class ApiExecutor(BaseNodeExecutor):
    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://api-server:5000/process",
                json={"data": inputs.get("data")}
            )
            return response.json()

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        return True, None

ExecutorRegistry.register("api", ApiExecutor)
```

### 조건 분기 Executor

```python
class IfExecutor(BaseNodeExecutor):
    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        condition = self.parameters.get("condition", {})
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        input_value = inputs.get(field)

        if operator == ">":
            result = input_value > value
        elif operator == "==":
            result = input_value == value
        else:
            result = False

        return {"condition_result": result, **inputs}

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        condition = self.parameters.get("condition")
        if not condition:
            return False, "condition이 필요합니다"
        if not all(k in condition for k in ["field", "operator", "value"]):
            return False, "condition에 field, operator, value가 필요합니다"
        return True, None

ExecutorRegistry.register("if", IfExecutor)
```

## 관련 문서

- [BlueprintFlow 개요](./01_overview.md)
- [노드 타입](./02_node_types.md)
- [API 스펙 작성 가이드](../../gateway-api/api_specs/CONVENTIONS.md)

---

**Version**: 1.0.0
**Last Updated**: 2025-12-31
**Maintained By**: AX Project Team
