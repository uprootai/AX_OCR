"""
Blueprint AI BOM Executor
Human-in-the-Loop 기반 BOM 생성 노드 실행기
"""

import logging
import httpx
from io import BytesIO
from typing import Dict, Any, Optional, Tuple
from PIL import Image
from .base_executor import BaseNodeExecutor, APICallerMixin
from .executor_registry import ExecutorRegistry

logger = logging.getLogger(__name__)


class BOMExecutor(BaseNodeExecutor, APICallerMixin):
    """
    Blueprint AI BOM 실행기

    Human-in-the-Loop 검증이 필요한 경우 UI URL을 반환하고,
    자동 모드에서는 직접 BOM을 생성합니다.

    APICallerMixin을 상속받아 재시도 로직이 포함된 API 호출 사용.
    """

    # Blueprint AI BOM 백엔드 URL
    BASE_URL = "http://blueprint-ai-bom-backend:5020"
    API_BASE_URL = "http://blueprint-ai-bom-backend:5020"  # APICallerMixin용
    FRONTEND_URL = "http://localhost:3000"

    # 재시도 설정 (APICallerMixin 오버라이드)
    DEFAULT_TIMEOUT = 60
    DEFAULT_MAX_RETRIES = 3

    # ========================================
    # API 호출 헬퍼 메서드 (레거시 호환 + 재시도 지원)
    # ========================================

    async def _call_api(
        self,
        method: str,
        endpoint: str,
        json_data: dict = None,
        files: dict = None,
        data: dict = None,
        timeout: int = 60,
        raise_on_error: bool = False,
        max_retries: int = 3,
    ) -> Tuple[bool, Optional[dict], Optional[str]]:
        """API 호출 헬퍼 메서드 (재시도 로직 포함)

        Args:
            method: HTTP 메서드 (GET, POST, PATCH, DELETE)
            endpoint: API 엔드포인트 (BASE_URL 이후 경로, 예: "/sessions/upload")
            json_data: JSON 바디
            files: 파일 업로드 (httpx files 형식)
            data: form data
            timeout: 타임아웃 (초)
            raise_on_error: 에러 시 예외 발생 여부
            max_retries: 최대 재시도 횟수 (기본값: 3)

        Returns:
            Tuple[bool, Optional[dict], Optional[str]]: (성공여부, 응답JSON, 에러메시지)
        """
        return await self._api_call_with_retry(
            method=method,
            endpoint=endpoint,
            json_data=json_data,
            files=files,
            data=data,
            timeout=timeout,
            max_retries=max_retries,
            raise_on_error=raise_on_error,
        )

    async def _post_api(
        self,
        endpoint: str,
        json_data: dict = None,
        files: dict = None,
        data: dict = None,
        timeout: int = 60,
        raise_on_error: bool = False
    ) -> Tuple[bool, Optional[dict], Optional[str]]:
        """POST API 호출 편의 메서드 (재시도 포함)"""
        return await self._call_api("POST", endpoint, json_data, files, data, timeout, raise_on_error)

    async def _patch_api(
        self,
        endpoint: str,
        json_data: dict = None,
        timeout: int = 60,
        raise_on_error: bool = False
    ) -> Tuple[bool, Optional[dict], Optional[str]]:
        """PATCH API 호출 편의 메서드 (재시도 포함)"""
        return await self._call_api("PATCH", endpoint, json_data, None, None, timeout, raise_on_error)

    # ========================================
    # 메인 실행 메서드
    # ========================================

    async def execute(self, inputs: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
        """
        BOM 세션 생성 및 검증 UI 열기

        이 노드는 자체적으로 검출을 수행하지 않습니다.
        반드시 YOLO 노드에서 detections를 받아야 합니다.
        세션 생성 후 검증 UI URL을 반환합니다.

        Args:
            inputs: 입력 데이터 (image, detections - 둘 다 필수)
            context: 실행 컨텍스트

        Returns:
            검증 UI URL, 세션 정보
        """
        try:
            # 0. 다중 부모 노드 입력 처리 (from_ prefix 병합)
            # input_collector.py는 부모가 2개 이상이면 from_<node_id> prefix를 유지함
            # 예: {'from_imageinput_1': {...}, 'from_yolo_1': {...}}
            # 이를 단일 딕셔너리로 병합: {'image': '...', 'detections': [...], ...}
            if any(key.startswith("from_") for key in inputs.keys()):
                merged_inputs = {}
                for key, value in inputs.items():
                    if key.startswith("from_") and isinstance(value, dict):
                        merged_inputs.update(value)
                    elif not key.startswith("from_"):
                        merged_inputs[key] = value
                logger.info(f"다중 부모 입력 병합: {list(inputs.keys())} → {list(merged_inputs.keys())}")
                inputs = merged_inputs
            # 0. 활성화할 기능 가져오기
            # ImageInput features + 노드 파라미터 features를 병합 (중복 제거)
            input_features = inputs.get("features", [])
            param_features = self.parameters.get("features", [])
            if isinstance(input_features, str):
                input_features = [input_features]
            if isinstance(param_features, str):
                param_features = [param_features]
            # 병합: input features + param features (중복 제거, 순서 유지)
            seen = set()
            features = []
            for f in list(input_features) + list(param_features):
                if f and f not in seen:
                    seen.add(f)
                    features.append(f)
            if not features:
                features = ["verification"]
            logger.info(f"활성화된 기능 (inputs: {input_features}, params: {param_features} → merged: {features})")

            # drawing_type: inputs 우선, 없으면 노드 파라미터, 최종 기본값 auto
            drawing_type = inputs.get("drawing_type") or self.parameters.get("drawing_type", "auto")
            logger.info(f"도면 타입: {drawing_type} (source: {'inputs' if inputs.get('drawing_type') else 'parameters'})")

            # 1. 이미지 확인 (필수)
            # 원본 이미지: 수작업 라벨 추가용 (깨끗한 이미지)
            # visualized_image: AI 검출 결과 비교용 (YOLO 결과 시각화)
            original_image = inputs.get("image")
            visualized_image = inputs.get("visualized_image")

            # 원본 이미지가 없으면 다른 소스에서 시도
            if not original_image:
                original_image = (
                    inputs.get("upscaled_image") or
                    inputs.get("segmented_image")
                )

            # 최소한 하나의 이미지는 필요
            if not original_image and not visualized_image:
                available_keys = list(inputs.keys())
                raise ValueError(f"이미지 입력이 필요합니다. 사용 가능한 키: {available_keys}")

            # 원본 이미지가 없으면 visualized_image를 원본으로 사용 (경고)
            if not original_image and visualized_image:
                logger.warning("원본 이미지(image)가 없어 visualized_image를 사용합니다. 수작업 라벨 추가 시 바운딩박스가 보일 수 있습니다.")
                original_image = visualized_image

            image_data = original_image

            # 2. detections 확인 (drawing_type에 따라 선택적)
            external_detections = inputs.get("detections", [])

            # drawing_type별 검출 요구사항
            # - auto: VLM 분류 미사용 시 detections 없이 허용 (수동 라벨링)
            # - dimension: 치수 도면 → detections 불필요 (OCR만 사용)
            # - dimension_bom: 치수+BOM → detections 불필요 (OCR + 수동 라벨링)
            # - electrical_panel, pid, assembly: detections 필수 (YOLO 사용)
            # 모든 타입에서 detections 없이 허용 (수동 라벨링 지원)
            # YOLO 연결 시 자동 가져오기, 없으면 검증 UI에서 수동 추가
            detection_optional_types = ["auto", "dimension", "dimension_bom", "electrical_panel", "pid", "assembly"]

            if drawing_type not in detection_optional_types:
                if not external_detections or len(external_detections) == 0:
                    raise ValueError(
                        f"detections 입력이 필요합니다. '{drawing_type}' 타입은 YOLO 노드가 필요합니다."
                    )
            else:
                if not external_detections:
                    logger.info(f"'{drawing_type}' 타입: detections 없이 세션 생성 (OCR 전용 모드)")

            # 3. 세션 생성 (이미지 크기 자동 추출 및 업데이트, 도면 타입, features 전달)
            # project_id, metadata는 inputs에서 가져옴 (BOM 계층 워크플로우)
            project_id = inputs.get("project_id") or self.parameters.get("project_id")
            metadata = inputs.get("metadata") or self.parameters.get("metadata")
            session_id, image_width, image_height = await self._create_session(
                image_data, drawing_type, features,
                project_id=project_id, metadata=metadata
            )
            logger.info(f"세션 생성됨: {session_id} (이미지 크기: {image_width}x{image_height}, features: {features}, project: {project_id})")

            # 4. YOLO 노드의 검출 결과 가져오기 (있는 경우만)
            if external_detections and len(external_detections) > 0:
                logger.info(f"YOLO detections 가져오기: {len(external_detections)}개")
                await self._import_detections_v2(session_id, external_detections)
            else:
                logger.info("detections 없음 - OCR 전용 모드로 세션 생성됨")

            # 5. GT 파일 업로드 (Builder에서 첨부된 경우)
            gt_file = inputs.get("gt_file")
            if gt_file:
                await self._upload_gt_file(session_id, gt_file, image_width, image_height)

            # 6. 단가 파일 업로드 (Builder에서 첨부된 경우)
            pricing_file = inputs.get("pricing_file")
            if pricing_file:
                await self._upload_pricing_file(session_id, pricing_file)

            # 7. eDOCr2 치수 결과 가져오기 (있는 경우)
            dimensions = inputs.get("dimensions", [])
            if dimensions and len(dimensions) > 0:
                logger.info(f"eDOCr2 dimensions 가져오기: {len(dimensions)}개")
                await self._import_dimensions(session_id, dimensions)
            else:
                logger.info("dimensions 없음 - 검증 UI에서 직접 치수 인식 필요")

            # 8. BOM 백엔드 자체 분석 실행 (PaddleOCR 타일 기반 치수 추출)
            success, result, error = await self._post_api(
                f"/analysis/run/{session_id}",
                timeout=120
            )
            if success and result:
                paddle_dims = result.get("dimensions_count", 0)
                internal_tables = result.get("tables_count", 0)
                logger.info(f"BOM 분석 완료: PaddleOCR dims={paddle_dims}, tables={internal_tables}")
            elif error:
                logger.warning(f"BOM 분석 실행 중 오류 (무시): {error}")

            # 9. Gateway Table Detector 결과 덮어쓰기 (내부 테이블보다 품질 높음)
            tables = inputs.get("tables", [])
            regions = inputs.get("regions", [])
            if tables and len(tables) > 0:
                await self._import_tables(session_id, tables, regions)
            else:
                logger.info("Table Detector 결과 없음 - 내부 테이블 유지")

            # 10. 검증 UI URL 반환 (항상 Human-in-the-Loop)
            # WorkflowPage 사용 - GT 비교, Precision, Recall, F1 Score 표시
            # features 파라미터를 URL에 포함
            features_param = ",".join(features) if features else "verification"
            verification_url = f"{self.FRONTEND_URL}/workflow?session={session_id}&features={features_param}"
            detection_count = len(external_detections) if external_detections else 0
            dimension_count = len(dimensions) if dimensions else 0

            # drawing_type에 따른 메시지
            if dimension_count > 0:
                message = f"eDOCr2에서 {dimension_count}개 치수 가져옴. 검증 UI에서 확인하세요."
            elif drawing_type in detection_optional_types and detection_count == 0:
                message = "OCR 전용 모드: 검증 UI에서 수동으로 부품을 추가하고 BOM을 생성하세요."
            else:
                message = "검증 UI에서 검출 결과를 확인하고 BOM을 생성하세요."

            return {
                "status": "pending_verification",
                "session_id": session_id,
                "verification_url": verification_url,
                "detection_count": detection_count,
                "dimension_count": dimension_count,
                "image_width": image_width,
                "image_height": image_height,
                "features": features,
                "drawing_type": drawing_type,
                "message": message,
                "interactive": True,
                "ui_action": {
                    "type": "open_url",
                    "url": verification_url,
                    "label": "검증 UI 열기"
                }
            }

        except Exception as e:
            logger.error(f"BOM 실행 실패: {e}")
            raise

    def validate_parameters(self) -> tuple[bool, Optional[str]]:
        """파라미터 유효성 검사 - 파라미터 없음"""
        return True, None

    async def _create_session(
        self, image_data: Any, drawing_type: str = "auto", features: list = None,
        project_id: str = None, metadata: dict = None
    ) -> Tuple[str, int, int]:
        """세션 생성 및 이미지 업로드

        Args:
            image_data: 이미지 데이터 (base64, URL, 바이트 등)
            drawing_type: 빌더에서 설정한 도면 타입
            features: 활성화된 기능 목록 (2025-12-24)
            project_id: 프로젝트 ID (BOM 계층 워크플로우)
            metadata: BOM 메타데이터 (drawing_number, material 등)

        Returns:
            Tuple[str, int, int]: (session_id, image_width, image_height)
        """
        import base64
        import json as _json

        file_bytes = None
        # features를 쉼표 구분 문자열로 변환
        features_param = ",".join(features) if features else ""
        upload_url = f"{self.BASE_URL}/sessions/upload?drawing_type={drawing_type}&features={features_param}"

        # project_id, metadata를 쿼리 파라미터로 추가
        if project_id:
            upload_url += f"&project_id={project_id}"
        if metadata:
            metadata_json = _json.dumps(metadata, ensure_ascii=False)
            from urllib.parse import quote
            upload_url += f"&metadata_json={quote(metadata_json)}"

        async with httpx.AsyncClient(timeout=60) as client:
            # Data URL 형식 (data:image/png;base64,...)
            if isinstance(image_data, str) and image_data.startswith("data:"):
                # data:image/png;base64,... 형식 파싱
                header, data = image_data.split(",", 1)
                mime_type = header.split(";")[0].split(":")[1]
                ext = mime_type.split("/")[1]
                file_bytes = base64.b64decode(data)

                files = {"file": (f"image.{ext}", file_bytes, mime_type)}
                response = await client.post(
                    upload_url,
                    files=files
                )
            elif isinstance(image_data, str):
                # Plain base64 string (without data: prefix)
                try:
                    # URL인 경우 (http:// 또는 https://로 시작, 단 /9j/는 JPEG base64이므로 제외)
                    if image_data.startswith(("http://", "https://")):
                        logger.info(f"URL 형식 이미지 감지: {image_data[:100]}...")
                        # URL에서 이미지 다운로드
                        img_response = await client.get(image_data)
                        img_response.raise_for_status()
                        file_bytes = img_response.content
                    else:
                        # Base64 디코딩 (/9j/는 JPEG, iVBOR은 PNG)
                        logger.info(f"Base64 이미지 디코딩 시도 (길이: {len(image_data)}, prefix: {image_data[:10]})")
                        file_bytes = base64.b64decode(image_data)

                    # 이미지 포맷 감지 (JPEG: FF D8 FF, PNG: 89 50 4E 47)
                    if file_bytes[:2] == b'\xff\xd8':
                        ext, mime_type = "jpg", "image/jpeg"
                    elif file_bytes[:4] == b'\x89PNG':
                        ext, mime_type = "png", "image/png"
                    else:
                        ext, mime_type = "png", "image/png"  # 기본값

                    logger.info(f"이미지 포맷: {mime_type}, 크기: {len(file_bytes)} bytes")

                    files = {"file": (f"image.{ext}", file_bytes, mime_type)}
                    response = await client.post(
                        upload_url,
                        files=files
                    )
                except Exception as e:
                    logger.error(f"이미지 처리 실패: {type(e).__name__}: {e}")
                    logger.error(f"image_data 타입: {type(image_data)}, 길이: {len(image_data) if isinstance(image_data, str) else 'N/A'}")
                    logger.error(f"image_data 샘플: {image_data[:200] if isinstance(image_data, str) else str(image_data)[:200]}...")
                    raise ValueError(f"이미지 데이터를 디코딩할 수 없습니다: {type(e).__name__}: {e}")
            else:
                # 바이트 데이터인 경우
                file_bytes = image_data
                files = {"file": ("image.png", image_data, "image/png")}
                response = await client.post(
                    upload_url,
                    files=files
                )

            response.raise_for_status()
            result = response.json()
            session_id = result["session_id"]

        # 이미지 크기 추출 (PIL 사용) - httpx 컨텍스트 매니저 밖에서 처리
        image_width, image_height = 0, 0
        if file_bytes:
            try:
                img = Image.open(BytesIO(file_bytes))
                image_width, image_height = img.size
                logger.info(f"이미지 크기 추출: {image_width}x{image_height}")

                # 세션에 이미지 크기 업데이트 (헬퍼 메서드 사용)
                success, _, error = await self._patch_api(
                    f"/sessions/{session_id}",
                    json_data={"image_width": image_width, "image_height": image_height}
                )
                if success:
                    logger.info(f"세션 이미지 크기 업데이트 완료: {session_id}")
                else:
                    logger.warning(f"세션 이미지 크기 업데이트 실패: {error}")
            except Exception as e:
                logger.warning(f"이미지 크기 추출 실패: {e}")

        return session_id, image_width, image_height

    async def _import_detections(self, session_id: str, detections: list):
        """외부 검출 결과 가져오기 (레거시 - _import_detections_v2 권장)"""
        for detection in detections:
            await self._post_api(
                f"/detection/{session_id}/manual",
                json_data={
                    "class_name": detection.get("class_name", "unknown"),
                    "bbox": detection.get("bbox", {})
                },
                timeout=60
            )

    async def _import_detections_v2(self, session_id: str, detections: list):
        """YOLO 노드의 검출 결과를 Blueprint AI BOM 세션에 가져오기 (Bulk API 사용)

        YOLO 노드의 출력 형식 (두 가지 가능):
        1. {x1, y1, x2, y2} - 코너 좌표
        2. {x, y, width, height} - 중심점/크기 또는 좌상단/크기

        기존 방식: 50개 검출 → 50번 HTTP 요청 (~150ms)
        Bulk 방식: 50개 검출 → 1번 HTTP 요청 (~3ms)
        """
        # 1. 모든 검출 결과를 먼저 변환
        bulk_detections = []

        for det in detections:
            try:
                class_name = det.get("class_name", "unknown")
                confidence = det.get("confidence", 1.0)
                bbox = det.get("bbox", {})

                # bbox 형식 정규화
                if isinstance(bbox, dict):
                    if "width" in bbox and "height" in bbox:
                        x = bbox.get("x", 0)
                        y = bbox.get("y", 0)
                        w = bbox.get("width", 0)
                        h = bbox.get("height", 0)
                        bbox_data = {
                            "x1": int(x),
                            "y1": int(y),
                            "x2": int(x + w),
                            "y2": int(y + h)
                        }
                    else:
                        bbox_data = {
                            "x1": int(bbox.get("x1", 0)),
                            "y1": int(bbox.get("y1", 0)),
                            "x2": int(bbox.get("x2", 0)),
                            "y2": int(bbox.get("y2", 0))
                        }
                elif isinstance(bbox, list) and len(bbox) == 4:
                    bbox_data = {
                        "x1": int(bbox[0]),
                        "y1": int(bbox[1]),
                        "x2": int(bbox[2]),
                        "y2": int(bbox[3])
                    }
                else:
                    logger.warning(f"알 수 없는 bbox 형식: {bbox}")
                    continue

                # bbox 유효성 검사
                if bbox_data["x2"] <= bbox_data["x1"] or bbox_data["y2"] <= bbox_data["y1"]:
                    logger.warning(f"유효하지 않은 bbox (크기 0 이하): {bbox_data}")
                    continue

                bulk_detections.append({
                    "class_name": class_name,
                    "bbox": bbox_data,
                    "confidence": confidence
                })

            except Exception as e:
                logger.warning(f"검출 변환 중 오류: {e}")
                continue

        # 2. Bulk API로 한 번에 전송
        if bulk_detections:
            success, result, error = await self._post_api(
                f"/detection/{session_id}/import-bulk",
                json_data={"detections": bulk_detections},
                timeout=120
            )
            if success and result:
                logger.info(f"Bulk import 완료: {result.get('imported_count', 0)}/{len(bulk_detections)}개")
            else:
                logger.error(f"Bulk import 실패: {error}")
        else:
            logger.warning("가져올 검출 결과가 없습니다")

    async def _upload_gt_file(self, session_id: str, gt_file: dict, image_width: int, image_height: int):
        """Builder에서 첨부된 GT 파일을 BOM 세션에 업로드

        Args:
            session_id: BOM 세션 ID
            gt_file: {"name": "labels.txt", "content": "data:...;base64,..."}
            image_width: 이미지 너비
            image_height: 이미지 높이
        """
        import base64

        try:
            gt_name = gt_file.get("name", "labels.txt")
            gt_content = gt_file.get("content", "")

            if not gt_content:
                logger.warning("GT 파일 내용이 비어있습니다")
                return

            # Data URL 디코딩
            if "," in gt_content:
                gt_bytes = base64.b64decode(gt_content.split(",", 1)[1])
            else:
                gt_bytes = gt_content.encode("utf-8")

            # GT 파일 업로드 (filename은 세션의 이미지명과 매칭)
            success, _, error = await self._post_api(
                "/api/ground-truth/upload",
                files={"file": (gt_name, gt_bytes, "text/plain")},
                data={
                    "filename": "image",
                    "image_width": str(image_width),
                    "image_height": str(image_height),
                },
                timeout=30
            )
            if success:
                logger.info(f"GT 파일 업로드 완료: {gt_name} → 세션 {session_id}")
            else:
                logger.warning(f"GT 파일 업로드 실패: {error}")

        except Exception as e:
            logger.error(f"GT 파일 업로드 중 오류: {e}")

    async def _upload_pricing_file(self, session_id: str, pricing_file: dict):
        """Builder에서 첨부된 단가 파일을 BOM 세션에 업로드

        Args:
            session_id: BOM 세션 ID
            pricing_file: {"name": "pricing.json", "content": "data:...;base64,..."}
        """
        import base64

        try:
            name = pricing_file.get("name", "pricing.json")
            content = pricing_file.get("content", "")

            if not content:
                logger.warning("단가 파일 내용이 비어있습니다")
                return

            # Data URL 디코딩
            if "," in content:
                file_bytes = base64.b64decode(content.split(",", 1)[1])
            else:
                file_bytes = content.encode("utf-8")

            success, _, error = await self._post_api(
                f"/bom/{session_id}/pricing",
                files={"file": (name, file_bytes, "application/json")},
                timeout=30
            )
            if success:
                logger.info(f"단가 파일 업로드 완료: {name} → 세션 {session_id}")
            else:
                logger.warning(f"단가 파일 업로드 실패: {error}")

        except Exception as e:
            logger.error(f"단가 파일 업로드 중 오류: {e}")

    async def _import_tables(self, session_id: str, tables: list, regions: list = None):
        """Gateway Table Detector 결과를 BOM 세션의 table_results 필드에 저장

        Table Detector 출력 형식:
        tables: [{"headers": [...], "data": [[...]], "html": "...", "source_region": "title_block"}, ...]

        프론트엔드 기대 형식 (table_results):
        [{"table_id": "...", "rows": N, "cols": M, "cells": [{text, row, col}], "html": "..."}]
        """
        try:
            table_results = []

            for i, table in enumerate(tables):
                headers = table.get("headers", [])
                data = table.get("data", [])
                rows_count = len(data) + (1 if headers else 0)
                cols_count = len(headers) if headers else (len(data[0]) if data else 0)

                # headers + data → cells 배열 변환
                cells = []
                if headers:
                    for col_idx, header_text in enumerate(headers):
                        cells.append({"text": str(header_text), "row": 0, "col": col_idx})
                for row_idx, row_data in enumerate(data):
                    actual_row = row_idx + (1 if headers else 0)
                    if isinstance(row_data, list):
                        for col_idx, cell_text in enumerate(row_data):
                            cells.append({"text": str(cell_text), "row": actual_row, "col": col_idx})
                    elif isinstance(row_data, dict):
                        for col_idx, (_, cell_text) in enumerate(row_data.items()):
                            cells.append({"text": str(cell_text), "row": actual_row, "col": col_idx})

                table_results.append({
                    "table_id": f"gateway_table_{i}",
                    "rows": rows_count,
                    "cols": cols_count,
                    "cells": cells,
                    "headers": headers,
                    "html": table.get("html", ""),
                    "source_region": table.get("source_region", ""),
                    "confidence": table.get("confidence", 0.9),
                })

            if table_results:
                success, _, error = await self._patch_api(
                    f"/sessions/{session_id}",
                    json_data={"table_results": table_results},
                    timeout=30
                )
                if success:
                    logger.info(f"테이블 import 완료: {len(table_results)}개 테이블 → table_results")
                else:
                    logger.warning(f"테이블 import 실패: {error}")
        except Exception as e:
            logger.warning(f"테이블 import 중 오류 (무시): {e}")

    async def _import_dimensions(self, session_id: str, dimensions: list):
        """eDOCr2 치수 결과를 Blueprint AI BOM 세션에 가져오기

        eDOCr2 노드의 출력 형식:
        {
            "text": "100mm",
            "bbox": {"x1": 100, "y1": 200, "x2": 300, "y2": 250},
            "confidence": 0.95,
            "type": "length",
            ...
        }
        """
        if not dimensions:
            logger.warning("가져올 치수 결과가 없습니다")
            return

        success, result, error = await self._post_api(
            f"/analysis/dimensions/{session_id}/import-bulk",
            json_data={
                "dimensions": dimensions,
                "source": "edocr2",
                "auto_approve_threshold": None  # 자동 승인 비활성화 - 검증 UI에서 확인
            },
            timeout=120
        )
        if success and result:
            logger.info(f"치수 import 완료: {result.get('imported_count', 0)}개")
        else:
            logger.error(f"치수 import 실패: {error}")


# 실행기 등록
ExecutorRegistry.register("blueprint-ai-bom", BOMExecutor)
