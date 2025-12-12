"""
Generic API Executor
동적으로 추가된 Custom API를 실행하는 범용 Executor
"""
from typing import Dict, Any, Optional
"""
Generic API Executor
동적으로 추가된 Custom API를 실행하는 범용 Executor
"""
from typing import Dict, Any, Optional
import httpx
import logging

logger = logging.getLogger(__name__)


class GenericAPIExecutor(BaseNodeExecutor):
    """
    범용 API 실행기 - 모든 REST API 호출 가능

    API Config에서 정의한 설정에 따라 동적으로 API를 호출합니다.
    """

    def __init__(self, node_id: str, node_type: str, parameters: Dict[str, Any], api_config: Dict[str, Any]):
        super().__init__(node_id, node_type, parameters)
        self.api_config = api_config
        self.logger.info(f"GenericAPIExecutor 생성: {api_config.get('name')} (URL: {api_config.get('baseUrl')})")

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic API 실행

        API Config에 정의된 설정에 따라 HTTP 요청을 보냅니다.
        """
        base_url = self.api_config.get("baseUrl", "")
        endpoint = self.api_config.get("endpoint", "/api/v1/process")
        method = self.api_config.get("method", "POST").upper()

        full_url = f"{base_url}{endpoint}"
        timeout = float(self.api_config.get("timeout", 60))
        content_type = self.api_config.get("contentType", "multipart/form-data")

        self.logger.info(f"Generic API 호출: {method} {full_url} (timeout: {timeout}s)")

        # 이미지 처리 (필요한 경우)
        requires_image = self.api_config.get("requiresImage", True)

        try:
            if method == "POST":
                if requires_image and "multipart" in content_type:
                    # 이미지를 multipart/form-data로 전송
                    file_bytes = prepare_image_for_api(inputs, context)

                    # 추가 파라미터
                    data = self._prepare_form_data()

                    async with httpx.AsyncClient(timeout=timeout) as client:
                        files = {"file": ("image.jpg", file_bytes, "image/jpeg")}
                        response = await client.post(full_url, files=files, data=data)
                elif not requires_image or "json" in content_type:
                    # JSON body로 전송
                    json_data = self._prepare_json_data(inputs)

                    async with httpx.AsyncClient(timeout=timeout) as client:
                        response = await client.post(full_url, json=json_data)

                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"Generic API 성공: {response.status_code}")
                    return self._extract_output(result)
                else:
                    raise Exception(f"API 에러: {response.status_code} - {response.text}")

            elif method == "GET":
                params = self._prepare_query_params()
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(full_url, params=params)

                if response.status_code == 200:
                    result = response.json()
                    return self._extract_output(result)
                else:
                    raise Exception(f"API 에러: {response.status_code} - {response.text}")

            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")

        except Exception as e:
            self.logger.error(f"Generic API 호출 실패: {e}")
            raise

    def _prepare_form_data(self) -> Dict[str, Any]:
        """Form data 준비"""
        data = {}

        # API Config의 parameters 정의에 따라 form data 구성
        for param_def in self.api_config.get("parameters", []):
            param_name = param_def["name"]

            # 노드 parameters에서 값 가져오기 (없으면 default 사용)
            if param_name in self.parameters:
                data[param_name] = self.parameters[param_name]
            elif "default" in param_def:
                data[param_name] = param_def["default"]

        return data

    def _prepare_json_data(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        JSON body 준비

        inputMappings가 있으면 필드명을 매핑하고,
        없으면 기존 방식대로 inputs/parameters로 래핑
        """
        input_mappings = self.api_config.get("inputMappings", {})

        if input_mappings:
            # ✅ 개선: inputMappings를 사용하여 필드명 매핑
            # 예: {"prompt": "inputs.text", "negative_prompt": "inputs.negative"}
            mapped_data = {}

            for api_field, workflow_field in input_mappings.items():
                # workflow_field 형식: "inputs.text" or "parameters.style"
                value = self._resolve_field_path(workflow_field, inputs, self.parameters)
                if value is not None:
                    mapped_data[api_field] = value

            # 매핑되지 않은 parameters도 추가
            for param_name, param_value in self.parameters.items():
                if param_name not in mapped_data:
                    mapped_data[param_name] = param_value

            return mapped_data
        else:
            # 기존 방식 (하위 호환성)
            return {
                "inputs": inputs,
                "parameters": self.parameters
            }

    def _resolve_field_path(self, field_path: str, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> Any:
        """
        필드 경로 해석

        예시:
        - "inputs.text" → inputs["text"]
        - "parameters.style" → parameters["style"]
        - "text" → inputs.get("text") or parameters.get("text")
        """
        if "." in field_path:
            parts = field_path.split(".", 1)
            source = parts[0]
            key = parts[1]

            if source == "inputs":
                return inputs.get(key)
            elif source == "parameters":
                return parameters.get(key)
            else:
                # 다단계 경로 (예: "inputs.data.text")
                return self._get_nested_value(inputs, field_path)
        else:
            # 단순 필드명 - inputs 우선, 없으면 parameters
            value = inputs.get(field_path)
            return value if value is not None else parameters.get(field_path)

    def _prepare_query_params(self) -> Dict[str, Any]:
        """Query parameters 준비"""
        return self.parameters

    def _extract_output(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        API 응답에서 출력 추출

        API Config의 outputs 정의에 따라 응답을 파싱합니다.
        """
        from adapters.ocr_adapter import normalize_ocr_output

        # 카테고리별 표준화 적용 (매핑 전)
        category = self.api_config.get("category")
        if category == "ocr":
            normalized_response = normalize_ocr_output(self.api_config.get("id"), response)
        else:
            normalized_response = response

        output = {}
        output_mappings = self.api_config.get("outputMappings", {})

        if output_mappings:
            # 명시적 매핑이 있는 경우
            for output_key, response_path in output_mappings.items():
                output[output_key] = self._get_nested_value(normalized_response, response_path)
        else:
            # 매핑이 없으면 전체 응답 반환
            output = normalized_response

        # 공통 필드 추가
        output["api_name"] = self.api_config.get("name")
        output["raw_response"] = response

        return output

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """
        중첩된 딕셔너리에서 값 추출
        예: "data.detections.count" -> data["data"]["detections"]["count"]
        """
        keys = path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # API Config에 정의된 required parameters 체크
        for param_def in self.api_config.get("parameters", []):
            if param_def.get("required", False):
                param_name = param_def["name"]
                if param_name not in self.parameters and "default" not in param_def:
                    return False, f"필수 파라미터 누락: {param_name}"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        # API Config의 inputs 정의 사용
        properties = {}
        required = []

        for input_def in self.api_config.get("inputs", []):
            properties[input_def["name"]] = {
                "type": input_def.get("type", "string"),
                "description": input_def.get("description", "")
            }
            if input_def.get("required", False):
                required.append(input_def["name"])

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        # API Config의 outputs 정의 사용
        properties = {}

        for output_def in self.api_config.get("outputs", []):
            properties[output_def["name"]] = {
                "type": output_def.get("type", "string"),
                "description": output_def.get("description", "")
            }

        return {
            "type": "object",
            "properties": properties
        }


def create_generic_executor(node_id: str, node_type: str, parameters: Dict[str, Any], api_config: Dict[str, Any]) -> GenericAPIExecutor:
    """
    Generic Executor 팩토리 함수

    런타임에 API Config를 기반으로 GenericAPIExecutor를 생성합니다.
    """
    return GenericAPIExecutor(node_id, node_type, parameters, api_config)



class GenericAPIExecutor(BaseNodeExecutor):
    """
    범용 API 실행기 - 모든 REST API 호출 가능

    API Config에서 정의한 설정에 따라 동적으로 API를 호출합니다.
    """

    def __init__(self, node_id: str, node_type: str, parameters: Dict[str, Any], api_config: Dict[str, Any]):
        super().__init__(node_id, node_type, parameters)
        self.api_config = api_config
        self.logger.info(f"GenericAPIExecutor 생성: {api_config.get('name')} (URL: {api_config.get('baseUrl')})")

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic API 실행

        API Config에 정의된 설정에 따라 HTTP 요청을 보냅니다.
        """
        base_url = self.api_config.get("baseUrl", "")
        endpoint = self.api_config.get("endpoint", "/api/v1/process")
        method = self.api_config.get("method", "POST").upper()

        full_url = f"{base_url}{endpoint}"
        timeout = float(self.api_config.get("timeout", 60))
        content_type = self.api_config.get("contentType", "multipart/form-data")

        self.logger.info(f"Generic API 호출: {method} {full_url} (timeout: {timeout}s)")

        # 이미지 처리 (필요한 경우)
        requires_image = self.api_config.get("requiresImage", True)

        try:
            if method == "POST":
                if requires_image and "multipart" in content_type:
                    # 이미지를 multipart/form-data로 전송
                    file_bytes = prepare_image_for_api(inputs, context)

                    # 추가 파라미터
                    data = self._prepare_form_data()

                    async with httpx.AsyncClient(timeout=timeout) as client:
                        files = {"file": ("image.jpg", file_bytes, "image/jpeg")}
                        response = await client.post(full_url, files=files, data=data)
                elif not requires_image or "json" in content_type:
                    # JSON body로 전송
                    json_data = self._prepare_json_data(inputs)

                    async with httpx.AsyncClient(timeout=timeout) as client:
                        response = await client.post(full_url, json=json_data)

                if response.status_code == 200:
                    result = response.json()
                    self.logger.info(f"Generic API 성공: {response.status_code}")
                    return self._extract_output(result)
                else:
                    raise Exception(f"API 에러: {response.status_code} - {response.text}")

            elif method == "GET":
                params = self._prepare_query_params()
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(full_url, params=params)

                if response.status_code == 200:
                    result = response.json()
                    return self._extract_output(result)
                else:
                    raise Exception(f"API 에러: {response.status_code} - {response.text}")

            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")

        except Exception as e:
            self.logger.error(f"Generic API 호출 실패: {e}")
            raise

    def _prepare_form_data(self) -> Dict[str, Any]:
        """Form data 준비"""
        data = {}

        # API Config의 parameters 정의에 따라 form data 구성
        for param_def in self.api_config.get("parameters", []):
            param_name = param_def["name"]

            # 노드 parameters에서 값 가져오기 (없으면 default 사용)
            if param_name in self.parameters:
                data[param_name] = self.parameters[param_name]
            elif "default" in param_def:
                data[param_name] = param_def["default"]

        return data

    def _prepare_json_data(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        JSON body 준비

        inputMappings가 있으면 필드명을 매핑하고,
        없으면 기존 방식대로 inputs/parameters로 래핑
        """
        input_mappings = self.api_config.get("inputMappings", {})

        if input_mappings:
            # ✅ 개선: inputMappings를 사용하여 필드명 매핑
            # 예: {"prompt": "inputs.text", "negative_prompt": "inputs.negative"}
            mapped_data = {}

            for api_field, workflow_field in input_mappings.items():
                # workflow_field 형식: "inputs.text" or "parameters.style"
                value = self._resolve_field_path(workflow_field, inputs, self.parameters)
                if value is not None:
                    mapped_data[api_field] = value

            # 매핑되지 않은 parameters도 추가
            for param_name, param_value in self.parameters.items():
                if param_name not in mapped_data:
                    mapped_data[param_name] = param_value

            return mapped_data
        else:
            # 기존 방식 (하위 호환성)
            return {
                "inputs": inputs,
                "parameters": self.parameters
            }

    def _resolve_field_path(self, field_path: str, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> Any:
        """
        필드 경로 해석

        예시:
        - "inputs.text" → inputs["text"]
        - "parameters.style" → parameters["style"]
        - "text" → inputs.get("text") or parameters.get("text")
        """
        if "." in field_path:
            parts = field_path.split(".", 1)
            source = parts[0]
            key = parts[1]

            if source == "inputs":
                return inputs.get(key)
            elif source == "parameters":
                return parameters.get(key)
            else:
                # 다단계 경로 (예: "inputs.data.text")
                return self._get_nested_value(inputs, field_path)
        else:
            # 단순 필드명 - inputs 우선, 없으면 parameters
            value = inputs.get(field_path)
            return value if value is not None else parameters.get(field_path)

    def _prepare_query_params(self) -> Dict[str, Any]:
        """Query parameters 준비"""
        return self.parameters

    def _extract_output(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        API 응답에서 출력 추출

        API Config의 outputs 정의에 따라 응답을 파싱합니다.
        """
        from adapters.ocr_adapter import normalize_ocr_output

        # 카테고리별 표준화 적용 (매핑 전)
        category = self.api_config.get("category")
        if category == "ocr":
            self.logger.info(f"Applying OCR normalization for API: {self.api_config.get('id')}")
            normalized_response = normalize_ocr_output(self.api_config.get("id"), response)
        else:
            normalized_response = response

        output = {}
        output_mappings = self.api_config.get("outputMappings", {})

        if output_mappings:
            # 명시적 매핑이 있는 경우
            for output_key, response_path in output_mappings.items():
                output[output_key] = self._get_nested_value(normalized_response, response_path)
        else:
            # 매핑이 없으면 전체 응답 반환
            output = normalized_response

        # 공통 필드 추가
        output["api_name"] = self.api_config.get("name")
        output["raw_response"] = response

        return output

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """
        중첩된 딕셔너리에서 값 추출
        예: "data.detections.count" -> data["data"]["detections"]["count"]
        """
        keys = path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사"""
        # API Config에 정의된 required parameters 체크
        for param_def in self.api_config.get("parameters", []):
            if param_def.get("required", False):
                param_name = param_def["name"]
                if param_name not in self.parameters and "default" not in param_def:
                    return False, f"필수 파라미터 누락: {param_name}"

        return True, None

    def get_input_schema(self) -> Dict[str, Any]:
        """입력 스키마"""
        # API Config의 inputs 정의 사용
        properties = {}
        required = []

        for input_def in self.api_config.get("inputs", []):
            properties[input_def["name"]] = {
                "type": input_def.get("type", "string"),
                "description": input_def.get("description", "")
            }
            if input_def.get("required", False):
                required.append(input_def["name"])

        return {
            "type": "object",
            "properties": properties,
            "required": required
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """출력 스키마"""
        # API Config의 outputs 정의 사용
        properties = {}

        for output_def in self.api_config.get("outputs", []):
            properties[output_def["name"]] = {
                "type": output_def.get("type", "string"),
                "description": output_def.get("description", "")
            }

        return {
            "type": "object",
            "properties": properties
        }


def create_generic_executor(node_id: str, node_type: str, parameters: Dict[str, Any], api_config: Dict[str, Any]) -> GenericAPIExecutor:
    """
    Generic Executor 팩토리 함수

    런타임에 API Config를 기반으로 GenericAPIExecutor를 생성합니다.
    """
    return GenericAPIExecutor(node_id, node_type, parameters, api_config)
